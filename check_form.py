from app import create_app
from app.models import Form, FormSection, FormQuestion

app = create_app()
with app.app_context():
    forms = Form.query.all()
    print(f"Total forms: {len(forms)}")
    for form in forms:
        print(f"\nForm ID {form.id}: {form.title}")
        sections = FormSection.query.filter_by(form_id=form.id).order_by(FormSection.order).all()
        print(f"  Sections: {len(sections)}")
        for sec in sections:
            print(f"    Section {sec.order}: {sec.title}")
            questions = FormQuestion.query.filter_by(section_id=sec.id).all()
            print(f"      Questions: {len(questions)}")
            for q in questions:
                print(f"        Q{q.order}: {q.question_text[:60]}...")