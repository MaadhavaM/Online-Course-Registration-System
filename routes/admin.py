from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from database.db import get_db
from werkzeug.security import generate_password_hash
from functools import wraps
from bson.objectid import ObjectId
import csv
from flask import Response
import io

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    db = get_db()
    stats = {
        'total_students': db.students.count_documents({}),
        'total_instructors': db.instructors.count_documents({}),
        'total_courses': db.courses.count_documents({}),
        'active_courses': db.courses.count_documents({'status': 'Active'}),
        'total_enrollments': db.enrollments.count_documents({})
    }
    
    # Aggregation for charts
    dept_distribution = list(db.students.aggregate([
        {'$group': {'_id': '$department', 'count': {'$sum': 1}}}
    ]))
    
    return render_template('admin/dashboard.html', stats=stats, dept_distribution=dept_distribution)

@admin_bp.route('/students')
@login_required
@admin_required
def manage_students():
    db = get_db()
    students = list(db.students.find())
    return render_template('admin/students.html', students=students)

@admin_bp.route('/instructors', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_instructors():
    db = get_db()
    if request.method == 'POST':
        # Add new instructor
        instructor_id = request.form.get('instructor_id')
        name = request.form.get('name')
        email = request.form.get('email')
        department = request.form.get('department')
        designation = request.form.get('designation')
        password = generate_password_hash(request.form.get('password'))
        
        if db.instructors.find_one({'instructor_id': instructor_id}) or db.instructors.find_one({'email': email}):
            flash('Instructor ID or Email already exists.', 'danger')
        else:
            db.instructors.insert_one({
                'instructor_id': instructor_id,
                'name': name,
                'email': email,
                'department': department,
                'designation': designation,
                'password': password,
                'profile_image': 'default.png'
            })
            flash('Instructor added successfully.', 'success')
            return redirect(url_for('admin.manage_instructors'))
            
    instructors = list(db.instructors.find())
    departments = list(db.departments.find())
    return render_template('admin/instructors.html', instructors=instructors, departments=departments)

@admin_bp.route('/courses')
@login_required
@admin_required
def manage_courses():
    db = get_db()
    courses = list(db.courses.find())
    return render_template('admin/courses.html', courses=courses)

@admin_bp.route('/departments_categories', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_dept_cat():
    db = get_db()
    if request.method == 'POST':
        action = request.form.get('action')
        name = request.form.get('name')
        if action == 'add_dept':
            if not db.departments.find_one({'name': name}):
                db.departments.insert_one({'name': name})
                flash('Department added.', 'success')
        elif action == 'add_cat':
            if not db.categories.find_one({'name': name}):
                db.categories.insert_one({'name': name})
                flash('Category added.', 'success')
        return redirect(url_for('admin.manage_dept_cat'))
        
    departments = list(db.departments.find())
    categories = list(db.categories.find())
    return render_template('admin/dept_cat.html', departments=departments, categories=categories)

@admin_bp.route('/export/students')
@login_required
@admin_required
def export_students():
    db = get_db()
    students = list(db.students.find())
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['Student ID', 'Name', 'Email', 'Phone', 'Department', 'Semester'])
    
    for s in students:
        writer.writerow([
            s.get('student_id', ''),
            s.get('name', ''),
            s.get('email', ''),
            s.get('phone', ''),
            s.get('department', ''),
            s.get('semester', '')
        ])
        
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=students_report.csv"}
    )

