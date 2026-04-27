from collections import defaultdict
from app.models import Evaluation, Response, FormQuestion, Course, Form, FormSection
import json
import numpy as np

def compute_course_stats(course_id, student_id=None):
    course = Course.query.get(course_id)
    if not course:
        return {
            'course_id': course_id,
            'course_name': 'Unknown',
            'course_code': 'Unknown',
            'num_responses': 0,
            'sections': [],
            'overall_distribution': {},
            'overall_mean': None,
            'overall_std': None,
            'strengths': [],
            'weaknesses': [],
            'insights': [],
            'prediction': ''
        }

    query = Evaluation.query.filter_by(course_id=course_id)
    if student_id:
        query = query.filter_by(student_id=student_id)

    evaluations = query.all()
    if not evaluations:
        return {
            'course_id': course.id,
            'course_name': course.name,
            'course_code': course.code,
            'semester': course.semester,
            'academic_year': course.academic_year,
            'lecturer': course.lecturer.full_name if course.lecturer else 'Not assigned',
            'num_responses': 0,
            'sections': [],
            'overall_distribution': {},
            'overall_mean': None,
            'overall_std': None,
            'strengths': [],
            'weaknesses': [],
            'insights': [],
            'prediction': ''
        }

    form_id = evaluations[0].form_id
    form = Form.query.get(form_id)
    sections_db = FormSection.query.filter_by(form_id=form_id).order_by(FormSection.order).all()

    sections_data = []
    all_likert_scores = []
    for section in sections_db:
        likert_questions = FormQuestion.query.filter_by(section_id=section.id, question_type='likert').order_by(FormQuestion.order).all()
        text_questions = FormQuestion.query.filter_by(section_id=section.id, question_type='text').order_by(FormQuestion.order).all()
        mc_questions = FormQuestion.query.filter_by(section_id=section.id, question_type='multiple_choice').order_by(FormQuestion.order).all()

        likert_data = defaultdict(list)
        text_responses = defaultdict(list)
        mc_responses = defaultdict(list)

        for eval in evaluations:
            for resp in eval.responses:
                if resp.form_question_id in [q.id for q in likert_questions] and resp.likert_value:
                    likert_data[resp.form_question_id].append(resp.likert_value)
                    all_likert_scores.append(resp.likert_value)
                elif resp.form_question_id in [q.id for q in text_questions] and resp.text_value:
                    text_responses[resp.form_question_id].append(resp.text_value)
                elif resp.form_question_id in [q.id for q in mc_questions] and resp.selected_options:
                    try:
                        options = json.loads(resp.selected_options)
                        mc_responses[resp.form_question_id].extend(options)
                    except:
                        pass

        question_stats = []
        for q in likert_questions:
            scores = likert_data.get(q.id, [])
            count = len(scores)
            mean = np.mean(scores) if scores else None
            std = np.std(scores) if scores else None
            freq = {i: scores.count(i) for i in range(1,6)} if scores else {}
            question_stats.append({
                'id': q.id,
                'text': q.question_text,
                'category': q.category or section.title,
                'mean': mean,
                'std': std,
                'count': count,
                'frequency': freq   # frequency distribution for the table
            })

        text_stats = [{'id': q.id, 'text': q.question_text, 'comments': text_responses.get(q.id, [])} for q in text_questions]
        mc_stats = []
        for q in mc_questions:
            responses = mc_responses.get(q.id, [])
            options = json.loads(q.options) if q.options else []
            counts = {opt: responses.count(opt) for opt in options}
            mc_stats.append({
                'id': q.id,
                'text': q.question_text,
                'options': options,
                'counts': counts,
                'total_responses': len(responses)
            })

        sec_means = [q['mean'] for q in question_stats if q['mean'] is not None]
        section_mean = np.mean(sec_means) if sec_means else None
        section_std = np.std(sec_means) if sec_means else None

        sections_data.append({
            'section_id': section.id,
            'title': section.title,
            'order': section.order,
            'likert_questions': question_stats,
            'text_questions': text_stats,
            'multiple_choice': mc_stats,
            'section_mean': section_mean,
            'section_std': section_std
        })

    overall_scores = []
    for eval in evaluations:
        if eval.overall_score:
            overall_scores.append(eval.overall_score)
    if overall_scores:
        overall_mean = np.mean(overall_scores)
        overall_std = np.std(overall_scores)
        overall_dist = {i: overall_scores.count(i) for i in range(1,6)}
    else:
        overall_mean = None
        overall_std = None
        overall_dist = {}

    all_questions_flat = []
    for sec in sections_data:
        for q in sec['likert_questions']:
            if q['mean'] is not None:
                all_questions_flat.append(q)
    all_questions_flat.sort(key=lambda x: x['mean'], reverse=True)

    strengths = [q for q in all_questions_flat if q['mean'] >= 4.0][:5]
    weaknesses = [q for q in all_questions_flat if q['mean'] <= 2.5][:5]

    insights = generate_insights(sections_data, overall_mean, None)
    prediction = generate_prediction(sections_data, overall_mean)

    return {
        'course_id': course.id,
        'course_name': course.name,
        'course_code': course.code,
        'semester': course.semester,
        'academic_year': course.academic_year,
        'lecturer': course.lecturer.full_name if course.lecturer else 'Not assigned',
        'form_title': form.title if form else 'Unknown Form',
        'num_responses': len(evaluations),
        'sections': sections_data,
        'overall_distribution': overall_dist,
        'overall_mean': overall_mean,
        'overall_std': overall_std,
        'strengths': strengths,
        'weaknesses': weaknesses,
        'insights': insights,
        'prediction': prediction
    }

