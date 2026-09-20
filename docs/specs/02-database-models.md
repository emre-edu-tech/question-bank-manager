# Step 2 — Database Models & Seed Data

**Goal:** the four SQLAlchemy models from `00-overview.md`, migrations set up, and a seed script producing enough realistic sample data that Step 3 (public frontend) can be built and tested without the admin panel existing yet.

## Tasks

1. **Install migration tooling**
   - `pip install Flask-Migrate`, add to `requirements.txt`.
   - Wire `Migrate(app, db)` into `create_app()` in `app/__init__.py`.

2. **Models** (`app/models.py`)
   - `Topic`: `id`, `name` (String, unique, not null). Relationship: `questions` (one-to-many).
   - `Question`: `id`, `topic_id` (FK), `text` (Text, not null), `image_path` (String, nullable), `choice_a`/`choice_b`/`choice_c`/`choice_d` (String, not null each), `correct_choice` (`db.Enum('A', 'B', 'C', 'D', name='correct_choice_enum')`, not null).
   - `Quiz`: `id`, `title` (String, not null), `slug` (String, unique, not null), `created_at` (DateTime, default `datetime.utcnow`).
   - `QuizQuestion`: `id`, `quiz_id` (FK → Quiz.id), `question_id` (FK → Question.id), `order` (Integer, not null). Add a `UniqueConstraint('quiz_id', 'question_id')`.
   - Add relationships so you can do `quiz.quiz_questions` ordered by `order`, and reach the underlying `Question` from each `QuizQuestion`.

3. **Migrations**
   - `flask db init`
   - `flask db migrate -m "initial schema"`
   - `flask db upgrade`
   - Confirm `instance/app.db` is created with all four tables.

4. **Seed script**
   - Add a Flask CLI command, e.g. in `app/__init__.py` or a new `app/seed.py` registered via `app.cli.command("seed-db")`.
   - Guard against double-seeding: if `Topic.query.count() > 0`, print a message and exit without inserting anything.
   - Insert:
     - 2–3 `Topic` rows relevant to 5th/6th grade ICT (e.g. "Bilgisayar Donanımı", "İnternet ve Ağ Güvenliği", "Yazılım ve Uygulamalar").
     - 8–10 `Question` rows spread across those topics, realistic multiple-choice content, varied `correct_choice` letters. Leave `image_path` null for most; for at least one question, place a sample image file in `app/static/uploads/questions/` and reference its relative path, so Step 3 can verify image rendering works.
     - 1 `Quiz` row (e.g. title "Örnek Quiz", slug `ornek-quiz`) with `QuizQuestion` rows linking 5–6 of the seeded questions in a deliberate order.

## Acceptance criteria

- `flask db upgrade` runs clean from an empty database.
- `flask seed-db` populates the tables; running it a second time does nothing (no duplicates).
- Via `flask shell`, `Quiz.query.filter_by(slug='ornek-quiz').first().quiz_questions` returns the seeded questions in the correct order.
- At least one seeded question has a non-null `image_path` pointing at a real file under `app/static/uploads/questions/`.
