from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import DecimalField, StringField, PasswordField, SubmitField, FloatField, SearchField, RadioField
from wtforms.validators import DataRequired, InputRequired, Email, EqualTo, ValidationError, NumberRange, Length
from models import User


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(),
                                       Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password',
                             validators=[DataRequired(),
                                         Length(min=8)])
    confirm_password = PasswordField(
        'Confirm Password', validators=[DataRequired(),
                                        EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError(
                'Username already taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError(
                'Email already registered. Please use a different one.')


class CSVUploadForm(FlaskForm):
    csv_file = FileField('Upload CSV/TSV File',
                         validators=[
                             FileRequired(),
                             FileAllowed(['csv', 'tsv', 'txt'],
                                         'CSV, TSV, or TXT files only!')
                         ])
    submit = SubmitField('Upload')


class AssessmentForm(FlaskForm):
    score_period_string = RadioField(
        'Score for Period (string)',
        choices=[('0', '0'), ('0.5', '0.5'), ('1', '1')],
        validators=[InputRequired(message='Please select a score')]
    )
    score_period_timeframe = RadioField(
        'Score for Period (time interval)',
        choices=[('0', '0'), ('0.5', '0.5'), ('1', '1')],
        validators=[InputRequired(message='Please select a score')]
    )
    score_location_string = RadioField(
        'Score for Location (string)',
        choices=[('0', '0'), ('0.5', '0.5'), ('1', '1')],
        validators=[InputRequired(message='Please select a score')]
    )
    score_location_qid = RadioField(
        'Score for Location (QID)',
        choices=[('0', '0'), ('0.5', '0.5'), ('1', '1')],
        validators=[InputRequired(message='Please select a score')]
    )
    submit = SubmitField('Submit Assessment')


class SearchForm(FlaskForm):
    query = SearchField('Search responses', validators=[DataRequired()])
    submit = SubmitField('Search')


class ExportForm(FlaskForm):
    submit = SubmitField('Export to TSV')
