"""
analysis.py — QA System Core Analysis Engine
Supports quantitative (Likert/QEI) + qualitative (text) mixed methods analysis
with NACTVET-aligned triangulation and recommendations.
"""

from collections import defaultdict
import json
import re
import numpy as np
from app import db
from app.models import Evaluation, Response, FormQuestion, Course, Form, FormSection, Campus

# ── NAQS / NACTVET constants ────────────────────────────────────────────────────

NAQS_LABELS = {
    'NAQS 1':  'Teaching Standards & Mission',
    'NAQS 2':  'Programme Approval & Fiscal Capacity',
    'NAQS 3':  'Physical Facilities & Learning Resources',
    'NAQS 4':  'Student Support Services',
    'NAQS 5':  'Student Learning Outcomes',
    'NAQS 6':  'Faculty Qualifications & Development',
    'NAQS 7':  'Institutional Effectiveness',
    'NAQS 8':  'Curriculum Design & Delivery',
    'NAQS 9':  'Assessment & Evaluation Practices',
    'NAQS 10': 'Institutional Mission & Work Load',
}

NACTVET_CRITERIA = {
    'curriculum':  {'label': 'Curriculum Design & Delivery',      'naqs': ['NAQS 8', 'NAQS 2'],  'threshold': 0.60},
    'teaching':    {'label': 'Teaching & Learning Methods',        'naqs': ['NAQS 1', 'NAQS 8'],  'threshold': 0.60},
    'outcomes':    {'label': 'Student Learning Outcomes',          'naqs': ['NAQS 5', 'NAQS 9'],  'threshold': 0.60},
    'support':     {'label': 'Student Support Services',           'naqs': ['NAQS 4'],             'threshold': 0.60},
    'environment': {'label': 'Physical Facilities & Resources',    'naqs': ['NAQS 3'],             'threshold': 0.60},
    'staff':       {'label': 'Faculty Qualifications & Dev.',      'naqs': ['NAQS 6'],             'threshold': 0.60},
    'overall':     {'label': 'Institutional Effectiveness (QEI)', 'naqs': ['NAQS 7', 'NAQS 10'], 'threshold': 0.60},
}

IDEAL_LIKERT = 5.0


# ── Qualitative / NLP keyword banks ────────────────────────────────────────────

