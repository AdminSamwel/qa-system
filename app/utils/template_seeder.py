"""
template_seeder.py
==================
Seeds the two standard evaluation form templates into the database.
Idempotent — skips creation if a template with the same title already exists.

Templates:
  1. NACTVET Mafunzo Marefu  — Certificate / Diploma / Degree (7 NACTVET criteria)
  2. TPSC QA Mafunzo Mafupi  — Short Courses / Public Servants (TPSC QA Policy)
"""

from app import db
from app.models import Form, FormSection, FormQuestion


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _likert(text, order, naqs_ref=None, category=''):
    return dict(question_text=text, question_type='likert', options=None,
                required=True, order=order, category=category,
                naqs_reference=naqs_ref)

def _text(text, order, required=False, category=''):
    return dict(question_text=text, question_type='text', options=None,
                required=required, order=order, category=category,
                naqs_reference=None)

def _create_form_with_sections(admin_user_id, title, description,
                                form_type, nactvet_version, policy_ref,
                                target_level, sections_data):
    """
    sections_data: list of dicts:
        {
          'title': str,
          'naqs_reference': str|None,
          'ideal_score': float,
          'questions': list[dict from _likert/_text]
        }
    """
    form = Form(
        title=title,
        description=description,
        created_by=admin_user_id,
        is_active=True,
        is_template=True,
        form_type=form_type,
        nactvet_version=nactvet_version,
        policy_ref=policy_ref,
        target_level=target_level,
    )
    db.session.add(form)
    db.session.flush()   # get form.id

    for sec_order, sec_data in enumerate(sections_data, start=1):
        section = FormSection(
            form_id=form.id,
            title=sec_data['title'],
            order=sec_order,
            naqs_reference=sec_data.get('naqs_reference'),
            ideal_score=sec_data.get('ideal_score', 5.0),
        )
        db.session.add(section)
        db.session.flush()   # get section.id

        for q_data in sec_data['questions']:
            question = FormQuestion(
                form_id=form.id,
                section_id=section.id,
                question_text=q_data['question_text'],
                question_type=q_data['question_type'],
                options=q_data.get('options'),
                required=q_data.get('required', True),
                order=q_data['order'],
                category=q_data.get('category', ''),
                naqs_reference=q_data.get('naqs_reference'),
            )
            db.session.add(question)

    return form


# ---------------------------------------------------------------------------
# Template 1 — NACTVET Mafunzo Marefu
# ---------------------------------------------------------------------------

