# Step 11 — Speed Bonus

**Context:** builds on `10-lives-and-limited-attempts.md`. Extends the `POST /quizzes/<slug>/answer` route and its client JS — does not touch `/start` or `/finish`.

**Goal:** answering correctly *and quickly* earns bonus XP on top of the base 10 XP from Step 09.

## Tasks

1. **Model addition**

   ```python
   # QuizAttemptAnswer — add:
   time_taken_seconds = db.Column(db.Float, nullable=True)
   ```

   `flask db migrate -m "add answer timing"` then `flask db upgrade`.

2. **Bonus tiers** (add to `app/gamification.py`)

   ```python
   def calculate_speed_bonus(time_taken_seconds: float) -> int:
       if time_taken_seconds <= 10:
           return 5
       elif time_taken_seconds <= 20:
           return 2
       return 0
   ```

3. **Client-side timing** (quiz-taking JS from Step 10)

   ```javascript
   const quizStartTime = Date.now();
   const firstInteractionMs = {};  // question_id -> ms since quiz start

   document.querySelectorAll('.question-card').forEach(card => {
     const questionId = card.dataset.questionId;
     card.querySelectorAll('input[type="radio"]').forEach(input => {
       input.addEventListener('change', () => {
         if (!(questionId in firstInteractionMs)) {
           firstInteractionMs[questionId] = Date.now() - quizStartTime;
         }
       });
     });
   });
   ```

   When calling `/answer`, compute this question's elapsed time as the difference between its `firstInteractionMs` entry and the previous question's (or `0` for the first question in order), convert to seconds, and include it in the payload:
   ```javascript
   { attempt_id, question_id, selected_choice, time_taken_seconds }
   ```
   Exact precision doesn't matter here — this is a classroom demo, not a timing-sensitive system. Approximate is fine.

4. **Award the bonus server-side** (in `answer_question`, from Step 10)

   ```python
   time_taken = data.get('time_taken_seconds')
   xp_awarded = 0
   speed_bonus = 0

   if is_correct:
       xp_awarded = XP_PER_CORRECT_ANSWER
       if time_taken is not None:
           speed_bonus = calculate_speed_bonus(time_taken)
           xp_awarded += speed_bonus

   answer = QuizAttemptAnswer(
       attempt_id=attempt.id,
       question_id=question.id,
       selected_choice=selected,
       is_correct=is_correct,
       time_taken_seconds=time_taken,
       xp_awarded=xp_awarded,
   )
   ```

   Include `speed_bonus` in the JSON response so the client can show it: `{"is_correct": true, "xp_awarded": 15, "speed_bonus": 5, ...}`.

5. **Display the bonus**

   When a question is answered correctly and quickly, show a small extra note alongside the existing green feedback, e.g. `"+10 XP (+5 hız bonusu!)"`. No bonus note when `speed_bonus` is 0.

## Acceptance criteria

- Answering correctly within 10 seconds of a question first being interacted with awards 15 XP total (10 base + 5 bonus); within 20 seconds awards 12 XP; slower or incorrect awards the Step 10 base behavior (10 or 0).
- The speed bonus is visibly shown on the question's immediate feedback when earned.
- `QuizAttemptAnswer.time_taken_seconds` is populated for every answered question (null only if the client failed to send it, which should not happen in normal use).
- Lives/game-over behavior from Step 10 is unaffected — speed bonus is purely additive to XP, never influences correctness or lives.