THEME_KEYWORDS = {
    'teaching_quality': {
        'label': 'Teaching Quality & Delivery',
        'naqs': ['NAQS 1', 'NAQS 8'],
        'icon': 'fa-chalkboard-teacher',
        'colour': 'primary',
        'keywords': [
            # English
            'teach', 'taught', 'lecture', 'explain', 'explained', 'delivery',
            'clear', 'clarity', 'method', 'methods', 'approach', 'technique',
            'skill', 'skills', 'knowledge', 'knowledgeable', 'prepared', 'preparation',
            'organized', 'organised', 'engaging', 'interactive', 'communicate',
            'communication', 'understandable', 'pace', 'timing',
            'punctual', 'professional', 'qualified', 'experienced', 'instructor',
            'teacher', 'facilitator', 'lecturer', 'tutor',
            # Swahili
            'kufundisha', 'kufundishwa', 'mwalimu', 'mkufunzi', 'ufafanuzi',
            'wazi', 'mbinu', 'ujuzi', 'uzoefu', 'maelezo', 'uelewa',
            'wakati', 'utaalamu', 'kujua', 'stadi', 'mhadhiri', 'mwongozo',
        ],
    },
    'learning_resources': {
        'label': 'Learning Resources & Materials',
        'naqs': ['NAQS 3', 'NAQS 8'],
        'icon': 'fa-book-open',
        'colour': 'info',
        'keywords': [
            # English
            'material', 'materials', 'resource', 'resources', 'book', 'books',
            'textbook', 'library', 'notes', 'handout', 'handouts', 'slides',
            'equipment', 'lab', 'laboratory', 'computer', 'computers',
            'internet', 'online', 'digital', 'tool', 'tools', 'technology',
            'software', 'access', 'available', 'availability', 'sufficient',
            'adequate', 'reading', 'reference', 'journal', 'article',
            # Swahili
            'nyenzo', 'vitabu', 'kitabu', 'maktaba', 'vifaa', 'kompyuta',
            'mtandao', 'teknolojia', 'upatikanaji', 'kutosha', 'rasilimali',
            'maandishi', 'machapisho',
        ],
    },
    'assessment': {
        'label': 'Assessment & Feedback',
        'naqs': ['NAQS 9', 'NAQS 5'],
        'icon': 'fa-clipboard-check',
        'colour': 'warning',
        'keywords': [
            # English
            'assessment', 'exam', 'examination', 'test', 'tests', 'assignment',
            'assignments', 'quiz', 'grade', 'grading', 'feedback', 'mark',
            'marking', 'score', 'evaluate', 'evaluation', 'result', 'results',
            'fair', 'transparent', 'timely', 'criteria', 'rubric',
            'continuous', 'formative', 'summative', 'project', 'coursework',
            # Swahili
            'tathmini', 'mtihani', 'maswali', 'majibu', 'alama', 'matokeo',
            'mrejesho', 'haki', 'uwazi', 'maoni', 'kazi', 'mradi',
        ],
    },
    'student_support': {
        'label': 'Student Support & Welfare',
        'naqs': ['NAQS 4'],
        'icon': 'fa-hands-helping',
        'colour': 'success',
        'keywords': [
            # English
            'support', 'help', 'helped', 'assist', 'assistance', 'guidance',
            'counsel', 'counseling', 'advisor', 'welfare', 'wellbeing', 'health',
            'mentor', 'mentoring', 'office', 'hours', 'approachable',
            'responsive', 'care', 'concern', 'accommodation',
            # Swahili
            'msaada', 'ushauri', 'huduma', 'ustawi', 'afya', 'wasiwasi',
            'upatikanaji', 'mahitaji', 'mwongozo', 'uongozaji', 'mwanafunzi',
        ],
    },
    'facilities': {
        'label': 'Physical Facilities & Environment',
        'naqs': ['NAQS 3'],
        'icon': 'fa-building',
        'colour': 'secondary',
        'keywords': [
            # English
            'classroom', 'classrooms', 'room', 'rooms', 'facility', 'facilities',
            'building', 'infrastructure', 'space', 'seating', 'chair', 'chairs',
            'desk', 'desks', 'projector', 'screen', 'board', 'whiteboard',
            'clean', 'cleanliness', 'comfort', 'comfortable', 'ventilation',
            'temperature', 'noise', 'quiet', 'environment', 'toilet',
            'wifi', 'power', 'electricity', 'lighting',
            # Swahili
            'darasa', 'madarasa', 'chumba', 'jengo', 'miundombinu', 'nafasi',
            'kiti', 'viti', 'ubao', 'mazingira', 'usafi', 'starehe', 'utulivu',
            'umeme', 'mwanga',
        ],
    },
    'curriculum': {
        'label': 'Curriculum & Course Content',
        'naqs': ['NAQS 8', 'NAQS 2'],
        'icon': 'fa-graduation-cap',
        'colour': 'dark',
        'keywords': [
            # English
            'curriculum', 'content', 'contents', 'syllabus', 'topic', 'topics',
            'subject', 'relevant', 'relevance', 'practical', 'theory', 'theoretical',
            'applied', 'updated', 'current', 'modern', 'industry', 'workplace',
            'objective', 'objectives', 'outcome', 'outcomes', 'goal', 'goals',
            'scope', 'coverage', 'course', 'module', 'unit', 'chapter',
            # Swahili
            'mtaala', 'maudhui', 'mada', 'masomo', 'malengo', 'madhumuni',
            'kufaa', 'kutumika', 'vitendo', 'nadharia', 'kisasa',
        ],
    },
    'student_outcomes': {
        'label': 'Student Learning Outcomes',
        'naqs': ['NAQS 5', 'NAQS 9'],
        'icon': 'fa-award',
        'colour': 'success',
        'keywords': [
            # English
            'learn', 'learned', 'learning', 'knowledge', 'skill', 'skills',
            'competency', 'competencies', 'ability', 'abilities',
            'understanding', 'apply', 'application', 'achieve', 'achieved',
            'achievement', 'progress', 'develop',
            'development', 'performance',
            'graduate', 'graduation', 'certificate', 'diploma',
            # Swahili
            'kujifunza', 'maarifa', 'uwezo', 'uelewa', 'matokeo',
            'maendeleo', 'mafanikio', 'kuhitimu', 'utendaji', 'stashahada',
        ],
    },
    'faculty': {
        'label': 'Faculty Qualifications & Development',
        'naqs': ['NAQS 6'],
        'icon': 'fa-user-tie',
        'colour': 'primary',
        'keywords': [
            # English
            'lecturer', 'lecturers', 'teacher', 'teachers', 'instructor',
            'faculty', 'staff', 'professor', 'qualification', 'qualifications',
            'qualified', 'degree', 'masters', 'phd', 'doctorate',
            'experience', 'expert', 'specialist', 'training', 'competent',
            # Swahili
            'mhadhiri', 'walimu', 'wafanyakazi', 'sifa', 'taaluma',
            'mafunzo', 'uzoefu', 'mtaalamu', 'utaalamu',
        ],
    },
}

POSITIVE_KEYWORDS = {
    # English
    'excellent', 'outstanding', 'exceptional', 'superb', 'brilliant',
    'good', 'great', 'wonderful', 'amazing', 'fantastic', 'impressive',
    'effective', 'efficient', 'productive', 'successful', 'accomplished',
    'clear', 'clarity', 'concise', 'organized', 'structured', 'systematic',
    'helpful', 'supportive', 'encouraging', 'motivating', 'inspiring',
    'knowledgeable', 'qualified', 'experienced', 'professional', 'expert',
    'timely', 'punctual', 'consistent', 'reliable', 'accessible',
    'relevant', 'practical', 'useful', 'applicable', 'informative',
    'fair', 'transparent', 'objective', 'balanced', 'comprehensive',
    'satisfied', 'satisfactory', 'happy', 'comfortable', 'enjoyed',
    'appreciate', 'appreciated', 'commend', 'praise', 'recommend',
    'best', 'advanced', 'gained', 'achieved', 'learned', 'understood',
    'engaging', 'interactive', 'interesting', 'enjoyable', 'well',
    # Swahili
    'nzuri', 'vizuri', 'bora', 'safi', 'mzuri', 'kizuri', 'mazuri',
    'msaada', 'hodari', 'stadi', 'mafanikio', 'faa', 'kufaa', 'kukidhi',
    'haki', 'pongezi', 'shukrani', 'asante', 'furahia', 'furaha',
    'ustadi', 'uzuri', 'sahihi', 'wazi',
}

