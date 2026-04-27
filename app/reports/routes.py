from flask import render_template, send_file, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.reports import bp
from app.models import (Course, Evaluation, FormQuestion, Response, FormSection, Form,
                        Campus, User, Enrollment, Programme)
from app.utils.analysis import compute_course_stats, compute_department_stats, generate_insights
from app.utils.visuals import create_bar_chart, create_pie_chart, create_radar_chart
from app.utils.pdf_generator import generate_pdf_report
from sqlalchemy import func
from datetime import datetime, timedelta
import io, json

def replace_lecturer(text, lecturer_name):
    return text.replace('NAME OF LECTURE', lecturer_name)\
               .replace('PUT NAME OF LECTURE', lecturer_name)\
               .replace('[NAME]', lecturer_name)

@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'student':
        evaluations = Evaluation.query.filter_by(student_id=current_user.id).all()
        return render_template('reports/student_dashboard.html', evaluations=evaluations)

    if current_user.role == 'admin' and current_user.campus_id is None:
        now = datetime.utcnow()
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(weeks=1)
        month_ago = now - timedelta(days=30)

        daily_evals = Evaluation.query.filter(Evaluation.submitted_at >= day_ago).count()
        weekly_evals = Evaluation.query.filter(Evaluation.submitted_at >= week_ago).count()
        monthly_evals = Evaluation.query.filter(Evaluation.submitted_at >= month_ago).count()

        daily_active_users = User.query.filter(User.last_active >= day_ago).count()
        weekly_active_users = User.query.filter(User.last_active >= week_ago).count()
        monthly_active_users = User.query.filter(User.last_active >= month_ago).count()

        five_min_ago = now - timedelta(minutes=5)
        online_users = User.query.filter(User.last_active >= five_min_ago).count()

        return render_template('reports/head_admin_dashboard.html',
                               daily_evals=daily_evals,
                               weekly_evals=weekly_evals,
                               monthly_evals=monthly_evals,
                               daily_active_users=daily_active_users,
                               weekly_active_users=weekly_active_users,
                               monthly_active_users=monthly_active_users,
                               online_users=online_users)

    if current_user.role == 'admin' and current_user.campus_id is not None:
        campus_id = current_user.campus_id
        programme_counts = db.session.query(Programme.name, func.count(Enrollment.id))\
            .join(Course, Enrollment.course_id == Course.id)\
            .join(Programme, Course.programme_id == Programme.id)\
            .filter(Course.campus_id == campus_id)\
            .group_by(Programme.name).all()
        five_min_ago = datetime.utcnow() - timedelta(minutes=5)
        campus_online = User.query.filter_by(campus_id=campus_id)\
            .filter(User.last_active >= five_min_ago).count()
        role_counts = db.session.query(User.role, func.count(User.id))\
            .filter_by(campus_id=campus_id).group_by(User.role).all()
        return render_template('reports/campus_admin_dashboard.html',
                               programme_counts=programme_counts,
                               campus_online=campus_online,
                               role_counts=role_counts)

    if current_user.role == 'qa_officer' and current_user.campus_id is None:
        campuses = Campus.query.all()
        campus_data = []
        for campus in campuses:
            total_courses = Course.query.filter_by(campus_id=campus.id).count()
            total_evals = Evaluation.query.join(Course).filter(Course.campus_id == campus.id).count()
            possible_evals = Enrollment.query.join(Course).filter(Course.campus_id == campus.id).count()
            participation = (total_evals / possible_evals * 100) if possible_evals > 0 else 0
            avg_score = db.session.query(func.avg(Evaluation.overall_score))\
                .join(Course).filter(Course.campus_id == campus.id).scalar()
            campus_data.append({
                'campus': campus,
                'total_courses': total_courses,
                'total_evals': total_evals,
                'possible_evals': possible_evals,
                'participation': round(participation, 1),
                'avg_score': round(avg_score, 2) if avg_score else None
            })
        return render_template('reports/qa_head_dashboard.html', campus_data=campus_data)

    if current_user.role == 'qa_officer' and current_user.campus_id is not None:
        campus_id = current_user.campus_id
        programmes = Programme.query.join(Course).filter(Course.campus_id == campus_id).distinct().all()
        programme_data = []
        for prog in programmes:
            courses = Course.query.filter_by(programme_id=prog.id, campus_id=campus_id).order_by(Course.code).all()
            if courses:
                programme_data.append({'programme': prog, 'courses': courses})
        return render_template('reports/campus_qa_dashboard.html', programme_data=programme_data)

    flash('No report dashboard available for your role.', 'info')
    return redirect(url_for('main.index'))

