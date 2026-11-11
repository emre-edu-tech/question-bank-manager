# Step 15 — Student Profile & Topic Mastery

**Context:** builds on `14-question-explanations-review.md`. Adds one public route and one template. No schema change — mastery is computed on the fly from `QuizAttemptAnswer` ⋈ `QuizAttempt` ⋈ `Question` ⋈ `Topic`. Follows the pattern of the existing `/my-history` and `/my-badges` pages (`@student_required` in `app/public/routes.py`).

**Goal:** students see how well they are doing **per topic** ("Ağ Temelleri: 75% 🟩"), turning raw XP into visible learning progress. This is the core educational-feedback piece of improvement scope v2.

## Tasks

1. **Route** — `GET /profile`, decorated `@student_required`, in `app/public/routes.py`:

   ```python
   @bp.route("/profile")
   @student_required
   def profile():
       student = Student.query.get_or_404(session['student_id'])
       level_number, level_name = calculate_level(student.total_xp)
       # overall stats: completed attempts, answered count, correct count
       # per-topic stats (see below)
       return render_template("public/profile.html", ...)
   ```

2. **Per-topic mastery query** (one grouped query, computed in the route):

   ```python
   rows = (
       db.session.query(
           Topic.id,
           Topic.name,
           db.func.count(QuizAttemptAnswer.id).label("answered"),
           db.func.sum(db.case((QuizAttemptAnswer.is_correct.is_(True), 1), else_=0)).label("correct"),
       )
       .join(Question, Question.topic_id == Topic.id)
       .join(QuizAttemptAnswer, QuizAttemptAnswer.question_id == Question.id)
       .join(QuizAttempt, QuizAttempt.id == QuizAttemptAnswer.attempt_id)
       .filter(
           QuizAttempt.student_id == student.id,
           QuizAttempt.completed.is_(True),   # only finished attempts count
       )
       .group_by(Topic.id, Topic.name)
       .order_by(Topic.name)
       .all()
   )
   ```

   Compute `accuracy = round(correct / answered * 100)` per topic (guard against `answered == 0`).

3. **Overall stats** for the header card:

   - total XP, level number + name (via `calculate_level`)
   - completed attempts count
   - total answered / total correct across completed attempts, overall accuracy %
   - badge count (`len(student.student_badges)`)

4. **Template** `app/templates/public/profile.html`:

   - **Header card:** nickname, class code, level ("Seviye 3 — Uzman"), XP, badge count, completed-attempt count, overall accuracy.
   - **Mastery list:** one row per topic with questions the student has answered:
     - topic name, `"correct/answered doğru"` and the percentage
     - a Tailwind progress bar: outer `bg-gray-200 rounded-full h-3 w-full`, inner fill `h-3 rounded-full` with width `style="width: X%"` (inline style, so no dynamic Tailwind class needed) and color by band:
       - ≥ 80% → `bg-green-500`
       - ≥ 50% → `bg-yellow-500`
       - else → `bg-red-500`
     - put the three color classes as plain literals in the template so Tailwind keeps them.
   - **Empty state:** no completed attempts yet → friendly message ("Henüz quiz tamamlamadın — bir quiz oynayarak konu ilerlemeni başlat!").
   - Turkish UI copy throughout, matching the tone of existing pages.

5. **Discovery / links** — wherever `/my-badges` and `/my-history` are already linked (nav in `app/templates/base.html` and/or the history page), add a *"Konu İlerlemem"* link to `/profile`. Also consider linking back from the quiz finish screen area to the profile.

6. **Build step** — ⚠️ per `AGENTS.md`: run `npm run build:css` and include the rebuilt `app/static/dist/output.css`.

7. **Update `docs/specs/00-overview.md`**: add `GET /profile` to the public route map and step 15 to the build order.

## Acceptance criteria

- A student who has completed quizzes sees one mastery row per touched topic with a correct percentage (spot-check one topic's numbers directly against the DB).
- Only **completed** attempts contribute — an abandoned/game-over-midway attempt's answers do not appear in mastery numbers (note: game-over attempts *are* marked completed by step 10, so they do count; verify the numbers match what you intend and document the behavior in the overview if needed).
- Accuracy bands color the bar green/yellow/red consistently.
- A student with zero completed attempts sees the empty state, not a crash or a division-by-zero.
- Visiting `/profile` without a student session redirects to `/play` (existing `student_required` behavior).
- `npm run build:css` was run; the committed `output.css` includes the new classes.
