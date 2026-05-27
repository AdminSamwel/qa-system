import json
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.forms_manager import bp
from app.models import Form, FormSection, FormQuestion, User
from app.forms import FormBuilderForm, FormSettingsForm, CloneTemplateForm

def check_access():
    if current_user.role not in ['qa_officer', 'admin', 'superadmin']:
        flash('Huna ruhusa ya kufikia ukurasa huu.', 'danger')
        return False
    return True

# ----------------------- FORM LIST / CREATE -----------------------
@bp.route('/')
@login_required
def list_forms():
    if not check_access():
        return redirect(url_for('main.index'))
    templates   = Form.query.filter_by(is_template=True).order_by(Form.created_at).all()
    active_forms = Form.query.filter_by(is_template=False).order_by(Form.created_at.desc()).all()
    return render_template('forms_manager/list_forms.html',
                           templates=templates, forms=active_forms)

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

# ----------------------- TEMPLATE VIEW (read-only) -----------------------
@bp.route('/templates/<int:form_id>')
@login_required
def view_template(form_id):
    if not check_access():
        return redirect(url_for('main.index'))
    tmpl = db.get_or_404(Form, form_id)
    if not tmpl.is_template:
        return redirect(url_for('forms_manager.edit_form', form_id=form_id))
    sections = FormSection.query.filter_by(form_id=form_id).order_by(FormSection.order).all()
    section_data = []
    for sec in sections:
        questions = FormQuestion.query.filter_by(section_id=sec.id).order_by(FormQuestion.order).all()
        section_data.append({'section': sec, 'questions': questions})
    # Existing clones from this template
    clones = Form.query.filter_by(cloned_from=form_id, is_template=False).order_by(Form.created_at.desc()).all()
    # Clone form
    clone_form = CloneTemplateForm()
    clone_form.title.data = clone_form.title.data or f'{tmpl.title} — Nakala'
    lecturers = User.query.filter(User.role.in_(['lecturer'])).order_by(User.full_name).all()
    clone_form.facilitator_id.choices = [(0, '-- Chagua (si lazima) --')] + \
                                        [(u.id, u.display_name) for u in lecturers]
    return render_template('forms_manager/template_detail.html',
                           tmpl=tmpl, section_data=section_data,
                           clones=clones, clone_form=clone_form)


# ----------------------- CLONE A TEMPLATE -----------------------
@bp.route('/templates/<int:form_id>/clone', methods=['POST'])
@login_required
def clone_template(form_id):
    if not check_access():
        return redirect(url_for('main.index'))
    tmpl = db.get_or_404(Form, form_id)
    if not tmpl.is_template:
        flash('Hii si template.', 'warning')
        return redirect(url_for('forms_manager.list_forms'))

    form = CloneTemplateForm()
    lecturers = User.query.filter(User.role.in_(['lecturer'])).order_by(User.full_name).all()
    form.facilitator_id.choices = [(0, '-- Chagua (si lazima) --')] + \
                                  [(u.id, u.display_name) for u in lecturers]

    if not form.validate_on_submit():
        flash('Tafadhali jaza kichwa cha fomu.', 'warning')
        return redirect(url_for('forms_manager.view_template', form_id=form_id))

    facilitator_id = form.facilitator_id.data if form.facilitator_id.data != 0 else None
    facilitator_name = form.facilitator_name.data.strip() or None

    # If facilitator was selected from dropdown, use their name
    if facilitator_id and not facilitator_name:
        u = db.session.get(User, facilitator_id)
        if u:
            facilitator_name = u.display_name

    # Create the new (editable) form cloned from template
    new_form = Form(
        title=form.title.data.strip(),
        description=tmpl.description,
        created_by=current_user.id,
        is_active=True,
        is_template=False,
        cloned_from=tmpl.id,
        form_type=tmpl.form_type,
        nactvet_version=tmpl.nactvet_version,
        policy_ref=tmpl.policy_ref,
        target_level=tmpl.target_level,
        facilitator_name=facilitator_name,
        facilitator_id=facilitator_id,
    )
    db.session.add(new_form)
    db.session.flush()

    # Deep-copy all sections and questions
    old_sections = FormSection.query.filter_by(form_id=tmpl.id).order_by(FormSection.order).all()
    for sec in old_sections:
        new_sec = FormSection(
            form_id=new_form.id,
            title=sec.title,
            order=sec.order,
            naqs_reference=sec.naqs_reference,
            ideal_score=sec.ideal_score,
        )
        db.session.add(new_sec)
        db.session.flush()
        old_questions = FormQuestion.query.filter_by(section_id=sec.id).order_by(FormQuestion.order).all()
        for q in old_questions:
            new_q = FormQuestion(
                form_id=new_form.id,
                section_id=new_sec.id,
                question_text=q.question_text,
                question_type=q.question_type,
                options=q.options,
                required=q.required,
                order=q.order,
                category=q.category,
                naqs_reference=q.naqs_reference,
            )
            db.session.add(new_q)

    db.session.commit()
    flash(f'Fomu "{new_form.title}" imeundwa kutoka template. Unaweza sasa kuihariri.', 'success')
    return redirect(url_for('forms_manager.edit_form', form_id=new_form.id))


