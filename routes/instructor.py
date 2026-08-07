from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from database.db import get_db, get_fs
from werkzeug.utils import secure_filename
from functools import wraps
from bson.objectid import ObjectId
from datetime import datetime
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

@instructor_bp.route('/edit_course/<course_id>', methods=['POST'])
@login_required
@instructor_required
def edit_course(course_id):
    db = get_db()
    instructor_id = current_user.user_data['instructor_id']
    
    course_data = {
        'course_name': request.form.get('course_name'),
        'description': request.form.get('description'),
        'category': request.form.get('category'),
        'credits': int(request.form.get('credits')),
        'duration': request.form.get('duration'),
        'capacity': int(request.form.get('capacity')),
    }
    
    result = db.courses.update_one(
        {'_id': ObjectId(course_id), 'instructor_id': instructor_id},
        {'$set': course_data}
    )
    
    if result.modified_count > 0:
        flash('Course updated successfully.', 'success')
    else:
        flash('Failed to update course or no changes made.', 'warning')
        
    return redirect(url_for('instructor.manage_courses'))

@instructor_bp.route('/delete_course/<course_id>', methods=['POST'])
@login_required
@instructor_required
def delete_course(course_id):
    db = get_db()
    instructor_id = current_user.user_data['instructor_id']
    
    result = db.courses.delete_one({'_id': ObjectId(course_id), 'instructor_id': instructor_id})
    
    if result.deleted_count > 0:
        flash('Course deleted successfully.', 'success')
    else:
        flash('Failed to delete course or unauthorized.', 'danger')
        
    return redirect(url_for('instructor.manage_courses'))


@instructor_bp.route('/assignments', methods=['GET', 'POST'])
@login_required
@instructor_required
def manage_assignments():
    db = get_db()
    instructor_id = current_user.user_data['instructor_id']
    my_courses = list(db.courses.find({'instructor_id': instructor_id}))
    course_codes = [c['course_code'] for c in my_courses]
    
    if request.method == 'POST':
        try:
            file = request.files.get('file')
            file_id = None
            filename = None
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                fs = get_fs()
                # Save file to GridFS
                file_id = fs.put(file.read(), filename=filename, content_type=file.content_type)
                
            assignment_data = {
                'course_code': request.form.get('course_code'),
                'section_number': int(request.form.get('section_number', 1)),
                'title': request.form.get('title'),
                'description': request.form.get('description'),
                'due_date': request.form.get('due_date'),
                'file_id': file_id,
                'filename': filename
            }
            db.assignments.insert_one(assignment_data)
            flash('Assignment added successfully.', 'success')
        except Exception as e:
            print(f"Error adding assignment: {e}")
            flash(f'An error occurred: {str(e)}', 'danger')
            
        return redirect(url_for('instructor.manage_assignments'))
        
    assignments = list(db.assignments.find({'course_code': {'$in': course_codes}}))
    return render_template('instructor/assignments.html', assignments=assignments, courses=my_courses)

@instructor_bp.route('/delete_assignment/<assignment_id>', methods=['POST'])
@login_required
@instructor_required
def delete_assignment(assignment_id):
    db = get_db()
    
    try:
        assignment = db.assignments.find_one({'_id': ObjectId(assignment_id)})
        if assignment:
            # Delete file from GridFS if it exists
            if assignment.get('file_id'):
                fs = get_fs()
                fs.delete(ObjectId(assignment.get('file_id')))
            
            # Delete assignment record
            db.assignments.delete_one({'_id': ObjectId(assignment_id)})
            flash('Assignment deleted successfully.', 'success')
        else:
            flash('Assignment not found.', 'danger')
    except Exception as e:
        print(f"Error deleting assignment: {e}")
        flash('An error occurred while deleting the assignment.', 'danger')
        
    return redirect(url_for('instructor.manage_assignments'))

@instructor_bp.route('/view_material/<file_id>')
@login_required
@instructor_required
def view_material(file_id):
    db = get_db()
    instructor_id = current_user.user_data['instructor_id']
    
    try:
        assignment = db.assignments.find_one({'file_id': ObjectId(file_id)})
    except:
        assignment = None
        
    if not assignment:
        flash('Material not found.', 'danger')
        return redirect(url_for('instructor.manage_assignments'))
        
    # Verify course ownership
    course = db.courses.find_one({'course_code': assignment['course_code'], 'instructor_id': instructor_id})
    if not course:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('instructor.manage_assignments'))
        
    return render_template('instructor/view_material.html', assignment=assignment)

