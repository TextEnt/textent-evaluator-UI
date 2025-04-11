from flask import render_template, redirect, url_for, flash, request, jsonify, session, send_file, current_app
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from io import StringIO, BytesIO
import json
import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

from app import app, db
from forms import LoginForm, RegistrationForm, CSVUploadForm, AssessmentForm, SearchForm, ExportForm
from models import User, CSVFile, Response, Assessment
from utils import (validate_csv, process_csv, get_assessment_criteria,
                   search_responses, calculate_average_scores,
                   export_results_to_csv)


# Make datetime available to all templates
@app.context_processor
def inject_datetime():
    return dict(datetime=datetime)


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
        login_user(user)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('dashboard')
        flash('Login successful!', 'success')
        return redirect(next_page)

    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    upload_form = CSVUploadForm()
    search_form = SearchForm()

    csv_files = CSVFile.query.filter_by(user_id=current_user.id).order_by(
        CSVFile.upload_date.desc()).all()

    # Handle CSV upload
    if upload_form.validate_on_submit():
        success, message = process_csv(upload_form.csv_file.data,
                                       current_user.id)
        if success:
            flash(message, 'success')
            return redirect(url_for('dashboard'))
        else:
            flash(message, 'danger')

    # Calculate stats for each file
    file_stats = []
    for csv_file in csv_files:
        avg_scores = calculate_average_scores(current_user.id, csv_file.id)
        file_stats.append({'file': csv_file, 'avg_scores': avg_scores})

    return render_template('dashboard.html',
                           upload_form=upload_form,
                           search_form=search_form,
                           file_stats=file_stats)


@app.route('/assessment/<int:file_id>', methods=['GET'])
@login_required
def assessment(file_id):
    csv_file = CSVFile.query.filter_by(id=file_id,
                                       user_id=current_user.id).first_or_404()

    # Get response ID from query params or session, or get the first unassessed response
    response_id = request.args.get('response_id')
    next_unassessed = request.args.get('next_unassessed', type=bool)
    
    logging.debug(f"Assessment route called with file_id={file_id}, response_id={response_id}, next_unassessed={next_unassessed}")
    
    if next_unassessed:
        # Always get the first unassessed response when next_unassessed is True (from dashboard)
        logging.debug("Looking for first unassessed response (from dashboard)")
        unassessed = Response.query.filter_by(csv_file_id=file_id)\
            .outerjoin(Assessment, (Assessment.response_id == Response.id) & (Assessment.user_id == current_user.id))\
            .filter(Assessment.id == None)\
            .first()

        if unassessed:
            logging.debug(f"Found unassessed response with ID: {unassessed.id}")
            response_id = unassessed.id
        else:
            logging.debug("No unassessed responses found, getting first response")
            first_response = Response.query.filter_by(
                csv_file_id=file_id).first()
            if first_response:
                response_id = first_response.id
    elif not response_id:
        # Try to get from session if no specific response_id is provided
        response_id = session.get(f'last_response_{file_id}')
        logging.debug(f"Retrieved response_id={response_id} from session")

        if not response_id:
            # Get first unassessed response as fallback
            logging.debug("No response ID in session, looking for first unassessed")
            unassessed = Response.query.filter_by(csv_file_id=file_id)\
                .outerjoin(Assessment, (Assessment.response_id == Response.id) & (Assessment.user_id == current_user.id))\
                .filter(Assessment.id == None)\
                .first()

            if unassessed:
                logging.debug(f"Found unassessed response with ID: {unassessed.id}")
                response_id = unassessed.id
            else:
                # If all are assessed, get the first response
                logging.debug("No unassessed responses found, getting first response")
                first_response = Response.query.filter_by(
                    csv_file_id=file_id).first()
                if first_response:
                    response_id = first_response.id

    if not response_id:
        flash('No responses found in this file.', 'warning')
        return redirect(url_for('dashboard'))

    # Store the current response ID in session
    session[f'last_response_{file_id}'] = response_id

    response = Response.query.filter_by(id=response_id,
                                        csv_file_id=file_id).first_or_404()

    # Get the assessment if it exists
    assessment = Assessment.query.filter_by(response_id=response.id,
                                            user_id=current_user.id).first()

    # Create a form with existing data if available
    form = AssessmentForm()
    if assessment:
        form.score_period_string.data = assessment.score_period_string
        form.score_period_timeframe.data = assessment.score_period_timeframe
        form.score_location_string.data = assessment.score_location_string
        form.score_location_qid.data = assessment.score_location_qid

    # Get assessment criteria for tooltips
    criteria = get_assessment_criteria()

    # Get navigation data (next/prev, progress)
    total_responses = Response.query.filter_by(csv_file_id=file_id).count()
    assessed_count = Assessment.query.join(Response).filter(
        Response.csv_file_id == file_id,
        Assessment.user_id == current_user.id).count()

    # Get the current index of this response
    all_responses = Response.query.filter_by(csv_file_id=file_id).all()
    response_ids = [r.id for r in all_responses]
    logging.debug(f"All response IDs: {response_ids}")
    logging.debug(f"Current response ID: {response.id}")
    
    current_index = response_ids.index(
        response.id) if response.id in response_ids else 0
    logging.debug(f"Current index: {current_index}")

    # Calculate next and previous response IDs
    prev_id = response_ids[current_index - 1] if current_index > 0 else None
    next_id = response_ids[
        current_index + 1] if current_index < len(response_ids) - 1 else None
    logging.debug(f"Previous ID: {prev_id}, Next ID: {next_id}")

    # Get average scores
    avg_scores = calculate_average_scores(current_user.id, file_id)

    export_form = ExportForm()

    return render_template('assessment.html',
                           form=form,
                           export_form=export_form,
                           response=response,
                           file_id=file_id,
                           criteria=criteria,
                           total_responses=total_responses,
                           assessed_count=assessed_count,
                           prev_id=prev_id,
                           next_id=next_id,
                           current_index=current_index + 1,
                           avg_scores=avg_scores)


