import os
import pandas as pd
import csv
import json
from io import StringIO
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
from app import db
from models import CSVFile, Response, Assessment

# CSV validation settings
REQUIRED_HEADERS = [
]  # No required headers - we'll auto-generate IDs if needed
RECOMMENDED_HEADERS = [
    'response_id',
    'prompt_id',
    'model_name',  # New field name
    'model_id',    # Keep for backward compatibility
    'document_id',
    'author',
    'title',
    'publication_date',
    'document_length',
    'keep_fine_tuning',

    # Time/Period fields
    'gt_period',
    'pred_period',
    'score_period_string',
    'gt_timeframe',
    'pred_timeframe',
    'score_period_timeframe',
    'gt_period_reason',
    'gt_period_reasoning',
    'pred_period_reasoning',
    'score_period_reasoning',

    # Location fields
    'gt_preferred_location',     # renamed from gt_location
    'gt_accepted_locations',     # new field
    'pred_location',
    'score_location_string',
    'gt_preferred_location_QID', # renamed from gt_location_QID
    'gt_acceptable_location_QIDs', # new field
    'pred_location_qid',
    'score_location_qid',
    'gt_location_reason',
    'pred_location_reasoning',
    'score_location_reasoning',
    
    # Keep old names for backward compatibility
    'gt_location',
    'gt_location_QID'
]


def validate_csv(file_storage):
    """
    Validate that the uploaded CSV/TSV has valid format
    """
    try:
        # Convert the FileStorage to a string buffer
        stream = StringIO(file_storage.stream.read().decode('utf-8'),
                          newline=None)
        file_storage.stream.seek(0)  # Rewind the file pointer for later use

        # Check file extension to determine delimiter
        filename = file_storage.filename.lower()
        is_tsv = filename.endswith('.tsv') or filename.endswith('.txt')
        delimiter = '\t' if is_tsv else ','

        # Try to read the file headers
        reader = csv.reader(stream, delimiter=delimiter)
        try:
            headers = next(reader)
        except StopIteration:
            return False, f"{'TSV' if is_tsv else 'CSV'} file appears to be empty"

        if not headers:
            return False, f"{'TSV' if is_tsv else 'CSV'} file has no headers"

        # Check if response_id is present
        has_response_id = 'response_id' in headers

        # Check which recommended headers are missing
        missing_recommended = [
            header for header in RECOMMENDED_HEADERS if header not in headers
        ]

        # Determine file type for messages
        file_type = 'TSV' if is_tsv else 'CSV'

        success_message = f"{file_type} file is valid"

        # If response_id is missing, inform user IDs will be auto-generated
        if not has_response_id:
            success_message += ". Note: 'response_id' column is missing; IDs will be auto-generated."

        # Mention other missing recommended fields
        other_missing = [h for h in missing_recommended if h != 'response_id']
        if other_missing:
            success_message += f" Some recommended columns are missing: {', '.join(other_missing[:5])}"
            if len(other_missing) > 5:
                success_message += f" and {len(other_missing) - 5} more"

        return True, success_message
    except Exception as e:
        return False, f"Error validating CSV: {str(e)}"


