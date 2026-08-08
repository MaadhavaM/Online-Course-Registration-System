from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from database.db import get_db, get_fs
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime
from bson.objectid import ObjectId

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
    
    # Calculate earned credits using the new comprehensive grading system
    credits_by_course = {}
    grades_by_course = {}
    
    for course in courses:
        cc = course['course_code']
        # Find Final Exam for this course
        final_exam = db.quizzes.find_one({'course_code': cc, 'is_final_exam': True})
        
        if not final_exam:
            credits_by_course[cc] = 0
            grades_by_course[cc] = 0
            continue
            
        # Get best final exam score
        quiz_subs = list(db.quiz_submissions.find({'student_id': student_id, 'course_code': cc, 'quiz_id': str(final_exam['_id'])}))
        best_score = max([sub.get('score_percentage', 0) for sub in quiz_subs] + [0])
        
        grades_by_course[cc] = best_score
        
        course_credits = course['credits']
        earned = 0
        if best_score >= 90:
            earned = course_credits * 1.0
        elif best_score >= 75:
            earned = course_credits * 0.75
        elif best_score >= 60:
            earned = course_credits * 0.50
        elif best_score >= 50:
            earned = course_credits * 0.25
            
        credits_by_course[cc] = earned
        
        # Update enrollment status if they passed the final exam
        if best_score >= 50:
            db.enrollments.update_one(
                {'student_id': student_id, 'course_code': cc},
                {'$set': {'status': 'Completed'}}
            )
        else:
            db.enrollments.update_one(
                {'student_id': student_id, 'course_code': cc, 'status': 'Completed'},
                {'$set': {'status': 'Registered'}}
            )
            
            
    # Refresh enrollments after possible status updates
    enrollments = list(db.enrollments.find({'student_id': student_id}))
            
    total_earned = sum(credits_by_course.values())
    total_credits = sum([c['credits'] for c in courses])
    active_courses = len([e for e in enrollments if e['status'] == 'Registered'])
    completed_courses = len([e for e in enrollments if e['status'] == 'Completed'])
    
    stats = {
        'registered_courses': active_courses,
        'completed_courses': completed_courses,
        'credits_earned': total_earned,
        'total_credits': total_credits
    }
    
    quizzes = list(db.quizzes.find({'course_code': {'$in': course_codes}}))
    quiz_map = {}
    for q in quizzes:
        if q['course_code'] not in quiz_map:
            quiz_map[q['course_code']] = []
        quiz_map[q['course_code']].append(q)
    
    return render_template('student/dashboard.html', stats=stats, courses=courses, enrollments=enrollments, quiz_map=quiz_map, grades_by_course=grades_by_course)

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
    
    # Sort courses so registered ones appear first
    courses.sort(key=lambda c: 0 if c['course_code'] in my_enrollments else 1)
    
    return render_template('student/browse.html', courses=courses, departments=departments, categories=categories, my_enrollments=my_enrollments)

@student_bp.route('/register_course/<course_code>', methods=['POST'])
@login_required
@student_required
def register_course(course_code):
    db = get_db()
    student_id = current_user.user_data['student_id']
    
    # Check if already registered
    existing_enrollment = db.enrollments.find_one({'student_id': student_id, 'course_code': course_code})
    if existing_enrollment:
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
        # Wipe past progress so credits are deregistered and fresh start is possible
        db.quiz_submissions.delete_many({'student_id': student_id, 'course_code': course_code})
        db.assignment_submissions.delete_many({'student_id': student_id, 'course_code': course_code})
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
    # Assignments and submissions
    assignments = list(db.assignments.find({'course_code': course_code}))
    assignment_submissions = list(db.assignment_submissions.find({'student_id': student_id, 'course_code': course_code}))
    assignment_subs_map = {sub['assignment_id']: sub for sub in assignment_submissions}

    # Quizzes and submissions
    quizzes = list(db.quizzes.find({'course_code': course_code}))
    submissions = list(db.quiz_submissions.find({'student_id': student_id, 'course_code': course_code}))
    quiz_scores = {}
    for sub in submissions:
        qid = sub['quiz_id']
        score = sub.get('score_percentage', 0)
        if qid not in quiz_scores or score > quiz_scores[qid]:
            quiz_scores[qid] = score
            
    # Calculate unlocked sections
    all_items = assignments + quizzes
    sections = sorted(list(set(item.get('section_number', 1) for item in all_items)))
    
    highest_unlocked = sections[0] if sections else 1
    all_regular_sections_completed = True
    
    for sec in sections:
        sec_items = [i for i in all_items if i.get('section_number', 1) == sec and not i.get('is_final_exam')]
        if not sec_items:
            continue
            
        sec_completed = True
        for item in sec_items:
            if 'questions' in item: # It's a quiz
                if quiz_scores.get(str(item['_id']), 0) < 50:
                    sec_completed = False
                    break
            else: # It's an assignment (Reading Material)
                pass # Reading materials do not block progress
                    
        if sec_completed:
            idx = sections.index(sec)
            if idx + 1 < len(sections):
                highest_unlocked = sections[idx + 1]
            else:
                highest_unlocked = sec + 1
        else:
            all_regular_sections_completed = False
            break
            
    # Group items for template
    grouped_sections = {}
    for sec in sections:
        grouped_sections[sec] = {
            'regular_items': [i for i in all_items if i.get('section_number', 1) == sec and not i.get('is_final_exam')],
            'final_exams': [i for i in all_items if i.get('section_number', 1) == sec and i.get('is_final_exam')]
        }
    
    return render_template('student/materials.html', course=course, grouped_sections=grouped_sections, highest_unlocked=highest_unlocked, all_regular_completed=all_regular_sections_completed, quiz_scores=quiz_scores, assignment_subs_map=assignment_subs_map)

