from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, ValidationError
from app.models import User, Department, Programme, Campus

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

class UserCreationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    full_name = StringField('Full Name', validators=[DataRequired()])
    role = SelectField('Role', choices=[
        ('student', 'Student'),
        ('lecturer', 'Lecturer'),
        ('qa_officer', 'QA Officer'),
        ('admin', 'Administrator')
    ])
    campus_id = SelectField('Campus', coerce=int, validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Create User')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered.')

class EditUserForm(FlaskForm):
    username = StringField('Username', render_kw={'readonly': True})
    email = StringField('Email', validators=[DataRequired(), Email()])
    full_name = StringField('Full Name', validators=[DataRequired()])
    role = SelectField('Role', choices=[
        ('student', 'Student'),
        ('lecturer', 'Lecturer'),
        ('qa_officer', 'QA Officer'),
        ('admin', 'Administrator')
    ])
    campus_id = SelectField('Campus', coerce=int)
    password = PasswordField('New Password (leave blank to keep current)')
    submit = SubmitField('Update User')

    def __init__(self, original_username, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user and user.username != self.original_username:
            raise ValidationError('Email already in use.')

class CampusForm(FlaskForm):
    name = StringField('Campus Name', validators=[DataRequired()])
    location = StringField('Location (City/Town)')
    submit = SubmitField('Save')

    def validate_name(self, name):
        """Reject duplicate campus names."""
        campus = Campus.query.filter_by(name=name.data).first()
        if campus:
            raise ValidationError('A campus with this name already exists.')

class DepartmentForm(FlaskForm):
    name = StringField('Department Name', validators=[DataRequired()])
    submit = SubmitField('Save')

class ProgrammeForm(FlaskForm):
    name = StringField('Programme Name', validators=[DataRequired()])
    department_id = SelectField('Department', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save')

class CourseForm(FlaskForm):
    code = StringField('Course Code', validators=[DataRequired()])
    name = StringField('Course Name', validators=[DataRequired()])
    campus_id = SelectField('Campus', coerce=int, validators=[DataRequired()])
    course_type = SelectField('Course Type', choices=[('long', 'Long Course'), ('short', 'Short Course')])
    department_id = SelectField('Department', coerce=int)
    programme_id = SelectField('Programme', coerce=int)
    level = SelectField('Level', choices=[
        ('', '-- Not applicable --'),
        ('NTA Level 4', 'NTA Level 4'),
        ('NTA Level 5', 'NTA Level 5'),
        ('NTA Level 6', 'NTA Level 6'),
        ('Certificate', 'Certificate'),
        ('Diploma', 'Diploma'),
        ('Degree', 'Degree')
    ])
    semester = SelectField('Semester', choices=[
        ('', '-- Not applicable --'),
        ('Semester 1', 'Semester 1'),
        ('Semester 2', 'Semester 2')
    ])
    academic_year = StringField('Academic Year (e.g., 2025/2026)')
    lecturer_id = SelectField('Lecturer', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save Course')

class FormBuilderForm(FlaskForm):
    title = StringField('Form Title', validators=[DataRequired()])
    description = TextAreaField('Description')
    target_level = SelectField('Target Level (Optional)', choices=[
        ('', 'All Levels'),
        ('Certificate', 'Certificate'),
        ('Diploma', 'Diploma'),
        ('Degree', 'Degree')
    ])
    submit = SubmitField('Create Form')

class FormSettingsForm(FlaskForm):
    show_progress = SelectField('Show progress bar', choices=[('1', 'Yes'), ('0', 'No')], coerce=int)
    deadline = StringField('Deadline (optional, format: YYYY-MM-DD HH:MM)')
    submit = SubmitField('Save Settings')