LONG_COURSE_SECTIONS = [
    {
        'title': 'Sehemu 1: Utoaji wa Mtaala (Curriculum Delivery)',
        'naqs_reference': 'NAQS 8',
        'ideal_score': 5.0,
        'questions': [
            _likert('Mwalimu alieleza malengo ya somo kabla ya kuanza kila kipindi', 1, 'NAQS 8', 'curriculum'),
            _likert('Maudhui ya somo yalihusiana na malengo ya mtaala na mpango wa masomo', 2, 'NAQS 8', 'curriculum'),
            _likert('Mwalimu alipanga na kupanga masomo vizuri kwa utaratibu unaofaa', 3, 'NAQS 8', 'curriculum'),
            _likert('Kiwango cha kina cha maudhui (depth) kilikuwa kinafaa kwa ngazi ya somo', 4, 'NAQS 8', 'curriculum'),
            _likert('Mwalimu alifunika maudhui yote ya mtaala ndani ya muda uliopangwa', 5, 'NAQS 8', 'curriculum'),
        ],
    },
    {
        'title': 'Sehemu 2: Mbinu za Kufundishia (Teaching Methodology)',
        'naqs_reference': 'NAQS 6',
        'ideal_score': 5.0,
        'questions': [
            _likert('Mwalimu alitumia mbinu mbalimbali za kufundishia (maelezo, majadiliano, mazoezi)', 1, 'NAQS 6', 'methodology'),
            _likert('Mwalimu alitumia vifaa vya kufundishia (projekta, mabodi, modeli) vinavyofaa', 2, 'NAQS 6', 'methodology'),
            _likert('Mwalimu aliweza kueleza dhana ngumu kwa urahisi unaoeleweka', 3, 'NAQS 6', 'methodology'),
            _likert('Mwalimu alitoa mifano inayohusiana na maisha halisi ya kazi na mazingira ya Tanzania', 4, 'NAQS 6', 'methodology'),
            _likert('Kasi ya ufundishaji ilikuwa inafaa — si ya haraka sana wala polepole sana', 5, 'NAQS 6', 'methodology'),
            _likert('Mwalimu alishirikisha wanafunzi kikamilifu katika mchakato wa kujifunza', 6, 'NAQS 6', 'methodology'),
        ],
    },
    {
        'title': 'Sehemu 3: Mwongozo na Msaada kwa Wanafunzi (Student Support)',
        'naqs_reference': 'NAQS 9',
        'ideal_score': 5.0,
        'questions': [
            _likert('Mwalimu alikuwa tayari kusaidia wanafunzi nje ya muda wa darasa', 1, 'NAQS 9', 'support'),
            _likert('Mwalimu alitoa maoni ya ujenzi (constructive feedback) kuhusu kazi za wanafunzi', 2, 'NAQS 9', 'support'),
            _likert('Wanafunzi walipewa fursa ya kutosha ya kuuliza maswali na kutoa maoni darasani', 3, 'NAQS 9', 'support'),
            _likert('Mwalimu aliheshimu, akasikiliza na kukubali maoni tofauti ya wanafunzi', 4, 'NAQS 9', 'support'),
            _likert('Mwalimu alitambua mahitaji maalum ya wanafunzi na kujibu ipasavyo', 5, 'NAQS 9', 'support'),
        ],
    },
    {
        'title': 'Sehemu 4: Mazingira ya Kujifunzia (Learning Environment)',
        'naqs_reference': 'NAQS 5, NAQS 10',
        'ideal_score': 5.0,
        'questions': [
            _likert('Darasa lilikuwa na mazingira mazuri ya kujifunzia (taa, hewa, ukimya)', 1, 'NAQS 5', 'environment'),
            _likert('Vifaa vya kufundishia vilikuwa vya kutosha na katika hali nzuri', 2, 'NAQS 5', 'environment'),
            _likert('Rasilimali za maktaba/vituo vya kujifunzia zilisaidia masomo yangu', 3, 'NAQS 10', 'environment'),
            _likert('Mazingira ya chuo yaliniwezesha kujifunza bila vizuizi', 4, 'NAQS 5', 'environment'),
        ],
    },
    {
        'title': 'Sehemu 5: Ujuzi na Utaalamu wa Mwalimu (Facilitator Competence)',
        'naqs_reference': 'NAQS 7',
        'ideal_score': 5.0,
        'questions': [
            _likert('Mwalimu alionyesha ujuzi wa kina na upana wa kina katika somo lake', 1, 'NAQS 7', 'competence'),
            _likert('Mwalimu alihusisha nadharia (theory) na vitendo (practice) vizuri', 2, 'NAQS 7', 'competence'),
            _likert('Mwalimu alionyesha uzoefu wa vitendo wa kweli katika eneo lake la utaalamu', 3, 'NAQS 7', 'competence'),
            _likert('Mwalimu alifika darasani kwa wakati na akaendesha masomo kwa ufanisi', 4, 'NAQS 7', 'competence'),
            _likert('Mwalimu alibaki mkweli na wa kuheshimika katika mawasiliano na wanafunzi', 5, 'NAQS 7', 'competence'),
        ],
    },
    {
        'title': 'Sehemu 6: Matokeo ya Ujifunzaji (Learning Outcomes)',
        'naqs_reference': 'NAQS 4',
        'ideal_score': 5.0,
        'questions': [
            _likert('Nimepata ujuzi mpya na wa kina kutoka katika somo hili', 1, 'NAQS 4', 'outcomes'),
            _likert('Ninajisikia tayari na nimejengwa uwezo wa kutumia maarifa haya kazini', 2, 'NAQS 4', 'outcomes'),
            _likert('Malengo ya kujifunza (learning outcomes) ya somo hili yalifikiwa kwa kiasi kikubwa', 3, 'NAQS 4', 'outcomes'),
            _likert('Somo hili litanisaidia katika maendeleo yangu ya kitaaluma na kitaaluma', 4, 'NAQS 4', 'outcomes'),
        ],
    },
    {
        'title': 'Sehemu 7: Tathmini ya Jumla (Overall Assessment)',
        'naqs_reference': None,
        'ideal_score': 5.0,
        'questions': [
            _likert('Kwa ujumla, mwalimu huyu anafundisha kwa ufanisi mkubwa', 1, None, 'overall'),
            _likert('Ningependekeza somo hili na mwalimu huyu kwa wanafunzi wengine', 2, None, 'overall'),
            _likert('Ubora wa kufundishwa katika somo hili unakidhi matarajio yangu', 3, None, 'overall'),
            _text('Taja nguvu kuu za mwalimu huyu katika ufundishaji (optional)', 4, required=False, category='overall'),
            _text('Toa mapendekezo ya kuboresha ufundishaji wa somo hili (optional)', 5, required=False, category='overall'),
        ],
    },
]


