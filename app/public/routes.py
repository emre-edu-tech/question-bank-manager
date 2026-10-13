from datetime import datetime
from functools import wraps

from flask import flash, jsonify, redirect, render_template, request, session, url_for

from app.extensions import db
from app.gamification import STARTING_LIVES, XP_PER_CORRECT_ANSWER, calculate_level
from app.models import Question, Quiz, QuizAttempt, QuizAttemptAnswer, QuizQuestion, Student
from app.public import bp


def student_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('student_id'):
            return redirect(url_for('public.identify_student', next=request.path))
        return view(*args, **kwargs)
    return wrapped


@bp.route("/")
def index():
    return render_template("public/index.html")


@bp.route("/quizzes")
def quiz_list():
    quizzes = Quiz.query.order_by(Quiz.id).all()
    return render_template("public/quizzes.html", quizzes=quizzes)


@bp.route('/play', methods=['GET', 'POST'])
def identify_student():
    if request.method == 'POST':
        nickname = request.form.get('nickname', '').strip()
        class_code = request.form.get('class_code', '').strip().upper()
        if not nickname or not class_code:
            flash('Lütfen takma adını ve sınıf kodunu gir.')
            return render_template('public/identify.html')

        student = Student.query.filter_by(nickname=nickname, class_code=class_code).first()
        if not student:
            student = Student(nickname=nickname, class_code=class_code)
            db.session.add(student)
            db.session.commit()

        session['student_id'] = student.id
        next_url = request.args.get('next') or url_for('public.quiz_list')
        return redirect(next_url)

    return render_template('public/identify.html')


@bp.route("/exit")
def exit_student():
    session.pop("student_id", None)
    return redirect(url_for("public.identify_student"))


@bp.route("/my-history")
@student_required
def my_history():
    student = Student.query.get(session['student_id'])
    attempts = (
        QuizAttempt.query.filter_by(student_id=session['student_id'])
        .order_by(QuizAttempt.id.desc())
        .all()
    )
    level_number, level_name = calculate_level(student.total_xp)
    return render_template(
        "public/history.html",
        attempts=attempts,
        student=student,
        level_number=level_number,
        level_name=level_name,
    )


def _get_quiz_or_404(slug):
    return Quiz.query.filter_by(slug=slug).first()


@bp.route("/quizzes/<slug>")
@student_required
def quiz_detail(slug):
    quiz = _get_quiz_or_404(slug)
    if quiz is None:
        return render_template("public/404.html"), 404
    quiz_questions = (
        QuizQuestion.query.filter_by(quiz_id=quiz.id)
        .order_by(QuizQuestion.order)
        .all()
    )
    return render_template(
        "public/quiz_detail.html", quiz=quiz, quiz_questions=quiz_questions
    )


@bp.route('/quizzes/<slug>/start', methods=['POST'])
@student_required
def start_attempt(slug):
    quiz = Quiz.query.filter_by(slug=slug).first_or_404()
    attempt = QuizAttempt(
        student_id=session['student_id'],
        quiz_id=quiz.id,
        total_questions=len(quiz.quiz_questions),
        lives_remaining=STARTING_LIVES,
        completed=False,
    )
    db.session.add(attempt)
    db.session.commit()
    return jsonify({"attempt_id": attempt.id, "lives_remaining": attempt.lives_remaining})


@bp.route('/quizzes/<slug>/answer', methods=['POST'])
@student_required
def answer_question(slug):
    data = request.get_json()
    attempt = QuizAttempt.query.get_or_404(data['attempt_id'])

    if attempt.student_id != session['student_id'] or attempt.completed:
        return jsonify({"error": "invalid attempt"}), 400

    question = Question.query.get_or_404(data['question_id'])
    selected = data.get('selected_choice')
    is_correct = (selected == question.correct_choice)

    xp_awarded = XP_PER_CORRECT_ANSWER if is_correct else 0

    answer = QuizAttemptAnswer(
        attempt_id=attempt.id,
        question_id=question.id,
        selected_choice=selected,
        is_correct=is_correct,
        xp_awarded=xp_awarded,
    )
    db.session.add(answer)

    if is_correct:
        attempt.score += 1
        attempt.xp_earned += xp_awarded
    else:
        attempt.lives_remaining -= 1

    game_over = attempt.lives_remaining <= 0
    if game_over:
        attempt.completed = True
        attempt.completed_at = datetime.utcnow()

    db.session.commit()

    return jsonify({
        "is_correct": is_correct,
        "correct_choice": question.correct_choice,
        "lives_remaining": attempt.lives_remaining,
        "xp_awarded": xp_awarded,
        "game_over": game_over,
    })


@bp.route('/quizzes/<slug>/finish', methods=['POST'])
@student_required
def finish_attempt(slug):
    data = request.get_json()
    attempt = QuizAttempt.query.get_or_404(data['attempt_id'])

    if attempt.student_id != session['student_id']:
        return jsonify({"error": "invalid attempt"}), 400

    if not attempt.completed:
        attempt.completed = True
        attempt.completed_at = datetime.utcnow()

    student = Student.query.get(session['student_id'])
    # Idempotency guard: /finish may be retried (double-click, auto-finish
    # racing the last answer). Credit this attempt's XP exactly once per
    # browser session without adding new schema.
    credited = session.get('credited_attempts', [])
    if attempt.id not in credited:
        student.total_xp += attempt.xp_earned
        credited.append(attempt.id)
        session['credited_attempts'] = credited
    db.session.commit()

    level_number, level_name = calculate_level(student.total_xp)
    return jsonify({
        "score": attempt.score,
        "total": attempt.total_questions,
        "xp_earned": attempt.xp_earned,
        "total_xp": student.total_xp,
        "level_number": level_number,
        "level_name": level_name,
        "lives_remaining": attempt.lives_remaining,
    })
