from flask import render_template, send_file, flash, redirect, url_for, Response, request
from flask_login import login_required, current_user
from app import db
from app.reports import bp
from app.models import (Course, Evaluation, FormQuestion, Response as EvalResponse,
                        FormSection, Form, Campus, User, Enrollment, Programme,
                        ReportAcknowledgement)
from app.utils.analysis import (compute_course_stats, compute_department_stats,
                                 compute_campus_summary, compute_institution_summary,
                                 qei_status, NAQS_LABELS)
from app.utils.visuals import (create_question_pie_chart, create_overall_pie_chart,
                               create_text_response_card, create_multiple_choice_chart)
from app.utils.pdf_generator import generate_pdf_report
from sqlalchemy import func
from datetime import datetime, timedelta
import io, json
import pandas as pd


def replace_lecturer(text, lecturer_name):
    return text.replace('NAME OF LECTURE', lecturer_name)\
               .replace('PUT NAME OF LECTURE', lecturer_name)\
               .replace('[NAME]', lecturer_name)


def _can_view_course(course):
    """Check if current user may view a course report."""
    role = current_user.role
    if role in ('qa_officer', 'admin', 'superadmin'):
        if current_user.campus_id is not None and course.campus_id != current_user.campus_id:
            return False
        return True
    if role == 'director':
        return course.campus_id == current_user.campus_id
    if role in ('ceo', 'superadmin'):
        return True
    return False


# ── Main dashboard dispatcher ─────────────────────────────────────────────────

