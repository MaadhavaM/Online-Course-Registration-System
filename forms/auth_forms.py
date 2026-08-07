from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Regexp
from database.db import get_db

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class StudentRegistrationForm(FlaskForm):
    student_id = StringField('Student ID', validators=[DataRequired(), Length(min=8, max=8), Regexp(r'^\d{8}$', message="Student ID must be exactly 8 digits.")])
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100), Regexp(r'^[A-Za-z\s]+$', message="Name must contain only alphabets and spaces.")])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[DataRequired(), Length(min=10, max=15), Regexp(r'^\d+$', message="Phone number must contain only digits.")])
    department = SelectField('Department', coerce=str, validators=[DataRequired()])
    semester = SelectField('Semester', choices=[('', 'Select Semester')] + [(str(i), f'Semester {i}') for i in range(1, 9)], validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8), Regexp(r'^(?=.*[a-zA-Z])(?=.*\d)(?=.*[\W_]).+$', message="Password must be at least 8 characters and include alphabets, numbers, and special characters.")])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register Student')

    def __init__(self, *args, **kwargs):
        super(StudentRegistrationForm, self).__init__(*args, **kwargs)
        db = get_db()
        if db is not None:
            self.department.choices = [('', 'Select Department')] + [(dept['name'], dept['name']) for dept in db.departments.find()]
        else:
            self.department.choices = [('', 'Select Department')]

    def validate_email(self, email):
        db = get_db()
        if db is not None and db.students.find_one({"email": email.data}):
            raise ValidationError('That email is already registered. Please choose a different one.')

    def validate_student_id(self, student_id):
        db = get_db()
        if db is not None and db.students.find_one({"student_id": student_id.data}):
            raise ValidationError('That Student ID is already registered. Please choose a different one.')

class AdminRegistrationForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100), Regexp(r'^[A-Za-z\s]+$', message="Name must contain only alphabets and spaces.")])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[DataRequired(), Length(min=10, max=15), Regexp(r'^\d+$', message="Phone number must contain only digits.")])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8), Regexp(r'^(?=.*[a-zA-Z])(?=.*\d)(?=.*[\W_]).+$', message="Password must be at least 8 characters and include alphabets, numbers, and special characters.")])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register Admin')

    def validate_email(self, email):
        db = get_db()
        if db is not None and db.admins.find_one({"email": email.data}):
            raise ValidationError('That email is already registered as an Admin. Please choose a different one.')

class ForgotPasswordForm(FlaskForm):
    role = SelectField('Role', choices=[('student', 'Student'), ('instructor', 'Instructor'), ('admin', 'Admin')], validators=[DataRequired()])
    phone = StringField('Registered Phone Number', validators=[DataRequired(), Length(min=10, max=15), Regexp(r'^\d+$', message="Phone number must contain only digits.")])
    submit = SubmitField('Send OTP')

class VerifyOTPForm(FlaskForm):
    otp = StringField('Enter 6-Digit OTP', validators=[DataRequired(), Length(min=6, max=6), Regexp(r'^\d+$', message="OTP must contain only digits.")])
    submit = SubmitField('Verify OTP')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=8), Regexp(r'^(?=.*[a-zA-Z])(?=.*\d)(?=.*[\W_]).+$', message="Password must be at least 8 characters and include alphabets, numbers, and special characters.")])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match.')])
    submit = SubmitField('Reset Password')

class LoginVerifyOTPForm(FlaskForm):
    otp = StringField('Enter 6-Digit OTP', validators=[DataRequired(), Length(min=6, max=6), Regexp(r'^\d+$', message="OTP must contain only digits.")])
    submit = SubmitField('Verify Login')

class StudentUpdateProfileForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100), Regexp(r'^[A-Za-z\s]+$', message="Name must contain only alphabets and spaces.")])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[DataRequired(), Length(min=10, max=15), Regexp(r'^\d+$', message="Phone number must contain only digits.")])
    department = SelectField('Department', coerce=str, validators=[DataRequired()])
    semester = SelectField('Semester', choices=[('', 'Select Semester')] + [(str(i), f'Semester {i}') for i in range(1, 9)], validators=[DataRequired()])
    submit = SubmitField('Save Changes')

    def __init__(self, *args, **kwargs):
        super(StudentUpdateProfileForm, self).__init__(*args, **kwargs)
        db = get_db()
        if db is not None:
            self.department.choices = [('', 'Select Department')] + [(dept['name'], dept['name']) for dept in db.departments.find()]
        else:
            self.department.choices = [('', 'Select Department')]