@student_bp.route('/view_material/<file_id>')
@login_required
@student_required
def view_material(file_id):
    db = get_db()
    student_id = current_user.user_data['student_id']
    
    try:
        assignment = db.assignments.find_one({'file_id': ObjectId(file_id)})
    except:
        assignment = None
        
    if not assignment:
        flash('Material not found.', 'danger')
        return redirect(url_for('student.dashboard'))
        
    # Verify enrollment
    if not db.enrollments.find_one({'student_id': student_id, 'course_code': assignment['course_code']}):
        flash('You are not registered for this course.', 'danger')
        return redirect(url_for('student.dashboard'))
        
    return render_template('student/view_material.html', assignment=assignment)

@student_bp.route('/submit_assignment/<assignment_id>', methods=['GET', 'POST'])
@login_required
@student_required
def submit_assignment(assignment_id):
    db = get_db()
    student_id = current_user.user_data['student_id']
    
    try:
        assignment = db.assignments.find_one({'_id': ObjectId(assignment_id)})
    except:
        assignment = None
        
    if not assignment:
        flash('Assignment not found.', 'danger')
        return redirect(url_for('student.dashboard'))
        
    # Verify enrollment
    if not db.enrollments.find_one({'student_id': student_id, 'course_code': assignment['course_code']}):
        flash('You are not registered for this course.', 'danger')
        return redirect(url_for('student.dashboard'))
        
    if request.method == 'POST':
        file = request.files.get('file')
        if not file or file.filename == '':
            flash('No file selected.', 'danger')
            return redirect(request.url)
            
        try:
            filename = secure_filename(file.filename)
            fs = get_fs()
            file_id = fs.put(file.read(), filename=filename, content_type=file.content_type)
            
            # Upsert submission (if they submit multiple times, overwrite or create new? Let's just create a new record or update existing)
            db.assignment_submissions.update_one(
                {'assignment_id': str(assignment_id), 'student_id': student_id},
                {'$set': {
                    'course_code': assignment['course_code'],
                    'file_id': file_id,
                    'filename': filename,
                    'submission_date': datetime.utcnow(),
                    'status': 'Submitted',
                    # Keep score if it was already graded? Probably reset score.
                    'score': None,
                    'graded_by': None
                }},
                upsert=True
            )
            flash('Assignment submitted successfully!', 'success')
            return redirect(url_for('student.view_materials', course_code=assignment['course_code']))
        except Exception as e:
            print(f"Error submitting assignment: {e}")
            flash('An error occurred during submission.', 'danger')
            
    # GET method - just render the form, but actually we'll do this in a modal or a separate page
    return render_template('student/submit_assignment.html', assignment=assignment)

@student_bp.route('/take_quiz/<quiz_id>', methods=['GET', 'POST'])
@login_required
@student_required
def take_quiz(quiz_id):
    db = get_db()
    student_id = current_user.user_data['student_id']
    quiz = db.quizzes.find_one({'_id': ObjectId(quiz_id)})
    
    if not quiz:
        flash('Quiz not found.', 'danger')
        return redirect(url_for('student.dashboard'))
        
    course_code = quiz['course_code']
    course = db.courses.find_one({'course_code': course_code})
    
    if request.method == 'POST':
        questions = quiz.get('questions', [])
        correct_count = 0
        total_q = len(questions)
        
        for i, q in enumerate(questions):
            ans = request.form.get(f'q{i}')
            if ans is not None and int(ans) == q['correct_option']:
                correct_count += 1
                
        score_percentage = (correct_count / total_q) * 100 if total_q > 0 else 0
        
        course_credits = course['credits']
        earned_credits = 0
        if score_percentage >= 90:
            earned_credits = course_credits * 1.0
        elif score_percentage >= 75:
            earned_credits = course_credits * 0.75
        elif score_percentage >= 60:
            earned_credits = course_credits * 0.50
        elif score_percentage >= 50:
            earned_credits = course_credits * 0.25
            
        status = 'Pass' if score_percentage >= 50 else 'Fail'
        
        result = db.quiz_submissions.insert_one({
            'quiz_id': str(quiz_id),
            'student_id': student_id,
            'student_name': current_user.user_data.get('name', 'Unknown'),
            'course_code': course_code,
            'score_percentage': score_percentage,
            'earned_credits': earned_credits,
            'status': status,
            'attempt_date': datetime.utcnow()
        })
        
        # Evaluate course completion ONLY based on Final Exam
        if quiz.get('is_final_exam') and score_percentage >= 50:
            db.enrollments.update_one(
                {'student_id': student_id, 'course_code': course_code},
                {'$set': {'status': 'Completed'}}
            )
            
        return redirect(url_for('student.quiz_result', submission_id=str(result.inserted_id)))
        
    return render_template('student/take_quiz.html', quiz=quiz, course=course)

