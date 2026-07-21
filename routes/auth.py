from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from forms.auth_forms import LoginForm, StudentRegistrationForm
from models.user import User, verify_password
from database.db import get_db
from werkzeug.security import generate_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'instructor':
            return redirect(url_for('instructor.dashboard'))
        else:
            return redirect(url_for('student.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        db = get_db()
        email = form.email.data
        password = form.password.data
        role = form.role.data

        user_data = None
        if role == 'admin':
            user_data = db.admins.find_one({'email': email})
        elif role == 'instructor':
            user_data = db.instructors.find_one({'email': email})
        elif role == 'student':
            user_data = db.students.find_one({'email': email})

        if user_data and verify_password(user_data['password'], password):
            user_obj = User(user_data, role)
            login_user(user_obj, remember=form.remember.data)
            flash('Logged in successfully.', 'success')
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
                
            if role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif role == 'instructor':
                return redirect(url_for('instructor.dashboard'))
            else:
                return redirect(url_for('student.dashboard'))
        else:
            flash('Invalid email or password', 'danger')

    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('student.dashboard'))
        
    form = StudentRegistrationForm()
    if form.validate_on_submit():
        db = get_db()
        hashed_password = generate_password_hash(form.password.data)
        
        student_data = {
            "student_id": form.student_id.data,
            "name": form.name.data,
            "email": form.email.data,
            "phone": form.phone.data,
            "department": form.department.data,
            "semester": form.semester.data,
            "password": hashed_password,
            "profile_image": "default.png"
        }
        
        db.students.insert_one(student_data)
        flash('Registration successful! You can now login.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
