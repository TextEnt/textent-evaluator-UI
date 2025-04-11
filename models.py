from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    assessments = db.relationship('Assessment', backref='reviewer', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class CSVFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_responses = db.Column(db.Integer, default=0)
    assessed_responses = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<CSVFile {self.filename}>'


class Response(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    response_id = db.Column(db.String(255), nullable=False)
    prompt_id = db.Column(db.String(255), nullable=True)
    model_name = db.Column(db.String(255), nullable=True)
    model_id = db.Column(db.String(255), nullable=True)  # Keep for backward compatibility
    document_id = db.Column(db.String(255), nullable=True)
    author = db.Column(db.String(255), nullable=True)
    title = db.Column(db.String(255), nullable=True)
    publication_date = db.Column(db.String(255), nullable=True)
    document_length = db.Column(db.Integer, nullable=True)
    keep_fine_tuning = db.Column(db.Boolean, nullable=True)

    # Ground truth and predictions - Time/Period
    gt_period = db.Column(db.String(255), nullable=True)
    pred_period = db.Column(db.String(255), nullable=True)
    score_period_string = db.Column(db.String(255), nullable=True)
    gt_timeframe = db.Column(db.String(255), nullable=True)
    pred_timeframe = db.Column(db.String(255), nullable=True)
    score_period_timeframe = db.Column(db.String(255), nullable=True)
    gt_period_reason = db.Column(db.Text, nullable=True)
    gt_period_reasoning = db.Column(db.Text, nullable=True)
    pred_period_reasoning = db.Column(db.Text, nullable=True)
    score_period_reasoning = db.Column(db.String(255), nullable=True)

    # Ground truth and predictions - Location
    # New/renamed columns
    gt_preferred_location = db.Column(db.String(255), nullable=True)
    gt_accepted_locations = db.Column(db.Text, nullable=True)  # New column
    gt_preferred_location_QID = db.Column(db.String(255), nullable=True)
    gt_acceptable_location_QIDs = db.Column(db.Text, nullable=True)  # New column
    
    # Keep old columns for backward compatibility
    gt_location = db.Column(db.String(255), nullable=True)
    gt_location_QID = db.Column(db.String(255), nullable=True)
    
    # Unchanged columns
    pred_location = db.Column(db.String(255), nullable=True)
    score_location_string = db.Column(db.String(255), nullable=True)
    pred_location_qid = db.Column(db.String(255), nullable=True)
    score_location_qid = db.Column(db.String(255), nullable=True)
    gt_location_reason = db.Column(db.Text, nullable=True)
    pred_location_reasoning = db.Column(db.Text, nullable=True)
    score_location_reasoning = db.Column(db.String(255), nullable=True)

    # CSV file reference
    csv_file_id = db.Column(db.Integer,
                            db.ForeignKey('csv_file.id'),
                            nullable=False)
    csv_file = db.relationship('CSVFile',
                               backref=db.backref('responses', lazy=True))

    # Assessment relationship
    assessment = db.relationship('Assessment',
                                 backref='response',
                                 uselist=False)

    def __repr__(self):
        return f'<Response {self.response_id}>'


class Assessment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    response_id = db.Column(db.Integer,
                            db.ForeignKey('response.id'),
                            nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score_period_string = db.Column(db.Float, nullable=True)
    score_period_timeframe = db.Column(db.Float, nullable=True)
    score_location_string = db.Column(db.Float, nullable=True)
    score_location_qid = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime,
                           default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Assessment for response {self.response_id}>'
