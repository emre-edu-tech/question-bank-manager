# Step 08 — Student Identity & Attempt Tracking

**Context:** this is the TÜBİTAK 4006 gamification extension, modifying the existing app from steps 01–07. It touches `app/models.py`, `app/public/routes.py`, the quiz-taking template from `03-public-frontend.md`, and `app/__init__.py` (for migrations). Read `00-overview.md` first for the full schema.

**Goal:** a lightweight, no-password student identity (nickname + class code), and quiz attempts actually get saved to the database. No new game mechanics yet — this is plumbing every later gamification step depends on. The existing bulk answer-all-then-submit UX from Step 03 is kept as-is for now.

## Why this exists

Everything from here on (XP, lives, badges, leaderboard) needs to know *which student* did *what*. Deliberately no passwords, emails, or real names — just a nickname plus a class code the teacher gives out verbally (e.g. "7A"). This keeps it simple and avoids collecting anything sensitive from children.

## Tasks

1. **Models** (add to `app/models.py`)

   ```python
   from datetime import datetime
   from app.extensions import db

   class Student(db.Model):
       id = db.Column(db.Integer, primary_key=True)
       nickname = db.Column(db.String(50), nullable=False)
       class_code = db.Column(db.String(20), nullable=False)
       created_at = db.Column(db.DateTime, default=datetime.utcnow)

       __table_args__ = (
           db.UniqueConstraint('nickname', 'class_code', name='uq_student_nickname_class'),
       )

   class QuizAttempt(db.Model):
       id = db.Column(db.Integer, primary_key=True)
       student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
       quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
       score = db.Column(db.Integer, nullable=False, default=0)
       total_questions = db.Column(db.Integer, nullable=False)
       completed = db.Column(db.Boolean, nullable=False, default=False)
       started_at = db.Column(db.DateTime, default=datetime.utcnow)
       completed_at = db.Column(db.DateTime, nullable=True)

       student = db.relationship('Student', backref='attempts')
       quiz = db.relationship('Quiz', backref='attempts')

   class QuizAttemptAnswer(db.Model):
       id = db.Column(db.Integer, primary_key=True)
       attempt_id = db.Column(db.Integer, db.ForeignKey('quiz_attempt.id'), nullable=False)
       question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
       selected_choice = db.Column(db.String(1), nullable=True)
       is_correct = db.Column(db.Boolean, nullable=False, default=False)

       attempt = db.relationship('QuizAttempt', backref='answers')
       question = db.relationship('Question')
   ```

   Run `flask db migrate -m "add student and attempt tracking"` then `flask db upgrade`.

2. **Identify-student route** (`app/public/routes.py`)

   ```python
   from flask import session, request, redirect, url_for, render_template, flash

   @public_bp.route('/play', methods=['GET', 'POST'])
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
           next_url = request.args.get('next') or url_for('public.quizzes_list')
           return redirect(next_url)

       return render_template('public/identify.html')
   ```

   Template `app/templates/public/identify.html`: a short branded form, two text inputs (nickname, class code), one submit button. Nothing fancy — this is a gate, not a feature.

3. **Student guard** (`app/public/routes.py` or a small helper)

   ```python
   from functools import wraps

   def student_required(view):
       @wraps(view)
       def wrapped(*args, **kwargs):
           if not session.get('student_id'):
               return redirect(url_for('public.identify_student', next=request.path))
           return view(*args, **kwargs)
       return wrapped
   ```

   Apply `@student_required` to the quiz-taking route (`GET /quizzes/<slug>`) and the submit route, so a student must identify themselves before playing.

4. **Persist attempts in the existing submit flow**

   In the `POST /quizzes/<slug>/submit` route from Step 03, after computing each question's correctness:
   - Create one `QuizAttempt` row (`student_id=session['student_id']`, `quiz_id`, `total_questions=len(questions)`, `completed=True`, `completed_at=datetime.utcnow()`).
   - Create one `QuizAttemptAnswer` row per question (`selected_choice`, `is_correct`).
   - Set `QuizAttempt.score` to the count of correct answers.
   - Commit once, after building all the rows (not once per row).
   - The JSON response shape returned to the client is unchanged from Step 03 — this step only adds persistence, not new behavior visible to the student yet.

5. **Minimal "my history" page** (`GET /my-history`, `@student_required`)

    Lists the current student's past `QuizAttempt` rows (quiz title, score/total, date), newest first. This exists purely so Step 08 is end-to-end testable — there's no game mechanic here yet, just proof the data is really being saved.
    Linked from the header nav (see task 6) so students can reach it without typing the URL.