@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'student':
        evaluations = Evaluation.query.filter_by(student_id=current_user.id).all()
        return render_template('reports/student_dashboard.html', evaluations=evaluations)

    if current_user.role == 'director':
        return redirect(url_for('reports.director_dashboard'))

    if current_user.role == 'ceo':
        return redirect(url_for('reports.ceo_dashboard'))

    if current_user.role in ('admin', 'superadmin') and current_user.campus_id is None:
        now = datetime.utcnow()
        day_ago   = now - timedelta(days=1)
        week_ago  = now - timedelta(weeks=1)
        month_ago = now - timedelta(days=30)
        daily_evals   = Evaluation.query.filter(Evaluation.submitted_at >= day_ago).count()
        weekly_evals  = Evaluation.query.filter(Evaluation.submitted_at >= week_ago).count()
        monthly_evals = Evaluation.query.filter(Evaluation.submitted_at >= month_ago).count()
        daily_active_users   = User.query.filter(User.last_active >= day_ago).count()
        weekly_active_users  = User.query.filter(User.last_active >= week_ago).count()
        monthly_active_users = User.query.filter(User.last_active >= month_ago).count()
        five_min_ago = now - timedelta(minutes=5)
        online_users = User.query.filter(User.last_active >= five_min_ago).count()
        return render_template('reports/head_admin_dashboard.html',
                               daily_evals=daily_evals, weekly_evals=weekly_evals,
                               monthly_evals=monthly_evals,
                               daily_active_users=daily_active_users,
                               weekly_active_users=weekly_active_users,
                               monthly_active_users=monthly_active_users,
                               online_users=online_users)

    if current_user.role in ('admin', 'superadmin') and current_user.campus_id is not None:
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
            total_evals   = Evaluation.query.join(Course).filter(Course.campus_id == campus.id).count()
            possible_evals = Enrollment.query.join(Course).filter(Course.campus_id == campus.id).count()
            participation = (total_evals / possible_evals * 100) if possible_evals > 0 else 0
            avg_score = db.session.query(func.avg(Evaluation.overall_score))\
                .join(Course).filter(Course.campus_id == campus.id).scalar()
            campus_data.append({
                'campus': campus, 'total_courses': total_courses, 'total_evals': total_evals,
                'possible_evals': possible_evals, 'participation': round(participation, 1),
                'avg_score': round(avg_score, 2) if avg_score else None,
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


# ── Director dashboard ────────────────────────────────────────────────────────

@bp.route('/director')
@login_required
def director_dashboard():
    if current_user.role != 'director':
        flash('Access denied.', 'danger')
        return redirect(url_for('reports.dashboard'))

    campus_id = current_user.campus_id
    if not campus_id:
        flash('Your account is not assigned to a campus.', 'warning')
        return redirect(url_for('main.index'))

    campus   = db.get_or_404(Campus, campus_id)
    summary  = compute_campus_summary(campus_id)

    # Load acknowledgement status for each course
    ack_map = {
        a.course_id: a
        for a in ReportAcknowledgement.query
        .filter_by(acknowledged_by=current_user.id).all()
    }
    for cs in summary['course_summaries']:
        cs['acknowledgement'] = ack_map.get(cs['course_id'])

    return render_template('reports/director_dashboard.html',
                           campus=campus, summary=summary)


# ── CEO dashboard ─────────────────────────────────────────────────────────────

@bp.route('/ceo')
@login_required
def ceo_dashboard():
    if current_user.role != 'ceo':
        flash('Access denied.', 'danger')
        return redirect(url_for('reports.dashboard'))

    institution = compute_institution_summary()

    # Load CEO acknowledgements for all courses
    ack_map = {
        a.course_id: a
        for a in ReportAcknowledgement.query
        .filter_by(acknowledged_by=current_user.id).all()
    }
    for campus_data in institution['campuses']:
        for cs in campus_data['course_summaries']:
            cs['acknowledgement'] = ack_map.get(cs['course_id'])

    return render_template('reports/ceo_dashboard.html', institution=institution)


# ── Per‑course QEI report ─────────────────────────────────────────────────────

@bp.route('/course/<int:course_id>/qei')
@login_required
def qei_report(course_id):
    course = db.get_or_404(Course, course_id)
    if not _can_view_course(course):
        flash('Access denied.', 'danger')
        return redirect(url_for('reports.dashboard'))

    stats = compute_course_stats(course_id)
    lecturer_name = course.lecturer.full_name if course.lecturer else 'the lecturer'
    for sec in stats.get('sections', []):
        sec['title'] = replace_lecturer(sec['title'], lecturer_name)

    return render_template('reports/qei_report.html',
                           course=course, stats=stats, naqs_labels=NAQS_LABELS)


# ── Acknowledge report (director / CEO) ──────────────────────────────────────

@bp.route('/course/<int:course_id>/acknowledge', methods=['POST'])
@login_required
def acknowledge_course(course_id):
    if current_user.role not in ('director', 'ceo'):
        flash('Access denied.', 'danger')
        return redirect(url_for('reports.dashboard'))

    course = db.get_or_404(Course, course_id)
    if not _can_view_course(course):
        flash('Access denied.', 'danger')
        return redirect(url_for('reports.dashboard'))

    notes          = request.form.get('notes', '').strip()
    action_needed  = bool(request.form.get('action_required'))

    ack = ReportAcknowledgement.query.filter_by(
        course_id=course_id, acknowledged_by=current_user.id
    ).first()
    if ack:
        ack.acknowledged_at = datetime.utcnow()
        ack.notes           = notes
        ack.action_required = action_needed
    else:
        ack = ReportAcknowledgement(
            course_id=course_id,
            acknowledged_by=current_user.id,
            notes=notes,
            action_required=action_needed,
            role=current_user.role,
        )
        db.session.add(ack)
    db.session.commit()
    flash('Report acknowledged.', 'success')

    if current_user.role == 'ceo':
        return redirect(url_for('reports.ceo_dashboard'))
    return redirect(url_for('reports.director_dashboard'))


# ── Standard course report (QA officer, admin, director, ceo) ────────────────

@bp.route('/course/<int:course_id>')
@login_required
def course_report(course_id):
    course = db.get_or_404(Course, course_id)
    lecturer_name = course.lecturer.full_name if course.lecturer else 'the lecturer'

    if current_user.role == 'student':
        evaluation = Evaluation.query.filter_by(
            student_id=current_user.id, course_id=course_id
        ).first()
        if not evaluation:
            flash('You have not evaluated this course.', 'warning')
            return redirect(url_for('reports.dashboard'))
        form = db.session.get(Form, evaluation.form_id)
        sections = FormSection.query.filter_by(form_id=form.id).order_by(FormSection.order).all()
        sec_data = []
        for sec in sections:
            qs = FormQuestion.query.filter_by(section_id=sec.id).order_by(FormQuestion.order).all()
            qlist = []
            for q in qs:
                q.display_text = replace_lecturer(q.question_text, lecturer_name)
                resp = EvalResponse.query.filter_by(
                    evaluation_id=evaluation.id, form_question_id=q.id
                ).first()
                qlist.append({'question': q, 'response': resp})
            sec_data.append({'section': sec, 'questions': qlist})
        return render_template('reports/student_submission.html',
                               course=course, form=form, sections=sec_data,
                               evaluation=evaluation)

    if current_user.role in ('qa_officer', 'admin', 'superadmin', 'director', 'ceo'):
        if not _can_view_course(course):
            flash('Access denied.', 'danger')
            return redirect(url_for('reports.dashboard'))

        stats = compute_course_stats(course_id)
        for sec in stats.get('sections', []):
            sec['title'] = replace_lecturer(sec['title'], lecturer_name)
            for q in sec.get('likert_questions', []):
                q['text'] = replace_lecturer(q['text'], lecturer_name)
            for q in sec.get('text_questions', []):
                q['text'] = replace_lecturer(q['text'], lecturer_name)

        overall_pie = None
        if stats['overall_distribution']:
            labels = ['Strongly\nDisagree', 'Disagree', 'Neutral', 'Agree', 'Strongly\nAgree']
            values = [stats['overall_distribution'].get(i, 0) for i in range(1, 6)]
            overall_pie = create_overall_pie_chart(labels, values, 'Overall Satisfaction Distribution')

        question_cards = []
        for sec in stats['sections']:
            for q in sec.get('likert_questions', []):
                chart_html = create_question_pie_chart(
                    q['text'], q['mean'] or 0, q['frequency'], q['count']
                )
                question_cards.append({
                    'section_title': sec['title'],
                    'question_text': q['text'],
                    'question_type': 'likert',
                    'chart_html':    chart_html,
                    'count':         q['count'],
                })
            for q in sec.get('text_questions', []):
                card_html = create_text_response_card(q['text'], q['comments'])
                question_cards.append({
                    'section_title': sec['title'],
                    'question_text': q['text'],
                    'question_type': 'text',
                    'card_html':     card_html,
                    'count':         len(q['comments']),
                })
            for q in sec.get('multiple_choice', []):
                chart_html = create_multiple_choice_chart(
                    q['text'], q['options'], q['counts'], q['total_responses']
                )
                question_cards.append({
                    'section_title': sec['title'],
                    'question_text': q['text'],
                    'question_type': 'multiple_choice',
                    'chart_html':    chart_html,
                    'count':         q['total_responses'],
                })

        # Load all acknowledgements for this course (director + CEO)
        acknowledgements = ReportAcknowledgement.query.filter_by(
            course_id=course_id
        ).order_by(ReportAcknowledgement.acknowledged_at.desc()).all()

        return render_template('reports/course_report.html',
                               course=course, stats=stats,
                               overall_pie=overall_pie,
                               question_cards=question_cards,
                               acknowledgements=acknowledgements)

    flash('Access denied.', 'danger')
    return redirect(url_for('reports.dashboard'))


# ── PDF download ──────────────────────────────────────────────────────────────

@bp.route('/course/<int:course_id>/pdf')
@login_required
def download_pdf(course_id):
    course = db.get_or_404(Course, course_id)
    lecturer_name = course.lecturer.full_name if course.lecturer else 'the lecturer'

    if current_user.role == 'student':
        evaluation = Evaluation.query.filter_by(
            student_id=current_user.id, course_id=course_id
        ).first()
        if not evaluation:
            flash('Access denied.', 'danger')
            return redirect(url_for('reports.dashboard'))
        pdf_bytes = _generate_student_submission_pdf(course, evaluation, lecturer_name)
        return send_file(io.BytesIO(pdf_bytes), mimetype='application/pdf',
                         as_attachment=True,
                         download_name=f'submission_{course.code}.pdf')

    if current_user.role in ('qa_officer', 'admin', 'superadmin', 'director', 'ceo'):
        if not _can_view_course(course):
            flash('Access denied.', 'danger')
            return redirect(url_for('reports.dashboard'))

        stats = compute_course_stats(course_id)
        for sec in stats.get('sections', []):
            sec['title'] = replace_lecturer(sec['title'], lecturer_name)
            for q in sec.get('likert_questions', []):
                q['text'] = replace_lecturer(q['text'], lecturer_name)
            for q in sec.get('text_questions', []):
                q['text'] = replace_lecturer(q['text'], lecturer_name)

        dept_stats  = compute_department_stats()
        college_mean = dept_stats.get('college_mean')
        from app.utils.analysis import generate_insights, generate_prediction
        insights   = generate_insights(stats['sections'], stats['overall_mean'], college_mean)
        prediction = stats.get('prediction', '')
        pdf_bytes  = generate_pdf_report(course, stats, insights, prediction)
        return send_file(io.BytesIO(pdf_bytes), mimetype='application/pdf',
                         as_attachment=True,
                         download_name=f'report_{course.code}_{course.semester}.pdf')

    flash('Access denied.', 'danger')
    return redirect(url_for('reports.dashboard'))


# ── Campus PDF report ─────────────────────────────────────────────────────────

@bp.route('/campus/<int:campus_id>/report')
@login_required
def campus_report(campus_id):
    if current_user.role not in ('qa_officer', 'director', 'ceo', 'admin', 'superadmin'):
        flash('Access denied.', 'danger')
        return redirect(url_for('reports.dashboard'))
    if current_user.role == 'director' and current_user.campus_id != campus_id:
        flash('Access denied.', 'danger')
        return redirect(url_for('reports.dashboard'))
    if current_user.role in ('qa_officer', 'admin') and current_user.campus_id is not None \
            and current_user.campus_id != campus_id:
        flash('Access denied.', 'danger')
        return redirect(url_for('reports.dashboard'))

    campus    = db.get_or_404(Campus, campus_id)
    pdf_bytes = _generate_campus_report_pdf(campus)
    return send_file(io.BytesIO(pdf_bytes), mimetype='application/pdf',
                     as_attachment=True,
                     download_name=f'campus_report_{campus.name}.pdf')


# ── CSV / Excel export ────────────────────────────────────────────────────────

def _build_evaluation_dataframe(course_id):
    course = db.session.get(Course, course_id)
    if not course:
        return None
    lecturer_name = course.lecturer.full_name if course.lecturer else 'the lecturer'
    evaluations   = Evaluation.query.filter_by(course_id=course_id).order_by(Evaluation.submitted_at).all()
    if not evaluations:
        return None
    form = (db.session.get(Form, course.form_id) if course.form_id
            else db.session.get(Form, evaluations[0].form_id))
    if not form:
        return None
    sections = FormSection.query.filter_by(form_id=form.id).order_by(FormSection.order).all()
    rows = []
    for ev in evaluations:
        row = {
            'Submission ID': ev.id,
            'Submitted At':  ev.submitted_at.strftime('%Y-%m-%d %H:%M') if ev.submitted_at else '',
            'Student':       ev.student.full_name if ev.student else 'Anonymous',
            'Participant Type': ev.participant_type or 'student',
            'Overall Score': ev.overall_score,
        }
        for sec in sections:
            questions = FormQuestion.query.filter_by(section_id=sec.id).order_by(FormQuestion.order).all()
            for q in questions:
                col = replace_lecturer(q.question_text, lecturer_name)
                if len(col) > 60:
                    col = col[:57] + '...'
                resp = EvalResponse.query.filter_by(
                    evaluation_id=ev.id, form_question_id=q.id
                ).first()
                if resp:
                    if q.question_type == 'likert':
                        row[col] = resp.likert_value
                    elif q.question_type == 'text':
                        row[col] = resp.text_value or ''
                    elif q.question_type in ('multiple_choice', 'checkbox'):
                        try:
                            row[col] = ', '.join(json.loads(resp.selected_options)) if resp.selected_options else ''
                        except Exception:
                            row[col] = resp.selected_options or ''
                else:
                    row[col] = ''
        rows.append(row)
    return pd.DataFrame(rows)


@bp.route('/course/<int:course_id>/export_csv')
@login_required
def export_csv(course_id):
    if current_user.role not in ('admin', 'superadmin', 'qa_officer', 'director', 'ceo'):
        flash('Access denied.', 'danger')
        return redirect(url_for('reports.dashboard'))
    course = db.get_or_404(Course, course_id)
    if not _can_view_course(course):
        flash('Access denied.', 'danger')
        return redirect(url_for('reports.dashboard'))
    df = _build_evaluation_dataframe(course_id)
    if df is None or df.empty:
        flash('No evaluation data to export.', 'warning')
        return redirect(url_for('reports.course_report', course_id=course_id))
    output = io.BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)
    return send_file(output, mimetype='text/csv', as_attachment=True,
                     download_name=f'evaluation_{course.code}.csv')


@bp.route('/course/<int:course_id>/export_excel')
@login_required
def export_excel(course_id):
    if current_user.role not in ('admin', 'superadmin', 'qa_officer', 'director', 'ceo'):
        flash('Access denied.', 'danger')
        return redirect(url_for('reports.dashboard'))
    course = db.get_or_404(Course, course_id)
    if not _can_view_course(course):
        flash('Access denied.', 'danger')
        return redirect(url_for('reports.dashboard'))
    df = _build_evaluation_dataframe(course_id)
    if df is None or df.empty:
        flash('No evaluation data to export.', 'warning')
        return redirect(url_for('reports.course_report', course_id=course_id))
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Evaluations')
    output.seek(0)
    return send_file(output,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True,
                     download_name=f'evaluation_{course.code}.xlsx')


# ── Private helpers ───────────────────────────────────────────────────────────

def _generate_student_submission_pdf(course, evaluation, lecturer_name):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.units import inch

    buffer = io.BytesIO()
    doc    = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story  = []

    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=16,
                                 alignment=1, textColor=colors.HexColor('#673ab7'))
    story.append(Paragraph(f"Evaluation Submission: {course.code} - {course.name}", title_style))
    story.append(Spacer(1, 0.15*inch))
    story.append(Paragraph(f"<b>Student:</b> {evaluation.student.full_name if evaluation.student else 'Anonymous'}",
                            styles['Normal']))
    story.append(Paragraph(f"<b>Semester:</b> {course.semester} {course.academic_year}", styles['Normal']))
    story.append(Paragraph(f"<b>Submitted:</b> {evaluation.submitted_at.strftime('%d %b %Y')}", styles['Normal']))
    story.append(Spacer(1, 0.15*inch))

    form     = db.session.get(Form, evaluation.form_id)
    sections = FormSection.query.filter_by(form_id=form.id).order_by(FormSection.order).all()
    for sec in sections:
        story.append(Paragraph(f"<b>{replace_lecturer(sec.title, lecturer_name)}</b>", styles['Heading2']))
        questions = FormQuestion.query.filter_by(section_id=sec.id).order_by(FormQuestion.order).all()
        for q in questions:
            display_text = replace_lecturer(q.question_text, lecturer_name)
            resp = EvalResponse.query.filter_by(
                evaluation_id=evaluation.id, form_question_id=q.id
            ).first()
            story.append(Paragraph(f"<i>{display_text}</i>", styles['Normal']))
            if resp:
                if q.question_type == 'likert' and resp.likert_value:
                    story.append(Paragraph(f"Answer: {resp.likert_value} / 5", styles['Normal']))
                elif q.question_type == 'text' and resp.text_value:
                    story.append(Paragraph(f"Answer: {resp.text_value}", styles['Normal']))
                elif q.question_type in ('multiple_choice', 'checkbox') and resp.selected_options:
                    try:
                        opts = json.loads(resp.selected_options)
                        story.append(Paragraph(f"Answer: {', '.join(opts)}", styles['Normal']))
                    except Exception:
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


