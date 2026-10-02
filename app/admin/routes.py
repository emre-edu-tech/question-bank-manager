import os
import re
import uuid

from flask import (
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename

from app.admin import bp
from app.auth.decorators import login_required
from app.extensions import db
from app.models import Question, Quiz, QuizQuestion, Topic

ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
MAX_IMAGE_SIZE = 2 * 1024 * 1024  # 2MB
UPLOAD_SUBDIR = os.path.join("uploads", "questions")


@bp.before_request
@login_required
def require_login():
    pass


@bp.route("/admin")
def dashboard():
    return render_template("admin/dashboard.html")


# ---------------------------------------------------------------------------
# Topics CRUD
# ---------------------------------------------------------------------------


@bp.route("/admin/topics", methods=["GET", "POST"])
def topic_list():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Konu adı boş olamaz.", "error")
            topics = Topic.query.order_by(Topic.name).all()
            return render_template(
                "admin/topics_list.html", topics=topics, form_name=name
            )
        topic = Topic(name=name)
        db.session.add(topic)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Bu isimde bir konu zaten var.", "error")
            topics = Topic.query.order_by(Topic.name).all()
            return render_template(
                "admin/topics_list.html", topics=topics, form_name=name
            )
        flash("Konu oluşturuldu.", "success")
        return redirect(url_for("admin.topic_list"))

    topics = Topic.query.order_by(Topic.name).all()
    return render_template("admin/topics_list.html", topics=topics)


@bp.route("/admin/topics/<int:topic_id>/edit", methods=["GET", "POST"])
def topic_edit(topic_id):
    topic = Topic.query.get_or_404(topic_id)
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            return render_template(
                "admin/topic_form.html",
                topic=topic,
                form_name=name,
                error="Konu adı boş olamaz.",
            )
        topic.name = name
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return render_template(
                "admin/topic_form.html",
                topic=topic,
                form_name=name,
                error="Bu isimde bir konu zaten var.",
            )
        flash("Konu güncellendi.", "success")
        return redirect(url_for("admin.topic_list"))
    return render_template(
        "admin/topic_form.html", topic=topic, form_name=topic.name
    )


@bp.route("/admin/topics/<int:topic_id>/delete", methods=["POST"])
def topic_delete(topic_id):
    topic = Topic.query.get_or_404(topic_id)
    question_count = Question.query.filter_by(topic_id=topic.id).count()
    if question_count:
        flash(
            "Bu konu silinemez: önce ona ait soruları başka bir konuya "
            "taşıyın veya silin. (Önce sorularını silin veya taşıyın.)",
            "error",
        )
        return redirect(url_for("admin.topic_list"))
    db.session.delete(topic)
    db.session.commit()
    flash("Konu silindi.", "success")
    return redirect(url_for("admin.topic_list"))


# ---------------------------------------------------------------------------
# Questions CRUD
# ---------------------------------------------------------------------------


def _validate_image(file_storage):
    """Return (ok, error_message, data_or_None) for an uploaded image."""
    if file_storage is None or not file_storage.filename:
        return True, None, None
    filename = secure_filename(file_storage.filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return (
            False,
            "Sadece .png, .jpg, .jpeg veya .webp dosyaları yüklenebilir.",
            None,
        )
    data = file_storage.read()
    if len(data) > MAX_IMAGE_SIZE:
        return (
            False,
            "Görsel 2MB sınırını aşıyor. Daha küçük bir dosya seçin.",
            None,
        )
    if not data:
        return False, "Yüklenen dosya boş.", None
    return True, None, (data, ext)


def _save_image(data, ext):
    upload_dir = os.path.join(current_app.static_folder, UPLOAD_SUBDIR)
    os.makedirs(upload_dir, exist_ok=True)
    filename = uuid.uuid4().hex + ext
    full_path = os.path.join(upload_dir, filename)
    with open(full_path, "wb") as f:
        f.write(data)
    return os.path.join(UPLOAD_SUBDIR, filename).replace(os.sep, "/")


def _delete_image_file(image_path):
    if not image_path:
        return
    full_path = os.path.join(current_app.static_folder, image_path)
    if os.path.isfile(full_path):
        os.remove(full_path)


def _validate_question_form(form):
    errors = {}
    topic_id_raw = form.get("topic_id", "").strip()
    text = form.get("text", "").strip()
    choice_a = form.get("choice_a", "").strip()
    choice_b = form.get("choice_b", "").strip()
    choice_c = form.get("choice_c", "").strip()
    choice_d = form.get("choice_d", "").strip()
    correct_choice = form.get("correct_choice", "").strip().upper()

    topic = None
    if not topic_id_raw:
        errors["topic_id"] = "Konu seçmek zorunludur."
    else:
        try:
            topic = Topic.query.get(int(topic_id_raw))
        except (TypeError, ValueError):
            topic = None
        if topic is None:
            errors["topic_id"] = "Geçerli bir konu seçin."
    if not text:
        errors["text"] = "Soru metni boş olamaz."
    if not choice_a:
        errors["choice_a"] = "A şıkkı boş olamaz."
    if not choice_b:
        errors["choice_b"] = "B şıkkı boş olamaz."
    if not choice_c:
        errors["choice_c"] = "C şıkkı boş olamaz."
    if not choice_d:
        errors["choice_d"] = "D şıkkı boş olamaz."
    if correct_choice not in ("A", "B", "C", "D"):
        errors["correct_choice"] = "Doğru cevabı işaretleyin (A, B, C veya D)."

    values = {
        "topic_id": topic_id_raw,
        "text": form.get("text", ""),
        "choice_a": form.get("choice_a", ""),
        "choice_b": form.get("choice_b", ""),
        "choice_c": form.get("choice_c", ""),
        "choice_d": form.get("choice_d", ""),
        "correct_choice": correct_choice,
    }
    return errors, values, topic


@bp.route("/admin/questions")
def question_list():
    topics = Topic.query.order_by(Topic.name).all()
    selected_topic_id = request.args.get("topic_id", "").strip()
    query = Question.query.order_by(Question.id.desc())
    selected_topic = None
    if selected_topic_id:
        try:
            selected_topic = Topic.query.get(int(selected_topic_id))
        except (TypeError, ValueError):
            selected_topic = None
        if selected_topic is None:
            return redirect(url_for("admin.question_list"))
        query = query.filter_by(topic_id=selected_topic.id)
    questions = query.all()
    return render_template(
        "admin/questions_list.html",
        questions=questions,
        topics=topics,
        selected_topic_id=str(selected_topic.id) if selected_topic else "",
    )


@bp.route("/admin/questions/new", methods=["GET", "POST"])
def question_new():
    topics = Topic.query.order_by(Topic.name).all()
    if request.method == "POST":
        errors, values, topic = _validate_question_form(request.form)
        file_storage = request.files.get("image")
        image_ok, image_error, image_data = _validate_image(file_storage)
        if image_error:
            errors["image"] = image_error
        if errors:
            return render_template(
                "admin/question_form.html",
                topics=topics,
                values=values,
                errors=errors,
                question=None,
                is_edit=False,
            )
        question = Question(
            topic_id=topic.id,
            text=values["text"].strip(),
            choice_a=values["choice_a"].strip(),
            choice_b=values["choice_b"].strip(),
            choice_c=values["choice_c"].strip(),
            choice_d=values["choice_d"].strip(),
            correct_choice=values["correct_choice"],
        )
        if image_data is not None:
            data, ext = image_data
            question.image_path = _save_image(data, ext)
        db.session.add(question)
        db.session.commit()
        flash("Soru oluşturuldu.", "success")
        return redirect(url_for("admin.question_list"))
    return render_template(
        "admin/question_form.html",
        topics=topics,
        values={},
        errors={},
        question=None,
        is_edit=False,
    )


@bp.route("/admin/questions/<int:question_id>/edit", methods=["GET", "POST"])
def question_edit(question_id):
    question = Question.query.get_or_404(question_id)
    topics = Topic.query.order_by(Topic.name).all()
    if request.method == "POST":
        errors, values, topic = _validate_question_form(request.form)
        file_storage = request.files.get("image")
        image_ok, image_error, image_data = _validate_image(file_storage)
        if image_error:
            errors["image"] = image_error
        if errors:
            return render_template(
                "admin/question_form.html",
                topics=topics,
                values=values,
                errors=errors,
                question=question,
                is_edit=True,
            )
        question.topic_id = topic.id
        question.text = values["text"].strip()
        question.choice_a = values["choice_a"].strip()
        question.choice_b = values["choice_b"].strip()
        question.choice_c = values["choice_c"].strip()
        question.choice_d = values["choice_d"].strip()
        question.correct_choice = values["correct_choice"]
        if image_data is not None:
            data, ext = image_data
            _delete_image_file(question.image_path)
            question.image_path = _save_image(data, ext)
        elif request.form.get("remove_image"):
            _delete_image_file(question.image_path)
            question.image_path = None
        db.session.commit()
        flash("Soru güncellendi.", "success")
        return redirect(url_for("admin.question_list"))
    values = {
        "topic_id": str(question.topic_id),
        "text": question.text,
        "choice_a": question.choice_a,
        "choice_b": question.choice_b,
        "choice_c": question.choice_c,
        "choice_d": question.choice_d,
        "correct_choice": question.correct_choice,
    }
    return render_template(
        "admin/question_form.html",
        topics=topics,
        values=values,
        errors={},
        question=question,
        is_edit=True,
    )


@bp.route("/admin/questions/<int:question_id>/delete", methods=["POST"])
def question_delete(question_id):
    question = Question.query.get_or_404(question_id)
    QuizQuestion.query.filter_by(question_id=question.id).delete()
    _delete_image_file(question.image_path)
    db.session.delete(question)
    db.session.commit()
    flash("Soru silindi.", "success")
    return redirect(url_for("admin.question_list"))


# ---------------------------------------------------------------------------
# Quiz builder
# ---------------------------------------------------------------------------


_TURKISH_SLUG_MAP = {
    "ç": "c",
    "Ç": "c",
    "ğ": "g",
    "Ğ": "g",
    "ı": "i",
    "I": "i",
    "İ": "i",
    "ö": "o",
    "Ö": "o",
    "ş": "s",
    "Ş": "s",
    "ü": "u",
    "Ü": "u",
}


def slugify(text):
    """Lowercase, ASCII-transliterated, hyphenated slug."""
    text = text or ""
    for tr, ascii_char in _TURKISH_SLUG_MAP.items():
        text = text.replace(tr, ascii_char)
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text)
    return text.strip("-")


def _unique_slug(base_slug, exclude_id=None):
    candidate = base_slug
    counter = 2
    while True:
        query = Quiz.query.filter_by(slug=candidate)
        if exclude_id is not None:
            query = query.filter(Quiz.id != exclude_id)
        if query.first() is None:
            return candidate
        candidate = f"{base_slug}-{counter}"
        counter += 1


def _parse_ordered_question_ids(form):
    raw_ids = form.getlist("question_ids")
    ordered = []
    seen = set()
    for raw in raw_ids:
        try:
            question_id = int(raw)
        except (TypeError, ValueError):
            continue
        if question_id in seen:
            continue
        seen.add(question_id)
        ordered.append(question_id)
    if not ordered:
        return []
    existing_ids = {
        row.id
        for row in Question.query.filter(Question.id.in_(ordered)).all()
    }
    return [qid for qid in ordered if qid in existing_ids]


def _save_quiz_questions(quiz, ordered_question_ids):
    existing = QuizQuestion.query.filter_by(quiz_id=quiz.id).all()
    by_question_id = {row.question_id: row for row in existing}
    selected_set = set(ordered_question_ids)
    for row in existing:
        if row.question_id not in selected_set:
            db.session.delete(row)
    for position, question_id in enumerate(ordered_question_ids, start=1):
        row = by_question_id.get(question_id)
        if row is None:
            db.session.add(
                QuizQuestion(
                    quiz_id=quiz.id,
                    question_id=question_id,
                    order=position,
                )
            )
        else:
            row.order = position


@bp.route("/admin/quizzes")
def quiz_list():
    quizzes = Quiz.query.order_by(Quiz.id.desc()).all()
    counts = {}
    if quizzes:
        rows = (
            db.session.query(
                QuizQuestion.quiz_id, db.func.count(QuizQuestion.id)
            )
            .filter(
                QuizQuestion.quiz_id.in_([quiz.id for quiz in quizzes])
            )
            .group_by(QuizQuestion.quiz_id)
            .all()
        )
        counts = {quiz_id: count for quiz_id, count in rows}
    return render_template(
        "admin/quizzes_list.html", quizzes=quizzes, counts=counts
    )


@bp.route("/admin/quizzes/new", methods=["GET", "POST"])
def quiz_new():
    topics = Topic.query.order_by(Topic.name).all()
    questions = Question.query.order_by(Question.id).all()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        slug_input = request.form.get("slug", "").strip()
        ordered_ids = _parse_ordered_question_ids(request.form)
        errors = {}
        if not title:
            errors["title"] = "Quiz başlığı boş olamaz."
        base_slug = slugify(slug_input) if slug_input else slugify(title)
        if not base_slug:
            errors["slug"] = "Geçerli bir slug girin."
        if not ordered_ids:
            errors["questions"] = "En az bir soru seçmelisiniz."
        if errors:
            return render_template(
                "admin/quiz_form.html",
                topics=topics,
                questions=questions,
                values={
                    "title": request.form.get("title", ""),
                    "slug": slug_input,
                },
                selected_ids=ordered_ids,
                errors=errors,
                quiz=None,
                is_edit=False,
            )
        quiz = Quiz(title=title, slug=_unique_slug(base_slug))
        db.session.add(quiz)
        db.session.flush()
        _save_quiz_questions(quiz, ordered_ids)
        db.session.commit()
        flash("Quiz oluşturuldu.", "success")
        return redirect(url_for("admin.quiz_list"))
    return render_template(
        "admin/quiz_form.html",
        topics=topics,
        questions=questions,
        values={},
        selected_ids=[],
        errors={},
        quiz=None,
        is_edit=False,
    )


@bp.route("/admin/quizzes/<int:quiz_id>/edit", methods=["GET", "POST"])
def quiz_edit(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    topics = Topic.query.order_by(Topic.name).all()
    questions = Question.query.order_by(Question.id).all()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        slug_input = request.form.get("slug", "").strip()
        ordered_ids = _parse_ordered_question_ids(request.form)
        errors = {}
        if not title:
            errors["title"] = "Quiz başlığı boş olamaz."
        base_slug = slugify(slug_input) if slug_input else slugify(title)
        if not base_slug:
            errors["slug"] = "Geçerli bir slug girin."
        if not ordered_ids:
            errors["questions"] = "En az bir soru seçmelisiniz."
        if errors:
            return render_template(
                "admin/quiz_form.html",
                topics=topics,
                questions=questions,
                values={
                    "title": request.form.get("title", ""),
                    "slug": slug_input,
                },
                selected_ids=ordered_ids,
                errors=errors,
                quiz=quiz,
                is_edit=True,
            )
        quiz.title = title
        quiz.slug = _unique_slug(base_slug, exclude_id=quiz.id)
        _save_quiz_questions(quiz, ordered_ids)
        db.session.commit()
        flash("Quiz güncellendi.", "success")
        return redirect(url_for("admin.quiz_list"))
    selected_ids = [
        row.question_id
        for row in QuizQuestion.query.filter_by(quiz_id=quiz.id)
        .order_by(QuizQuestion.order)
        .all()
    ]
    return render_template(
        "admin/quiz_form.html",
        topics=topics,
        questions=questions,
        values={"title": quiz.title, "slug": quiz.slug},
        selected_ids=selected_ids,
        errors={},
        quiz=quiz,
        is_edit=True,
    )


@bp.route("/admin/quizzes/<int:quiz_id>/delete", methods=["POST"])
def quiz_delete(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    QuizQuestion.query.filter_by(quiz_id=quiz.id).delete()
    db.session.delete(quiz)
    db.session.commit()
    flash("Quiz silindi.", "success")
    return redirect(url_for("admin.quiz_list"))
