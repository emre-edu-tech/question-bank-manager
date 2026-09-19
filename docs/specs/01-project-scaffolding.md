# Step 1 — Project Scaffolding

**Goal:** a runnable Flask skeleton with the app factory, three blueprints wired up, a working Tailwind build pipeline, and both entry points (`app.py` for local dev, `wsgi.py` for production) — nothing functional yet, just the skeleton and proof it all boots.

Read `00-overview.md` first for the folder structure, tech stack, and route map this step must produce.

## Tasks

1. **Python environment**
   - Create and activate a virtual environment (`python -m venv venv`).
   - `pip install Flask Flask-SQLAlchemy Flask-Migrate python-dotenv`
   - Freeze into `requirements.txt`.

2. **Folder structure**
   - Create the exact structure from `00-overview.md`: `app/`, `app/auth/`, `app/admin/`, `app/public/`, `app/static/{src,dist,js,uploads/questions}`, `app/templates/{auth,admin,public}`.
   - Each blueprint package (`auth`, `admin`, `public`) gets an `__init__.py` that creates its `Blueprint` object, and a `routes.py` importing it.

3. **Config**
   - `config.py`: a `Config` class reading from environment variables via `python-dotenv`:
     - `SECRET_KEY`
     - `SQLALCHEMY_DATABASE_URI` — default to `sqlite:///` + absolute path to `instance/app.db`
     - `SQLALCHEMY_TRACK_MODIFICATIONS = False`
     - `ADMIN_USERNAME`, `ADMIN_PASSWORD` (used later in step 4)

4. **Extensions**
   - `app/extensions.py`: instantiate `db = SQLAlchemy()` (no app bound yet).

5. **App factory**
   - `app/__init__.py`: `create_app()` that:
     - creates the Flask app with correct `static_folder`/`template_folder`
     - loads `Config`
     - calls `db.init_app(app)`
     - registers the three blueprints
     - returns `app`
   - Each blueprint's `routes.py` gets one placeholder route for now (e.g. `public` → `/` returns a rendered `base.html`; `auth` → `/admin/login` returns plain text "login placeholder"; `admin` → `/admin` returns plain text "admin placeholder"). These get replaced in later steps.

6. **Templates**
   - `app/templates/base.html`: HTML skeleton, links to `static/dist/output.css`, a simple header with the "Media Pons" text wordmark, and `{% block content %}{% endblock %}`.
   - Public's placeholder route renders `base.html` with a short "coming soon" message in the content block.

7. **Tailwind pipeline**
   - `npm init -y`, `npm install -D tailwindcss@3`
   - `npx tailwindcss init` → `tailwind.config.js`, set `content` to include `app/templates/**/*.html` and `app/static/js/**/*.js`.
   - `app/static/src/input.css` with the three `@tailwind` directives.
   - Add npm scripts to `package.json`:
     - `"build:css": "tailwindcss -i ./app/static/src/input.css -o ./app/static/dist/output.css --minify"`
     - `"watch:css": "tailwindcss -i ./app/static/src/input.css -o ./app/static/dist/output.css --watch"`
   - Run `npm run build:css` once to produce `app/static/dist/output.css`.

8. **Local dev entry point**
   - `app.py` at the project root — this is what you actually run locally, never `wsgi.py`:
     ```python
     from app import create_app

     app = create_app()

     if __name__ == "__main__":
         app.run(debug=True)
     ```
   - Supports both `python app.py` and `flask run` for local development.

9. **Passenger entry point**
   - `wsgi.py` at the project root — production only, never run by hand:
     ```python
     from app import create_app
     application = create_app()
     ```
   - This file gets committed to git — it is the one Phusion Passenger expects. Keep it separate from `app.py`; do not merge the two or make one import the other.

10. **Environment files**
    - `.env.example` listing `SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `FLASK_ENV`.
    - Create your own local `.env` from it (not committed).
    - `.flaskenv` (committed — no secrets in it) containing `FLASK_APP=app.py`, so every `flask` CLI command (`flask run`, `flask db migrate`, `flask seed-db` in later steps) targets the local dev entry point unambiguously. This has no effect on production — Passenger imports `wsgi.py` directly and never consults `FLASK_APP`.

11. **.gitignore**
    - Ignore: `venv/`, `node_modules/`, `instance/`, `__pycache__/`, `*.pyc`, `.env`
    - Do **NOT** ignore: `app/static/dist/output.css`, `app.py`, `wsgi.py`, `.flaskenv` — all committed on purpose.

## Acceptance criteria

- `python app.py` starts the dev server without errors.
- `flask run` also starts it without errors or needing `FLASK_APP` set manually (picked up from `.flaskenv`).
- `/` renders `base.html` with the Media Pons wordmark and the Tailwind-compiled styles visibly applied (e.g. a styled heading, not unstyled browser default text).
- `/admin` and `/admin/login` return their placeholder text with no errors.
- `npm run build:css` runs clean and produces `app/static/dist/output.css`.
- `wsgi.py` imports and calls `create_app()` without errors when run through `python -c "import wsgi"` — and is otherwise never used to run the app locally.
