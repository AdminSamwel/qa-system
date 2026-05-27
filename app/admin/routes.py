import csv, io
from flask import render_template, redirect, url_for, flash, request, Response
from flask_login import login_required, current_user
from app import db
from app.admin import bp
from app.models import User, Course, Enrollment, Department, Programme, Campus, SupportMessage, Form
from app.forms import (UserCreationForm, EditUserForm, DepartmentForm, ProgrammeForm,
                       CourseForm, CampusForm)
from sqlalchemy import or_

# ---------- Permission helpers ----------

def is_superadmin():
    """True for superadmin role, or legacy admin with no campus (head office)."""
    return current_user.role == 'superadmin' or (
        current_user.role == 'admin' and current_user.campus_id is None
    )

def admin_required():
    if current_user.role not in ('admin', 'superadmin'):
        flash('Access denied.', 'danger')
        return False
    return True

def headoffice_required():
    if not is_superadmin():
        flash('Only head‑office admin can perform this action.', 'danger')
        return False
    return True

def can_view_setup():
    if current_user.role in ('admin', 'superadmin', 'qa_officer'):
        return True
    flash('Access denied.', 'danger')
    return False

def get_user_scope():
    if is_superadmin():
        return User.query
    return User.query.filter_by(campus_id=current_user.campus_id)

def get_course_scope():
    if is_superadmin():
        return Course.query
    return Course.query.filter_by(campus_id=current_user.campus_id)

def _allowed_roles_for_creator():
    """Return (allowed_roles, campus_choices) based on who is creating a user."""
    if is_superadmin():
        roles = ['superadmin', 'admin', 'qa_officer', 'director', 'ceo', 'lecturer', 'student']
        campuses = [(0, '-- None (Head Office) --')] + [
            (c.id, c.name) for c in Campus.query.order_by('name')
        ]
    elif current_user.campus_id is not None:
        roles = ['qa_officer', 'director', 'lecturer', 'student']
        campuses = [(current_user.campus_id,
                     db.session.get(Campus, current_user.campus_id).name)]
    else:
        roles = ['admin', 'qa_officer', 'director', 'ceo', 'lecturer', 'student']
        campuses = [(c.id, c.name) for c in Campus.query.order_by('name')]
    return roles, campuses

# ========== CAMPUSES ==========
@bp.route('/campuses')
@login_required
def list_campuses():
    if not can_view_setup():
        return redirect(url_for('main.index'))
    campuses = Campus.query.order_by(Campus.name).all()
    return render_template('admin/campuses.html', campuses=campuses)

@bp.route('/campuses/add', methods=['GET', 'POST'])
@login_required
def add_campus():
    if not headoffice_required():
        return redirect(url_for('admin.list_campuses'))
    form = CampusForm()
    if form.validate_on_submit():
        campus = Campus(name=form.name.data, location=form.location.data)
        db.session.add(campus)
        db.session.commit()
        flash('Campus created.', 'success')
        return redirect(url_for('admin.list_campuses'))
    return render_template('admin/campus_form.html', form=form, title='Add Campus')

