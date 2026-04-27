from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.main import bp
from app.models import User, SupportMessage
import re

@bp.route('/')
@bp.route('/index')
@login_required
def index():
    return render_template('index.html')

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        if full_name:
            current_user.full_name = full_name
        if email:
            current_user.email = email
        if new_password:
            if new_password != confirm_password:
                flash('Passwords do not match.', 'danger')
                return redirect(url_for('main.profile'))
            current_user.set_password(new_password)
        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('main.profile'))
    return render_template('profile.html', user=current_user)

@bp.route('/help', methods=['GET'])
@login_required
def help_page():
    return render_template('help.html')

@bp.route('/help/send', methods=['POST'])
@login_required
def send_message():
    subject = request.form.get('subject', '')
    message = request.form.get('message', '')
    if not message.strip():
        flash('Message cannot be empty.', 'warning')
        return redirect(url_for('main.help_page'))
    msg = SupportMessage(
        sender_id=current_user.id,
        subject=subject,
        message=message
    )
    db.session.add(msg)
    db.session.commit()
    flash('Your message has been sent. We will get back to you soon.', 'success')
    return redirect(url_for('main.help_page'))

# ---------- Enhanced FAQ Chatbot with keyword scoring ----------

FAQ_TOPICS = [
    {
        "keywords": ["evaluation", "report", "analytics", "dashboard", "stats", "summary"],
        "reply": "You can view evaluation reports under <b>Reports</b>. Students see their own submissions; QA officers see full analytics per course or campus.",
        "suggestions": ["How to evaluate a course", "Where to find campus reports", "How to download a report"]
    },
    {
        "keywords": ["evaluate", "course", "fill", "form", "submit", "rate"],
        "reply": "To evaluate a course, go to <b>Evaluations</b>, select your department / programme, pick a course and fill the form section by section.",
        "suggestions": ["How to see my submitted evaluations", "What if I already evaluated", "Can I edit my evaluation"]
    },
    {
        "keywords": ["create", "edit", "build", "design", "form", "questionnaire", "section", "question"],
        "reply": "Go to <b>Forms</b> (QA/Admin only). You can create a new form, add sections, and define questions. Use conditional logic to show/hide questions based on previous answers.",
        "suggestions": ["How to add conditional logic", "How to reorder questions", "How to set a deadline"]
    },
    {
        "keywords": ["deadline", "close", "expire", "time", "limit"],
        "reply": "QA officers can set a deadline for each form under <b>Form Settings</b>. After the deadline, students cannot submit evaluations.",
        "suggestions": ["How to change deadline", "What happens after deadline", "How to extend time"]
    },
    {
        "keywords": ["progress", "bar", "track", "percentage"],
        "reply": "The QA officer can enable a progress bar in <b>Form Settings</b>. It shows students how many questions they have answered.",
        "suggestions": ["Why don't I see the progress bar", "How accurate is the progress bar"]
    },
    {
        "keywords": ["campus", "branch", "location", "centre"],
        "reply": "Campuses are managed by the head‑office admin under <b>Setup → Campuses</b>. Each campus has its own users, courses, and evaluations.",
        "suggestions": ["How to add a new campus", "How to move a user to another campus"]
    },
    {
        "keywords": ["enroll", "enrollment", "register", "assign", "student"],
        "reply": "To enroll a student, go to <b>Setup → Enrollments</b> (admin/QA). Select a student and a course, then click <b>Enroll</b>.",
        "suggestions": ["How to remove a student from a course", "Why a student cannot see a course"]
    },
    {
        "keywords": ["password", "login", "account", "profile", "change password", "update"],
        "reply": "You can update your name, email and password under <b>Profile</b> (click your name in the top right). If you forgot your password, contact your administrator.",
        "suggestions": ["How to reset a forgotten password", "Who can change my role"]
    },
    {
        "keywords": ["accessibility", "blind", "low vision", "read", "text size", "zoom"],
        "reply": "Click the <b>Accessibility</b> icon (bottom right) to adjust text size or use the page reader. The site works with screen readers and keyboard navigation.",
        "suggestions": []
    },
    {
        "keywords": ["short course", "long course", "type", "duration"],
        "reply": "The system supports both <b>long courses</b> (semester‑based) and <b>short courses</b>. When adding a course, select the type accordingly.",
        "suggestions": ["How to add a short course", "Do short courses have evaluations"]
    }
]

GREETINGS = [
    (r'\b(hello|hi|good morning|good afternoon|how are you)\b', 
     "Hello! I'm your QA virtual assistant. You can ask me about evaluations, reports, forms, campus, enrollments, account issues, and more. What can I help with today?",
     ["How to evaluate a course", "Where to see reports", "How to change password"])
]

THANKS = [
    (r'\b(thank|thanks|thank you|appreciate)\b',
     "You're welcome! If you need more help, just ask or use the contact form.",
     [])
]

def score_match(keywords, user_message):
    """Count how many keywords appear in the user message."""
    return sum(1 for kw in keywords if kw in user_message)

def find_best_reply(user_message):
    """Return the best matching topic and a list of all possible suggestions."""
    user_message_lower = user_message.lower()

    # Check greetings
    for pattern, reply, suggestions in GREETINGS:
        if re.search(pattern, user_message_lower):
            return reply, suggestions

    # Check thanks
    for pattern, reply, suggestions in THANKS:
        if re.search(pattern, user_message_lower):
            return reply, suggestions

    # Score FAQ topics
    scored = []
    for topic in FAQ_TOPICS:
        score = score_match(topic["keywords"], user_message_lower)
        if score > 0:
            scored.append((score, topic))
    if scored:
        # Return the highest scored topic
        best_topic = max(scored, key=lambda x: x[0])[1]
        return best_topic["reply"], best_topic.get("suggestions", [])

    # Fallback – suggest common topics based on partial similarity
    # Gather all suggestions from all topics that have at least one suggestion
    all_suggestions = []
    for topic in FAQ_TOPICS:
        if topic.get("suggestions"):
            all_suggestions.extend(topic["suggestions"][:1])  # take first suggestion from each
    unique_suggestions = list(dict.fromkeys(all_suggestions))[:5]

    fallback_reply = "I'm not sure how to help with that. You can ask about <b>evaluations</b>, <b>reports</b>, <b>form building</b>, <b>account issues</b>, or use the contact form. Here are some common questions:"
    return fallback_reply, unique_suggestions

@bp.route('/help/chat', methods=['POST'])
@login_required
def chatbot():
    user_message = request.json.get('message', '').strip()
    if not user_message:
        return jsonify({'reply': 'Please ask a question.', 'suggestions': []})

    reply, suggestions = find_best_reply(user_message)
    return jsonify({'reply': reply, 'suggestions': suggestions})