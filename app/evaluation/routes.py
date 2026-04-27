from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.evaluation import bp
from app.models import (User, Course, Enrollment, Evaluation, Form, FormQuestion, Response,
                        Department, Programme, FormSection, Campus)
from app.forms import CourseForm
import json
from datetime import datetime

@bp.route('/courses')
@login_required
def list_courses():
    if current_user.role == 'student':
        # Show only departments/programmes that are related to courses the student is enrolled in
        enrolled_ids = [e.course_id for e in Enrollment.query.filter_by(student_id=current_user.id).all()]
        if not enrolled_ids:
            departments = []
            programmes = []
        else:
            departments = Department.query.filter(
                Department.id.in_(
                    db.session.query(Programme.department_id).join(Course).filter(
                        Course.id.in_(enrolled_ids)
                    )
                )
            ).order_by(Department.name).all()
            programmes = Programme.query.filter(
                Programme.id.in_(
                    db.session.query(Course.programme_id).filter(
                        Course.id.in_(enrolled_ids)
                    )
                )
            ).order_by(Programme.name).all()
        return render_template('evaluation/select_programme.html',
                               departments=departments, programmes=programmes)
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

    course = Course.query.get_or_404(course_id)

    enrollment = Enrollment.query.filter_by(student_id=current_user.id, course_id=course_id).first()
    if not enrollment:
        flash('You are not enrolled in this course.', 'danger')
        return redirect(url_for('evaluation.list_courses'))

    existing = Evaluation.query.filter_by(student_id=current_user.id, course_id=course_id).first()
    if existing:
        flash('You have already evaluated this course.', 'warning')
        return redirect(url_for('evaluation.list_courses'))

    active_form = Form.query.filter_by(is_active=True).filter(
        (Form.target_level == course.level) | (Form.target_level == None)
    ).options(db.joinedload(Form.sections).joinedload(FormSection.questions)).first()
    if not active_form:
        flash('No active evaluation form for this course.', 'warning')
        return redirect(url_for('evaluation.list_courses'))

    if active_form.deadline and active_form.deadline < datetime.utcnow():
        flash('The evaluation deadline has passed.', 'danger')
        return redirect(url_for('evaluation.list_courses'))

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
        for q in section.questions:
            questions.append(q)

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

@bp.route('/course/add', methods=['GET', 'POST'])
@login_required
def add_course():
    if current_user.role not in ['admin', 'qa_officer']:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    form = CourseForm()
    form.department_id.choices = [(d.id, d.name) for d in Department.query.order_by('name')]
    form.programme_id.choices = [(p.id, p.name) for p in Programme.query.order_by('name')]
    lecturers = User.query.filter_by(role='lecturer').all()
    form.lecturer_id.choices = [(l.id, l.full_name) for l in lecturers]
    if current_user.campus_id is None:
        form.campus_id.choices = [(c.id, c.name) for c in Campus.query.order_by('name')]
    else:
        form.campus_id.choices = [(current_user.campus_id, Campus.query.get(current_user.campus_id).name)]
    if form.validate_on_submit():
        course = Course(
            code=form.code.data, name=form.name.data,
            campus_id=form.campus_id.data,
            course_type=form.course_type.data,
            department_id=form.department_id.data or None,
            programme_id=form.programme_id.data or None,
            level=form.level.data or None, semester=form.semester.data or None,
            academic_year=form.academic_year.data or None,
            lecturer_id=form.lecturer_id.data
        )
        db.session.add(course)
        db.session.commit()
        flash('Course added.', 'success')
        return redirect(url_for('evaluation.list_courses'))
    return render_template('evaluation/course_form.html', form=form, title='Add Module')