from app.models import SupportMessage 
import csv, io
from flask import render_template, redirect, url_for, flash, request, Response
from flask_login import login_required, current_user
from app import db
from app.admin import bp
from app.models import User, Course, Enrollment, Department, Programme, Campus
from app.forms import (UserCreationForm, EditUserForm, DepartmentForm, ProgrammeForm,
                       CourseForm, CampusForm)
from sqlalchemy import or_

def admin_required():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return False
    return True

def headoffice_required():
    if current_user.role != 'admin' or current_user.campus_id is not None:
        flash('Only head‑office admin can perform this action.', 'danger')
        return False
    return True

def get_user_scope():
    if current_user.campus_id is None:
        return User.query
    return User.query.filter_by(campus_id=current_user.campus_id)

def get_course_scope():
    if current_user.campus_id is None:
        return Course.query
    return Course.query.filter_by(campus_id=current_user.campus_id)

# ---------- CAMPUS MANAGEMENT ----------
@bp.route('/campuses')
@login_required
def list_campuses():
    if not admin_required():
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
        # The custom validator will catch duplicates, but we rely on it
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
    campus = Campus.query.get_or_404(campus_id)
    form = CampusForm(obj=campus)
    if form.validate_on_submit():
        # Manually check for duplicate name (excluding the current campus)
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
    campus = Campus.query.get_or_404(campus_id)
    db.session.delete(campus)
    db.session.commit()
    flash('Campus deleted.', 'success')
    return redirect(url_for('admin.list_campuses'))

# ---------- DEPARTMENT MANAGEMENT ----------
@bp.route('/departments')
@login_required
def list_departments():
    if not admin_required():
        return redirect(url_for('main.index'))
    departments = Department.query.order_by(Department.name).all()
    return render_template('admin/departments.html', departments=departments)

@bp.route('/departments/add', methods=['GET', 'POST'])
@login_required
def add_department():
    if not admin_required():
        return redirect(url_for('main.index'))
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
    if not admin_required():
        return redirect(url_for('main.index'))
    dept = Department.query.get_or_404(dept_id)
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
    if not admin_required():
        return redirect(url_for('main.index'))
    dept = Department.query.get_or_404(dept_id)
    db.session.delete(dept)
    db.session.commit()
    flash('Department deleted.', 'success')
    return redirect(url_for('admin.list_departments'))

# ---------- PROGRAMME MANAGEMENT ----------
@bp.route('/programmes')
@login_required
def list_programmes():
    if not admin_required():
        return redirect(url_for('main.index'))
    programmes = Programme.query.order_by(Programme.name).all()
    return render_template('admin/programmes.html', programmes=programmes)

@bp.route('/programmes/add', methods=['GET', 'POST'])
@login_required
def add_programme():
    if not admin_required():
        return redirect(url_for('main.index'))
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
    if not admin_required():
        return redirect(url_for('main.index'))
    prog = Programme.query.get_or_404(prog_id)
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
    if not admin_required():
        return redirect(url_for('main.index'))
    prog = Programme.query.get_or_404(prog_id)
    db.session.delete(prog)
    db.session.commit()
    flash('Programme deleted.', 'success')
    return redirect(url_for('admin.list_programmes'))

# ---------- USER MANAGEMENT (campus scoped) ----------
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
    form = UserCreationForm()
    if current_user.campus_id is None:
        form.campus_id.choices = [(c.id, c.name) for c in Campus.query.order_by('name')]
    else:
        form.campus_id.choices = [(current_user.campus_id, Campus.query.get(current_user.campus_id).name)]
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            role=form.role.data,
            campus_id=form.campus_id.data
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
            if role not in ['student', 'lecturer', 'qa_officer', 'admin']:
                errors.append(f'Row {row_num}: invalid role')
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
    form = EditUserForm(original_username=user.username, obj=user)
    if current_user.campus_id is None:
        form.campus_id.choices = [(c.id, c.name) for c in Campus.query.order_by('name')]
    else:
        form.campus_id.choices = [(current_user.campus_id, Campus.query.get(current_user.campus_id).name)]
    if form.validate_on_submit():
        user.email = form.email.data
        user.full_name = form.full_name.data
        user.role = form.role.data
        user.campus_id = form.campus_id.data
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
    return redirect(url_for('admin.user_list'))

# ---------- COURSE MANAGEMENT (campus scoped) ----------
@bp.route('/courses')
@login_required
def list_courses():
    if not admin_required():
        return redirect(url_for('main.index'))
    courses = get_course_scope().order_by(Course.code).all()
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
        form.campus_id.choices = [(current_user.campus_id, Campus.query.get(current_user.campus_id).name)]
    form.department_id.choices = [(d.id, d.name) for d in Department.query.order_by('name')]
    form.programme_id.choices = [(p.id, p.name) for p in Programme.query.order_by('name')]
    lecturers = User.query.filter_by(role='lecturer')
    if current_user.campus_id is not None:
        lecturers = lecturers.filter_by(campus_id=current_user.campus_id)
    form.lecturer_id.choices = [(l.id, l.full_name) for l in lecturers.all()]
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
            lecturer_id=form.lecturer_id.data
        )
        db.session.add(course)
        db.session.commit()
        flash('Course added.', 'success')
        return redirect(url_for('admin.list_courses'))
    return render_template('admin/course_form.html', form=form, title='Add Course')

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
        form.campus_id.choices = [(current_user.campus_id, Campus.query.get(current_user.campus_id).name)]
    form.department_id.choices = [(d.id, d.name) for d in Department.query.order_by('name')]
    form.programme_id.choices = [(p.id, p.name) for p in Programme.query.order_by('name')]
    lecturers = User.query.filter_by(role='lecturer')
    if current_user.campus_id is not None:
        lecturers = lecturers.filter_by(campus_id=current_user.campus_id)
    form.lecturer_id.choices = [(l.id, l.full_name) for l in lecturers.all()]
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
        db.session.commit()
        flash('Course updated.', 'success')
        return redirect(url_for('admin.list_courses'))
    return render_template('admin/course_form.html', form=form, title='Edit Course')

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

# ---------- ENROLLMENTS (campus scoped) ----------
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
    enrollment = Enrollment.query.get_or_404(enrollment_id)
    if current_user.campus_id and enrollment.course.campus_id != current_user.campus_id:
        flash('Access denied.', 'danger')
        return redirect(url_for('admin.list_enrollments'))
    db.session.delete(enrollment)
    db.session.commit()
    flash('Removed.', 'info')
    return redirect(url_for('admin.list_enrollments'))
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
    msg = SupportMessage.query.get_or_404(msg_id)
    msg.is_read = True
    db.session.commit()
    return redirect(url_for('admin.list_messages'))