NEGATIVE_KEYWORDS = {
    # English
    'poor', 'bad', 'terrible', 'awful', 'horrible', 'dreadful',
    'weak', 'inadequate', 'insufficient', 'lacking', 'missing', 'absent',
    'unclear', 'confusing', 'confused', 'difficult', 'impossible',
    'slow', 'late', 'unprepared', 'disorganized', 'chaotic', 'inconsistent',
    'unhelpful', 'unresponsive', 'unavailable', 'inaccessible', 'neglect',
    'irrelevant', 'outdated', 'obsolete', 'useless', 'impractical',
    'unfair', 'biased', 'incomplete',
    'boring', 'dull', 'monotonous', 'uninteresting', 'unmotivating',
    'unqualified', 'inexperienced', 'unprofessional', 'incompetent',
    'overcrowded', 'noisy', 'uncomfortable', 'dirty', 'broken', 'faulty',
    'limited', 'scarce', 'deficient',
    'failed', 'failure', 'decline', 'decreased', 'worsened',
    'problem', 'problems', 'issue', 'issues', 'complaint', 'complaints',
    'dissatisfied', 'disappointed', 'frustrating', 'frustrated',
    'wasted', 'pointless', 'never', 'rarely', 'lack',
    # Swahili
    'mbaya', 'vibaya', 'kasoro', 'tatizo', 'matatizo', 'upungufu', 'ukosefu',
    'vigumu', 'ngumu', 'shida', 'changamoto', 'hapana',
    'kelele', 'mchafu', 'chafu', 'ovyo', 'bovu',
    'kutofaa', 'kukosa', 'kushindwa', 'lalamika', 'malalamiko',
    'pungufu', 'hawezi', 'haiwezi',
}

# Specific action texts per NACTVET criterion
_CRITERION_ACTIONS = {
    'curriculum': (
        "Review and update the curriculum to align with current industry standards and NACTVET NAQS 8 requirements. "
        "Map learning objectives explicitly to NACTVET competency frameworks. "
        "Involve industry partners in the next curriculum review cycle to ensure relevance."
    ),
    'teaching': (
        "Provide structured pedagogical development for lecturers on learner-centred and active learning strategies. "
        "Introduce a peer observation scheme with structured feedback. "
        "Diversify teaching methods to include case studies, group work, and practical demonstrations aligned with NAQS 1 & 8."
    ),
    'outcomes': (
        "Map all assessments directly to stated learning outcomes as required by NAQS 5. "
        "Implement outcome-based rubrics and share them with students in advance. "
        "Establish a graduate tracking system to measure employability as an indirect outcome indicator."
    ),
    'support': (
        "Strengthen student support services including academic counselling, career guidance, "
        "and welfare services to meet NAQS 4 standards. "
        "Assign personal tutors and ensure office hours are prominently communicated to all students."
    ),
    'environment': (
        "Conduct a physical facilities audit against NAQS 3 standards covering space, lighting, "
        "ventilation, and equipment. "
        "Develop a phased facility improvement plan with clear timelines and budget allocation. "
        "Address any health, safety, or comfort issues as immediate priority."
    ),
    'staff': (
        "Audit all teaching staff qualifications against NAQS 6 minimum requirements. "
        "Develop a staff development plan covering further education sponsorship, "
        "professional certifications, and conference attendance. "
        "Recruit specialist staff in areas where qualification gaps are identified."
    ),
    'overall': (
        "Develop a comprehensive Quality Improvement Plan (QIP) addressing all non-compliant NACTVET criteria. "
        "Establish a Quality Assurance Committee with quarterly monitoring meetings. "
        "Report QEI progress to the Director/CEO and Board on a semester basis."
    ),
}

_CRITERION_OUTCOMES = {
    'curriculum':   "Updated curriculum achieving QEI ≥ 0.60 for curriculum criteria and improved graduate employability.",
    'teaching':     "Enhanced teaching effectiveness and student engagement, with QEI trending toward ≥ 0.80 (Excellent).",
    'outcomes':     "Demonstrable student learning outcome achievement, improved NACTVET NAQS 5 & 9 compliance.",
    'support':      "Reduced dropout rates, improved student satisfaction scores, NAQS 4 compliance.",
    'environment':  "Improved learning environment meeting NAQS 3 standards, higher student comfort ratings.",
    'staff':        "Qualified teaching staff meeting NACTVET NAQS 6 standards, enhanced teaching quality.",
    'overall':      "Overall institutional QEI improvement toward ≥ 0.60, full NACTVET compliance achieved.",
}


# ── QEI helpers ─────────────────────────────────────────────────────────────────

def compute_qei(current_score, ideal_score=None):
    """QEI = RC / RI  (NACTVET formula)."""
    ri = ideal_score if ideal_score is not None else IDEAL_LIKERT
    if not ri:
        return None
    return round(current_score / ri, 3)


def qei_status(qei):
    """Return (label, Bootstrap colour class) for a QEI value."""
    if qei is None:
        return 'No Data', 'secondary'
    if qei >= 0.80:
        return 'Excellent', 'success'
    if qei >= 0.60:
        return 'Satisfactory', 'info'
    if qei >= 0.40:
        return 'Needs Improvement', 'warning'
    return 'Unsatisfactory', 'danger'


# ── NACTVET compliance ───────────────────────────────────────────────────────────

def compute_nactvet_compliance(sections_data, overall_qei):
    criteria_results = {}
    met = 0

    for key, cfg in NACTVET_CRITERIA.items():
        if key == 'overall':
            qei_val = overall_qei
        else:
            relevant_means = []
            for sec in sections_data:
                sec_naqs = sec.get('naqs_reference') or ''
                sec_refs = [r.strip() for r in sec_naqs.split(',')]
                if any(n in sec_refs for n in cfg['naqs']):
                    if sec.get('section_mean') is not None:
                        ideal = sec.get('ideal_score', IDEAL_LIKERT)
                        relevant_means.append(compute_qei(sec['section_mean'], ideal))
            qei_val = float(np.mean(relevant_means)) if relevant_means else None

        threshold = cfg['threshold']
        compliant = qei_val is not None and qei_val >= threshold
        if compliant:
            met += 1

        label, colour = qei_status(qei_val)
        criteria_results[key] = {
            'label':     cfg['label'],
            'naqs':      ', '.join(cfg['naqs']),
            'qei':       qei_val,
            'threshold': threshold,
            'compliant': compliant,
            'status':    label,
            'colour':    colour,
        }

    total = len(NACTVET_CRITERIA)
    compliance_pct = round(met / total * 100, 1)
    overall_status = 'Compliant' if compliance_pct >= 60 else 'Non-Compliant'

    return {
        'compliance_pct': compliance_pct,
        'status':         overall_status,
        'met':            met,
        'total':          total,
        'criteria':       criteria_results,
    }


