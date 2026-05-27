from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

# Roles available in the system:
# superadmin  – Head Office admin (campus_id=None)
# admin       – Campus admin (campus_id set)
# qa_officer  – QA at Head Office (campus_id=None) or campus (campus_id set)
# director    – Campus Director (campus_id set) — receives all campus reports
# ceo         – Chief Executive Officer (campus_id=None) — receives all institutional reports
# lecturer    – Teaches courses
# student     – Enrolled in courses


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    full_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)
    campus_id = db.Column(db.Integer, db.ForeignKey('campuses.id'), nullable=True)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    phone = db.Column(db.String(20), nullable=True)
    title = db.Column(db.String(50), nullable=True)  # Dr., Mr., Ms., etc.

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

    @property
    def is_head_office(self):
        return self.campus_id is None

    @property
    def display_name(self):
        prefix = f"{self.title} " if self.title else ""
        return f"{prefix}{self.full_name}"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class Campus(db.Model):
    __tablename__ = 'campuses'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    location = db.Column(db.String(200))
    contact_email = db.Column(db.String(120), nullable=True)
    contact_phone = db.Column(db.String(20), nullable=True)


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
    nta_level = db.Column(db.String(20), nullable=True)  # NTA Level 4, 5, 6, etc.
    courses = db.relationship('Course', back_populates='programme')


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
    course_type = db.Column(db.String(10), default='long')  # long | short
    public_token = db.Column(db.String(36), unique=True, nullable=True)
    form_id = db.Column(db.Integer, db.ForeignKey('forms.id'), nullable=True)
    # Short course / public servant fields
    target_audience = db.Column(db.String(20), default='students')  # students | public_servants | both
    contact_hours = db.Column(db.Integer, nullable=True)

    lecturer = db.relationship('User', back_populates='teachings', foreign_keys=[lecturer_id])
    programme = db.relationship('Programme', back_populates='courses')
    department = db.relationship('Department')
    campus = db.relationship('Campus', backref='courses')
    enrollments = db.relationship('Enrollment', back_populates='course')
    evaluations = db.relationship('Evaluation', back_populates='course')
    form = db.relationship('Form', backref='courses')


class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'))
    enrollment_date = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('User', back_populates='enrollments', foreign_keys=[student_id])
    course = db.relationship('Course', back_populates='enrollments')

    __table_args__ = (db.UniqueConstraint('student_id', 'course_id', name='unique_enrollment'),)


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
    form_type = db.Column(db.String(20), default='standard')  # standard | short_course | public_servant
    # NACTVET policy compliance metadata
    nactvet_version = db.Column(db.String(10), default='2023')
    policy_ref = db.Column(db.String(100), nullable=True)
    # Template system
    is_template    = db.Column(db.Boolean, default=False)           # True = base template, read-only
    cloned_from    = db.Column(db.Integer, db.ForeignKey('forms.id'), nullable=True)  # source template id
    # Facilitator being evaluated
    facilitator_name = db.Column(db.String(150), nullable=True)     # free-text name
    facilitator_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # optional user FK

    creator = db.relationship('User', foreign_keys=[created_by])
    facilitator = db.relationship('User', foreign_keys='Form.facilitator_id', backref='forms_as_facilitator')
    sections = db.relationship('FormSection', back_populates='form', cascade='all, delete-orphan',
                               order_by='FormSection.order')
    questions = db.relationship('FormQuestion', primaryjoin='Form.id == FormQuestion.form_id', viewonly=True)
    evaluations = db.relationship('Evaluation', back_populates='form')


class FormSection(db.Model):
    __tablename__ = 'form_sections'
    id = db.Column(db.Integer, primary_key=True)
    form_id = db.Column(db.Integer, db.ForeignKey('forms.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    order = db.Column(db.Integer, nullable=False)
    # NACTVET NAQS standard reference for this section
    naqs_reference = db.Column(db.String(50), nullable=True)  # e.g., "NAQS 8", "NAQS 6,9"
    ideal_score = db.Column(db.Float, default=5.0)  # Ideal/target score for QEI

    form = db.relationship('Form', back_populates='sections')
    questions = db.relationship('FormQuestion', back_populates='section', cascade='all, delete-orphan',
                                order_by='FormQuestion.order', foreign_keys='FormQuestion.section_id')


class FormQuestion(db.Model):
    __tablename__ = 'form_questions'
    id = db.Column(db.Integer, primary_key=True)
    form_id = db.Column(db.Integer, db.ForeignKey('forms.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('form_sections.id'), nullable=True)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), nullable=False)  # likert|text|multiple_choice|checkbox|rating
    options = db.Column(db.Text)  # JSON
    required = db.Column(db.Boolean, default=True)
    order = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(50))
    naqs_reference = db.Column(db.String(50), nullable=True)
    parent_question_id = db.Column(db.Integer, db.ForeignKey('form_questions.id'), nullable=True)
    condition_value = db.Column(db.String(200), nullable=True)
    go_to_section_id = db.Column(db.Integer, db.ForeignKey('form_sections.id'), nullable=True)

    form = db.relationship('Form', back_populates='questions', foreign_keys=[form_id])
    section = db.relationship('FormSection', back_populates='questions', foreign_keys=[section_id])
    responses = db.relationship('Response', back_populates='question')
    parent = db.relationship('FormQuestion', remote_side=[id], backref='children')
    jump_to_section = db.relationship('FormSection', foreign_keys=[go_to_section_id],
                                      backref=db.backref('jumped_from', lazy=True))


class Evaluation(db.Model):
    __tablename__ = 'evaluations'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'))
    form_id = db.Column(db.Integer, db.ForeignKey('forms.id'))
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    overall_score = db.Column(db.Float)
    # Public servant / short course fields
    participant_type = db.Column(db.String(20), default='student')  # student | public_servant
    participant_name = db.Column(db.String(100), nullable=True)
    participant_org = db.Column(db.String(150), nullable=True)
    participant_email = db.Column(db.String(120), nullable=True)

    student = db.relationship('User', foreign_keys=[student_id])
    course = db.relationship('Course', back_populates='evaluations')
    form = db.relationship('Form', back_populates='evaluations')
    responses = db.relationship('Response', back_populates='evaluation', cascade='all, delete-orphan')


class Response(db.Model):
    __tablename__ = 'responses'
    id = db.Column(db.Integer, primary_key=True)
    evaluation_id = db.Column(db.Integer, db.ForeignKey('evaluations.id'))
    form_question_id = db.Column(db.Integer, db.ForeignKey('form_questions.id'))
    likert_value = db.Column(db.Integer)
    text_value = db.Column(db.Text)
    selected_options = db.Column(db.Text)  # JSON

    evaluation = db.relationship('Evaluation', back_populates='responses')
    question = db.relationship('FormQuestion', back_populates='responses')


class SupportMessage(db.Model):
    __tablename__ = 'support_messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    subject = db.Column(db.String(200))
    message = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    sender = db.relationship('User', backref='support_messages')


class ReportAcknowledgement(db.Model):
    """Director or CEO acknowledges/reviews a course report."""
    __tablename__ = 'report_acknowledgements'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    acknowledged_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    acknowledged_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)
    action_required = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(20), nullable=False)  # director | ceo

    course = db.relationship('Course', backref='acknowledgements')
    acknowledger = db.relationship('User', backref='acknowledgements')
