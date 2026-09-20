# Question Bank Manager — Project Overview

**Owner:** Media Pons
**Audience:** 5th & 6th grade secondary school students (public-facing quizzes) + a single teacher/admin (question authoring)

## Purpose

A small, deliberately simple web app with two halves:

1. **Public frontend** — anyone with a link can browse published quizzes and take them. They see a score and a right/wrong breakdown at the end. Nothing is saved server-side.
2. **Admin panel** — a single logged-in admin creates Topics, Questions (classic 4-option multiple choice, one correct answer, optional image), and assembles hand-picked Questions into named, linkable Quizzes.

This is a deliberately trimmed-down successor to an earlier over-scoped "exam paper generator" project. Keep every step as small and boring as possible — no extra features beyond what's specified here.

## Tech stack

- Backend: Python Flask, app-factory pattern, Blueprints
- ORM: Flask-SQLAlchemy + Flask-Migrate
- DB: SQLite
- Styling: Tailwind CSS v3 (npm build), **compiled output committed to git** — no build step runs on the production server
- Interactivity: Vanilla JS + `fetch` for AJAX (quiz submission only; admin CRUD uses plain form posts)
- Auth: session-based, single admin account defined via `.env` — **no admin user database table**
- Deployment: Plesk-managed VPS, Nginx + Phusion Passenger, entry point `wsgi.py` (committed to git)
- Local dev entry point: `app.py` (separate from `wsgi.py`, which is production-only)
- Python virtual environment for all dependencies

## Folder structure

```
question-bank-manager/
├── app/
│   ├── __init__.py            # create_app()
│   ├── extensions.py          # db = SQLAlchemy()
│   ├── models.py              # Topic, Question, Quiz, QuizQuestion
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── decorators.py
│   ├── admin/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── public/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── static/
│   │   ├── src/input.css
│   │   ├── dist/output.css    # committed, never gitignored
│   │   ├── js/
│   │   └── uploads/questions/ # question images
│   └── templates/
│       ├── base.html
│       ├── auth/
│       ├── admin/
│       └── public/
├── migrations/                 # Flask-Migrate
├── instance/                   # SQLite database lives here (app.db) — folder committed, contents gitignored
├── config.py
├── app.py                      # LOCAL DEV entry point only
├── wsgi.py                     # PRODUCTION entry point — Passenger, committed to git
├── requirements.txt
├── package.json
├── tailwind.config.js
├── .env.example
├── .flaskenv                   # FLASK_APP=app.py, so `flask` CLI commands target the dev entry point
├── .gitignore
└── README.md
```

## Local dev vs. production entry points

Two separate entry points, never merge them:

- **`app.py`** — local development only. Creates the app via the factory and runs Flask's built-in dev server:
  ```python
  from app import create_app

  app = create_app()

  if __name__ == "__main__":
      app.run(debug=True)
  ```
  Run it directly with `python app.py`, or via `flask run` — either works locally.

- **`wsgi.py`** — production only. Never run directly by hand; Phusion Passenger imports this file and expects a module-level `application` object. Do not repurpose it for local dev and do not delete/regenerate it once it exists.

- **`.flaskenv`** sets `FLASK_APP=app.py` so every `flask` CLI command (`flask run`, `flask db migrate`, `flask db upgrade`, `flask seed-db`) unambiguously targets the dev entry point locally. Passenger on the server ignores `FLASK_APP` entirely — it always imports `wsgi.py` directly.

## Database schema

```
Topic
  id              INTEGER PK
  name            TEXT, unique, not null

Question
  id              INTEGER PK
  topic_id        INTEGER FK -> Topic.id, not null
  text            TEXT, not null
  image_path      TEXT, nullable          # e.g. "uploads/questions/abc123.png"
  choice_a        TEXT, not null
  choice_b        TEXT, not null
  choice_c        TEXT, not null
  choice_d        TEXT, not null
  correct_choice  ENUM('A','B','C','D'), not null

Quiz
  id              INTEGER PK
  title           TEXT, not null
  slug            TEXT, unique, not null   # used in public URL /quizzes/<slug>
  created_at      DATETIME, default now

QuizQuestion                               # junction table — hand-picked, ordered
  id              INTEGER PK
  quiz_id         INTEGER FK -> Quiz.id, not null
  question_id     INTEGER FK -> Question.id, not null
  order           INTEGER, not null
  unique(quiz_id, question_id)
```

No answer-choice images (question image only). No results/attempts are persisted anywhere — scoring happens per-request and is thrown away.

## Route map

**Public** (`app/public`)
- `GET  /` — landing page
- `GET  /quizzes` — list of published quizzes
- `GET  /quizzes/<slug>` — take a quiz (renders questions + choices, NEVER includes `correct_choice`)
- `POST /quizzes/<slug>/submit` — AJAX grading endpoint, returns JSON score + per-question reveal

**Auth** (`app/auth`)
- `GET/POST /admin/login`
- `GET /admin/logout`

**Admin** (`app/admin`, all behind `@login_required`)
- `GET /admin` — dashboard
- Topics CRUD under `/admin/topics`
- Questions CRUD under `/admin/questions`
- Quiz builder under `/admin/quizzes`

## Key design decisions (don't relitigate these mid-build)

- **Flat schema, not a separate Choices table** — `choice_a`..`choice_d` + `correct_choice` on `Question` itself. Classic, simple, matches "four fixed options" exactly.
- **No exposure of correct answers before submission.** The quiz-taking page's HTML/JS must never contain `correct_choice`. Grading happens server-side in the `/submit` endpoint.
- **No admin user table.** Credentials live in `.env` (`ADMIN_USERNAME`, `ADMIN_PASSWORD`), compared with `secrets.compare_digest`, session flag on success.
- **Only question images**, not per-choice images.
- **Nothing is persisted after a quiz attempt** — no results table.

## Build order (one spec file per Opencode session)

1. `01-project-scaffolding.md` — app factory, blueprint skeletons, Tailwind pipeline, `app.py` + `wsgi.py`
2. `02-database-models.md` — models, migrations, seed script
3. `03-public-frontend.md` — landing, listing, quiz-taking, AJAX grading + reveal
4. `04-auth.md` — login/logout, session guard
5. `05-admin-topics-questions.md` — Topics & Questions CRUD, image upload
6. `06-admin-quiz-builder.md` — assemble quizzes from the question bank
7. `07-polish-deployment.md` — final build, README, deployment checklist

Frontend is built before the admin panel so there's something visible and clickable early, using seeded data from step 2.