6. **Student exit** (`app/public/routes.py` + `app/templates/base.html`)

    Science-fair kiosk flow: many students share one screen, so the current student must be able to step aside for the next one without touching the admin login.

    ```python
    @public_bp.route("/exit")
    def exit_student():
        session.pop("student_id", None)
        return redirect(url_for("public.identify_student"))
    ```

    Only `student_id` is popped — never `session.clear()` — so a teacher logged in as admin on the same browser stays logged in. After exit the next student lands directly on the `/play` identify form.
    Header nav in `app/templates/base.html`: the Quizler link stays first and always visible; a "Geçmişim" link (`url_for('public.my_history')`, same styling as Quizler) and the exit button below are rendered only when a student is identified:

    ```html
    <nav class="flex items-center gap-4">
        <a href="{{ url_for('public.quiz_list') }}" class="...">Quizler</a>
        {% if session.get('student_id') %}
        <a href="{{ url_for('public.my_history') }}" class="...">Geçmişim</a>
        <a href="{{ url_for('public.exit_student') }}" title="Çıkış yap, sıradaki öğrenci giriş yapabilsin" class="...">👋 Çıkış</a>
        {% endif %}
    </nav>
    ```

    "Geçmişim" shares the guard's behavior: it is hidden while anonymous (there is no history to show), and the `@student_required` decorator on `/my-history` remains the enforcement — the nav link is discoverability, not access control.

## Acceptance criteria

- Visiting `/quizzes/<slug>` while `session['student_id']` is unset redirects to `/play?next=/quizzes/<slug>`.
- Submitting the identify form with a new nickname+class_code creates exactly one `Student` row; submitting the same pair again reuses the existing row (no duplicate).
- Taking and submitting a quiz creates one `QuizAttempt` row and one `QuizAttemptAnswer` row per question, with correct `score` and `is_correct` values.
- `/my-history` shows the attempt just completed.
- The header shows neither "Geçmişim" nor an exit button while anonymous; once a student is identified it shows a "Geçmişim" link to `/my-history` plus a "👋 Çıkış" button linking to `/exit`, and hides both again after exiting.
- Visiting `/exit` pops only `student_id` (an admin session on the same browser survives), redirects to `/play`, and afterwards `/quizzes/<slug>` redirects back to `/play?next=...`.
- The quiz-taking UX and the submit JSON response are otherwise unchanged from Step 03 — a student notices no visible difference yet except being asked to identify themselves first.

## Deploying this step to production (Plesk/Passenger)

This is the first step since the initial schema that adds tables, so it is the first step that requires a **production database migration**. The pattern below applies to this and every later schema-changing step (09–13).

**Local machine — commit and push everything first:**

1. This step creates a *new, untracked* file, `migrations/versions/53e7d576b4d2_add_student_and_attempt_tracking.py`. A plain `git commit` of modified files will silently leave it behind, and then `flask db upgrade` on the server will report "already at head" while the tables are still missing. So stage explicitly and confirm:
   ```bash
   git add app/models.py app/public/routes.py app/templates/base.html app/templates/public/identify.html app/templates/public/history.html app/static/dist/output.css migrations/versions/53e7d576b4d2_add_student_and_attempt_tracking.py
   git status --short   # the migration file must be listed as added (A), not untracked (??)
   git commit -m "..."
   git push
   ```

**Server — SSH in as the subscription system user, `cd` to the project root, then in this order:**

2. Pull the code (this brings the new `migrations/versions/*.py` file):
   ```bash
   git pull
   ```
3. Back up the live SQLite database *before* touching it (adjust the path if the server's `.env` sets `SQLALCHEMY_DATABASE_URI` somewhere other than the default `instance/app.db`):
   ```bash
   cp instance/app.db "instance/app.db.bak-$(date +%F)"
   ```
4. Apply the migration. This is the production equivalent of the local `flask db upgrade` — and yes, this is exactly the command to run. Two details matter:
   - **Never run `flask db migrate` on the server.** Migrations are generated locally, reviewed, and committed; the server only *applies* them with `upgrade`.
   - `.flaskenv` is gitignored, so it does not exist on the server and the `flask` CLI won't know which app to target. Set `FLASK_APP` explicitly and use the server venv's python (same interpreter Passenger uses per `wsgi.py`):
   ```bash
   FLASK_APP=app.py venv/bin/python -m flask db upgrade
   ```
5. Verify the migration actually applied:
   ```bash
   FLASK_APP=app.py venv/bin/python -m flask db current
   ```
   It must print `53e7d576b4d2 (head)`. If it prints the older revision instead, the migration file didn't arrive — go back to step 1 and check the push/pull.
6. Restart the app so Passenger picks up the new code:
   ```bash
   touch tmp/restart.txt
   ```
7. Smoke test: open a quiz, identify as a student, submit, and check the score saves (the new `student`, `quiz_attempt`, and `quiz_attempt_answer` tables now exist in the live DB).

**Rollback:** if anything goes wrong, restore the backup and restart:
```bash
cp "instance/app.db.bak-<date>" instance/app.db
touch tmp/restart.txt
```
(`flask db downgrade -1` also works, but restoring the backup is simpler and safer for SQLite.)