# ── Qualitative Analysis Engine ──────────────────────────────────────────────────

def _tokenize(text):
    """Lowercase, remove punctuation, split into words."""
    text = text.lower()
    text = re.sub(r"[^\w\s']", ' ', text)
    return [w.strip("'") for w in text.split() if len(w) > 2]


def _score_sentiment(tokens):
    """Return (positive_hits, negative_hits) counts for a token list."""
    pos = sum(1 for t in tokens if t in POSITIVE_KEYWORDS)
    neg = sum(1 for t in tokens if t in NEGATIVE_KEYWORDS)
    return pos, neg


def _classify_sentiment(pos, neg):
    """Classify a comment's sentiment given positive/negative hit counts."""
    if pos == 0 and neg == 0:
        return 'neutral'
    net = pos - neg
    if net > 0:
        return 'positive'
    if net < 0:
        return 'negative'
    return 'neutral'


def _detect_themes(tokens):
    """Return list of theme_ids that match token set."""
    token_set = set(tokens)
    matched = []
    for theme_id, theme_data in THEME_KEYWORDS.items():
        hits = sum(1 for kw in theme_data['keywords'] if kw in token_set)
        if hits >= 1:
            matched.append((theme_id, hits))
    return matched  # list of (theme_id, hit_count)


def analyze_qualitative_responses(text_questions_data):
    """
    Perform keyword-based qualitative analysis on text responses.

    Args:
        text_questions_data: list of dicts with:
            - 'id'       : question id
            - 'text'     : question text
            - 'comments' : list of string responses

    Returns dict with:
        - 'total_comments'         : int
        - 'analysed_comments'      : int  (non-empty)
        - 'sentiment_distribution' : {'positive': n, 'neutral': n, 'negative': n}
        - 'sentiment_percentages'  : {'positive': %, 'neutral': %, 'negative': %}
        - 'dominant_sentiment'     : str
        - 'themes'                 : list of theme dicts sorted by frequency (desc)
        - 'per_question'           : list of per-question analysis dicts
        - 'top_positive_quotes'    : list of str (up to 3 most positive comments)
        - 'top_constructive_quotes': list of str (up to 3 most constructive/negative comments)
        - 'has_sufficient_data'    : bool (True if ≥ 3 analysed comments)
        - 'summary'                : narrative text summary
    """
    all_comments = []
    per_question = []

    for q_data in text_questions_data:
        qid      = q_data.get('id')
        q_text   = q_data.get('text', '')
        comments = [c.strip() for c in (q_data.get('comments') or []) if c and c.strip()]

        q_sentiments    = {'positive': 0, 'neutral': 0, 'negative': 0}
        q_theme_counts  = defaultdict(int)
        scored_comments = []

        for comment in comments:
            tokens = _tokenize(comment)
            pos, neg = _score_sentiment(tokens)
            sentiment = _classify_sentiment(pos, neg)
            q_sentiments[sentiment] += 1
            themes_hit = _detect_themes(tokens)
            for tid, hits in themes_hit:
                q_theme_counts[tid] += hits

            scored_comments.append({
                'text':      comment,
                'sentiment': sentiment,
                'pos_score': pos,
                'neg_score': neg,
                'themes':    [tid for tid, _ in themes_hit],
            })
            all_comments.append(scored_comments[-1])

        per_question.append({
            'id':           qid,
            'text':         q_text,
            'count':        len(comments),
            'sentiments':   q_sentiments,
            'theme_counts': dict(q_theme_counts),
            'comments':     scored_comments,
        })

    total_comments    = len(all_comments)
    analysed_comments = total_comments  # all non-empty comments

    # ── Aggregate sentiment ──────────────────────────────────────────────────
    sentiment_dist = {'positive': 0, 'neutral': 0, 'negative': 0}
    for c in all_comments:
        sentiment_dist[c['sentiment']] += 1

    if analysed_comments > 0:
        sentiment_pct = {
            k: round(v / analysed_comments * 100, 1)
            for k, v in sentiment_dist.items()
        }
    else:
        sentiment_pct = {'positive': 0.0, 'neutral': 0.0, 'negative': 0.0}

    dominant_sentiment = 'neutral'
    if sentiment_dist['positive'] > max(sentiment_dist['neutral'], sentiment_dist['negative']):
        dominant_sentiment = 'positive'
    elif sentiment_dist['negative'] > max(sentiment_dist['positive'], sentiment_dist['neutral']):
        dominant_sentiment = 'negative'

    # ── Aggregate themes ────────────────────────────────────────────────────
    theme_counts    = defaultdict(int)
    theme_pos_neg   = defaultdict(lambda: {'positive': 0, 'negative': 0, 'neutral': 0})
    theme_sample_q  = defaultdict(list)   # sample quotes per theme

    for c in all_comments:
        for tid in c['themes']:
            theme_counts[tid] += 1
            theme_pos_neg[tid][c['sentiment']] += 1
            if len(theme_sample_q[tid]) < 3:
                theme_sample_q[tid].append(c['text'])

    themes_list = []
    for tid, freq in sorted(theme_counts.items(), key=lambda x: -x[1]):
        meta       = THEME_KEYWORDS.get(tid, {})
        pn         = theme_pos_neg[tid]
        total_t    = pn['positive'] + pn['negative'] + pn['neutral']
        sentiment  = 'neutral'
        if pn['positive'] > max(pn['negative'], pn['neutral']):
            sentiment = 'positive'
        elif pn['negative'] > max(pn['positive'], pn['neutral']):
            sentiment = 'negative'

        themes_list.append({
            'theme_id':      tid,
            'label':         meta.get('label', tid),
            'naqs':          meta.get('naqs', []),
            'icon':          meta.get('icon', 'fa-tag'),
            'colour':        meta.get('colour', 'secondary'),
            'frequency':     freq,
            'positive_count': pn['positive'],
            'negative_count': pn['negative'],
            'neutral_count':  pn['neutral'],
            'dominant_sentiment': sentiment,
            'sample_quotes': theme_sample_q[tid],
            'pct_positive':  round(pn['positive'] / total_t * 100, 0) if total_t else 0,
            'pct_negative':  round(pn['negative'] / total_t * 100, 0) if total_t else 0,
        })

    # ── Top quotes ──────────────────────────────────────────────────────────
    sorted_by_pos = sorted(all_comments, key=lambda c: (c['pos_score'] - c['neg_score']), reverse=True)
    top_positive    = [c['text'] for c in sorted_by_pos if c['sentiment'] == 'positive'][:3]
    top_constructive = [c['text'] for c in reversed(sorted_by_pos) if c['sentiment'] == 'negative'][:3]

    has_sufficient = analysed_comments >= 3

    # ── Narrative summary ────────────────────────────────────────────────────
    summary = _build_qualitative_summary(
        analysed_comments, sentiment_dist, sentiment_pct, dominant_sentiment,
        themes_list, has_sufficient
    )

    return {
        'total_comments':          total_comments,
        'analysed_comments':       analysed_comments,
        'sentiment_distribution':  sentiment_dist,
        'sentiment_percentages':   sentiment_pct,
        'dominant_sentiment':      dominant_sentiment,
        'themes':                  themes_list,
        'per_question':            per_question,
        'top_positive_quotes':     top_positive,
        'top_constructive_quotes': top_constructive,
        'has_sufficient_data':     has_sufficient,
        'summary':                 summary,
    }