@instructor_bp.route('/grade_assignments/<course_code>')
@login_required
@instructor_required
def grade_assignments(course_code):
    db = get_db()
    instructor_id = current_user.user_data['instructor_id']
    
    # Verify course ownership
    course = db.courses.find_one({'course_code': course_code, 'instructor_id': instructor_id})
    if not course:
        flash('Course not found or unauthorized.', 'danger')
        return redirect(url_for('instructor.manage_assignments'))
        
    assignments = list(db.assignments.find({'course_code': course_code}))
    
    # Get all submissions for this course
    submissions = list(db.assignment_submissions.find({'course_code': course_code}))
    
    # Map student details
    student_ids = [s['student_id'] for s in submissions]
    students = list(db.students.find({'student_id': {'$in': student_ids}}))
    student_map = {s['student_id']: s for s in students}
    
    # Group submissions by assignment
    subs_by_assignment = {}
    for sub in submissions:
        aid = sub['assignment_id']
        if aid not in subs_by_assignment:
            subs_by_assignment[aid] = []
        subs_by_assignment[aid].append(sub)
        
    return render_template('instructor/grade_assignments.html', course=course, assignments=assignments, subs_by_assignment=subs_by_assignment, student_map=student_map)

@instructor_bp.route('/submit_grade/<submission_id>', methods=['POST'])
@login_required
@instructor_required
def submit_grade(submission_id):
    db = get_db()
    instructor_id = current_user.user_data['instructor_id']
    
    try:
        score = float(request.form.get('score'))
        if score < 0 or score > 100:
            flash('Score must be between 0 and 100.', 'danger')
            return redirect(request.referrer)
            
        submission = db.assignment_submissions.find_one({'_id': ObjectId(submission_id)})
        if not submission:
            flash('Submission not found.', 'danger')
            return redirect(request.referrer)
            
        # Verify course ownership
        course = db.courses.find_one({'course_code': submission['course_code'], 'instructor_id': instructor_id})
        if not course:
            flash('Unauthorized.', 'danger')
            return redirect(request.referrer)
            
        db.assignment_submissions.update_one(
            {'_id': ObjectId(submission_id)},
            {'$set': {
                'score': score,
                'status': 'Graded',
                'graded_by': instructor_id,
                'graded_date': datetime.utcnow()
            }}
        )
        flash('Grade submitted successfully.', 'success')
        
    except Exception as e:
        print(f"Error submitting grade: {e}")
        flash('Invalid score format or database error.', 'danger')
        
    return redirect(request.referrer)

@instructor_bp.route('/students')
@login_required
@instructor_required
def view_students():
    db = get_db()
    instructor_id = current_user.user_data['instructor_id']
    
    # Get courses taught by this instructor
    my_courses = list(db.courses.find({'instructor_id': instructor_id}))
    course_codes = [c['course_code'] for c in my_courses]
    
    # Get enrollments for these courses
    enrollments = list(db.enrollments.find({'course_code': {'$in': course_codes}}))
    
    # Get student details for these enrollments
    student_ids = [e['student_id'] for e in enrollments]
    students = list(db.students.find({'student_id': {'$in': student_ids}}))
    
    # To easily map student_id to student name/email
    student_map = {s['student_id']: s for s in students}
    course_map = {c['course_code']: c['course_name'] for c in my_courses}
    
    return render_template('instructor/students.html', enrollments=enrollments, student_map=student_map, course_map=course_map)