@app.route('/submit_assessment/<int:file_id>/<int:response_id>',
           methods=['POST'])
@login_required
def submit_assessment(file_id, response_id):
    form = AssessmentForm()

    if form.validate_on_submit():

        # Check if response belongs to the file and user has access
        response = Response.query.join(CSVFile).filter(
            Response.id == response_id, Response.csv_file_id == file_id,
            CSVFile.user_id == current_user.id).first_or_404()

        # Check if assessment already exists
        assessment = Assessment.query.filter_by(
            response_id=response_id, user_id=current_user.id).first()

        if assessment:
            # Update existing assessment
            assessment.score_period_string = float(form.score_period_string.data)
            assessment.score_period_timeframe = float(form.score_period_timeframe.data)
            assessment.score_location_string = float(form.score_location_string.data)
            assessment.score_location_qid = float(form.score_location_qid.data)
            #assessment.score_space = form.score_space.data
            assessment.updated_at = datetime.datetime.utcnow()
            flash('Assessment updated successfully!', 'success')
        else:
            # Create new assessment
            assessment = Assessment(
                response_id=response_id,
                user_id=current_user.id,
                score_period_string=float(form.score_period_string.data),
                score_period_timeframe=float(form.score_period_timeframe.data),
                score_location_string=float(form.score_location_string.data),
                score_location_qid=float(form.score_location_qid.data),
            )
            db.session.add(assessment)
            flash('Assessment submitted successfully!', 'success')

            # Update the assessed count for the CSV file
            csv_file = CSVFile.query.get(file_id)
            csv_file.assessed_responses = Assessment.query.join(
                Response).filter(
                    Response.csv_file_id == file_id,
                    Assessment.user_id == current_user.id).count()

        db.session.commit()

        # Check if all responses have been assessed
        total_responses = Response.query.filter_by(csv_file_id=file_id).count()
        assessed_count = Assessment.query.join(Response).filter(
            Response.csv_file_id == file_id,
            Assessment.user_id == current_user.id).count()
        
        logging.debug(f"Total responses: {total_responses}, Assessed count: {assessed_count}")
        
        if assessed_count >= total_responses:
            # All responses have been assessed
            flash('🎉 Congratulations! You have assessed all responses for this file. (100% complete)', 'success')
            return redirect(url_for('dashboard'))
            
        # Get next unassessed response
        unassessed = Response.query.filter_by(csv_file_id=file_id)\
            .outerjoin(Assessment, (Assessment.response_id == Response.id) & (Assessment.user_id == current_user.id))\
            .filter(Assessment.id == None)\
            .first()
            
        if unassessed:
            logging.debug(f"Redirecting to next unassessed response: {unassessed.id}")
            return redirect(
                url_for('assessment',
                        file_id=file_id,
                        response_id=unassessed.id))
        else:
            # If all are assessed (double-check), redirect to dashboard with success message
            flash('🎉 Great job! You have assessed all responses for this file.', 'success')
            return redirect(url_for('dashboard'))

    for field, errors in form.errors.items():
        for error in errors:
            flash(f"{field}: {error}", 'danger')

    return redirect(
        url_for('assessment', file_id=file_id, response_id=response_id))


