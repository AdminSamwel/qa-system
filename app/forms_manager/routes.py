import json
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.forms_manager import bp
from app.models import Form, FormSection, FormQuestion
from app.forms import FormBuilderForm, FormSettingsForm

def check_access():
    if current_user.role not in ['qa_officer', 'admin']:
        flash('Access denied.', 'danger')
        return False
    return True

# ----------------------- FORM LIST / CREATE -----------------------
@bp.route('/')
@login_required
def list_forms():
    if not check_access():
        return redirect(url_for('main.index'))
    forms = Form.query.order_by(Form.created_at.desc()).all()
    return render_template('forms_manager/list_forms.html', forms=forms)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_form():
    if not check_access():
        return redirect(url_for('main.index'))
    form = FormBuilderForm()
    if form.validate_on_submit():
        new_form = Form(
            title=form.title.data,
            description=form.description.data,
            created_by=current_user.id,
            target_level=form.target_level.data or None
        )
        db.session.add(new_form)
        db.session.commit()
        section = FormSection(form_id=new_form.id, title='Section 1', order=1)
        db.session.add(section)
        db.session.commit()
        flash('Form created. Now add sections and questions.', 'success')
        return redirect(url_for('forms_manager.edit_form', form_id=new_form.id))
    return render_template('forms_manager/create_form.html', form=form)

# ----------------------- EDIT FORM (with sections) -----------------------
@bp.route('/<int:form_id>/edit')
@login_required
def edit_form(form_id):
    if not check_access():
        return redirect(url_for('main.index'))
    form_obj = Form.query.get_or_404(form_id)
    sections = FormSection.query.filter_by(form_id=form_id).order_by(FormSection.order).all()
    section_data = []
    all_questions_dict = []
    for sec in sections:
        questions = FormQuestion.query.filter_by(section_id=sec.id).order_by(FormQuestion.order).all()
        section_data.append({
            'section': sec,
            'questions': questions
        })
        for q in questions:
            q_dict = {
                'id': q.id,
                'section_id': q.section_id,
                'question_text': q.question_text,
                'question_type': q.question_type,
                'options': json.loads(q.options) if q.options else [],
                'required': q.required,
                'category': q.category or '',
                'order': q.order,
                'parent_question_id': q.parent_question_id,
                'condition_value': q.condition_value,
                'go_to_section_id': q.go_to_section_id
            }
            all_questions_dict.append(q_dict)

    return render_template(
        'forms_manager/edit_form.html',
        form=form_obj,
        section_data=section_data,
        all_sections=sections,
        all_questions_dict=all_questions_dict
    )

# ----------------------- FORM SETTINGS (progress bar, deadline) -----------------------
@bp.route('/<int:form_id>/settings', methods=['GET', 'POST'])
@login_required
def form_settings(form_id):
    if not check_access():
        return redirect(url_for('main.index'))
    form_obj = Form.query.get_or_404(form_id)
    form = FormSettingsForm(obj=form_obj)
    if form_obj.deadline:
        form.deadline.data = form_obj.deadline.strftime('%Y-%m-%d %H:%M')
    if form.validate_on_submit():
        form_obj.show_progress = bool(form.show_progress.data)
        if form.deadline.data:
            try:
                form_obj.deadline = datetime.strptime(form.deadline.data, '%Y-%m-%d %H:%M')
            except ValueError:
                flash('Invalid date format.', 'danger')
                return redirect(url_for('forms_manager.form_settings', form_id=form_id))
        else:
            form_obj.deadline = None
        db.session.commit()
        flash('Settings saved.', 'success')
        return redirect(url_for('forms_manager.edit_form', form_id=form_id))
    return render_template('forms_manager/form_settings.html', form=form_obj, settings_form=form)

# ----------------------- SECTION / QUESTION CRUD (unchanged from previous full version) -----------------------
@bp.route('/<int:form_id>/sections/add', methods=['POST'])
@login_required
def add_section(form_id):
    if not check_access():
        return jsonify({'error': 'Access denied'}), 403
    data = request.get_json()
    title = data.get('title', 'New Section')
    max_order = db.session.query(db.func.max(FormSection.order)).filter_by(form_id=form_id).scalar() or 0
    section = FormSection(form_id=form_id, title=title, order=max_order + 1)
    db.session.add(section)
    db.session.commit()
    return jsonify({'success': True, 'section_id': section.id, 'order': section.order})

