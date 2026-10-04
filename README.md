# Question Bank Manager

Small Flask app with a public quiz frontend (no login, nothing persisted)
and a single-admin panel for Topics, Questions (4-option multiple choice,
optional image) and hand-assembled Quizzes.

## Local setup

1. **Create a virtual environment**

   ```bash
   python -m venv venv
   ```

2. **Activate it**

   ```bash
   venv/Scripts/Activate.ps1
   ```

   or (Linux/macOS):

   ```bash
   source venv/bin/activate
   ```

3. **Install Python dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Install Node dependencies**

   ```bash
   npm install
   ```

5. **Configure environment**

   Copy `.env.example` to `.env` and fill it in:

   ```bash
   copy .env.example .env
   ```

   or (Linux/macOS):

   ```bash
   cp .env.example .env
   ```

   Required variables (`ADMIN_USERNAME`, `ADMIN_PASSWORD`, `SECRET_KEY`,
   `FLASK_ENV` — see `.env.example`):

   - `SECRET_KEY` — Flask session signing key.
   - `ADMIN_USERNAME` / `ADMIN_PASSWORD` — single admin login (no admin
     user table; compared with `secrets.compare_digest`).
   - `FLASK_ENV` — `development` locally.

6. **Generating a `SECRET_KEY`**

   The app reads `SECRET_KEY` from the environment (local `.env` file) and
   refuses to start if it is missing. Generate one with:

   ```
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

   Then paste the printed value as `SECRET_KEY=<value>` in your local `.env`
   file (`.env.example` intentionally keeps the `SECRET_KEY=change-me`
   placeholder).

   This must be run again on the production server to generate a
   **separate** key for the server's `.env` — the local development key
   must never be reused in production.

7. **Build the CSS**

   ```bash
   npm run build:css
   ```

   This compiles `app/static/src/input.css` to
   `app/static/dist/output.css` (minified). The compiled file is committed
   to git — always rebuild and commit it after changing any template or
   `app/static/js` file.

8. **Run migrations**

   ```bash
   flask db upgrade
   ```

   That creates `instance/app.db` with **all four tables**.
   (`.flaskenv` sets `FLASK_APP=app.py`, so `flask` commands target the
   local dev entry point. If there is no `.flaskenv` on a machine, use
   `export FLASK_APP=app.py` / `$env:FLASK_APP = "app.py"` first.)

   **Important Note**: If you are using `echo` command of Powershell then
   you can get `encoding` error. That's why create files using a text
   editor instead.

9. **Seed sample data (optional, dev only)**

   ```bash
   flask seed-db
   ```

   Seeding is optional — only for local testing. There is a guard that
   refuses to run on a non-empty database, so it can never duplicate or
   overwrite real content.

10. **Run the dev server**

    ```bash
    flask run
    ```

    or:

    ```bash
    python app.py
    ```

## Deployment notes (Plesk VPS + Phusion Passenger)

- Passenger expects `wsgi.py` at the project root exposing `application`.
  Do not rename it, do not repurpose it for local dev (`app.py` is the
  local entry point):

  ```python
  import sys
  import os

  # Set the project root directory
  project_home = os.path.dirname(__file__)
  sys.path.insert(0, project_home)

  # Set Python interpreter to your venv
  INTERP = os.path.join(project_home, "venv", "bin", "python3")
  if sys.executable != INTERP:
      os.execl(INTERP, INTERP, *sys.argv)

  # Import the app factory and create the application instance
  from app import create_app

  application = create_app()
  ```

- The compiled `app/static/dist/output.css` is committed and served
  as-is — no build step runs on the server. Rebuild locally with
  `npm run build:css` and commit the result before deploying.

- Admin credentials are set via the server's `.env`, not in code.
  Generate a separate `SECRET_KEY` on the server (see above) and never
  reuse the local dev key.

- `Domain > Hosting & DNS > Apache & nginx > Disable Proxy Mode`
- `Domain > Hosting & DNS > Apache & nginx > Additional nginx Directives`

  ```text
  passenger_enabled on;
  passenger_app_type wsgi;
  passenger_startup_file wsgi.py;
  passenger_app_root /var/www/vhosts/example.com/subdomain.example.com;
  passenger_python /var/www/vhosts/example.com/subdomain.example.com/venv/bin/python;
  ```

- On the server, create and use a virtual environment (never use the
  system python):

  ```bash
  python -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  ```

- Run migrations on the server (`FLASK_APP=app.py` must be set if there
  is no `.flaskenv` there):

  ```bash
  flask db upgrade
  ```

- After each update, restart the application server:

  ```bash
  git pull
  touch tmp/restart.txt
  ```