def process_csv(file_storage, user_id):
    """
    Process and save CSV file data to the database
    """
    try:
        # Validate CSV
        is_valid, message = validate_csv(file_storage)
        if not is_valid:
            return False, message

        # Check file extension to determine delimiter
        filename = file_storage.filename.lower()
        is_tsv = filename.endswith('.tsv') or filename.endswith('.txt')
        delimiter = '\t' if is_tsv else ','

        # Reset file pointer and read with pandas using appropriate delimiter
        file_storage.stream.seek(0)
        df = pd.read_csv(file_storage.stream, delimiter=delimiter)

        # Create CSV file record
        csv_file = CSVFile(filename=file_storage.filename,
                           user_id=user_id,
                           total_responses=len(df))
        db.session.add(csv_file)
        db.session.flush()  # Get the ID without committing

        # Process each row
        for idx, row in df.iterrows():
            # Check if we have a response_id column
            if 'response_id' in df.columns:
                # Use the existing response_id or generate one if cell is empty/null
                response_id = row['response_id'] if pd.notna(
                    row['response_id']) else f'auto_gen_{idx}'
            else:
                # No response_id column exists, generate one
                response_id = f'auto_gen_{idx}'

            response = Response(
                response_id=response_id,
                prompt_id=row.get('prompt_id'),
                model_name=row.get('model_name') or row.get('model_id'),
                model_id=row.get('model_id') or row.get('model_name'),
                document_id=row.get('document_id'),
                author=row.get('author'),
                title=row.get('title'),
                publication_date=row.get('publication_date'),
                document_length=row.get('document_length'),
                keep_fine_tuning=row.get('keep_fine_tuning'),

                # Time/Period fields
                gt_period=row.get('gt_period'),
                pred_period=row.get('pred_period'),
                score_period_string=row.get('score_period_string'),
                gt_timeframe=row.get('gt_timeframe'),
                pred_timeframe=row.get('pred_timeframe'),
                score_period_timeframe=row.get('score_period_timeframe'),
                gt_period_reason=row.get('gt_period_reason'),
                gt_period_reasoning=row.get('gt_period_reasoning'),
                pred_period_reasoning=row.get('pred_period_reasoning'),
                score_period_reasoning=row.get('score_period_reasoning'),

                # Location fields with new/renamed columns
                # Handle renamed columns with backward compatibility
                gt_preferred_location=row.get('gt_preferred_location') or row.get('gt_location'),
                gt_accepted_locations=row.get('gt_accepted_locations'),
                gt_preferred_location_QID=row.get('gt_preferred_location_QID') or row.get('gt_location_QID'),
                gt_acceptable_location_QIDs=row.get('gt_acceptable_location_QIDs'),
                
                # Keep old column values for backward compatibility
                gt_location=row.get('gt_location') or row.get('gt_preferred_location'),
                gt_location_QID=row.get('gt_location_QID') or row.get('gt_preferred_location_QID'),
                
                # Unchanged fields
                pred_location=row.get('pred_location'),
                score_location_string=row.get('score_location_string'),
                pred_location_qid=row.get('pred_location_qid'),
                score_location_qid=row.get('score_location_qid'),
                gt_location_reason=row.get('gt_location_reason'),
                pred_location_reasoning=row.get('pred_location_reasoning'),
                score_location_reasoning=row.get('score_location_reasoning'),
                csv_file_id=csv_file.id)
            db.session.add(response)

        db.session.commit()
        return True, f"Successfully processed {len(df)} responses"

    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error: {str(e)}")
        return False, f"Database error: {str(e)}"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error processing file: {str(e)}")
        return False, f"Error processing file: {str(e)}"


def get_assessment_criteria():
    """
    Load assessment criteria from config file
    """
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            return config.get('assessment_criteria', {})
    except Exception as e:
        current_app.logger.error(
            f"Error loading assessment criteria: {str(e)}")
        return {
            "time": "Assess accuracy of predicted time period (0-1)",
            "space": "Assess accuracy of predicted location (0-1)"
        }


def search_responses(query, user_id):
    """
    Search responses by author, title, or text
    """
    search_term = f"%{query}%"
    return Response.query.join(CSVFile).filter(
        CSVFile.user_id == user_id,
        (Response.author.ilike(search_term) | Response.title.ilike(search_term)
         | Response.response_id.ilike(search_term)
         | Response.document_id.ilike(search_term)
         | Response.model_name.ilike(search_term)
         | Response.model_id.ilike(search_term)
         | Response.prompt_id.ilike(search_term)
         | Response.gt_period.ilike(search_term)
         | Response.pred_period.ilike(search_term)
         | Response.gt_timeframe.ilike(search_term)
         | Response.pred_timeframe.ilike(search_term)
         | Response.gt_preferred_location.ilike(search_term)
         | Response.gt_accepted_locations.ilike(search_term)
         | Response.gt_preferred_location_QID.ilike(search_term)
         | Response.gt_acceptable_location_QIDs.ilike(search_term)
         | Response.gt_location.ilike(search_term)
         | Response.pred_location.ilike(search_term))).all()


