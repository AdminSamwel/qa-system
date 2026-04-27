from app import create_app, db
from app.models import (User, Course, Enrollment, Form, FormSection, FormQuestion,
                        Department, Programme, Campus)
import json

app = create_app()
app.app_context().push()

# ---------- CAMPUSES ----------
head = Campus(name='Head Office', location='Dar es Salaam')
campus1 = Campus(name='Dar Campus', location='Dar es Salaam')
campus2 = Campus(name='Mwanza Campus', location='Mwanza')
db.session.add_all([head, campus1, campus2])
db.session.commit()

# ---------- USERS ----------
admin = User(username='admin', email='admin@college.tz', full_name='Head Admin', role='admin', campus_id=None)
admin.set_password('admin123')
qa_head = User(username='qahead', email='qahead@college.tz', full_name='QA Head Office', role='qa_officer', campus_id=head.id)
qa_head.set_password('qa123')
admin1 = User(username='admin1', email='admin1@dar.tz', full_name='Campus Admin Dar', role='admin', campus_id=campus1.id)
admin1.set_password('admin123')
qa1 = User(username='qadar', email='qadar@dar.tz', full_name='QA Dar', role='qa_officer', campus_id=campus1.id)
qa1.set_password('qa123')
lecturer1 = User(username='jmushi', email='jmushi@dar.tz', full_name='Dr. John Mushi', role='lecturer', campus_id=campus1.id)
lecturer1.set_password('lecturer123')
student1 = User(username='student1', email='student1@dar.tz', full_name='Amina Juma', role='student', campus_id=campus1.id)
student1.set_password('student123')
student2 = User(username='student2', email='student2@dar.tz', full_name='Baraka Mwanga', role='student', campus_id=campus1.id)
student2.set_password('student123')
db.session.add_all([admin, qa_head, admin1, qa1, lecturer1, student1, student2])
db.session.commit()

# ---------- DEPARTMENTS & PROGRAMMES ----------
dept1 = Department(name='Public Administration')
dept2 = Department(name='Information Technology')
db.session.add_all([dept1, dept2])
db.session.commit()

prog1 = Programme(name='Diploma in Public Administration', department_id=dept1.id)
prog2 = Programme(name='Diploma in IT', department_id=dept2.id)
prog3 = Programme(name='Short Course: Leadership', department_id=dept1.id)
db.session.add_all([prog1, prog2, prog3])
db.session.commit()

# ---------- COURSES ----------
c1 = Course(code='PA101', name='Intro to Public Admin', campus_id=campus1.id, course_type='long',
            department_id=dept1.id, programme_id=prog1.id,
            level='NTA Level 5', semester='Semester 1', academic_year='2025/2026', lecturer_id=lecturer1.id)
c2 = Course(code='IT101', name='Computer Fundamentals', campus_id=campus1.id, course_type='long',
            department_id=dept2.id, programme_id=prog2.id,
            level='NTA Level 5', semester='Semester 1', academic_year='2025/2026', lecturer_id=lecturer1.id)
c3 = Course(code='SHRT1', name='Effective Leadership', campus_id=campus1.id, course_type='short',
            department_id=dept1.id, programme_id=prog3.id,
            level=None, semester=None, academic_year=None, lecturer_id=lecturer1.id)
db.session.add_all([c1, c2, c3])
db.session.commit()

# ---------- ENROLLMENTS ----------
db.session.add_all([
    Enrollment(student_id=student1.id, course_id=c1.id),
    Enrollment(student_id=student1.id, course_id=c2.id),
    Enrollment(student_id=student1.id, course_id=c3.id),
    Enrollment(student_id=student2.id, course_id=c1.id)
])
db.session.commit()

# ---------- DEFAULT FORM ----------
form = Form(title='Course Evaluation Form (TPSC)', description='Standard evaluation',
            created_by=qa_head.id, is_active=True)
db.session.add(form)
db.session.commit()

# Helper to create a question quickly
def add_question(form_id, section_id, text, qtype='likert', required=True, order=1, options=None, parent_question_id=None, condition_value=None):
    q = FormQuestion(
        form_id=form_id,
        section_id=section_id,
        question_text=text,
        question_type=qtype,
        options=json.dumps(options) if options else None,
        required=required,
        order=order,
        parent_question_id=parent_question_id,
        condition_value=condition_value
    )
    db.session.add(q)
    return q