# ---------- Course report (extended access) ----------
@bp.route('/course/<int:course_id>')
@login_required
def course_report(course_id):
    course = Course.query.get_or_404(course_id)
    lecturer_name = course.lecturer.full_name if course.lecturer else 'the lecturer'

    if current_user.role == 'student':
        evaluation = Evaluation.query.filter_by(student_id=current_user.id, course_id=course_id).first()
        if not evaluation:
            flash('You have not evaluated this course.', 'warning')
            return redirect(url_for('reports.dashboard'))
        form = Form.query.get(evaluation.form_id)
        sections = FormSection.query.filter_by(form_id=form.id).order_by(FormSection.order).all()
        sec_data = []
        for sec in sections:
            qs = FormQuestion.query.filter_by(section_id=sec.id).order_by(FormQuestion.order).all()
            qlist = []
            for q in qs:
                q.display_text = replace_lecturer(q.question_text, lecturer_name)
                resp = Response.query.filter_by(evaluation_id=evaluation.id, form_question_id=q.id).first()
                qlist.append({'question': q, 'response': resp})
            sec_data.append({'section': sec, 'questions': qlist})
        return render_template('reports/student_submission.html',
                               course=course, form=form, sections=sec_data, evaluation=evaluation)

    if current_user.role == 'qa_officer':
        if current_user.campus_id is not None and course.campus_id != current_user.campus_id:
            flash('Access denied.', 'danger')
            return redirect(url_for('reports.dashboard'))
        stats = compute_course_stats(course_id)
        for sec in stats.get('sections', []):
            sec['title'] = replace_lecturer(sec['title'], lecturer_name)
            for q in sec.get('likert_questions', []):
                q['text'] = replace_lecturer(q['text'], lecturer_name)
            for q in sec.get('text_questions', []):
                q['text'] = replace_lecturer(q['text'], lecturer_name)
            for q in sec.get('multiple_choice', []):
                q['text'] = replace_lecturer(q['text'], lecturer_name)
        dept_stats = compute_department_stats()
        college_mean = dept_stats.get('college_mean')
        insights = generate_insights(stats['sections'], stats['overall_mean'], college_mean)
        prediction = stats.get('prediction', '')
        charts = {}
        if stats['sections']:
            sections_names = [sec['title'][:20] for sec in stats['sections']]
            sections_means = [sec['section_mean'] if sec['section_mean'] else 0 for sec in stats['sections']]
            sections_stds = [sec['section_std'] if sec['section_std'] else 0 for sec in stats['sections']]
            charts['section_bar'] = create_bar_chart(sections_names, sections_means, 'Section Mean Scores', errors=sections_stds)
            for sec in stats['sections']:
                if sec['likert_questions']:
                    cat_names = [q['text'][:25] for q in sec['likert_questions']]
                    cat_means = [q['mean'] if q['mean'] else 0 for q in sec['likert_questions']]
                    charts['radar'] = create_radar_chart(cat_names, cat_means, f"Profile of {sec['title']}")
                    break
        if stats['overall_distribution']:
            labels = list(stats['overall_distribution'].keys())
            values = list(stats['overall_distribution'].values())
            charts['pie'] = create_pie_chart(labels, values, 'Overall Satisfaction Distribution')
        return render_template('reports/course_report.html', course=course, stats=stats,
                               charts=charts, insights=insights, prediction=prediction)

    flash('Access denied.', 'danger')
    return redirect(url_for('reports.dashboard'))

# ---------- PDF DOWNLOAD (restored) ----------
@bp.route('/course/<int:course_id>/pdf')
@login_required
def download_pdf(course_id):
    course = Course.query.get_or_404(course_id)
    lecturer_name = course.lecturer.full_name if course.lecturer else 'the lecturer'

    # Student: download submission PDF
    if current_user.role == 'student':
        evaluation = Evaluation.query.filter_by(student_id=current_user.id, course_id=course_id).first()
        if not evaluation:
            flash('Access denied.', 'danger')
            return redirect(url_for('reports.dashboard'))
        pdf_bytes = generate_student_submission_pdf(course, evaluation, lecturer_name)
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'submission_{course.code}.pdf'
        )

    # QA: download analytics PDF
    if current_user.role == 'qa_officer':
        if current_user.campus_id is not None and course.campus_id != current_user.campus_id:
            flash('Access denied.', 'danger')
            return redirect(url_for('reports.dashboard'))
        stats = compute_course_stats(course_id)
        # Replace lecturer name in stats
        for sec in stats.get('sections', []):
            sec['title'] = replace_lecturer(sec['title'], lecturer_name)
            for q in sec.get('likert_questions', []):
                q['text'] = replace_lecturer(q['text'], lecturer_name)
            for q in sec.get('text_questions', []):
                q['text'] = replace_lecturer(q['text'], lecturer_name)
            for q in sec.get('multiple_choice', []):
                q['text'] = replace_lecturer(q['text'], lecturer_name)
        dept_stats = compute_department_stats()
        college_mean = dept_stats.get('college_mean')
        insights = generate_insights(stats['sections'], stats['overall_mean'], college_mean)
        prediction = stats.get('prediction', '')
        pdf_bytes = generate_pdf_report(course, stats, insights, prediction)
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'report_{course.code}_{course.semester}.pdf'
        )

    flash('Access denied.', 'danger')
    return redirect(url_for('reports.dashboard'))