@student_bp.route('/quiz_result/<submission_id>')
@login_required
@student_required
def quiz_result(submission_id):
    db = get_db()
    student_id = current_user.user_data['student_id']
    submission = db.quiz_submissions.find_one({'_id': ObjectId(submission_id), 'student_id': student_id})
    
    if not submission:
        flash('Result not found.', 'danger')
        return redirect(url_for('student.dashboard'))
        
    quiz = db.quizzes.find_one({'_id': ObjectId(submission['quiz_id'])})
    course = db.courses.find_one({'course_code': submission['course_code']})
    
    return render_template('student/quiz_result.html', submission=submission, quiz=quiz, course=course)

@student_bp.route('/certificate/<course_code>')
@login_required
@student_required
def certificate(course_code):
    db = get_db()
    student_id = current_user.user_data['student_id']
    
    # Check enrollment status
    enrollment = db.enrollments.find_one({'student_id': student_id, 'course_code': course_code})
    if not enrollment or enrollment.get('status') != 'Completed':
        flash('You must complete the course to view your certificate.', 'warning')
        return redirect(url_for('student.dashboard'))
        
    course = db.courses.find_one({'course_code': course_code})
    
    # Calculate grade from Final Exam only
    final_exam = db.quizzes.find_one({'course_code': course_code, 'is_final_exam': True})
    avg_score = 0
    if final_exam:
        quiz_subs = list(db.quiz_submissions.find({'student_id': student_id, 'course_code': course_code, 'quiz_id': str(final_exam['_id'])}))
        if quiz_subs:
            avg_score = max([sub.get('score_percentage', 0) for sub in quiz_subs])
        
    student_name = current_user.user_data.get('name', 'Student')
    # Use today's date or completion date if available
    date = datetime.now().strftime("%B %d, %Y")
    
    instructor = db.instructors.find_one({'instructor_id': course.get('instructor_id')})
    instructor_name = instructor.get('name') if instructor else "Course Instructor"
    
    return render_template('student/certificate.html', course=course, student_name=student_name, grade=avg_score, date=date, instructor_name=instructor_name)

@student_bp.route('/profile')
@login_required
@student_required
def profile():
    db = get_db()
    student_id = current_user.user_data['student_id']
    student = db.students.find_one({'student_id': student_id})
    return render_template('student/profile.html', student=student)

@student_bp.route('/update_profile', methods=['GET', 'POST'])
@login_required
@student_required
def update_profile():
    db = get_db()
    student_id = current_user.user_data['student_id']
    student = db.students.find_one({'student_id': student_id})
    
    from forms.auth_forms import StudentUpdateProfileForm
    form = StudentUpdateProfileForm()
    
    if form.validate_on_submit():
        if form.email.data != student['email']:
            existing = db.students.find_one({'email': form.email.data})
            if existing:
                flash('Email already in use.', 'danger')
                return render_template('student/update_profile.html', form=form, student=student)
                
        db.students.update_one(
            {'student_id': student_id},
            {'$set': {
                'name': form.name.data,
                'email': form.email.data,
                'phone': form.phone.data,
                'department': form.department.data,
                'semester': form.semester.data
            }}
        )
        
        # Update current user data in session
        current_user.user_data['name'] = form.name.data
        current_user.user_data['email'] = form.email.data
        current_user.user_data['phone'] = form.phone.data
        current_user.user_data['department'] = form.department.data
        current_user.user_data['semester'] = form.semester.data
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('student.update_profile'))
        
    elif request.method == 'GET':
        form.name.data = student.get('name', '')
        form.email.data = student.get('email', '')
        form.phone.data = student.get('phone', '')
        form.department.data = student.get('department', '')
        form.semester.data = student.get('semester', '')
        
    return render_template('student/update_profile.html', form=form, student=student)