@bp.route('/sections/<int:section_id>/update', methods=['POST'])
@login_required
def update_section(section_id):
    if not check_access():
        return jsonify({'error': 'Access denied'}), 403
    section = FormSection.query.get_or_404(section_id)
    data = request.get_json()
    if 'title' in data:
        section.title = data['title']
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/sections/<int:section_id>/delete', methods=['POST'])
@login_required
def delete_section(section_id):
    if not check_access():
        return jsonify({'error': 'Access denied'}), 403
    section = FormSection.query.get_or_404(section_id)
    form_id = section.form_id
    db.session.delete(section)
    remaining = FormSection.query.filter_by(form_id=form_id).order_by(FormSection.order).all()
    for idx, sec in enumerate(remaining, start=1):
        sec.order = idx
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/sections/reorder', methods=['POST'])
@login_required
def reorder_sections():
    if not check_access():
        return jsonify({'error': 'Access denied'}), 403
    data = request.get_json()
    for item in data['order']:
        sec = FormSection.query.get(item['id'])
        if sec:
            sec.order = item['order']
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/sections/<int:section_id>/questions/add', methods=['POST'])
@login_required
def add_question_to_section(section_id):
    if not check_access():
        return jsonify({'error': 'Access denied'}), 403
    section = FormSection.query.get_or_404(section_id)
    form_id = section.form_id
    data = request.get_json()
    max_order = db.session.query(db.func.max(FormQuestion.order)).filter_by(section_id=section_id).scalar() or 0
    new_order = max_order + 1

    parent_id = data.get('parent_question_id')
    if parent_id:
        parent_id = int(parent_id)
    condition_value = data.get('condition_value') if parent_id else None
    go_to_section_id = data.get('go_to_section_id')
    if go_to_section_id:
        go_to_section_id = int(go_to_section_id)

    question = FormQuestion(
        form_id=form_id,
        section_id=section_id,
        question_text=data['question_text'],
        question_type=data['question_type'],
        options=json.dumps(data.get('options', [])) if data['question_type'] in ['multiple_choice', 'checkbox'] else None,
        required=data.get('required', True),
        order=new_order,
        category=data.get('category', ''),
        parent_question_id=parent_id,
        condition_value=condition_value,
        go_to_section_id=go_to_section_id
    )
    db.session.add(question)
    db.session.commit()
    return jsonify({'success': True, 'question_id': question.id})

@bp.route('/questions/<int:question_id>/update', methods=['POST'])
@login_required
def update_question(question_id):
    if not check_access():
        return jsonify({'error': 'Access denied'}), 403
    question = FormQuestion.query.get_or_404(question_id)
    data = request.get_json()
    question.question_text = data.get('question_text', question.question_text)
    question.question_type = data.get('question_type', question.question_type)
    if 'options' in data:
        question.options = json.dumps(data['options']) if data['options'] else None
    question.required = data.get('required', question.required)
    question.category = data.get('category', question.category)
    question.parent_question_id = data.get('parent_question_id') or None
    question.condition_value = data.get('condition_value') if question.parent_question_id else None
    question.go_to_section_id = data.get('go_to_section_id') or None
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/questions/<int:question_id>/delete', methods=['POST'])
@login_required
def delete_question(question_id):
    if not check_access():
        return jsonify({'error': 'Access denied'}), 403
    question = FormQuestion.query.get_or_404(question_id)
    section_id = question.section_id
    db.session.delete(question)
    remaining = FormQuestion.query.filter_by(section_id=section_id).order_by(FormQuestion.order).all()
    for idx, q in enumerate(remaining, start=1):
        q.order = idx
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/questions/reorder', methods=['POST'])
@login_required
def reorder_questions():
    if not check_access():
        return jsonify({'error': 'Access denied'}), 403
    data = request.get_json()
    for item in data['order']:
        q = FormQuestion.query.get(item['id'])
        if q:
            q.order = item['order']
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/<int:form_id>/preview')
@login_required
def preview_form(form_id):
    if not check_access():
        return redirect(url_for('main.index'))
    form_obj = Form.query.get_or_404(form_id)
    sections = FormSection.query.filter_by(form_id=form_id).order_by(FormSection.order).all()
    return render_template('forms_manager/preview_form.html', form=form_obj, sections=sections)

@bp.route('/<int:form_id>/toggle_active', methods=['POST'])
@login_required
def toggle_active(form_id):
    if not check_access():
        return redirect(url_for('main.index'))
    form_obj = Form.query.get_or_404(form_id)
    form_obj.is_active = not form_obj.is_active
    db.session.commit()
    flash(f"Form '{form_obj.title}' is now {'active' if form_obj.is_active else 'inactive'}.", 'info')
    return redirect(url_for('forms_manager.list_forms'))