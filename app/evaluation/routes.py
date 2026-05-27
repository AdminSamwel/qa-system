from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.evaluation import bp
from app.models import (User, Course, Enrollment, Evaluation, Form, FormQuestion, Response,
                        Department, Programme, FormSection, Campus)
from app.forms import CourseForm
import json
from datetime import datetime
import uuid

@bp.route('/courses')
@login_required
def list_courses():
    if current_user.role == 'student':
        enrolled_ids = [e.course_id for e in Enrollment.query.filter_by(student_id=current_user.id).all()]
        if not enrolled_ids:
            departments = []
            programmes = []
        else:
            departments = Department.query.filter(
                Department.id.in_(
                    db.session.query(Programme.department_id).join(Course).filter(Course.id.in_(enrolled_ids))
                )
            ).order_by(Department.name).all()
            programmes = Programme.query.filter(
                Programme.id.in_(
                    db.session.query(Course.programme_id).filter(Course.id.in_(enrolled_ids))
                )
            ).order_by(Programme.name).all()
        return render_template('evaluation/select_programme.html', departments=departments, programmes=programmes)
    elif current_user.role == 'lecturer':
        courses = Course.query.filter_by(lecturer_id=current_user.id).all()
        return render_template('evaluation/list_courses.html', courses=courses)
    else:
        courses = Course.query.all()
        return render_template('evaluation/list_courses.html', courses=courses)

@bp.route('/courses/filter', methods=['POST'])
@login_required
def filter_courses():
    if current_user.role != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))

    department_id = request.form.get('department_id', type=int)
    programme_id = request.form.get('programme_id', type=int)
    level = request.form.get('level')
    academic_year = request.form.get('academic_year')
    semester = request.form.get('semester')

    enrolled_ids = [e.course_id for e in Enrollment.query.filter_by(student_id=current_user.id).all()]
    if not enrolled_ids:
        return render_template('evaluation/list_filtered_courses.html', course_status=[])

    query = Course.query.filter(Course.id.in_(enrolled_ids))
    if department_id:
        query = query.filter_by(department_id=department_id)
    if programme_id:
        query = query.filter_by(programme_id=programme_id)
    if level:
        query = query.filter_by(level=level)
    if academic_year:
        query = query.filter_by(academic_year=academic_year)
    if semester:
        query = query.filter_by(semester=semester)

    courses = query.order_by(Course.code).all()
    evaluated_ids = [e.course_id for e in Evaluation.query.filter_by(student_id=current_user.id).all()]
    course_status = [{'course': c, 'evaluated': c.id in evaluated_ids} for c in courses]
    return render_template('evaluation/list_filtered_courses.html', course_status=course_status)

@bp.route('/evaluate/<int:course_id>', methods=['GET', 'POST'])
@login_required
def evaluate_course(course_id):
    if current_user.role != 'student':
        flash('Only students can submit evaluations.', 'danger')
        return redirect(url_for('main.index'))

    course = db.get_or_404(Course, course_id)

    enrollment = Enrollment.query.filter_by(student_id=current_user.id, course_id=course_id).first()
    if not enrollment:
        flash('You are not enrolled in this course.', 'danger')
        return redirect(url_for('evaluation.list_courses'))

    existing = Evaluation.query.filter_by(student_id=current_user.id, course_id=course_id).first()
    if existing:
        flash('You have already evaluated this course.', 'warning')
        return redirect(url_for('evaluation.list_courses'))

    # Use the form assigned to the course, or fallback to any active form
    if course.form_id:
        active_form = Form.query.options(
            db.joinedload(Form.sections).joinedload(FormSection.questions)
        ).get(course.form_id)
        # If the assigned form is not active, ignore it
        if active_form and not active_form.is_active:
            active_form = None
    else:
        active_form = None

    if not active_form:
        active_form = Form.query.filter_by(is_active=True).filter(
            (Form.target_level == course.level) | (Form.target_level == None)
        ).options(db.joinedload(Form.sections).joinedload(FormSection.questions)).first()

    if not active_form:
        flash('No active evaluation form for this course.', 'warning')
        return redirect(url_for('evaluation.list_courses'))

    if active_form.deadline and active_form.deadline < datetime.utcnow():
        flash('The evaluation deadline has passed.', 'danger')
        return redirect(url_for('evaluation.list_courses'))

    # Lecturer name substitution
    lecturer_name = course.lecturer.full_name if course.lecturer else 'the lecturer'
    for section in active_form.sections:
        section.display_title = section.title.replace('NAME OF LECTURE', lecturer_name)\
                                             .replace('PUT NAME OF LECTURE', lecturer_name)\
                                             .replace('[NAME]', lecturer_name)
        for q in section.questions:
            q.display_text = q.question_text.replace('NAME OF LECTURE', lecturer_name)\
                                            .replace('PUT NAME OF LECTURE', lecturer_name)\
                                            .replace('[NAME]', lecturer_name)

    questions = []
    for section in active_form.sections:
        questions.extend(section.questions)

    if request.method == 'POST':
        evaluation = Evaluation(student_id=current_user.id, course_id=course_id, form_id=active_form.id)
        db.session.add(evaluation)
        db.session.flush()

        overall_score = 0
        likert_count = 0
        for q in questions:
            if q.question_type == 'likert':
                val = request.form.get(f'q_{q.id}')
                if val:
                    resp = Response(evaluation_id=evaluation.id, form_question_id=q.id, likert_value=int(val))
                    db.session.add(resp)
                    overall_score += int(val)
                    likert_count += 1
            elif q.question_type == 'text':
                val = request.form.get(f'q_{q.id}')
                if val:
                    resp = Response(evaluation_id=evaluation.id, form_question_id=q.id, text_value=val)
                    db.session.add(resp)
            elif q.question_type in ['multiple_choice', 'checkbox']:
                vals = request.form.getlist(f'q_{q.id}')
                if vals:
                    resp = Response(evaluation_id=evaluation.id, form_question_id=q.id, selected_options=json.dumps(vals))
                    db.session.add(resp)
        if likert_count > 0:
            evaluation.overall_score = round(overall_score / likert_count)
        db.session.commit()
        flash('Evaluation submitted!', 'success')
        return redirect(url_for('evaluation.list_courses'))

    return render_template('evaluation/form.html', course=course, form=active_form)