@instructor_bp.route('/quizzes', methods=['GET', 'POST'])
@login_required
@instructor_required
def manage_quizzes():
    db = get_db()
    instructor_id = current_user.user_data['instructor_id']
    my_courses = list(db.courses.find({'instructor_id': instructor_id}))
    course_codes = [c['course_code'] for c in my_courses]
    
    if request.method == 'POST':
        course_code = request.form.get('course_code')
        title = request.form.get('title')
        
        questions = []
        question_count = int(request.form.get('question_count', 0))
        for i in range(1, question_count + 1):
            q_text = request.form.get(f'q{i}_text')
            if q_text:
                options = [
                    request.form.get(f'q{i}_opt1'),
                    request.form.get(f'q{i}_opt2'),
                    request.form.get(f'q{i}_opt3'),
                    request.form.get(f'q{i}_opt4')
                ]
                correct_opt = int(request.form.get(f'q{i}_correct'))
                questions.append({
                    'question_text': q_text,
                    'options': options,
                    'correct_option': correct_opt
                })
        
        quiz_data = {
            'course_code': course_code,
            'instructor_id': instructor_id,
            'section_number': int(request.form.get('section_number', 1)),
            'is_final_exam': request.form.get('is_final_exam') == 'on',
            'title': title,
            'questions': questions
        }
        db.quizzes.insert_one(quiz_data)
        flash('Quiz created successfully.', 'success')
        return redirect(url_for('instructor.manage_quizzes'))
        
    quizzes = list(db.quizzes.find({'course_code': {'$in': course_codes}}))
    return render_template('instructor/quizzes.html', quizzes=quizzes, courses=my_courses)

@instructor_bp.route('/edit_quiz/<quiz_id>', methods=['GET', 'POST'])
@login_required
@instructor_required
def edit_quiz(quiz_id):
    db = get_db()
    instructor_id = current_user.user_data['instructor_id']
    
    quiz = db.quizzes.find_one({'_id': ObjectId(quiz_id), 'instructor_id': instructor_id})
    if not quiz:
        flash('Quiz not found.', 'danger')
        return redirect(url_for('instructor.manage_quizzes'))
        
    if request.method == 'POST':
        title = request.form.get('title')
        course_code = request.form.get('course_code')
        
        questions = []
        question_count = int(request.form.get('question_count', 0))
        for i in range(1, question_count + 1):
            q_text = request.form.get(f'q{i}_text')
            if q_text:
                options = [
                    request.form.get(f'q{i}_opt1'),
                    request.form.get(f'q{i}_opt2'),
                    request.form.get(f'q{i}_opt3'),
                    request.form.get(f'q{i}_opt4')
                ]
                correct_opt = request.form.get(f'q{i}_correct')
                if correct_opt is not None:
                    correct_opt = int(correct_opt)
                else:
                    correct_opt = 0 # Default if somehow missing
                questions.append({
                    'question_text': q_text,
                    'options': options,
                    'correct_option': correct_opt
                })
                
        db.quizzes.update_one(
            {'_id': ObjectId(quiz_id)},
            {'$set': {
                'title': title,
                'course_code': course_code,
                'section_number': int(request.form.get('section_number', 1)),
                'is_final_exam': request.form.get('is_final_exam') == 'on',
                'questions': questions
            }}
        )
        flash('Quiz updated successfully.', 'success')
        return redirect(url_for('instructor.manage_quizzes'))
        
    my_courses = list(db.courses.find({'instructor_id': instructor_id}))
    return render_template('instructor/edit_quiz.html', quiz=quiz, courses=my_courses)

@instructor_bp.route('/delete_quiz/<quiz_id>', methods=['POST'])
@login_required
@instructor_required
def delete_quiz(quiz_id):
    db = get_db()
    instructor_id = current_user.user_data['instructor_id']
    db.quizzes.delete_one({'_id': ObjectId(quiz_id), 'instructor_id': instructor_id})
    db.quiz_submissions.delete_many({'quiz_id': str(quiz_id)})
    flash('Quiz deleted successfully.', 'success')
    return redirect(url_for('instructor.manage_quizzes'))
    
@instructor_bp.route('/quiz_results/<quiz_id>')
@login_required
@instructor_required
def quiz_results(quiz_id):
    db = get_db()
    instructor_id = current_user.user_data['instructor_id']
    quiz = db.quizzes.find_one({'_id': ObjectId(quiz_id), 'instructor_id': instructor_id})
    if not quiz:
        flash('Quiz not found.', 'danger')
        return redirect(url_for('instructor.manage_quizzes'))
        
    submissions = list(db.quiz_submissions.find({'quiz_id': str(quiz_id)}))
    
    student_ids = [s['student_id'] for s in submissions]
    students = list(db.students.find({'student_id': {'$in': student_ids}}))
    student_map = {s['student_id']: s['name'] for s in students}
    
    return render_template('instructor/quiz_results.html', quiz=quiz, submissions=submissions, student_map=student_map)
