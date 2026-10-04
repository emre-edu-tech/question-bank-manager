# Step 7 — Polish & Deployment

**Goal:** tie off loose ends and get the app genuinely ready to deploy on the Plesk/Passenger VPS.

## Tasks

1. **Final CSS build**
   - Run `npm run build:css` (minified) one last time and commit the resulting `app/static/dist/output.css`.

2. **Error pages**
   - Add branded 404 and 500 error pages (`app/templates/public/404.html`, `500.html` or similar), registered via Flask error handlers, so a broken link or server error never shows a raw stack trace or Flask's default page to a student.

3. **Verify the Passenger entry point**
   - Confirm `wsgi.py` (created in Step 1, do not regenerate it) correctly exposes `application = create_app()` and that `python -c "import wsgi"` runs clean from the project root with the venv active.

4. **Seed command safety**
   - Confirm the `flask seed-db` guard from Step 2 (skip if data already exists) is still in place, so it can't be run accidentally against a live database and duplicate or overwrite real content.

5. **.env / secrets check**
   - Confirm `.env` is gitignored and `.env.example` is up to date with every variable the app actually reads (`SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `FLASK_ENV`, anything added along the way).

6. **README.md**
   - Local setup: create venv, `pip install -r requirements.txt`, `npm install`, `npm run build:css`, copy `.env.example` to `.env` and fill it in, `flask db upgrade`, `flask seed-db` (optional, dev only), `flask run`.
   - Deployment notes: Plesk/Passenger expects `wsgi.py` at the project root exposing `application`; the compiled `app/static/dist/output.css` is committed and served as-is — no build step runs on the server.
   - Admin credentials are set via the server's `.env`, not in code.
   - **Generating a `SECRET_KEY`:** include a section with the exact command:
     ```
     python -c "import secrets; print(secrets.token_hex(32))"
     ```
     State explicitly that this must be run again on the production server to generate a **separate** key for the server's `.env` — the local development key must never be reused in production. If Step 4 already added this section, just confirm it's present and accurate rather than duplicating it.

7. **Manual smoke test checklist** (walk through and confirm each, don't just assume):
   - [ ] Create a topic → create a question with an image → create a quiz using it, from a clean admin login.
   - [ ] Take that quiz as a student, submit, verify the score and reveal are correct.
   - [ ] Log out, confirm every `/admin/*` route redirects to login.
   - [ ] Visit an invalid quiz slug and an invalid admin sub-page — both show the branded error pages, not stack traces.
   - [ ] Check the quiz-taking page's rendered source has no correct answers in it.

## Acceptance criteria

- All smoke test checklist items pass.
- `output.css` is committed and reflects the final UI (no missing Tailwind classes from late-added markup).
- README is complete enough that picking this project back up in six months requires no guesswork.
- The app runs correctly when served through `wsgi.py` locally (`gunicorn -w 1 wsgi:application` or equivalent local check), simulating how Passenger will invoke it.
