# Step 09 — XP & Levels

**Context:** builds directly on `08-student-identity-and-attempts.md`. Modifies `app/models.py`, the `POST /quizzes/<slug>/submit` route, and the results-reveal UI from Step 03.

**Goal:** correct answers earn XP, XP accumulates on the student, and a level is derived from total XP. This is the base currency every later feature (speed bonus, badges, leaderboard) is denominated in.

## Tasks

1. **Model additions**

   ```python
   # Student — add:
   total_xp = db.Column(db.Integer, nullable=False, default=0)

   # QuizAttempt — add:
   xp_earned = db.Column(db.Integer, nullable=False, default=0)

   # QuizAttemptAnswer — add:
   xp_awarded = db.Column(db.Integer, nullable=False, default=0)
   ```

   `flask db migrate -m "add xp tracking"` then `flask db upgrade`.

2. **XP constant & level thresholds** (new small module, e.g. `app/gamification.py`)

   ```python
   XP_PER_CORRECT_ANSWER = 10

   LEVEL_THRESHOLDS = [
       (0,    1, "Çaylak"),
       (50,   2, "Kaşif"),
       (150,  3, "Uzman"),
       (300,  4, "Usta"),
       (500,  5, "Efsane"),
   ]

   def calculate_level(total_xp: int):
       """Returns (level_number, level_name) for a given XP total."""
       current = LEVEL_THRESHOLDS[0]
       for threshold_xp, level_number, level_name in LEVEL_THRESHOLDS:
           if total_xp >= threshold_xp:
               current = (threshold_xp, level_number, level_name)
       return current[1], current[2]
   ```

   Keep the thresholds in one place so later steps (leaderboard, badges) import the same function instead of recalculating.

3. **Award XP in the submit route**

   Inside the existing `POST /quizzes/<slug>/submit` loop from Step 08, when building each `QuizAttemptAnswer`:

   ```python
   xp_awarded = XP_PER_CORRECT_ANSWER if is_correct else 0
   answer = QuizAttemptAnswer(
       attempt_id=attempt.id,
       question_id=question.id,
       selected_choice=selected_choice,
       is_correct=is_correct,
       xp_awarded=xp_awarded,
   )
   attempt_xp_total += xp_awarded
   ```

   After the loop:
   ```python
   attempt.xp_earned = attempt_xp_total
   student.total_xp += attempt_xp_total
   db.session.commit()
   ```

   Add `xp_earned` and the student's new `total_xp` to the JSON response the client already receives from Step 03/08:
   ```json
   { "score": 4, "total": 6, "xp_earned": 40, "total_xp": 190, "level_number": 3, "level_name": "Uzman", "results": [...] }
   ```

4. **Display on the results reveal** (client JS from Step 03)

   After showing the score banner, add an XP line: `"+40 deneyim puanı kazandın! Toplam: 190 deneyim puanı — Seviye 3 (Uzman)"`. Keep it simple text/badge styling, consistent with the existing Tailwind components — no new page needed yet.

5. **Minimal profile glance**

   On `/my-history` (from Step 08), add the student's current `total_xp` and level name at the top of the page, above the attempt list.

## Acceptance criteria

- Completing a quiz with N correct answers increases `Student.total_xp` by exactly `N * 10`.
- The results reveal shows the XP earned this attempt and the student's new total + level name.
- `calculate_level(0)` returns `(1, "Çaylak")`; `calculate_level(500)` returns `(5, "Efsane")`; values between thresholds round down to the lower level.
- `/my-history` shows the current level and total XP, updating correctly after each new attempt.
