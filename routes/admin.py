from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from database.db import get_db
from werkzeug.security import generate_password_hash
from functools import wraps
from bson.objectid import ObjectId
import csv
from flask import Response
import io
import re

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

@admin_bp.route('/delete_student/<student_id>', methods=['POST'])
@login_required
@admin_required
def delete_student(student_id):
    db = get_db()
    db.students.delete_one({'_id': ObjectId(student_id)})
    flash('Student deleted successfully.', 'success')
    return redirect(url_for('admin.manage_students'))

@admin_bp.route('/instructors', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_instructors():
    db = get_db()
    if request.method == 'POST':
        # Add new instructor
        instructor_id = request.form.get('instructor_id')
        name = request.form.get('name', '').strip()
        email = request.form.get('email')
        department = request.form.get('department')
        designation = request.form.get('designation')
        password = generate_password_hash(request.form.get('password'))
        
        if not re.match(r'^[A-Za-z\s]+$', name):
            flash('Invalid name. Only alphabets and spaces are allowed.', 'danger')
            return redirect(url_for('admin.manage_instructors'))
        
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

@admin_bp.route('/edit_instructor/<instructor_id>', methods=['POST'])
@login_required
@admin_required
def edit_instructor(instructor_id):
    db = get_db()
    name = request.form.get('name', '').strip()
    email = request.form.get('email')
    department = request.form.get('department')
    designation = request.form.get('designation')
    
    if not re.match(r'^[A-Za-z\s]+$', name):
        flash('Invalid name. Only alphabets and spaces are allowed.', 'danger')
        return redirect(url_for('admin.manage_instructors'))
        
    db.instructors.update_one(
        {'_id': ObjectId(instructor_id)},
        {'$set': {'name': name, 'email': email, 'department': department, 'designation': designation}}
    )
    flash('Instructor updated successfully.', 'success')
    return redirect(url_for('admin.manage_instructors'))

@admin_bp.route('/delete_instructor/<instructor_id>', methods=['POST'])
@login_required
@admin_required
def delete_instructor(instructor_id):
    db = get_db()
    db.instructors.delete_one({'_id': ObjectId(instructor_id)})
    flash('Instructor deleted successfully.', 'success')
    return redirect(url_for('admin.manage_instructors'))

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
        name = request.form.get('name', '').strip()
        
        if not re.match(r'^[A-Za-z\s]+$', name):
            flash('Invalid name. Only alphabets and spaces are allowed.', 'danger')
            return redirect(url_for('admin.manage_dept_cat'))
            
        if action == 'add_dept':
            if not db.departments.find_one({'name': name}):
                db.departments.insert_one({'name': name})
                flash('Department added.', 'success')
            else:
                flash('Department already exists.', 'warning')
        elif action == 'add_cat':
            if not db.categories.find_one({'name': name}):
                db.categories.insert_one({'name': name})
                flash('Category added.', 'success')
            else:
                flash('Category already exists.', 'warning')
        return redirect(url_for('admin.manage_dept_cat'))
        
    departments = list(db.departments.find())
    categories = list(db.categories.find())
    return render_template('admin/dept_cat.html', departments=departments, categories=categories)

@admin_bp.route('/delete_dept/<dept_id>', methods=['POST'])
@login_required
@admin_required
def delete_dept(dept_id):
    db = get_db()
    db.departments.delete_one({'_id': ObjectId(dept_id)})
    flash('Department deleted.', 'success')
    return redirect(url_for('admin.manage_dept_cat'))

@admin_bp.route('/delete_cat/<cat_id>', methods=['POST'])
@login_required
@admin_required
def delete_cat(cat_id):
    db = get_db()
    db.categories.delete_one({'_id': ObjectId(cat_id)})
    flash('Category deleted.', 'success')
    return redirect(url_for('admin.manage_dept_cat'))

@admin_bp.route('/admins', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_admins():
    db = get_db()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password_raw = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not re.match(r'^[A-Za-z\s]+$', name):
            flash('Invalid name. Only alphabets and spaces are allowed.', 'danger')
        elif password_raw != confirm_password:
            flash('Passwords do not match.', 'danger')
        elif len(password_raw) < 6:
            flash('Password must be at least 6 characters.', 'danger')
        elif db.admins.find_one({'email': email}):
            flash('An admin with this email already exists.', 'danger')
        else:
            db.admins.insert_one({
                'name': name,
                'email': email,
                'phone': phone,
                'password': generate_password_hash(password_raw)
            })
            flash('New admin account created successfully.', 'success')
            return redirect(url_for('admin.manage_admins'))
            
    admins = list(db.admins.find())
    return render_template('admin/admins.html', admins=admins)

@admin_bp.route('/delete_admin/<admin_id>', methods=['POST'])
@login_required
@admin_required
def delete_admin(admin_id):
    db = get_db()
    # Prevent the last admin from being deleted, or prevent deleting oneself
    if str(current_user.id) == admin_id:
        flash('You cannot delete your own admin account.', 'danger')
    else:
        db.admins.delete_one({'_id': ObjectId(admin_id)})
        flash('Admin deleted successfully.', 'success')
    return redirect(url_for('admin.manage_admins'))

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

