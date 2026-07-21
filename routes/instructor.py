from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from database.db import get_db
from werkzeug.utils import secure_filename
from functools import wraps
import os
from config import Config

instructor_bp = Blueprint('instructor', __name__)

def instructor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'instructor':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@instructor_bp.route('/dashboard')
@login_required
@instructor_required
def dashboard():
    db = get_db()
    instructor_id = current_user.user_data['instructor_id']
    
    my_courses = list(db.courses.find({'instructor_id': instructor_id}))
    course_codes = [c['course_code'] for c in my_courses]
    
    total_enrollments = db.enrollments.count_documents({'course_code': {'$in': course_codes}})
    active_courses = len([c for c in my_courses if c['status'] == 'Active'])
    total_assignments = db.assignments.count_documents({'course_code': {'$in': course_codes}})
    
    stats = {
        'my_courses': len(my_courses),
        'total_students': total_enrollments,
        'active_courses': active_courses,
        'total_assignments': total_assignments
    }
    
    return render_template('instructor/dashboard.html', stats=stats, courses=my_courses)

@instructor_bp.route('/courses', methods=['GET', 'POST'])
@login_required
@instructor_required
def manage_courses():
    db = get_db()
    instructor_id = current_user.user_data['instructor_id']
    
    if request.method == 'POST':
        course_data = {
            'course_code': request.form.get('course_code'),
            'course_name': request.form.get('course_name'),
            'description': request.form.get('description'),
            'department': current_user.user_data['department'],
            'category': request.form.get('category'),
            'credits': int(request.form.get('credits')),
            'duration': request.form.get('duration'),
            'capacity': int(request.form.get('capacity')),
            'instructor_id': instructor_id,
            'status': 'Active'
        }
        
        if db.courses.find_one({'course_code': course_data['course_code']}):
            flash('Course Code already exists.', 'danger')
        else:
            db.courses.insert_one(course_data)
            flash('Course created successfully.', 'success')
            return redirect(url_for('instructor.manage_courses'))
            
    courses = list(db.courses.find({'instructor_id': instructor_id}))
    categories = list(db.categories.find())
    return render_template('instructor/courses.html', courses=courses, categories=categories)

@instructor_bp.route('/assignments', methods=['GET', 'POST'])
@login_required
@instructor_required
def manage_assignments():
    db = get_db()
    instructor_id = current_user.user_data['instructor_id']
    my_courses = list(db.courses.find({'instructor_id': instructor_id}))
    course_codes = [c['course_code'] for c in my_courses]
    
    if request.method == 'POST':
        file = request.files.get('file')
        filename = None
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(Config.UPLOAD_FOLDER, filename))
            
        assignment_data = {
            'course_code': request.form.get('course_code'),
            'title': request.form.get('title'),
            'description': request.form.get('description'),
            'due_date': request.form.get('due_date'),
            'file': filename
        }
        db.assignments.insert_one(assignment_data)
        flash('Assignment added successfully.', 'success')
        return redirect(url_for('instructor.manage_assignments'))
        
    assignments = list(db.assignments.find({'course_code': {'$in': course_codes}}))
    return render_template('instructor/assignments.html', assignments=assignments, courses=my_courses)