@app.route('/search', methods=['POST'])
@login_required
def search():
    form = SearchForm()
    if form.validate_on_submit():
        query = form.query.data
        results = search_responses(query, current_user.id)

        # Group results by CSV file
        grouped_results = {}
        for response in results:
            file_id = response.csv_file_id
            if file_id not in grouped_results:
                grouped_results[file_id] = {
                    'file': response.csv_file,
                    'responses': []
                }
            grouped_results[file_id]['responses'].append(response)

        return render_template('dashboard.html',
                               upload_form=CSVUploadForm(),
                               search_form=form,
                               search_results=grouped_results)

    flash('Invalid search query', 'danger')
    return redirect(url_for('dashboard'))


@app.route('/export/<int:file_id>', methods=['POST'])
@login_required
def export(file_id):
    logging.debug(f"Export route called for file_id={file_id}")
    form = ExportForm()
    if form.validate_on_submit():
        logging.debug("Export form validated")
        csv_data = export_results_to_csv(current_user.id, file_id)
        logging.debug(f"CSV data returned: {bool(csv_data)}")
        if csv_data:
            # Create a response with TSV data
            csv_file = CSVFile.query.get_or_404(file_id)
            now = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f"assessment_results_{csv_file.filename.split('.')[0]}_{now}.tsv"

            # Convert string data to bytes for BytesIO
            try:
                logging.debug(f"Converting CSV data to bytes (length: {len(csv_data)})")
                output = BytesIO()
                output.write(csv_data.encode('utf-8'))
                output.seek(0)
                logging.debug("BytesIO conversion successful")
            except Exception as e:
                logging.error(f"Error converting to BytesIO: {str(e)}")
                import traceback
                logging.error(traceback.format_exc())
                flash(f'Error preparing export file: {str(e)}', 'danger')
                return redirect(url_for('assessment', file_id=file_id))
            
            return send_file(output,
                             mimetype='text/tab-separated-values',
                             as_attachment=True,
                             download_name=filename)
        else:
            flash('Error generating export file', 'danger')

    return redirect(url_for('assessment', file_id=file_id))


@app.route('/delete_file/<int:file_id>', methods=['POST'])
@login_required
def delete_file(file_id):
    """Delete a CSV file and all associated responses and assessments"""
    # Ensure the user owns this file
    csv_file = CSVFile.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
    
    try:
        # Get all responses for this file
        responses = Response.query.filter_by(csv_file_id=file_id).all()
        
        # Delete all associated assessments first
        for response in responses:
            assessments = Assessment.query.filter_by(response_id=response.id).all()
            for assessment in assessments:
                db.session.delete(assessment)
        
        # Delete all responses
        for response in responses:
            db.session.delete(response)
        
        # Delete the file record
        db.session.delete(csv_file)
        db.session.commit()
        
        flash(f'Job "{csv_file.filename}" and all associated data deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting file: {str(e)}")
        flash(f'Error deleting file: {str(e)}', 'danger')
    
    return redirect(url_for('dashboard'))


@app.route('/responses/<int:file_id>', methods=['GET'])
@login_required
def get_responses(file_id):
    """Get all responses for a file for client-side navigation"""
    # Check user has access to this file
    csv_file = CSVFile.query.filter_by(id=file_id,
                                     user_id=current_user.id).first_or_404()
    
    # Get all responses for this file
    responses = Response.query.filter_by(csv_file_id=file_id).all()
    
    # Convert to JSON-serializable format
    response_data = [{'id': r.id, 'author': r.author, 'title': r.title} for r in responses]
    
    return jsonify(response_data)
