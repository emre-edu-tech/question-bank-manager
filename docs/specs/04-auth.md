# Step 4 — Admin Authentication

**Goal:** a single-admin, session-based login gate for everything under `/admin`. No database table for users — credentials come from `.env`.

## Tasks

1. **Login route** (`GET/POST /admin/login`, `app/auth/routes.py`)
   - `GET`: render a simple, branded login form (username, password).
   - `POST`: compare submitted values against `current_app.config['ADMIN_USERNAME']` / `['ADMIN_PASSWORD']` using `secrets.compare_digest` for both fields (avoid short-circuit timing leaks).
   - On success: `session['is_admin'] = True`, redirect to `/admin` (or to a `next` query param if present and safe).
   - On failure: flash an error message, re-render the login form (don't leak which field was wrong).
   - **Login form design** (`app/templates/auth/login.html`): the card is narrow (`max-w-sm`) and horizontally centered (`mx-auto`); header content (lock badge, brand line, heading, subtitle) is center-aligned (`text-center`); vertical rhythm uses one consistent spacing scale (`space-y-5` in the form, `mt-2` label→input, `mt-6` between blocks); error flashes are centered with an icon; inputs get `autofocus` on username; the submit button has a hover + active state; a "← Quizlere dön" link sits centered below the form.

2. **Logout route** (`GET /admin/logout`)
   - Clear `session['is_admin']`, redirect to the login page.

3. **Login guard** (`app/auth/decorators.py`)
   - A `login_required` decorator: if `session.get('is_admin')` is falsy, redirect to `/admin/login?next=<requested path>`; otherwise call the wrapped view.
   - Apply this decorator to every route in `app/admin/routes.py` (a blueprint-level `before_request` hook is fine too — pick whichever is simpler to apply consistently).

4. **Session hardening & `SECRET_KEY` generation**
   - In `config.py`, set `SESSION_COOKIE_HTTPONLY = True` and `SESSION_COOKIE_SAMESITE = 'Lax'`.
   - Generate a real local `SECRET_KEY` — don't leave it blank or use a placeholder string:
     ```
     python -c "import secrets; print(secrets.token_hex(32))"
     ```
   - Take the printed value and paste it as `SECRET_KEY=<value>` in the local `.env` file (not `.env.example`, which keeps a placeholder like `SECRET_KEY=change-me`).
   - Confirm `config.py` actually reads `SECRET_KEY` from the environment and the app fails loudly (raises an error) at startup if it's missing, rather than silently falling back to an insecure default.
   - **Note on README:** if `README.md` already exists in the project at this point, append a short "Generating a SECRET_KEY" section to it covering both the command above and the note that production needs its own separately-generated key (never reuse the local dev key on the server). If `README.md` doesn't exist yet, skip this — it's covered when the README is created in Step 7.

5. **Placeholder dashboard**
   - Replace the Step 1 `/admin` placeholder with a minimal dashboard page (branded, just a heading and logout link for now) — the real admin sections get built in Steps 5–6.

6. **Rebuild the compiled CSS**
   - Styling is Tailwind CSS v3 with the compiled output committed to git (`app/static/dist/output.css`) — no build step runs on the production server.
   - After any template change that introduces new Tailwind classes, rebuild locally before checking the page visually, or the new classes will silently have no styles:
     ```
     npm run build:css
     ```
   - Commit the rebuilt `app/static/dist/output.css` together with the template changes.

## Important: rebuild Tailwind CSS after template changes

Styling is Tailwind CSS v3 with the compiled output committed to git (`app/static/dist/output.css` — no build step runs on the production server). Tailwind only generates CSS for classes it finds in the templates at build time, so **any template change that introduces new utility classes requires a rebuild before checking the page visually**:

```
npm run build:css
```

Skipping this leaves the new classes unstyled and the page looks broken even though the HTML is correct. Commit the rebuilt `output.css` together with the template changes.

## Acceptance criteria

- Visiting any `/admin/*` route while logged out redirects to `/admin/login`.
- Submitting correct credentials logs in and lands on `/admin`.
- Submitting incorrect credentials shows a generic error and does not log in.
- `/admin/logout` clears the session; a subsequent visit to `/admin` redirects back to login.
- Local `.env` contains a real, randomly-generated `SECRET_KEY` (not a placeholder); the app raises a clear error on startup if `SECRET_KEY` is unset.
