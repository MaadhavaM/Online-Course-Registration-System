from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from database.db import get_db
from functools import wraps
from datetime import datetime

student_bp = Blueprint('student', __name__)

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'student':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@student_bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    db = get_db()
    student_id = current_user.user_data['student_id']
    
    enrollments = list(db.enrollments.find({'student_id': student_id}))
    course_codes = [e['course_code'] for e in enrollments]
    courses = list(db.courses.find({'course_code': {'$in': course_codes}}))
    
    total_credits = sum([c['credits'] for c in courses])
    active_courses = len([e for e in enrollments if e['status'] == 'Registered'])
    completed_courses = len([e for e in enrollments if e['status'] == 'Completed'])
    
    stats = {
        'registered_courses': active_courses,
        'completed_courses': completed_courses,
        'credits_earned': total_credits if completed_courses > 0 else 0, # Simplify logic for demo
        'total_credits': total_credits
    }
    
    return render_template('student/dashboard.html', stats=stats, courses=courses, enrollments=enrollments)

@student_bp.route('/browse')
@login_required
@student_required
def browse_courses():
    db = get_db()
    search = request.args.get('search', '')
    department_filter = request.args.get('department', '')
    category_filter = request.args.get('category', '')
    
    query = {'status': 'Active'}
    if search:
        query['course_name'] = {'$regex': search, '$options': 'i'}
    if department_filter:
        query['department'] = department_filter
    if category_filter:
        query['category'] = category_filter
        
    courses = list(db.courses.find(query))
    departments = list(db.departments.find())
    categories = list(db.categories.find())
    
    # Get user's current enrollments to disable register button
    student_id = current_user.user_data['student_id']
    my_enrollments = [e['course_code'] for e in db.enrollments.find({'student_id': student_id})]
    
    return render_template('student/browse.html', courses=courses, departments=departments, categories=categories, my_enrollments=my_enrollments)

@student_bp.route('/register_course/<course_code>', methods=['POST'])
@login_required
@student_required
def register_course(course_code):
    db = get_db()
    student_id = current_user.user_data['student_id']
    
    # Check if already registered
    if db.enrollments.find_one({'student_id': student_id, 'course_code': course_code}):
        flash('You are already registered for this course.', 'warning')
        return redirect(url_for('student.browse_courses'))
        
    course = db.courses.find_one({'course_code': course_code})
    if not course:
        flash('Course not found.', 'danger')
        return redirect(url_for('student.browse_courses'))
        
    # Check capacity
    current_enrollments = db.enrollments.count_documents({'course_code': course_code})
    if current_enrollments >= course['capacity']:
        flash('Course is full. Registration failed.', 'danger')
        return redirect(url_for('student.browse_courses'))
        
    db.enrollments.insert_one({
        'student_id': student_id,
        'course_code': course_code,
        'registration_date': datetime.utcnow(),
        'status': 'Registered'
    })
    
    flash(f'Successfully registered for {course_code} - {course["course_name"]}.', 'success')
    return redirect(url_for('student.dashboard'))

@student_bp.route('/drop_course/<course_code>', methods=['POST'])
@login_required
@student_required
def drop_course(course_code):
    db = get_db()
    student_id = current_user.user_data['student_id']
    
    result = db.enrollments.delete_one({'student_id': student_id, 'course_code': course_code})
    if result.deleted_count > 0:
        flash(f'Successfully dropped course {course_code}.', 'success')
    else:
        flash('Failed to drop course.', 'danger')
        
    return redirect(url_for('student.dashboard'))

@student_bp.route('/materials/<course_code>')
@login_required
@student_required
def view_materials(course_code):
    db = get_db()
    student_id = current_user.user_data['student_id']
    
    # Check enrollment
    if not db.enrollments.find_one({'student_id': student_id, 'course_code': course_code}):
        flash('You are not registered for this course.', 'danger')
        return redirect(url_for('student.dashboard'))
        
    course = db.courses.find_one({'course_code': course_code})
    assignments = list(db.assignments.find({'course_code': course_code}))
    
    return render_template('student/materials.html', course=course, assignments=assignments)