def _build_qualitative_summary(total, dist, pct, dominant, themes, sufficient):
    if not sufficient:
        return (f"Only {total} open-ended comment(s) were received — insufficient data "
                "for reliable qualitative conclusions. More responses are needed to identify "
                "patterns and themes.")

    pos_pct = pct.get('positive', 0)
    neg_pct = pct.get('negative', 0)
    neu_pct = pct.get('neutral', 0)

    if dominant == 'positive':
        tone = (f"Student feedback is predominantly positive ({pos_pct}% of {total} comments). "
                "The majority of open-ended responses reflect satisfaction with the course. ")
    elif dominant == 'negative':
        tone = (f"Student feedback is predominantly constructive/critical ({neg_pct}% of {total} comments). "
                "The majority of open-ended responses identify areas requiring improvement. ")
    else:
        tone = (f"Student feedback is mixed across {total} comments "
                f"({pos_pct}% positive, {neg_pct}% critical, {neu_pct}% neutral). ")

    if themes:
        top3 = [t['label'] for t in themes[:3]]
        theme_txt = (f"The most frequently discussed themes are: {', '.join(top3)}. ")
    else:
        theme_txt = "No dominant themes were identified. "

    return tone + theme_txt


# ── Mixed Methods Recommendations Engine ────────────────────────────────────────

