from datetime import datetime
from functools import wraps

from flask import flash, jsonify, redirect, render_template, request, session, url_for

from app.extensions import db
from app.models import Quiz, QuizAttempt, QuizAttemptAnswer, QuizQuestion, Student
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
    attempts = (
        QuizAttempt.query.filter_by(student_id=session['student_id'])
        .order_by(QuizAttempt.id.desc())
        .all()
    )
    return render_template("public/history.html", attempts=attempts)


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


@bp.route("/quizzes/<slug>/submit", methods=["POST"])
@student_required
def quiz_submit(slug):
    quiz = _get_quiz_or_404(slug)
    if quiz is None:
        return jsonify({"error": "Quiz bulunamadı."}), 404

    payload = request.get_json(silent=True) or {}
    # Accept either a flat { "<question_id>": "A" } payload (as sent by quiz.js)
    # or a wrapped { "answers": { ... } } payload.
    if isinstance(payload, dict) and isinstance(payload.get("answers"), dict):
        payload = payload["answers"]

    quiz_questions = (
        QuizQuestion.query.filter_by(quiz_id=quiz.id)
        .order_by(QuizQuestion.order)
        .all()
    )

    valid_choices = ("A", "B", "C", "D")
    results = []
    score = 0
    per_question = []
    for qq in quiz_questions:
        question = qq.question
        qid = question.id
        selected = payload.get(str(qid))
        if selected is None:
            selected = payload.get(qid)
        if selected not in valid_choices:
            selected = None
        is_correct = selected == question.correct_choice
        if is_correct:
            score += 1
        results.append(
            {
                "question_id": qid,
                "selected": selected,
                "correct_choice": question.correct_choice,
                "is_correct": is_correct,
            }
        )
        per_question.append(
            {"question_id": qid, "selected_choice": selected, "is_correct": is_correct}
        )

    attempt = QuizAttempt(
        student_id=session['student_id'],
        quiz_id=quiz.id,
        total_questions=len(quiz_questions),
        score=score,
        completed=True,
        completed_at=datetime.utcnow(),
    )
    db.session.add(attempt)
    db.session.flush()
    for item in per_question:
        db.session.add(
            QuizAttemptAnswer(
                attempt_id=attempt.id,
                question_id=item["question_id"],
                selected_choice=item["selected_choice"],
                is_correct=item["is_correct"],
            )
        )
    db.session.commit()

    return jsonify({"score": score, "total": len(results), "results": results})
