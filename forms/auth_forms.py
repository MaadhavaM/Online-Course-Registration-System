from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from database.db import get_db

class LoginForm(FlaskForm):
    role = SelectField('Role', choices=[('student', 'Student'), ('instructor', 'Instructor'), ('admin', 'Admin')], validators=[DataRequired()])
    # We will use either email or username/id for login. Let's use Email for all as per standard, or specific ID.
    # The prompt specifies email for Admins and Instructors, and maybe ID for students?
    # Admins: username, email. Students: student_id, email. Instructors: instructor_id, email.
    # Let's use Email for all for simplicity.
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class StudentRegistrationForm(FlaskForm):
    student_id = StringField('Student ID', validators=[DataRequired(), Length(min=4, max=20)])
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[DataRequired(), Length(min=10, max=15)])
    department = SelectField('Department', coerce=str, validators=[DataRequired()])
    semester = SelectField('Semester', choices=[(str(i), f'Semester {i}') for i in range(1, 9)], validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def __init__(self, *args, **kwargs):
        super(StudentRegistrationForm, self).__init__(*args, **kwargs)
        db = get_db()
        if db is not None:
            self.department.choices = [(dept['name'], dept['name']) for dept in db.departments.find()]
        else:
            self.department.choices = []

    def validate_email(self, email):
        db = get_db()
        if db is not None and db.students.find_one({"email": email.data}):
            raise ValidationError('That email is already registered. Please choose a different one.')

    def validate_student_id(self, student_id):
        db = get_db()
        if db is not None and db.students.find_one({"student_id": student_id.data}):
            raise ValidationError('That Student ID is already registered. Please choose a different one.')
