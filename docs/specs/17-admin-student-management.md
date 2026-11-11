# Step 17 — Admin Student Management & Idle Cleanup

**Context:** builds on `16-presentation-juice.md`. Adds a new admin section under `/admin/students` (the blueprint's `before_request` already enforces `@login_required` for everything under `app/admin`). **No schema change.** Motivation: students create a nickname and abandon quizzes mid-way, littering the leaderboard and DB — the admin needs visibility and a safe cleanup tool.

**Goal:** the admin can browse students (filter by class, search by nickname), inspect a student's activity, delete individual students, and bulk-delete **idle** students after an explicit preview-and-confirm step.

## Tasks

1. **Deletion semantics (decide once, apply everywhere)**

   - Hard delete, **explicit child-row deletes in order** (the models define no DB-level cascades; follow the existing pattern in `question_delete`, which deletes `QuizQuestion` rows first):
     1. `StudentBadge.query.filter_by(student_id=...)` → `.delete()`
     2. collect the student's `QuizAttempt.id`s, then `QuizAttemptAnswer.query.filter(QuizAttemptAnswer.attempt_id.in_(ids))` → `.delete()`
     3. `QuizAttempt.query.filter_by(student_id=...)` → `.delete()`
     4. `db.session.delete(student)`
   - A deleted student can re-register fresh with the same nickname+class (existing `/play` behavior creates a new row).
   - **Stale-session guard:** a student deleted while their browser session is still alive would hit FK/logic errors on `/start`, `/answer`, `/finish`. Fix `student_required` in `app/public/routes.py`: if `session['student_id']` is set but `Student.query.get(...)` is `None`, pop the session key and redirect to `/play` instead of proceeding. (Apply the same check inside the attempt routes' ownership validation where a `student` row is fetched.)

2. **List page** — `GET /admin/students` (`app/templates/admin/students_list.html`)

   - Columns: nickname, class code, total XP, level name (via `calculate_level`), completed/total attempt counts, **last activity** (`max(QuizAttempt.started_at)` for the student, falling back to `created_at` when they never started a quiz), badge count.
   - Avoid N+1: fetch the aggregate counts with grouped queries (`db.func.count`, `db.func.max`) joined on student ids, like the quiz-list count pattern in `app/admin/routes.py`.
   - Order: by class code, then nickname.
   - **Filters:** `?class_code=` (dropdown populated from distinct `Student.class_code`) and `?q=` (case-insensitive `nickname` contains). Show a total-count line ("X öğrenci").
   - Row actions: *Detay* link; delete is only on the detail page (keeps the list calm).
   - Link to a cleanup page: *"Boşta bekleyen öğrencileri temizle"*.

3. **Detail page** — `GET /admin/students/<int:student_id>` (`admin/student_detail.html`)

   - Profile card (nickname, class, XP, level, created date, badges with earned dates).
   - Attempts table: quiz title, score/total, XP earned, completed?, started/completed dates — newest first.
   - **Delete button:** a `POST` form to the delete endpoint with an inline JS confirmation (`onclick="return confirm('Bu öğrenci ve tüm denemeleri kalıcı olarak silinecek. Emin misiniz?')"`) — consistent with the app's plain-form admin pattern, but destructive actions get an explicit confirm.

4. **Single delete** — `POST /admin/students/<int:student_id>/delete`

   - Applies the deletion semantics from task 1, flashes `"Öğrenci silindi."`, redirects to the list (preserving the current `class_code` filter if present).

5. **Idle-cleanup preview** — `GET /admin/students/cleanup`

   - **Idle definition (fixed, documented in the template):** students with **zero completed attempts** whose **last activity** is older than **7 days** (default; `?days=N` accepted, clamped 1–90).
   - Show the matching students in a form with one **checkbox per row (all pre-checked)** plus nickname/class/last-activity columns, so the admin can deselect individuals. Show the count ("X öğrenci seçili").
   - Empty result → friendly "Temizlenecek öğrenci yok." message.
   - The form POSTs the selected student ids (hidden per-row inputs from the checkboxes).

6. **Bulk delete** — `POST /admin/students/cleanup/delete`

   - Accepts the id list; **re-validate each student still has zero completed attempts** before deleting (protects against a student finishing a quiz between preview and confirm — skip, don't error, and report how many were deleted vs. skipped in the flash message).
   - Applies deletion semantics per student, redirects back to the cleanup page (or the list) with a summary flash.

7. **Admin dashboard** — add a "Öğrenciler" link to `app/templates/admin/dashboard.html` alongside the existing section links.

8. **Update `docs/specs/00-overview.md`**: add the `/admin/students` routes to the admin route map and step 17 to the build order.

9. **Build step** — ⚠️ per `AGENTS.md`: run `npm run build:css` and include the rebuilt `app/static/dist/output.css` (new templates).

## Acceptance criteria

- The list renders correct counts and last-activity dates for a mix of students (active, abandoned, never-started) and N+1 queries are avoided (verify with SQL echo or query count).
- Class filter and nickname search both work; combined they narrow correctly.
- Deleting a student removes exactly their `StudentBadge`, `QuizAttemptAnswer`, `QuizAttempt`, and `Student` rows — nothing else (verify counts before/after in the DB).
- After an admin deletes student X, a browser still holding X's session is cleanly redirected to `/play` on its next protected request (no 500s).
- The cleanup preview lists only zero-completed-attempt students idle for ≥ N days; deselecting a row excludes it; the bulk POST skips any selected student who gained a completed attempt in the meantime.
- A re-registered nickname+class works normally after the original was deleted.
- All new admin pages are unreachable without login (blueprint guard holds).
- `npm run build:css` was run; the committed `output.css` includes the new classes.