def generate_mixed_recommendations(sections_data, qualitative_analysis, overall_qei, nactvet_compliance):
    """
    Generate NACTVET-aligned recommendations by triangulating:
    - Quantitative: section QEI scores, NACTVET compliance
    - Qualitative: identified themes, sentiment, student comments

    Returns:
        list of recommendation dicts, sorted by priority (critical → high → medium → positive)
    """
    recommendations = []
    seen_areas      = set()

    theme_by_id = {t['theme_id']: t for t in (qualitative_analysis or {}).get('themes', [])}

    def _qualitative_support(naqs_list):
        """Find qualitative themes referencing the same NAQS standards."""
        support = []
        for tid, meta in THEME_KEYWORDS.items():
            if any(n in meta.get('naqs', []) for n in naqs_list):
                if tid in theme_by_id and theme_by_id[tid]['frequency'] > 0:
                    t = theme_by_id[tid]
                    support.append({
                        'label': t['label'],
                        'frequency': t['frequency'],
                        'sentiment': t['dominant_sentiment'],
                        'sample': t['sample_quotes'][:2],
                    })
        return sorted(support, key=lambda x: -x['frequency'])[:3]

    # ─ 1. Recommendations from NACTVET non-compliance ─────────────────────
    if nactvet_compliance:
        for key, criterion in nactvet_compliance.get('criteria', {}).items():
            if criterion.get('compliant'):
                continue
            qei_val   = criterion.get('qei')
            area_key  = criterion['label']
            if area_key in seen_areas:
                continue
            seen_areas.add(area_key)

            naqs_list = criterion['naqs'].split(', ')
            qual_supp = _qualitative_support(naqs_list)
            triangulated = bool(qual_supp and
                                any(s['sentiment'] == 'negative' for s in qual_supp))

            if qei_val is None:
                priority = 'medium'
            elif qei_val < 0.40:
                priority = 'critical'
            else:
                priority = 'high'

            recommendations.append({
                'priority':          priority,
                '_order':            {'critical': 1, 'high': 2, 'medium': 3, 'low': 4, 'positive': 5}[priority],
                'area':              area_key,
                'naqs_refs':         criterion['naqs'],
                'quantitative': {
                    'qei':     qei_val,
                    'finding': (f"QEI = {qei_val:.2f} — {criterion['status']}, "
                                f"below {criterion['threshold']:.2f} NACTVET threshold"
                                if qei_val is not None
                                else "No quantitative data available for this criterion"),
                },
                'qualitative': {
                    'themes': qual_supp,
                    'triangulated': triangulated,
                },
                'action':           _CRITERION_ACTIONS.get(key, f"Address identified weaknesses in {area_key}."),
                'expected_outcome': _CRITERION_OUTCOMES.get(key, f"Improved NACTVET compliance for {area_key}."),
                'source':           'nactvet',
            })

    # ─ 2. Recommendations from weak sections (not already captured) ────────
    for sec in sections_data:
        sec_qei  = sec.get('section_qei')
        sec_mean = sec.get('section_mean')
        if sec_qei is None or sec_qei >= 0.60:
            continue
        area_key = sec['title']
        if area_key in seen_areas:
            continue
        seen_areas.add(area_key)

        sec_naqs  = [r.strip() for r in (sec.get('naqs_reference') or '').split(',') if r.strip()]
        qual_supp = _qualitative_support(sec_naqs)
        triangulated = bool(qual_supp and any(s['sentiment'] == 'negative' for s in qual_supp))
        priority  = 'critical' if sec_qei < 0.40 else 'high'

        recommendations.append({
            'priority':     priority,
            '_order':       {'critical': 1, 'high': 2, 'medium': 3, 'low': 4, 'positive': 5}[priority],
            'area':         area_key,
            'naqs_refs':    sec.get('naqs_reference', 'N/A'),
            'quantitative': {
                'qei':     sec_qei,
                'finding': (f"Section QEI = {sec_qei:.2f} (Mean = {sec_mean:.2f}/5.00), "
                            f"below 0.60 threshold" if sec_mean else f"Section QEI = {sec_qei:.2f}"),
            },
            'qualitative': {
                'themes': qual_supp,
                'triangulated': triangulated,
            },
            'action': (
                f"Conduct a targeted review of '{area_key}'. Identify the specific factors "
                f"driving low scores through student consultation and faculty self-assessment. "
                f"Develop and implement a Section Improvement Action Plan with measurable milestones."
            ),
            'expected_outcome': (
                f"QEI improvement toward ≥ 0.60 (Satisfactory) in '{area_key}' within one semester."
            ),
            'source': 'section',
        })

    # ─ 3. Qualitative-only concerns (adequate QEI but negative themes) ─────
    for theme in (qualitative_analysis or {}).get('themes', []):
        if theme['negative_count'] < 3:
            continue
        if theme['negative_count'] <= theme['positive_count']:
            continue
        area_key = theme['label']
        if area_key in seen_areas:
            continue
        seen_areas.add(area_key)

        naqs_refs = ', '.join(THEME_KEYWORDS.get(theme['theme_id'], {}).get('naqs', ['N/A']))
        recommendations.append({
            'priority':     'medium',
            '_order':       3,
            'area':         area_key,
            'naqs_refs':    naqs_refs,
            'quantitative': {
                'qei':     None,
                'finding': "Quantitative (Likert) scores are adequate, but open-ended comments signal emerging concerns.",
            },
            'qualitative': {
                'themes':      [theme],
                'triangulated': False,
            },
            'action': (
                f"Investigate student concerns about {area_key.lower()} through a focused discussion or "
                f"supplementary survey. Address issues proactively before they affect Likert satisfaction scores."
            ),
            'expected_outcome': (
                f"Early resolution of concerns, maintaining high satisfaction and preventing QEI deterioration in {area_key.lower()}."
            ),
            'source': 'qualitative',
        })

    # ─ 4. Strengths to sustain (positive recommendations) ─────────────────
    strong_sections = sorted(
        [s for s in sections_data if (s.get('section_qei') or 0) >= 0.80],
        key=lambda x: -(x.get('section_qei') or 0)
    )
    for sec in strong_sections[:2]:
        area_key = sec['title']
        if area_key in seen_areas:
            continue
        seen_areas.add(area_key)

        recommendations.append({
            'priority':     'positive',
            '_order':       5,
            'area':         area_key,
            'naqs_refs':    sec.get('naqs_reference', 'N/A'),
            'quantitative': {
                'qei':     sec.get('section_qei'),
                'finding': (f"Section QEI = {sec['section_qei']:.2f} (Excellent) — a recognised strength."),
            },
            'qualitative': {
                'themes':      [],
                'triangulated': False,
            },
            'action': (
                f"Document and share the practices driving high performance in '{area_key}'. "
                f"Consider using this section as a model for other underperforming areas."
            ),
            'expected_outcome': (
                f"Sustained excellence in '{area_key}', contributing positively to overall institutional QEI."
            ),
            'source': 'strength',
        })

    # ─ Sort ───────────────────────────────────────────────────────────────
    recommendations.sort(key=lambda r: r['_order'])
    return recommendations


# ── Per-course statistics ────────────────────────────────────────────────────────