# ---------- Campus PDF download for QA Head Office ----------
@bp.route('/campus/<int:campus_id>/report')
@login_required
def campus_report(campus_id):
    if not (current_user.role == 'qa_officer' and current_user.campus_id is None):
        flash('Access denied.', 'danger')
        return redirect(url_for('reports.dashboard'))
    campus = Campus.query.get_or_404(campus_id)
    pdf_bytes = generate_campus_report_pdf(campus)
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'campus_report_{campus.name}.pdf'
    )

# ---------- Helper: Student submission PDF ----------
def generate_student_submission_pdf(course, evaluation, lecturer_name):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.units import inch

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=16, alignment=1,
                                 textColor=colors.HexColor('#009EDB'))
    story.append(Paragraph(f"Evaluation Submission: {course.code} - {course.name}", title_style))
    story.append(Spacer(1, 0.15*inch))
    story.append(Paragraph(f"<b>Student:</b> {evaluation.student.full_name}", styles['Normal']))
    story.append(Paragraph(f"<b>Semester:</b> {course.semester} {course.academic_year}", styles['Normal']))
    story.append(Paragraph(f"<b>Submitted:</b> {evaluation.submitted_at.strftime('%d %b %Y')}", styles['Normal']))
    story.append(Spacer(1, 0.15*inch))

    form = Form.query.get(evaluation.form_id)
    sections = FormSection.query.filter_by(form_id=form.id).order_by(FormSection.order).all()
    for sec in sections:
        sec_title = replace_lecturer(sec.title, lecturer_name)
        story.append(Paragraph(f"<b>{sec_title}</b>", styles['Heading2']))
        questions = FormQuestion.query.filter_by(section_id=sec.id).order_by(FormQuestion.order).all()
        for q in questions:
            display_text = replace_lecturer(q.question_text, lecturer_name)
            resp = Response.query.filter_by(evaluation_id=evaluation.id, form_question_id=q.id).first()
            story.append(Paragraph(f"<i>{display_text}</i>", styles['Normal']))
            if resp:
                if q.question_type == 'likert' and resp.likert_value:
                    story.append(Paragraph(f"Answer: {resp.likert_value} / 5", styles['Normal']))
                elif q.question_type == 'text' and resp.text_value:
                    story.append(Paragraph(f"Answer: {resp.text_value}", styles['Normal']))
                elif q.question_type in ['multiple_choice', 'checkbox'] and resp.selected_options:
                    try:
                        options = json.loads(resp.selected_options)
                        story.append(Paragraph(f"Answer: {', '.join(options)}", styles['Normal']))
                    except:
                        story.append(Paragraph(f"Answer: {resp.selected_options}", styles['Normal']))
                else:
                    story.append(Paragraph("Answer: -", styles['Normal']))
            else:
                story.append(Paragraph("Answer: - (not answered)", styles['Normal']))
            story.append(Spacer(1, 0.05*inch))
        story.append(Spacer(1, 0.15*inch))
    doc.build(story)
    buffer.seek(0)
    return buffer.read()

# ---------- Helper: Campus PDF report ----------
def generate_campus_report_pdf(campus):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.units import inch

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, alignment=1,
                                 textColor=colors.HexColor('#009EDB'))
    story.append(Paragraph(f"Tathmini ya {campus.name}", title_style))
    story.append(Spacer(1, 0.15*inch))

    total_courses = Course.query.filter_by(campus_id=campus.id).count()
    total_evals = Evaluation.query.join(Course).filter(Course.campus_id == campus.id).count()
    possible_evals = Enrollment.query.join(Course).filter(Course.campus_id == campus.id).count()
    participation = (total_evals / possible_evals * 100) if possible_evals > 0 else 0
    avg_score = db.session.query(func.avg(Evaluation.overall_score))\
        .join(Course).filter(Course.campus_id == campus.id).scalar()

    story.append(Paragraph(f"Number of courses: {total_courses}", styles['Normal']))
    story.append(Paragraph(f"Evaluations submitted: {total_evals}", styles['Normal']))
    story.append(Paragraph(f"Enrolled students: {possible_evals}", styles['Normal']))
    story.append(Paragraph(f"Participation rate: {participation:.1f}%", styles['Normal']))
    story.append(Paragraph(f"Average score: {avg_score:.2f}" if avg_score else "Average score: N/A", styles['Normal']))
    story.append(Spacer(1, 0.15*inch))

    courses = Course.query.filter_by(campus_id=campus.id).all()
    data = [['Course Code', 'Responses', 'Mean Score']]
    for c in courses:
        cs = compute_course_stats(c.id)
        data.append([c.code, str(cs['num_responses']),
                     f"{cs['overall_mean']:.2f}" if cs['overall_mean'] else '-'])
    if len(data) > 1:
        table = Table(data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#009EDB')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ]))
        story.append(table)

    doc.build(story)
    buffer.seek(0)
    return buffer.read()