# ---------------------------------------------------------------------------
# Template 2 — TPSC QA Mafunzo Mafupi / Short Courses
# ---------------------------------------------------------------------------

SHORT_COURSE_SECTIONS = [
    {
        'title': 'Sehemu 1: Maudhui ya Mafunzo (Course Content)',
        'naqs_reference': 'TPSC QA 4.2.1',
        'ideal_score': 5.0,
        'questions': [
            _likert('Maudhui ya mafunzo yalikuwa yanafaa kabisa kwa mahitaji yangu ya kazi', 1, 'TPSC QA 4.2.1', 'content'),
            _likert('Maudhui yalikuwa ya kisasa na yanayohusiana na mazingira ya sasa ya utumishi wa umma', 2, 'TPSC QA 4.2.1', 'content'),
            _likert('Kina na upana (depth and breadth) wa maudhui ulikuwa wa kutosha', 3, 'TPSC QA 4.2.1', 'content'),
            _likert('Maudhui yaliendelea vizuri kutoka sehemu moja hadi nyingine (logical flow)', 4, 'TPSC QA 4.2.1', 'content'),
            _likert('Maudhui yalifikia malengo yaliyotangazwa ya mafunzo', 5, 'TPSC QA 4.2.1', 'content'),
        ],
    },
    {
        'title': 'Sehemu 2: Uwasilishaji wa Mkufunzi (Facilitator Delivery)',
        'naqs_reference': 'TPSC QA 4.2.2',
        'ideal_score': 5.0,
        'questions': [
            _likert('Mkufunzi alieleza maudhui vizuri na kwa uwazi unaoeleweka', 1, 'TPSC QA 4.2.2', 'delivery'),
            _likert('Mkufunzi alionyesha ujuzi wa kina na uelewa mkubwa wa mada', 2, 'TPSC QA 4.2.2', 'delivery'),
            _likert('Mkufunzi alitumia mbinu za kushirikisha washiriki kikamilifu (interactive methods)', 3, 'TPSC QA 4.2.2', 'delivery'),
            _likert('Mkufunzi aliheshimu na kusikia maswali na maoni ya washiriki', 4, 'TPSC QA 4.2.2', 'delivery'),
            _likert('Mkufunzi alijibu maswali kwa ujuzi, uwazi na uvumilivu', 5, 'TPSC QA 4.2.2', 'delivery'),
            _likert('Mkufunzi alikuwa na nidhamu ya muda — alianza na kumaliza kwa wakati', 6, 'TPSC QA 4.2.2', 'delivery'),
        ],
    },
    {
        'title': 'Sehemu 3: Nyenzo na Vifaa vya Mafunzo (Training Materials & Resources)',
        'naqs_reference': 'TPSC QA 4.2.3',
        'ideal_score': 5.0,
        'questions': [
            _likert('Majarida/vitabu vya mafunzo (handouts) vilikuwa vya kutosha na vya ubora', 1, 'TPSC QA 4.2.3', 'materials'),
            _likert('Nyenzo za mafunzo zilikuwa za kisasa, zinazofaa na za kueleweka', 2, 'TPSC QA 4.2.3', 'materials'),
            _likert('Matumizi ya teknolojia (projekta, kompyuta, mtandao) yalikuwa mazuri na yaliyopangwa', 3, 'TPSC QA 4.2.3', 'materials'),
            _likert('Nyenzo na vifaa vya mafunzo vilisaidia kuelewa maudhui vizuri zaidi', 4, 'TPSC QA 4.2.3', 'materials'),
        ],
    },
    {
        'title': 'Sehemu 4: Mazingira na Miundombinu (Venue & Facilities)',
        'naqs_reference': 'TPSC QA 4.2.4',
        'ideal_score': 5.0,
        'questions': [
            _likert('Ukumbi wa mafunzo ulikuwa na nafasi ya kutosha, starehe na mazingira mazuri', 1, 'TPSC QA 4.2.4', 'venue'),
            _likert('Mapumziko na milo (chai, chakula cha mchana) yalikuwa ya wakati na ya kutosha', 2, 'TPSC QA 4.2.4', 'venue'),
            _likert('Usafi na utunzaji wa eneo la mafunzo ulikuwa wa hali nzuri', 3, 'TPSC QA 4.2.4', 'venue'),
            _likert('Kwa ujumla, mipangilio ya kiutawala ya mafunzo ilikuwa nzuri', 4, 'TPSC QA 4.2.4', 'venue'),
        ],
    },
    {
        'title': 'Sehemu 5: Matokeo na Manufaa ya Mafunzo (Outcomes & Benefits)',
        'naqs_reference': 'TPSC QA 4.2.5',
        'ideal_score': 5.0,
        'questions': [
            _likert('Mafunzo haya yataboresha utendaji wangu wa kazi kwa kiasi kikubwa', 1, 'TPSC QA 4.2.5', 'outcomes'),
            _likert('Nitaweza kutumia maarifa/ujuzi huu mara moja katika mazingira yangu ya kazi', 2, 'TPSC QA 4.2.5', 'outcomes'),
            _likert('Mafunzo yaliongeza uelewa wangu wa mada hii kwa kiasi kikubwa', 3, 'TPSC QA 4.2.5', 'outcomes'),
            _likert('Thamani ya muda nilioutumia katika mafunzo haya ilikuwa ya hali', 4, 'TPSC QA 4.2.5', 'outcomes'),
        ],
    },
    {
        'title': 'Sehemu 6: Tathmini ya Jumla (Overall Evaluation)',
        'naqs_reference': 'TPSC QA 4.2.6',
        'ideal_score': 5.0,
        'questions': [
            _likert('Kwa ujumla, nilifurahi sana na mafunzo haya', 1, None, 'overall'),
            _likert('Ningependa kushiriki tena katika mafunzo kama haya yanayotolewa na TPSC', 2, None, 'overall'),
            _likert('Ningeipendekeza TPSC kwa wenzangu kwa mafunzo ya aina hii', 3, None, 'overall'),
            _text('Taja nguvu kuu za mafunzo haya ulizopenda zaidi (optional)', 4, required=False, category='overall'),
            _text('Toa mapendekezo ya kuboresha mafunzo haya na huduma za TPSC (optional)', 5, required=False, category='overall'),
            _text('Je, ungependekeza mada gani kwa mafunzo ya siku zijazo? (optional)', 6, required=False, category='overall'),
        ],
    },
]


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def seed_templates(admin_user_id=None):
    """
    Create the two standard evaluation templates if they don't exist yet.
    Call from the CLI or seed_data.seed().

    Returns (created_count, skipped_count).
    """
    from app.models import User

    # Resolve admin user
    if admin_user_id is None:
        admin = (User.query.filter_by(role='superadmin').first()
                 or User.query.filter_by(role='admin').first()
                 or User.query.first())
        if admin is None:
            raise RuntimeError("No users in DB — run seed-db first, then seed-templates.")
        admin_user_id = admin.id

    TEMPLATES = [
        dict(
            title='Fomu ya Tathmini ya Ubora — Mafunzo Marefu (NACTVET)',
            description=(
                'Fomu rasmi ya tathmini ya ubora wa ufundishaji kwa wanafunzi wa mafunzo '
                'marefu (Certificate, Diploma, Degree). Imejengwa kulingana na vigezo 7 vya '
                'NACTVET Quality Assurance Policy (Sehemu 3.5) na viwango vya NAQS 4–10. '
                'Fomu hii ni TEMPLATE — nakili (Clone) ili uweze kuihariri.'
            ),
            form_type='long_course',
            nactvet_version='2023',
            policy_ref='NACTVET Quality Assurance Policy 2023, Section 3.5; NAQS Standards 4-10',
            target_level='',
            sections_data=LONG_COURSE_SECTIONS,
        ),
        dict(
            title='Fomu ya Tathmini ya Ubora — Mafunzo Mafupi / Short Courses (TPSC QA)',
            description=(
                'Fomu rasmi ya tathmini ya mafunzo mafupi kwa watumishi wa umma na washiriki '
                'wa mafunzo ya muda mfupi. Imejengwa kulingana na TPSC Quality Assurance '
                'Policy, Sehemu 4.2. Inashughulikia maudhui, uwasilishaji wa mkufunzi, '
                'nyenzo, mazingira na matokeo ya mafunzo. '
                'Fomu hii ni TEMPLATE — nakili (Clone) ili uweze kuihariri.'
            ),
            form_type='short_course',
            nactvet_version='2023',
            policy_ref='TPSC Quality Assurance Policy, Section 4.2',
            target_level='',
            sections_data=SHORT_COURSE_SECTIONS,
        ),
    ]

    created = skipped = 0
    for tpl in TEMPLATES:
        existing = Form.query.filter_by(title=tpl['title'], is_template=True).first()
        if existing:
            skipped += 1
            continue
        _create_form_with_sections(admin_user_id, **tpl)
        created += 1

    db.session.commit()
    return created, skipped