def compute_department_stats():
    courses = Course.query.all()
    means = []
    for c in courses:
        stats = compute_course_stats(c.id)
        if stats and stats.get('overall_mean') is not None:
            means.append(stats['overall_mean'])
    return {
        'college_mean': np.mean(means) if means else None,
        'total_courses': len(courses)
    }

def generate_insights(sections_data, overall_mean, college_mean):
    insights = []
    if overall_mean is None:
        insights.append("No evaluation data available for insights.")
        return insights

    # Overall satisfaction
    if overall_mean >= 4.0:
        insights.append(f"The course received a high overall satisfaction score (mean {overall_mean:.2f}), indicating strong student approval.")
    elif overall_mean <= 2.5:
        insights.append(f"The overall satisfaction score is low (mean {overall_mean:.2f}), signaling an urgent need for improvement.")
    else:
        insights.append(f"The overall satisfaction is moderate (mean {overall_mean:.2f}). There is room for improvement.")

    # Comparison with college average
    if college_mean is not None:
        diff = overall_mean - college_mean
        if diff > 0.5:
            insights.append(f"This course performs above the college average ({college_mean:.2f}).")
        elif diff < -0.5:
            insights.append(f"This course is below the college average ({college_mean:.2f}). Action is recommended.")

    # Section highlights
    for sec in sections_data:
        if sec['section_mean'] is not None:
            if sec['section_mean'] >= 4.0:
                insights.append(f"Section '{sec['title']}' scored highly ({sec['section_mean']:.2f}) – capitalize on this strength.")
            elif sec['section_mean'] <= 2.5:
                insights.append(f"Section '{sec['title']}' needs focused attention (mean {sec['section_mean']:.2f}).")

    # Top and bottom single questions
    all_q = []
    for sec in sections_data:
        for q in sec['likert_questions']:
            if q['mean'] is not None:
                all_q.append(q)
    if all_q:
        top_q = max(all_q, key=lambda x: x['mean'])
        bottom_q = min(all_q, key=lambda x: x['mean'])
        insights.append(f"Highest rated item: '{top_q['text']}' (mean {top_q['mean']:.2f}).")
        insights.append(f"Lowest rated item: '{bottom_q['text']}' (mean {bottom_q['mean']:.2f}) – this area requires improvement.")

    return insights

def generate_prediction(sections_data, overall_mean):
    if overall_mean is None:
        return "No data available for prediction."
    weak_count = 0
    for sec in sections_data:
        for q in sec['likert_questions']:
            if q['mean'] is not None and q['mean'] <= 2.5:
                weak_count += 1
    if overall_mean < 3.0 and weak_count > 2:
        return "There is a high probability of continued low satisfaction if the identified weaknesses are not addressed."
    elif overall_mean >= 4.0:
        return "The course is expected to maintain high satisfaction if current strengths are sustained."
    else:
        return "With targeted improvements, satisfaction can be significantly increased."