from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

# ---------- USER ----------
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False)
    full_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)
    campus_id = db.Column(db.Integer, db.ForeignKey('campuses.id'), nullable=True)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)

    campus = db.relationship('Campus', backref='users')
    enrollments = db.relationship('Enrollment', back_populates='student', foreign_keys='Enrollment.student_id')
    teachings = db.relationship('Course', back_populates='lecturer', foreign_keys='Course.lecturer_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self):
        return self.active

    @is_active.setter
    def is_active(self, value):
        self.active = value

    def __repr__(self):
        return f'<User {self.username} - {self.role}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------- CAMPUS ----------
class Campus(db.Model):
    __tablename__ = 'campuses'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    location = db.Column(db.String(200))

# ---------- DEPARTMENT / PROGRAMME ----------
class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    programmes = db.relationship('Programme', backref='department', lazy=True)

class Programme(db.Model):
    __tablename__ = 'programmes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    courses = db.relationship('Course', back_populates='programme')

# ---------- COURSE / ENROLLMENT ----------
class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    semester = db.Column(db.String(20), nullable=True)
    academic_year = db.Column(db.String(10), nullable=True)
    lecturer_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    level = db.Column(db.String(20), nullable=True)
    programme_id = db.Column(db.Integer, db.ForeignKey('programmes.id'), nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    campus_id = db.Column(db.Integer, db.ForeignKey('campuses.id'), nullable=False)
    course_type = db.Column(db.String(10), default='long')

    lecturer = db.relationship('User', back_populates='teachings', foreign_keys=[lecturer_id])
    programme = db.relationship('Programme', back_populates='courses')
    department = db.relationship('Department')
    campus = db.relationship('Campus', backref='courses')
    enrollments = db.relationship('Enrollment', back_populates='course')
    evaluations = db.relationship('Evaluation', back_populates='course')

class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'))
    enrollment_date = db.Column(db.DateTime, default=datetime.utcnow)
    student = db.relationship('User', back_populates='enrollments', foreign_keys=[student_id])
    course = db.relationship('Course', back_populates='enrollments')
    __table_args__ = (db.UniqueConstraint('student_id', 'course_id', name='unique_enrollment'),)

# ---------- FORM STRUCTURE ----------
class Form(db.Model):
    __tablename__ = 'forms'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    target_level = db.Column(db.String(20))
    show_progress = db.Column(db.Boolean, default=False)
    deadline = db.Column(db.DateTime, nullable=True)

    creator = db.relationship('User', foreign_keys=[created_by])
    sections = db.relationship('FormSection', back_populates='form', cascade='all, delete-orphan', order_by='FormSection.order')
    questions = db.relationship('FormQuestion', primaryjoin='Form.id == FormQuestion.form_id', viewonly=True)
    evaluations = db.relationship('Evaluation', back_populates='form')

class FormSection(db.Model):
    __tablename__ = 'form_sections'
    id = db.Column(db.Integer, primary_key=True)
    form_id = db.Column(db.Integer, db.ForeignKey('forms.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    order = db.Column(db.Integer, nullable=False)

    form = db.relationship('Form', back_populates='sections')
    questions = db.relationship('FormQuestion', back_populates='section', cascade='all, delete-orphan', order_by='FormQuestion.order',
                                foreign_keys='FormQuestion.section_id')

class FormQuestion(db.Model):
    __tablename__ = 'form_questions'
    id = db.Column(db.Integer, primary_key=True)
    form_id = db.Column(db.Integer, db.ForeignKey('forms.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('form_sections.id'), nullable=True)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), nullable=False)
    options = db.Column(db.Text)
    required = db.Column(db.Boolean, default=True)
    order = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(50))
    parent_question_id = db.Column(db.Integer, db.ForeignKey('form_questions.id'), nullable=True)
    condition_value = db.Column(db.String(200), nullable=True)
    go_to_section_id = db.Column(db.Integer, db.ForeignKey('form_sections.id'), nullable=True)

    form = db.relationship('Form', back_populates='questions', foreign_keys=[form_id])
    section = db.relationship('FormSection', back_populates='questions', foreign_keys=[section_id])
    responses = db.relationship('Response', back_populates='question')
    parent = db.relationship('FormQuestion', remote_side=[id], backref='children')
    jump_to_section = db.relationship('FormSection', foreign_keys=[go_to_section_id], backref=db.backref('jumped_from', lazy=True))

# ---------- EVALUATION / RESPONSE ----------
class Evaluation(db.Model):
    __tablename__ = 'evaluations'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'))
    form_id = db.Column(db.Integer, db.ForeignKey('forms.id'))
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    overall_score = db.Column(db.Integer)

    student = db.relationship('User', foreign_keys=[student_id])
    course = db.relationship('Course', back_populates='evaluations')
    form = db.relationship('Form', back_populates='evaluations')
    responses = db.relationship('Response', back_populates='evaluation', cascade='all, delete-orphan')
    __table_args__ = (db.UniqueConstraint('student_id', 'course_id', name='unique_evaluation'),)

class Response(db.Model):
    __tablename__ = 'responses'
    id = db.Column(db.Integer, primary_key=True)
    evaluation_id = db.Column(db.Integer, db.ForeignKey('evaluations.id'))
    form_question_id = db.Column(db.Integer, db.ForeignKey('form_questions.id'))
    likert_value = db.Column(db.Integer)
    text_value = db.Column(db.Text)
    selected_options = db.Column(db.Text)

    evaluation = db.relationship('Evaluation', back_populates='responses')
    question = db.relationship('FormQuestion', back_populates='responses')

# ---------- NEW: SUPPORT MESSAGE ----------
class SupportMessage(db.Model):
    __tablename__ = 'support_messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    subject = db.Column(db.String(200))
    message = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    sender = db.relationship('User', backref='support_messages')