def compute_course_stats(course_id, student_id=None):
    course = db.session.get(Course, course_id)
    if not course:
        return _empty_stats(course_id)

    query = db.select(Evaluation).filter_by(course_id=course_id)
    if student_id:
        query = query.filter_by(student_id=student_id)
    evaluations = db.session.execute(query).scalars().all()

    if not evaluations:
        return _empty_stats(course_id, course=course)

    form = (db.session.get(Form, course.form_id) if course.form_id
            else db.session.get(Form, evaluations[0].form_id))
    if not form:
        return _empty_stats(course_id, course=course, num_responses=len(evaluations))

    sections_db = (db.session.execute(
        db.select(FormSection).filter_by(form_id=form.id).order_by(FormSection.order)
    ).scalars().all())

    sections_data     = []
    all_likert_scores = []
    all_text_questions = []   # collected across sections for qualitative analysis

    for section in sections_db:
        lq_ids, tq_ids, mcq_ids = _section_question_ids(section)

        likert_data = defaultdict(list)
        text_resp   = defaultdict(list)
        mc_resp     = defaultdict(list)

        for ev in evaluations:
            for resp in ev.responses:
                qid = resp.form_question_id
                if qid in lq_ids and resp.likert_value:
                    likert_data[qid].append(resp.likert_value)
                    all_likert_scores.append(resp.likert_value)
                elif qid in tq_ids and resp.text_value:
                    text_resp[qid].append(resp.text_value)
                elif qid in mcq_ids and resp.selected_options:
                    try:
                        mc_resp[qid].extend(json.loads(resp.selected_options))
                    except Exception:
                        pass

        lqs  = _get_questions(section, 'likert')
        tqs  = _get_questions(section, 'text')
        mcqs = _get_questions(section, 'multiple_choice')

        q_stats  = [_q_stat(q, likert_data.get(q.id, [])) for q in lqs]
        t_stats  = [{'id': q.id, 'text': q.question_text, 'comments': text_resp.get(q.id, [])}
                    for q in tqs]
        mc_stats = [_mc_stat(q, mc_resp.get(q.id, [])) for q in mcqs]

        # Collect text questions for global qualitative analysis
        all_text_questions.extend(t_stats)

        sec_means   = [q['mean'] for q in q_stats if q['mean'] is not None]
        section_mean = float(np.mean(sec_means)) if sec_means else None
        ideal_score  = section.ideal_score if section.ideal_score else IDEAL_LIKERT
        section_qei  = compute_qei(section_mean, ideal_score) if section_mean is not None else None
        qei_lbl, qei_col = qei_status(section_qei)

        sections_data.append({
            'section_id':       section.id,
            'title':            section.title,
            'order':            section.order,
            'naqs_reference':   section.naqs_reference,
            'ideal_score':      ideal_score,
            'likert_questions': q_stats,
            'text_questions':   t_stats,
            'multiple_choice':  mc_stats,
            'section_mean':     section_mean,
            'section_std':      float(np.std(sec_means)) if sec_means else None,
            'section_qei':      section_qei,
            'qei_label':        qei_lbl,
            'qei_colour':       qei_col,
        })

    overall_scores = [ev.overall_score for ev in evaluations if ev.overall_score is not None]
    if overall_scores:
        overall_mean = float(np.mean(overall_scores))
        overall_std  = float(np.std(overall_scores))
        overall_dist = {i: overall_scores.count(i) for i in range(1, 6)}
    else:
        overall_mean = (float(np.mean(all_likert_scores)) if all_likert_scores else None)
        overall_std  = (float(np.std(all_likert_scores))  if all_likert_scores else None)
        overall_dist = {}

    overall_qei      = compute_qei(overall_mean) if overall_mean is not None else None
    qei_lbl, qei_col = qei_status(overall_qei)
    nactvet          = compute_nactvet_compliance(sections_data, overall_qei)

    all_q_flat = sorted(
        [q for sec in sections_data for q in sec['likert_questions'] if q['mean'] is not None],
        key=lambda x: x['mean'], reverse=True
    )
    strengths  = [q for q in all_q_flat if q['mean'] >= 4.0][:5]
    weaknesses = [q for q in reversed(all_q_flat) if q['mean'] <= 2.5][:5]

    # ── Mixed methods ──────────────────────────────────────────────────────
    qualitative_analysis = analyze_qualitative_responses(all_text_questions)
    recommendations      = generate_mixed_recommendations(
        sections_data, qualitative_analysis, overall_qei, nactvet
    )

    return {
        'course_id':            course.id,
        'course_name':          course.name,
        'course_code':          course.code,
        'semester':             course.semester,
        'academic_year':        course.academic_year,
        'lecturer':             course.lecturer.full_name if course.lecturer else 'Not assigned',
        'form_title':           form.title,
        'num_responses':        len(evaluations),
        'sections':             sections_data,
        'overall_distribution': overall_dist,
        'overall_mean':         overall_mean,
        'overall_std':          overall_std,
        'overall_qei':          overall_qei,
        'qei_label':            qei_lbl,
        'qei_colour':           qei_col,
        'nactvet_compliance':   nactvet,
        'strengths':            strengths,
        'weaknesses':           weaknesses,
        'insights':             generate_insights(sections_data, overall_mean, None),
        'prediction':           generate_prediction(sections_data, overall_mean),
        'qualitative_analysis': qualitative_analysis,
        'recommendations':      recommendations,
    }


# ── Campus / institutional aggregates ───────────────────────────────────────────

def compute_campus_summary(campus_id):
    courses = db.session.execute(
        db.select(Course).filter_by(campus_id=campus_id)
    ).scalars().all()

    course_summaries = []
    all_qei = []

    for c in courses:
        stats = compute_course_stats(c.id)
        qei   = stats.get('overall_qei')
        lbl, col = qei_status(qei)
        course_summaries.append({
            'course_id':     c.id,
            'code':          c.code,
            'name':          c.name,
            'num_responses': stats.get('num_responses', 0),
            'overall_qei':   qei,
            'qei_label':     lbl,
            'qei_colour':    col,
        })
        if qei is not None:
            all_qei.append(qei)

    campus_qei = float(np.mean(all_qei)) if all_qei else None
    lbl, col   = qei_status(campus_qei)
    below      = [c for c in course_summaries if c['overall_qei'] is not None and c['overall_qei'] < 0.60]
    total_evals = sum(c['num_responses'] for c in course_summaries)

    return {
        'campus_id':               campus_id,
        'campus_qei':              campus_qei,
        'qei_label':               lbl,
        'qei_colour':              col,
        'course_summaries':        course_summaries,
        'total_evaluations':       total_evals,
        'courses_below_threshold': below,
        'total_courses':           len(courses),
    }