# ----------------------- EDIT FORM (with sections) -----------------------
@bp.route('/<int:form_id>/edit')
@login_required
def edit_form(form_id):
    if not check_access():
        return redirect(url_for('main.index'))
    form_obj = db.get_or_404(Form, form_id)
    # Templates are read-only; redirect to the template viewer
    if form_obj.is_template:
        flash('Template inaweza kusomwa tu. Nakili kwanza ili kuihariri.', 'info')
        return redirect(url_for('forms_manager.view_template', form_id=form_id))
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

    # Origin template (if cloned)
    origin_template = db.session.get(Form, form_obj.cloned_from) if form_obj.cloned_from else None
    return render_template(
        'forms_manager/edit_form.html',
        form=form_obj,
        section_data=section_data,
        all_sections=sections,
        all_questions_dict=all_questions_dict,
        origin_template=origin_template,
    )

# ----------------------- FORM SETTINGS (progress bar, deadline) -----------------------
@bp.route('/<int:form_id>/settings', methods=['GET', 'POST'])
@login_required
def form_settings(form_id):
    if not check_access():
        return redirect(url_for('main.index'))
    form_obj = db.get_or_404(Form, form_id)
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
    section = db.get_or_404(FormSection, section_id)
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
    section = db.get_or_404(FormSection, section_id)
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
        sec = db.session.get(FormSection, item['id'])
        if sec:
            sec.order = item['order']
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/sections/<int:section_id>/questions/add', methods=['POST'])
@login_required
def add_question_to_section(section_id):
    if not check_access():
        return jsonify({'error': 'Access denied'}), 403
    section = db.get_or_404(FormSection, section_id)
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
    question = db.get_or_404(FormQuestion, question_id)
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
    question = db.get_or_404(FormQuestion, question_id)
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
        q = db.session.get(FormQuestion, item['id'])
        if q:
            q.order = item['order']
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/<int:form_id>/preview')
@login_required
def preview_form(form_id):
    if not check_access():
        return redirect(url_for('main.index'))
    form_obj = db.get_or_404(Form, form_id)
    sections = FormSection.query.filter_by(form_id=form_id).order_by(FormSection.order).all()
    return render_template('forms_manager/preview_form.html', form=form_obj, sections=sections)

@bp.route('/<int:form_id>/toggle_active', methods=['POST'])
@login_required
def toggle_active(form_id):
    if not check_access():
        return redirect(url_for('main.index'))
    form_obj = db.get_or_404(Form, form_id)
    form_obj.is_active = not form_obj.is_active
    db.session.commit()
    flash(f"Form '{form_obj.title}' is now {'active' if form_obj.is_active else 'inactive'}.", 'info')
    return redirect(url_for('forms_manager.list_forms'))