def calculate_average_scores(user_id, csv_file_id):
    """
    Calculate separate average scores for time period (string), time period (interval),
    location (string), and location (QID)
    """
    assessments = Assessment.query.join(Response).join(CSVFile).filter(
        CSVFile.id == csv_file_id, Assessment.user_id == user_id).all()

    if not assessments:
        return {
            "period_string": 0, 
            "period_timeframe": 0, 
            "location_string": 0, 
            "location_qid": 0, 
            "count": 0
        }

    # Collect each type of score separately
    period_string_scores = [
        a.score_period_string for a in assessments
        if a.score_period_string is not None
    ]
    
    period_timeframe_scores = [
        a.score_period_timeframe for a in assessments
        if a.score_period_timeframe is not None
    ]
    
    location_string_scores = [
        a.score_location_string for a in assessments
        if a.score_location_string is not None
    ]
    
    location_qid_scores = [
        a.score_location_qid for a in assessments
        if a.score_location_qid is not None
    ]

    # Calculate averages for each type
    avg_period_string = sum(period_string_scores) / len(period_string_scores) if period_string_scores else 0
    avg_period_timeframe = sum(period_timeframe_scores) / len(period_timeframe_scores) if period_timeframe_scores else 0
    avg_location_string = sum(location_string_scores) / len(location_string_scores) if location_string_scores else 0
    avg_location_qid = sum(location_qid_scores) / len(location_qid_scores) if location_qid_scores else 0

    return {
        "period_string": round(avg_period_string, 2),
        "period_timeframe": round(avg_period_timeframe, 2),
        "location_string": round(avg_location_string, 2),
        "location_qid": round(avg_location_qid, 2),
        # Keep these for backward compatibility
        "time": round(avg_period_string, 2),
        "space": round(avg_location_string, 2),
        "count": len(assessments)
    }


def export_results_to_csv(user_id, csv_file_id):
    """
    Export assessment results to CSV or TSV based on original file format
    """
    try:
        # Get all responses with assessments
        responses = Response.query.join(CSVFile).filter(
            CSVFile.id == csv_file_id, CSVFile.user_id == user_id).all()

        # Prepare data for export
        export_data = []
        for response in responses:
            row = {
                # Basic response info
                "response_id":
                response.response_id,
                "prompt_id":
                response.prompt_id,
                "model_name":
                response.model_name,
                "model_id":
                response.model_id,
                "document_id":
                response.document_id,
                "author":
                response.author,
                "title":
                response.title,
                "publication_date":
                response.publication_date,

                # Period/time info
                "gt_period":
                response.gt_period,
                "pred_period":
                response.pred_period,
                "score_period_string":
                response.score_period_string,
                "gt_timeframe":
                response.gt_timeframe,
                "pred_timeframe":
                response.pred_timeframe,
                "score_period_timeframe":
                response.score_period_timeframe,

                # Location info with new fields
                "gt_preferred_location":
                response.gt_preferred_location,
                "gt_accepted_locations":
                response.gt_accepted_locations,
                "pred_location":
                response.pred_location,
                "score_location_string":
                response.score_location_string,
                "gt_preferred_location_QID":
                response.gt_preferred_location_QID,
                "gt_acceptable_location_QIDs":
                response.gt_acceptable_location_QIDs,
                "pred_location_qid":
                response.pred_location_qid,
                "score_location_qid":
                response.score_location_qid,
                
                # Include old field names for backward compatibility
                "gt_location":
                response.gt_location,
                "gt_location_QID":
                response.gt_location_QID,

                # Manual assessment scores
                "period_string_score":
                response.assessment.score_period_string
                if response.assessment else None,
                "period_timeframe_score":
                response.assessment.score_period_timeframe
                if response.assessment else None,
                "location_string_score":
                response.assessment.score_location_string
                if response.assessment else None,
                "location_qid_score":
                response.assessment.score_location_qid
                if response.assessment else None,
                "assessment_date":
                response.assessment.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                if response.assessment else None
            }
            export_data.append(row)

        # Always use TSV format with tab separator
        delimiter = '\t'

        # Convert to DataFrame and export
        df = pd.DataFrame(export_data)
        output = StringIO()
        df.to_csv(output, index=False, sep=delimiter)

        return output.getvalue()

    except Exception as e:
        current_app.logger.error(f"Error exporting results: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return None