def compute_institution_summary():
    campuses   = db.session.execute(db.select(Campus)).scalars().all()
    campus_data = []
    all_qei    = []

    for campus in campuses:
        summary = compute_campus_summary(campus.id)
        campus_data.append({'campus_id': campus.id, 'campus_name': campus.name, **summary})
        if summary['campus_qei'] is not None:
            all_qei.append(summary['campus_qei'])

    institution_qei = float(np.mean(all_qei)) if all_qei else None
    lbl, col = qei_status(institution_qei)

    return {
        'institution_qei': institution_qei,
        'qei_label':       lbl,
        'qei_colour':      col,
        'campuses':        campus_data,
    }


def compute_department_stats():
    courses = db.session.execute(db.select(Course)).scalars().all()
    means = [
        s['overall_mean']
        for c in courses
        if (s := compute_course_stats(c.id)) and s.get('overall_mean') is not None
    ]
    return {
        'college_mean':  float(np.mean(means)) if means else None,
        'total_courses': len(courses),
    }


# ── Insight / prediction text ────────────────────────────────────────────────────

def generate_insights(sections_data, overall_mean, college_mean):
    insights = []
    if overall_mean is None:
        insights.append("No evaluation data available for insights.")
        return insights

    qei = compute_qei(overall_mean)
    lbl, _ = qei_status(qei)
    insights.append(f"Overall mean score is {overall_mean:.2f}/5.00 (QEI = {qei:.2f} — {lbl}).")

    if college_mean is not None:
        diff = overall_mean - college_mean
        if diff > 0.5:
            insights.append(f"This course performs above the institutional average ({college_mean:.2f}).")
        elif diff < -0.5:
            insights.append(f"This course is below the institutional average ({college_mean:.2f}). Action is recommended.")

    for sec in sections_data:
        m = sec.get('section_mean')
        if m is not None:
            if m >= 4.0:
                insights.append(f"Section '{sec['title']}' scored highly ({m:.2f}) – a recognised strength.")
            elif m <= 2.5:
                insights.append(f"Section '{sec['title']}' needs focused attention (mean {m:.2f}).")

    all_q = [q for sec in sections_data for q in sec['likert_questions'] if q['mean'] is not None]
    if all_q:
        top_q = max(all_q, key=lambda x: x['mean'])
        bot_q = min(all_q, key=lambda x: x['mean'])
        insights.append(f"Highest rated item: '{top_q['text']}' (mean {top_q['mean']:.2f}).")
        insights.append(f"Lowest rated item: '{bot_q['text']}' (mean {bot_q['mean']:.2f}) – requires improvement.")

    return insights


def generate_prediction(sections_data, overall_mean):
    if overall_mean is None:
        return "No data available for prediction."
    weak_count = sum(
        1 for sec in sections_data
        for q in sec['likert_questions']
        if q['mean'] is not None and q['mean'] <= 2.5
    )
    if overall_mean < 3.0 and weak_count > 2:
        return ("There is a high probability of continued low satisfaction unless the identified "
                "weaknesses are addressed urgently.")
    if overall_mean >= 4.0:
        return "The course is expected to maintain high satisfaction if current strengths are sustained."
    return "With targeted improvements in the identified weak areas, satisfaction can be significantly raised."


# ── Private helpers ──────────────────────────────────────────────────────────────

def _get_questions(section, q_type):
    return db.session.execute(
        db.select(FormQuestion)
        .filter_by(section_id=section.id, question_type=q_type)
        .order_by(FormQuestion.order)
    ).scalars().all()


def _section_question_ids(section):
    lq_ids  = {q.id for q in _get_questions(section, 'likert')}
    tq_ids  = {q.id for q in _get_questions(section, 'text')}
    mcq_ids = {q.id for q in _get_questions(section, 'multiple_choice')}
    return lq_ids, tq_ids, mcq_ids


def _q_stat(q, scores):
    count = len(scores)
    return {
        'id':        q.id,
        'text':      q.question_text,
        'category':  q.category or '',
        'naqs':      q.naqs_reference or '',
        'mean':      float(np.mean(scores)) if scores else None,
        'std':       float(np.std(scores))  if scores else None,
        'count':     count,
        'frequency': {i: scores.count(i) for i in range(1, 6)} if scores else {},
    }


def _mc_stat(q, responses):
    options = json.loads(q.options) if q.options else []
    return {
        'id':              q.id,
        'text':            q.question_text,
        'options':         options,
        'counts':          {opt: responses.count(opt) for opt in options},
        'total_responses': len(responses),
    }


def _empty_stats(course_id, course=None, num_responses=0):
    return {
        'course_id':            course_id,
        'course_name':          course.name  if course else 'Unknown',
        'course_code':          course.code  if course else 'Unknown',
        'semester':             course.semester      if course else None,
        'academic_year':        course.academic_year if course else None,
        'lecturer':             (course.lecturer.full_name if course and course.lecturer else 'Not assigned'),
        'form_title':           'Unknown Form',
        'num_responses':        num_responses,
        'sections':             [],
        'overall_distribution': {},
        'overall_mean':         None,
        'overall_std':          None,
        'overall_qei':          None,
        'qei_label':            'No Data',
        'qei_colour':           'secondary',
        'nactvet_compliance':   None,
        'strengths':            [],
        'weaknesses':           [],
        'insights':             [],
        'prediction':           '',
        'qualitative_analysis': None,
        'recommendations':      [],
    }