# ========== PUBLIC EVALUATION (SHORT COURSES) ==========
@bp.route('/public/<int:course_id>/<token>', methods=['GET', 'POST'])
def public_evaluate(course_id, token):
    course = Course.query.filter_by(id=course_id, public_token=token).first_or_404()
    if course.course_type != 'short':
        flash('This link is only valid for short courses.', 'danger')
        return redirect(url_for('main.index'))

    # Use the form assigned to the course, or fallback to any active form
    if course.form_id:
        active_form = Form.query.options(
            db.joinedload(Form.sections).joinedload(FormSection.questions)
        ).get(course.form_id)
        if active_form and not active_form.is_active:
            active_form = None
    else:
        active_form = None

    if not active_form:
        active_form = Form.query.filter_by(is_active=True).filter(
            (Form.target_level == course.level) | (Form.target_level == None)
        ).options(db.joinedload(Form.sections).joinedload(FormSection.questions)).first()

    if not active_form:
        flash('No active evaluation form available.', 'warning')
        return redirect(url_for('main.index'))

    if active_form.deadline and active_form.deadline < datetime.utcnow():
        flash('The evaluation deadline has passed.', 'danger')
        return redirect(url_for('main.index'))

    # Resolve the best available facilitator name:
    # 1. form.facilitator_name  (set when cloning a template for a specific facilitator)
    # 2. form.facilitator.display_name  (user FK on the form)
    # 3. course.lecturer.display_name  (lecturer assigned to the course)
    if active_form.facilitator_name:
        facilitator_name = active_form.facilitator_name
    elif active_form.facilitator_id and active_form.facilitator:
        facilitator_name = active_form.facilitator.display_name
    elif course.lecturer:
        facilitator_name = course.lecturer.display_name
    else:
        facilitator_name = None   # unknown — template will handle gracefully

    # Replace [lecturer name] placeholders inside section/question text
    _fname = facilitator_name or 'Mkufunzi'
    for section in active_form.sections:
        section.display_title = section.title.replace('NAME OF LECTURE', _fname)\
                                             .replace('PUT NAME OF LECTURE', _fname)\
                                             .replace('[NAME]', _fname)
        for q in section.questions:
            q.display_text = q.question_text.replace('NAME OF LECTURE', _fname)\
                                            .replace('PUT NAME OF LECTURE', _fname)\
                                            .replace('[NAME]', _fname)

    questions = []
    for section in active_form.sections:
        questions.extend(section.questions)

    if request.method == 'POST':
        participant_type  = request.form.get('participant_type', 'student')
        participant_name  = request.form.get('participant_name', '').strip() or None
        participant_org   = request.form.get('participant_org', '').strip() or None
        participant_email = request.form.get('participant_email', '').strip() or None

        evaluation = Evaluation(
            student_id=None,
            course_id=course_id,
            form_id=active_form.id,
            participant_type=participant_type,
            participant_name=participant_name,
            participant_org=participant_org,
            participant_email=participant_email,
        )
        db.session.add(evaluation)
        db.session.flush()

        overall_score = 0
        likert_count  = 0
        for q in questions:
            if q.question_type == 'likert':
                val = request.form.get(f'q_{q.id}')
                if val:
                    resp = Response(evaluation_id=evaluation.id, form_question_id=q.id, likert_value=int(val))
                    db.session.add(resp)
                    overall_score += int(val)
                    likert_count  += 1
            elif q.question_type == 'text':
                val = request.form.get(f'q_{q.id}')
                if val:
                    resp = Response(evaluation_id=evaluation.id, form_question_id=q.id, text_value=val)
                    db.session.add(resp)
            elif q.question_type in ('multiple_choice', 'checkbox'):
                vals = request.form.getlist(f'q_{q.id}')
                if vals:
                    resp = Response(evaluation_id=evaluation.id, form_question_id=q.id,
                                    selected_options=json.dumps(vals))
                    db.session.add(resp)
        if likert_count > 0:
            evaluation.overall_score = round(overall_score / likert_count, 2)
        db.session.commit()
        flash('Thank you for your feedback!', 'success')
        return redirect(url_for('evaluation.thank_you'))

    return render_template('public_evaluation_form.html',
                           course=course, form=active_form,
                           facilitator_name=facilitator_name)

# ========== THANK YOU PAGE ==========
@bp.route('/thank-you')
def thank_you():
    return render_template('thank_you.html')