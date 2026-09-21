from flask import jsonify, render_template, request

from app.models import Quiz, QuizQuestion
from app.public import bp


@bp.route("/")
def index():
    return render_template("public/index.html")


@bp.route("/quizzes")
def quiz_list():
    quizzes = Quiz.query.order_by(Quiz.id).all()
    return render_template("public/quizzes.html", quizzes=quizzes)


def _get_quiz_or_404(slug):
    return Quiz.query.filter_by(slug=slug).first()


@bp.route("/quizzes/<slug>")
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

    return jsonify({"score": score, "total": len(results), "results": results})


@bp.app_errorhandler(404)
def not_found(error):
    return render_template("public/404.html"), 404