# Section 1
sec1 = FormSection(form_id=form.id, title='SECTION 1: CONTENT (MAUDHUI YA SOMO)', order=1)
db.session.add(sec1)
db.session.flush()
add_question(form.id, sec1.id, 'Are the contents of this course relevant to your career?', order=1)
add_question(form.id, sec1.id, 'Are the contents of this course adequate to give you required competence?', order=2)

# Section 2
sec2 = FormSection(form_id=form.id, title='SECTION 2: Please rate the Facilitator PUT NAME OF LECTURE on the following areas. Teaching/Facilitation (Ufundishaji)', order=2)
db.session.add(sec2)
db.session.flush()
sec2_questions = [
    'Course Introduction, setting clear learning objectives and providing course outline',
    'Audibility (anasikika anapozungumza)',
    'Understandability (anaeleweka na ana uwezo wa kufanya somo lake lieleweke)',
    'Organization of materials and presentation',
    'Knowledge/mastery on the respective subject',
    'Allows questions from students and answers them thoroughly',
    'Encourages critical thinking',
    'Allows discussions and guides students until a proper conclusion is reached',
    'Is able to give practical application of the subject in real environment',
    'Management of class (class well arranged, attentiveness of students)',
    'Performs corrections of tests/assignments given'
]
for i, text in enumerate(sec2_questions, start=1):
    add_question(form.id, sec2.id, text, order=i)

# Section 3
sec3 = FormSection(form_id=form.id, title='SECTION 3: Time Management (Matumizi ya Muda)', order=3)
db.session.add(sec3)
db.session.flush()
sec3_questions = [
    'Attends all classes and compensates lessons missed',
    'Gets in class on time (anaingia darasani kwa wakati)',
    'Properly utilizes class time',
    'Covers topics in time (anamaliza kufundisha mada kwa wakati)',
    'Returns tests/assignments in time'
]
for i, text in enumerate(sec3_questions, start=1):
    add_question(form.id, sec3.id, text, order=i)

# Section 4
sec4 = FormSection(form_id=form.id, title='SECTION 4: General behaviors (Tabia kwa Ujumla)', order=4)
db.session.add(sec4)
db.session.flush()
add_question(form.id, sec4.id, 'Dress code (mavazi/uvaaji)', order=1)
add_question(form.id, sec4.id, 'Language used to students', order=2)

# Section 5
sec5 = FormSection(form_id=form.id, title="SECTION 5: Students' Guidance (Ushauri Nasaha)", order=5)
db.session.add(sec5)
db.session.flush()
add_question(form.id, sec5.id, 'Availability of the facilitator for consultation', order=1)
add_question(form.id, sec5.id, "Follows up on students' affairs", order=2)
add_question(form.id, sec5.id, 'Gives Guidance and motivates students', order=3)

# Section 6 – with branching
sec6 = FormSection(form_id=form.id, title='SECTION 6: General Observation (Maoni kwa Ujumla)', order=6)
db.session.add(sec6)
db.session.flush()
q6_1 = add_question(form.id, sec6.id, 'Is there unethical/inappropriate behavior observed from this facilitator?', qtype='multiple_choice', options=['Yes', 'No'], order=1)
q6_2 = add_question(form.id, sec6.id, 'What good can you tell about this facilitator?', qtype='text', required=False, order=2)
# The branching question
q6_3 = add_question(form.id, sec6.id, 'Would you suggest that this facilitator continue to teach this subject?', qtype='multiple_choice', options=['Yes', 'No'], order=3)
# Dependent question: only shown if above answer is 'No'
q6_4 = add_question(form.id, sec6.id, 'If answer is "No", please explain why.', qtype='text', required=False, order=4,
                    parent_question_id=q6_3.id, condition_value='No')
q6_5 = add_question(form.id, sec6.id, 'Your suggestions for further improvement of learning at TPSC', qtype='text', required=False, order=5)

# Section 7
sec7 = FormSection(form_id=form.id, title='SECTION 7: Learning environment and facilities', order=7)
db.session.add(sec7)
db.session.flush()
sec7_questions = ['Toilets', 'Classes', 'College Compounds', 'Current Reading materials',
                  'Furniture (e.g chairs, tables etc)', 'Computers']
for i, text in enumerate(sec7_questions, start=1):
    add_question(form.id, sec7.id, text, order=i)

db.session.commit()
print("Seed data loaded with branching logic.")