@bp.route('/campuses/<int:campus_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_campus(campus_id):
    if not headoffice_required():
        return redirect(url_for('admin.list_campuses'))
    campus = db.get_or_404(Campus, campus_id)
    form = CampusForm(obj=campus)
    if form.validate_on_submit():
        existing = Campus.query.filter(Campus.name == form.name.data, Campus.id != campus_id).first()
        if existing:
            flash('A campus with this name already exists.', 'danger')
        else:
            campus.name = form.name.data
            campus.location = form.location.data
            db.session.commit()
            flash('Campus updated.', 'success')
            return redirect(url_for('admin.list_campuses'))
    return render_template('admin/campus_form.html', form=form, title='Edit Campus')

@bp.route('/campuses/<int:campus_id>/delete', methods=['POST'])
@login_required
def delete_campus(campus_id):
    if not headoffice_required():
        return redirect(url_for('admin.list_campuses'))
    campus = db.get_or_404(Campus, campus_id)
    db.session.delete(campus)
    db.session.commit()
    flash('Campus deleted.', 'success')
    return redirect(url_for('admin.list_campuses'))

# ========== DEPARTMENTS ==========
@bp.route('/departments')
@login_required
def list_departments():
    if not can_view_setup():
        return redirect(url_for('main.index'))
    departments = Department.query.order_by(Department.name).all()
    return render_template('admin/departments.html', departments=departments)

@bp.route('/departments/add', methods=['GET', 'POST'])
@login_required
def add_department():
    if not headoffice_required():
        return redirect(url_for('admin.list_departments'))
    form = DepartmentForm()
    if form.validate_on_submit():
        dept = Department(name=form.name.data)
        db.session.add(dept)
        db.session.commit()
        flash('Department created.', 'success')
        return redirect(url_for('admin.list_departments'))
    return render_template('admin/department_form.html', form=form, title='Add Department')

@bp.route('/departments/<int:dept_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_department(dept_id):
    if not headoffice_required():
        return redirect(url_for('admin.list_departments'))
    dept = db.get_or_404(Department, dept_id)
    form = DepartmentForm(obj=dept)
    if form.validate_on_submit():
        dept.name = form.name.data
        db.session.commit()
        flash('Department updated.', 'success')
        return redirect(url_for('admin.list_departments'))
    return render_template('admin/department_form.html', form=form, title='Edit Department')

@bp.route('/departments/<int:dept_id>/delete', methods=['POST'])
@login_required
def delete_department(dept_id):
    if not headoffice_required():
        return redirect(url_for('admin.list_departments'))
    dept = db.get_or_404(Department, dept_id)
    db.session.delete(dept)
    db.session.commit()
    flash('Department deleted.', 'success')
    return redirect(url_for('admin.list_departments'))

# ========== PROGRAMMES ==========
@bp.route('/programmes')
@login_required
def list_programmes():
    if not can_view_setup():
        return redirect(url_for('main.index'))
    programmes = Programme.query.order_by(Programme.name).all()
    return render_template('admin/programmes.html', programmes=programmes)

@bp.route('/programmes/add', methods=['GET', 'POST'])
@login_required
def add_programme():
    if not headoffice_required():
        return redirect(url_for('admin.list_programmes'))
    form = ProgrammeForm()
    form.department_id.choices = [(d.id, d.name) for d in Department.query.order_by('name')]
    if form.validate_on_submit():
        prog = Programme(name=form.name.data, department_id=form.department_id.data)
        db.session.add(prog)
        db.session.commit()
        flash('Programme created.', 'success')
        return redirect(url_for('admin.list_programmes'))
    return render_template('admin/programme_form.html', form=form, title='Add Programme')

@bp.route('/programmes/<int:prog_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_programme(prog_id):
    if not headoffice_required():
        return redirect(url_for('admin.list_programmes'))
    prog = db.get_or_404(Programme, prog_id)
    form = ProgrammeForm(obj=prog)
    form.department_id.choices = [(d.id, d.name) for d in Department.query.order_by('name')]
    if form.validate_on_submit():
        prog.name = form.name.data
        prog.department_id = form.department_id.data
        db.session.commit()
        flash('Programme updated.', 'success')
        return redirect(url_for('admin.list_programmes'))
    return render_template('admin/programme_form.html', form=form, title='Edit Programme')

@bp.route('/programmes/<int:prog_id>/delete', methods=['POST'])
@login_required
def delete_programme(prog_id):
    if not headoffice_required():
        return redirect(url_for('admin.list_programmes'))
    prog = db.get_or_404(Programme, prog_id)
    db.session.delete(prog)
    db.session.commit()
    flash('Programme deleted.', 'success')
    return redirect(url_for('admin.list_programmes'))

# ========== USER MANAGEMENT ==========
@bp.route('/users')
@login_required
def user_list():
    if not admin_required():
        return redirect(url_for('main.index'))
    search_query = request.args.get('q', '').strip()
    users = get_user_scope()
    if search_query:
        users = users.filter(
            or_(User.username.ilike(f'%{search_query}%'),
                User.email.ilike(f'%{search_query}%'),
                User.full_name.ilike(f'%{search_query}%'))
        )
    users = users.order_by(User.username).all()
    return render_template('admin/user_list.html', users=users, search_query=search_query)

@bp.route('/users/add', methods=['GET', 'POST'])
@login_required
def add_user():
    if not admin_required():
        return redirect(url_for('main.index'))

    allowed_roles, campus_choices = _allowed_roles_for_creator()
    form = UserCreationForm(allowed_roles=allowed_roles)
    form.campus_id.choices = campus_choices

    if form.validate_on_submit():
        if current_user.campus_id is not None:
            campus_id = current_user.campus_id
        else:
            # 0 = Head Office (no campus)
            campus_id = form.campus_id.data if form.campus_id.data != 0 else None

        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            role=form.role.data,
            campus_id=campus_id
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f'User {user.username} created.', 'success')
        return redirect(url_for('admin.user_list'))

    return render_template('admin/add_user.html', form=form)

@bp.route('/users/upload', methods=['GET', 'POST'])
@login_required
def upload_users():
    if not admin_required():
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        file = request.files.get('csv_file')
        if not file or not file.filename.endswith('.csv'):
            flash('Please upload a valid CSV file.', 'danger')
            return redirect(url_for('admin.upload_users'))
        stream = io.StringIO(file.stream.read().decode('utf-8'))
        reader = csv.DictReader(stream)
        created = 0
        errors = []
        for row_num, row in enumerate(reader, start=2):
            username = row.get('username', '').strip()
            email = row.get('email', '').strip()
            full_name = row.get('full_name', '').strip()
            role = row.get('role', '').strip()
            password = row.get('password', '').strip()
            campus_id = row.get('campus_id', '').strip()
            if not all([username, email, full_name, role, password, campus_id]):
                errors.append(f'Row {row_num}: missing fields')
                continue

            allowed, _ = _allowed_roles_for_creator()
            if role not in allowed:
                errors.append(f'Row {row_num}: role "{role}" not permitted for your account')
                continue

            try:
                campus_id_int = int(campus_id)
            except ValueError:
                errors.append(f'Row {row_num}: invalid campus_id')
                continue

            if current_user.campus_id is not None and campus_id_int != current_user.campus_id:
                errors.append(f'Row {row_num}: cannot create user in another campus')
                continue

            if User.query.filter((User.username == username) | (User.email == email)).first():
                errors.append(f'Row {row_num}: username/email exists')
                continue

            user = User(username=username, email=email, full_name=full_name, role=role, campus_id=campus_id_int)
            user.set_password(password)
            db.session.add(user)
            created += 1

        db.session.commit()
        flash(f'{created} users created. {len(errors)} errors.', 'info')
        for err in errors:
            flash(err, 'warning')
        return redirect(url_for('admin.user_list'))
    return render_template('admin/upload_csv.html')

@bp.route('/users/download_template')
@login_required
def download_template():
    if not admin_required():
        return redirect(url_for('main.index'))
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['username', 'email', 'full_name', 'role', 'password', 'campus_id'])
    writer.writerow(['john.doe', 'john@college.tz', 'John Doe', 'student', 'temp123', '1'])
    output.seek(0)
    return Response(output, mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=user_template.csv'})

@bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if not admin_required():
        return redirect(url_for('main.index'))
    user = get_user_scope().filter_by(id=user_id).first_or_404()

    allowed_roles, campus_choices = _allowed_roles_for_creator()
    form = EditUserForm(original_username=user.username, obj=user, allowed_roles=allowed_roles)
    form.campus_id.choices = campus_choices

    if form.validate_on_submit():
        if form.role.data not in allowed_roles:
            flash('You cannot assign that role.', 'danger')
            return redirect(url_for('admin.edit_user', user_id=user_id))

        user.email = form.email.data
        user.full_name = form.full_name.data
        user.role = form.role.data
        if current_user.campus_id is not None:
            user.campus_id = current_user.campus_id
        else:
            campus_val = form.campus_id.data
            user.campus_id = campus_val if campus_val != 0 else None
        if form.password.data:
            user.set_password(form.password.data)
        db.session.commit()
        flash('User updated.', 'success')
        return redirect(url_for('admin.user_list'))
    return render_template('admin/edit_user.html', form=form, user=user)

@bp.route('/users/<int:user_id>/toggle_active', methods=['POST'])
@login_required
def toggle_active(user_id):
    if not admin_required():
        return redirect(url_for('main.index'))
    user = get_user_scope().filter_by(id=user_id).first_or_404()
    user.is_active = not user.is_active
    db.session.commit()
    flash(f'User {user.username} toggled.', 'success')
    return redirect(url_for('admin.user_list'))

@bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    if not admin_required():
        return redirect(url_for('main.index'))
    user = get_user_scope().filter_by(id=user_id).first_or_404()
    if user.role == 'admin' and User.query.filter_by(role='admin').count() <= 1:
        flash('Cannot delete last admin.', 'danger')
    else:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted.', 'success')

    redirect_to = request.form.get('redirect_to')
    if redirect_to == 'user_assignments':
        return redirect(url_for('admin.list_user_assignments'))
    return redirect(url_for('admin.user_list'))

# ========== USER‑CAMPUS ASSIGNMENT ==========
@bp.route('/user_assignments')
@login_required
def list_user_assignments():
    if not headoffice_required():
        return redirect(url_for('admin.user_list'))
    users = User.query.order_by(User.username).all()
    campuses = Campus.query.order_by(Campus.name).all()
    return render_template('admin/user_assignments.html', users=users, campuses=campuses)

@bp.route('/user_assignments/update', methods=['POST'])
@login_required
def update_user_campus():
    if not headoffice_required():
        flash('Only head‑office admin can assign campuses.', 'danger')
        return redirect(url_for('admin.list_user_assignments'))
    user_id = request.form.get('user_id', type=int)
    campus_id = request.form.get('campus_id', type=int)
    if not user_id or not campus_id:
        flash('Please select both user and campus.', 'warning')
        return redirect(url_for('admin.list_user_assignments'))
    user = db.get_or_404(User, user_id)
    campus = db.get_or_404(Campus, campus_id)
    old_campus = user.campus.name if user.campus else 'None'
    user.campus_id = campus.id
    db.session.commit()
    flash(f'{user.full_name} moved from {old_campus} to {campus.name}.', 'success')
    return redirect(url_for('admin.list_user_assignments'))

# ========== COURSE MANAGEMENT ==========
@bp.route('/courses')
@login_required
def list_courses():
    if not can_view_setup() and not admin_required():
        return redirect(url_for('main.index'))
    courses = get_course_scope() if current_user.role == 'admin' else Course.query
    courses = courses.order_by(Course.code).all()
    return render_template('admin/courses.html', courses=courses)

@bp.route('/courses/add', methods=['GET', 'POST'])
@login_required
def add_course():
    if not admin_required():
        return redirect(url_for('main.index'))
    form = CourseForm()
    if current_user.campus_id is None:
        form.campus_id.choices = [(c.id, c.name) for c in Campus.query.order_by('name')]
    else:
        form.campus_id.choices = [(current_user.campus_id, db.session.get(Campus, current_user.campus_id).name)]
    form.department_id.choices = [(d.id, d.name) for d in Department.query.order_by('name')]
    form.programme_id.choices = [(p.id, p.name) for p in Programme.query.order_by('name')]
    lecturers = User.query.filter_by(role='lecturer')
    if current_user.campus_id is not None:
        lecturers = lecturers.filter_by(campus_id=current_user.campus_id)
    form.lecturer_id.choices = [(l.id, l.full_name) for l in lecturers.all()]
    form.form_id.choices = [(f.id, f.title) for f in Form.query.filter_by(is_active=True).order_by(Form.title).all()]

    if form.validate_on_submit():
        course = Course(
            code=form.code.data,
            name=form.name.data,
            campus_id=form.campus_id.data,
            course_type=form.course_type.data,
            department_id=form.department_id.data or None,
            programme_id=form.programme_id.data or None,
            level=form.level.data or None,
            semester=form.semester.data or None,
            academic_year=form.academic_year.data or None,
            lecturer_id=form.lecturer_id.data,
            form_id=form.form_id.data or None
        )
        if form.course_type.data == 'short':
            import uuid
            course.public_token = str(uuid.uuid4())
        db.session.add(course)
        db.session.commit()
        flash('Course added successfully.', 'success')
        return redirect(url_for('admin.list_courses'))
    return render_template('admin/course_form.html', form=form, title='Add Module')

@bp.route('/courses/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_course(course_id):
    if not admin_required():
        return redirect(url_for('main.index'))
    course = get_course_scope().filter_by(id=course_id).first_or_404()
    form = CourseForm(obj=course)
    if current_user.campus_id is None:
        form.campus_id.choices = [(c.id, c.name) for c in Campus.query.order_by('name')]
    else:
        form.campus_id.choices = [(current_user.campus_id, db.session.get(Campus, current_user.campus_id).name)]
    form.department_id.choices = [(d.id, d.name) for d in Department.query.order_by('name')]
    form.programme_id.choices = [(p.id, p.name) for p in Programme.query.order_by('name')]
    lecturers = User.query.filter_by(role='lecturer')
    if current_user.campus_id is not None:
        lecturers = lecturers.filter_by(campus_id=current_user.campus_id)
    form.lecturer_id.choices = [(l.id, l.full_name) for l in lecturers.all()]
    form.form_id.choices = [(f.id, f.title) for f in Form.query.filter_by(is_active=True).order_by(Form.title).all()]

    if form.validate_on_submit():
        course.code = form.code.data
        course.name = form.name.data
        course.campus_id = form.campus_id.data
        course.course_type = form.course_type.data
        course.department_id = form.department_id.data or None
        course.programme_id = form.programme_id.data or None
        course.level = form.level.data or None
        course.semester = form.semester.data or None
        course.academic_year = form.academic_year.data or None
        course.lecturer_id = form.lecturer_id.data
        course.form_id = form.form_id.data or None
        if form.course_type.data == 'short' and not course.public_token:
            import uuid
            course.public_token = str(uuid.uuid4())
        db.session.commit()
        flash('Course updated.', 'success')
        return redirect(url_for('admin.list_courses'))
    return render_template('admin/course_form.html', form=form, title='Edit Module')

@bp.route('/courses/<int:course_id>/delete', methods=['POST'])
@login_required
def delete_course(course_id):
    if not admin_required():
        return redirect(url_for('main.index'))
    course = get_course_scope().filter_by(id=course_id).first_or_404()
    db.session.delete(course)
    db.session.commit()
    flash('Course deleted.', 'success')
    return redirect(url_for('admin.list_courses'))

# ========== ENROLLMENTS ==========
@bp.route('/enrollments')
@login_required
def list_enrollments():
    if not admin_required():
        return redirect(url_for('main.index'))
    students = get_user_scope().filter_by(role='student').order_by(User.username).all()
    courses = get_course_scope().order_by(Course.code).all()
    if current_user.campus_id:
        enrollments = Enrollment.query.join(Course).filter(Course.campus_id == current_user.campus_id).all()
    else:
        enrollments = Enrollment.query.all()
    return render_template('admin/enrollments.html', students=students, courses=courses, enrollments=enrollments)

@bp.route('/enrollments/add', methods=['POST'])
@login_required
def enroll_student():
    if not admin_required():
        return redirect(url_for('main.index'))
    student_id = request.form.get('student_id', type=int)
    course_id = request.form.get('course_id', type=int)
    if not student_id or not course_id:
        flash('Select student and course', 'danger')
        return redirect(url_for('admin.list_enrollments'))
    student = get_user_scope().filter_by(id=student_id).first()
    course = get_course_scope().filter_by(id=course_id).first()
    if not student or not course:
        flash('Invalid student or course.', 'danger')
        return redirect(url_for('admin.list_enrollments'))
    if Enrollment.query.filter_by(student_id=student_id, course_id=course_id).first():
        flash('Already enrolled.', 'warning')
    else:
        db.session.add(Enrollment(student_id=student_id, course_id=course_id))
        db.session.commit()
        flash('Enrolled.', 'success')
    return redirect(url_for('admin.list_enrollments'))

@bp.route('/enrollments/<int:enrollment_id>/remove', methods=['POST'])
@login_required
def remove_enrollment(enrollment_id):
    if not admin_required():
        return redirect(url_for('main.index'))
    enrollment = db.get_or_404(Enrollment, enrollment_id)
    if current_user.campus_id and enrollment.course.campus_id != current_user.campus_id:
        flash('Access denied.', 'danger')
        return redirect(url_for('admin.list_enrollments'))
    db.session.delete(enrollment)
    db.session.commit()
    flash('Removed.', 'info')
    return redirect(url_for('admin.list_enrollments'))

# ========== SUPPORT MESSAGES ==========
@bp.route('/messages')
@login_required
def list_messages():
    if not admin_required():
        return redirect(url_for('main.index'))
    messages = SupportMessage.query.order_by(SupportMessage.sent_at.desc()).all()
    return render_template('admin/messages.html', messages=messages)

@bp.route('/messages/<int:msg_id>/read', methods=['POST'])
@login_required
def mark_read(msg_id):
    if not admin_required():
        return redirect(url_for('main.index'))
    msg = db.get_or_404(SupportMessage, msg_id)
    msg.is_read = True
    db.session.commit()
    return redirect(url_for('admin.list_messages'))