def _generate_campus_report_pdf(campus):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.units import inch

    buffer = io.BytesIO()
    doc    = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story  = []

    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18,
                                 alignment=1, textColor=colors.HexColor('#673ab7'))
    story.append(Paragraph(f"Campus Report: {campus.name}", title_style))
    story.append(Spacer(1, 0.15*inch))

    total_courses  = Course.query.filter_by(campus_id=campus.id).count()
    total_evals    = Evaluation.query.join(Course).filter(Course.campus_id == campus.id).count()
    possible_evals = Enrollment.query.join(Course).filter(Course.campus_id == campus.id).count()
    participation  = (total_evals / possible_evals * 100) if possible_evals > 0 else 0
    avg_score      = db.session.query(func.avg(Evaluation.overall_score))\
        .join(Course).filter(Course.campus_id == campus.id).scalar()

    story.append(Paragraph(f"Number of courses: {total_courses}", styles['Normal']))
    story.append(Paragraph(f"Evaluations submitted: {total_evals}", styles['Normal']))
    story.append(Paragraph(f"Enrolled students: {possible_evals}", styles['Normal']))
    story.append(Paragraph(f"Participation rate: {participation:.1f}%", styles['Normal']))
    story.append(Paragraph(
        f"Average score: {avg_score:.2f}" if avg_score else "Average score: N/A",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.15*inch))

    courses = Course.query.filter_by(campus_id=campus.id).all()
    data = [['Course Code', 'Responses', 'Mean Score', 'QEI']]
    for c in courses:
        cs  = compute_course_stats(c.id)
        qei = cs.get('overall_qei')
        data.append([
            c.code,
            str(cs['num_responses']),
            f"{cs['overall_mean']:.2f}" if cs['overall_mean'] else '-',
            f"{qei:.2f}" if qei is not None else '-',
        ])
    if len(data) > 1:
        table = Table(data, colWidths=[2.5*inch, 1.2*inch, 1.2*inch, 1.2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#673ab7')),
            ('TEXTCOLOR',  (0,0), (-1,0), colors.whitesmoke),
            ('GRID',       (0,0), (-1,-1), 1, colors.black),
        ]))
        story.append(table)

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
