from flask import Blueprint, render_template, redirect, url_for, flash, request, session
import random
from flask_login import login_user, logout_user, login_required, current_user
from forms.auth_forms import LoginForm, StudentRegistrationForm, AdminRegistrationForm
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

        user_data = None
        role = None

        if db.admins.find_one({'email': email}):
            user_data = db.admins.find_one({'email': email})
            role = 'admin'
        elif db.instructors.find_one({'email': email}):
            user_data = db.instructors.find_one({'email': email})
            role = 'instructor'
        elif db.students.find_one({'email': email}):
            user_data = db.students.find_one({'email': email})
            role = 'student'

        if user_data and verify_password(user_data['password'], password):
            if role in ['admin', 'instructor']:
                otp = str(random.randint(100000, 999999))
                session['login_pending_email'] = email
                session['login_pending_role'] = role
                session['login_pending_remember'] = form.remember.data
                session['login_pending_otp'] = otp
                
                flash(f'MOCK SMS: Your login OTP is {otp}', 'info')
                return redirect(url_for('auth.login_verify_otp'))
            else:
                user_obj = User(user_data, role)
                login_user(user_obj, remember=form.remember.data)
                flash('Logged in successfully.', 'success')
                
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect(url_for('student.dashboard'))
        else:
            flash('Invalid email or password', 'danger')

    return render_template('auth/login.html', form=form)

@auth_bp.route('/login-verify-otp', methods=['GET', 'POST'])
def login_verify_otp():
    if 'login_pending_otp' not in session:
        flash('No login in progress or session expired. Please log in again.', 'warning')
        return redirect(url_for('auth.login'))
        
    from forms.auth_forms import LoginVerifyOTPForm
    form = LoginVerifyOTPForm()
    
    if form.validate_on_submit():
        if form.otp.data == session.get('login_pending_otp'):
            db = get_db()
            email = session.get('login_pending_email')
            role = session.get('login_pending_role')
            remember = session.get('login_pending_remember')
            
            user_data = None
            if role == 'admin':
                user_data = db.admins.find_one({'email': email})
            elif role == 'instructor':
                user_data = db.instructors.find_one({'email': email})
                
            if user_data:
                user_obj = User(user_data, role)
                login_user(user_obj, remember=remember)
                
                session.pop('login_pending_email', None)
                session.pop('login_pending_role', None)
                session.pop('login_pending_remember', None)
                session.pop('login_pending_otp', None)
                
                flash('Logged in successfully.', 'success')
                
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                    
                if role == 'admin':
                    return redirect(url_for('admin.dashboard'))
                else:
                    return redirect(url_for('instructor.dashboard'))
            else:
                flash('Error retrieving user data.', 'danger')
                return redirect(url_for('auth.login'))
        else:
            flash('Invalid OTP. Please try again.', 'danger')
            
    return render_template('auth/login_verify_otp.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'instructor':
            return redirect(url_for('instructor.dashboard'))
        else:
            return redirect(url_for('student.dashboard'))
        
    student_form = StudentRegistrationForm()
    admin_form = AdminRegistrationForm()

    if student_form.submit.data and student_form.validate():
        db = get_db()
        hashed_password = generate_password_hash(student_form.password.data)
        
        student_data = {
            "student_id": student_form.student_id.data,
            "name": student_form.name.data,
            "email": student_form.email.data,
            "phone": student_form.phone.data,
            "department": student_form.department.data,
            "semester": student_form.semester.data,
            "password": hashed_password,
            "profile_image": "default.png"
        }
        
        db.students.insert_one(student_data)
        flash('Student Registration successful! You can now login.', 'success')
        return redirect(url_for('auth.login'))

    if admin_form.submit.data and admin_form.validate():
        db = get_db()
        hashed_password = generate_password_hash(admin_form.password.data)
        
        admin_data = {
            "name": admin_form.name.data,
            "email": admin_form.email.data,
            "phone": admin_form.phone.data,
            "password": hashed_password,
            "profile_image": "default.png"
        }
        
        db.admins.insert_one(admin_data)
        flash('Admin Registration successful! You can now login.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html', student_form=student_form, admin_form=admin_form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    from forms.auth_forms import ForgotPasswordForm
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        db = get_db()
        role = form.role.data
        phone = form.phone.data
        
        user_data = None
        if role == 'admin':
            user_data = db.admins.find_one({'phone': phone})
        elif role == 'instructor':
            user_data = db.instructors.find_one({'phone': phone})
        elif role == 'student':
            user_data = db.students.find_one({'phone': phone})
            
        if user_data:
            otp = str(random.randint(100000, 999999))
            session['reset_otp'] = otp
            session['reset_phone'] = phone
            session['reset_role'] = role
            
            # Mock SMS functionality
            flash(f'MOCK SMS: Your password reset OTP is {otp}', 'info')
            return redirect(url_for('auth.verify_otp'))
        else:
            flash('No account found with that phone number and role.', 'danger')
            
    return render_template('auth/forgot_password.html', form=form)

@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if 'reset_otp' not in session:
        flash('Session expired. Please request a new OTP.', 'warning')
        return redirect(url_for('auth.forgot_password'))
        
    from forms.auth_forms import VerifyOTPForm
    form = VerifyOTPForm()
    if form.validate_on_submit():
        if form.otp.data == session.get('reset_otp'):
            session['otp_verified'] = True
            return redirect(url_for('auth.reset_password'))
        else:
            flash('Invalid OTP. Please try again.', 'danger')
            
    return render_template('auth/verify_otp.html', form=form)

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if not session.get('otp_verified'):
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('auth.login'))
        
    from forms.auth_forms import ResetPasswordForm
    form = ResetPasswordForm()
    if form.validate_on_submit():
        db = get_db()
        role = session.get('reset_role')
        phone = session.get('reset_phone')
        hashed_password = generate_password_hash(form.password.data)
        
        if role == 'admin':
            db.admins.update_one({'phone': phone}, {'$set': {'password': hashed_password}})
        elif role == 'instructor':
            db.instructors.update_one({'phone': phone}, {'$set': {'password': hashed_password}})
        elif role == 'student':
            db.students.update_one({'phone': phone}, {'$set': {'password': hashed_password}})
            
        session.pop('reset_otp', None)
        session.pop('reset_phone', None)
        session.pop('reset_role', None)
        session.pop('otp_verified', None)
        
        flash('Password reset successfully! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/reset_password.html', form=form)
