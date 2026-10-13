# Step 10 — Lives & Limited Attempts

**Context:** builds on `09-xp-and-levels.md`. This step **replaces the bulk `POST /quizzes/<slug>/submit` endpoint** built in Step 03 and extended in Steps 08–09, along with its all-at-once client JS, with a per-question flow. Read those three files first so you know exactly what you're removing.

**Goal:** students get 3 lives per quiz attempt. A wrong answer costs a life, with immediate feedback — no more waiting until the end to find out. Running out of lives ends the attempt early ("Oyun Bitti").

## Why the architecture changes here

Lives only makes sense with immediate per-question feedback. That requires grading each question the moment it's answered, not in one batch at the end. This also happens to be the right foundation for Speed Bonus (Step 11), which needs per-question timing — so this step does the heavier lifting once, and Step 11 just extends it.

## Tasks

1. **Model addition**

   ```python
   # QuizAttempt — add:
   lives_remaining = db.Column(db.Integer, nullable=True)
   ```

   `flask db migrate -m "add lives tracking"` then `flask db upgrade`.
   Add a constant in `app/gamification.py`: `STARTING_LIVES = 3`.

2. **Remove the old bulk submit route**

   Delete the `POST /quizzes/<slug>/submit` view entirely (from Step 03/08/09). Its XP-awarding logic (`XP_PER_CORRECT_ANSWER`, updating `student.total_xp`) gets carried forward into the new `/answer` route below — don't lose it.

3. **Start-attempt route**

   ```python
   @public_bp.route('/quizzes/<slug>/start', methods=['POST'])
   @student_required
   def start_attempt(slug):
       quiz = Quiz.query.filter_by(slug=slug).first_or_404()
       attempt = QuizAttempt(
           student_id=session['student_id'],
           quiz_id=quiz.id,
           total_questions=len(quiz.quiz_questions),
           lives_remaining=STARTING_LIVES,
           completed=False,
       )
       db.session.add(attempt)
       db.session.commit()
       return jsonify({"attempt_id": attempt.id, "lives_remaining": attempt.lives_remaining})
   ```

4. **Per-question answer route**

   ```python
   @public_bp.route('/quizzes/<slug>/answer', methods=['POST'])
   @student_required
   def answer_question(slug):
       data = request.get_json()
       attempt = QuizAttempt.query.get_or_404(data['attempt_id'])

       if attempt.student_id != session['student_id'] or attempt.completed:
           return jsonify({"error": "invalid attempt"}), 400

       question = Question.query.get_or_404(data['question_id'])
       selected = data.get('selected_choice')
       is_correct = (selected == question.correct_choice)

       xp_awarded = XP_PER_CORRECT_ANSWER if is_correct else 0

       answer = QuizAttemptAnswer(
           attempt_id=attempt.id,
           question_id=question.id,
           selected_choice=selected,
           is_correct=is_correct,
           xp_awarded=xp_awarded,
       )
       db.session.add(answer)

       if is_correct:
           attempt.score += 1
           attempt.xp_earned += xp_awarded
       else:
           attempt.lives_remaining -= 1

       game_over = attempt.lives_remaining <= 0
       if game_over:
           attempt.completed = True
           attempt.completed_at = datetime.utcnow()

       db.session.commit()

       return jsonify({
           "is_correct": is_correct,
           "correct_choice": question.correct_choice,
           "lives_remaining": attempt.lives_remaining,
           "xp_awarded": xp_awarded,
           "game_over": game_over,
       })
   ```

5. **Finish route**

   ```python
   @public_bp.route('/quizzes/<slug>/finish', methods=['POST'])
   @student_required
   def finish_attempt(slug):
       data = request.get_json()
       attempt = QuizAttempt.query.get_or_404(data['attempt_id'])

       if attempt.student_id != session['student_id']:
           return jsonify({"error": "invalid attempt"}), 400

       if not attempt.completed:
           attempt.completed = True
           attempt.completed_at = datetime.utcnow()

       student = Student.query.get(session['student_id'])
       student.total_xp += attempt.xp_earned
       db.session.commit()

       level_number, level_name = calculate_level(student.total_xp)
       return jsonify({
           "score": attempt.score,
           "total": attempt.total_questions,
           "xp_earned": attempt.xp_earned,
           "total_xp": student.total_xp,
           "level_number": level_number,
           "level_name": level_name,
           "lives_remaining": attempt.lives_remaining,
       })
   ```

   Note: `student.total_xp` is only updated here (once, at finish), not inside `/answer` — this avoids double-counting if a student's browser retries a request.

6. **Quiz-taking template & JS rewrite** (`app/templates/public/quiz_take.html` + its JS, from Step 03)

   - Add a lives display at the top: 3 heart icons (e.g. `❤️❤️❤️`), updated live as lives are lost.
   - On page load, JS calls `POST /quizzes/<slug>/start`, stores the returned `attempt_id`.
   - Each question's choice buttons, on click:
     - Disable that question's inputs immediately (prevent double-answer).
     - `POST /quizzes/<slug>/answer` with `{attempt_id, question_id, selected_choice}`.
     - On response: highlight the student's choice green/red, and if wrong, also highlight the correct one. Update the hearts display.
     - If `game_over: true` in the response: disable all remaining unanswered questions, show a "Oyun Bitti!" banner, and call `/finish` automatically.
     - If this was the last question and not game over: call `/finish` automatically.
   - Replace the old single "Submit" button entirely — there's no more bulk submit, answering the last question (or losing all lives) triggers finishing automatically.
   - After `/finish` resolves, show the final summary banner (score, XP earned, level) in place of the old bulk-reveal banner from Step 03.

## Acceptance criteria

- Starting a quiz creates a `QuizAttempt` with `lives_remaining = 3`.
- Answering a question immediately shows correct/incorrect feedback for that question only (not the others).
- Three wrong answers in a row ends the attempt early, shows "Oyun Bitti", and locks the remaining questions.
- Completing all questions without running out of lives shows the normal summary (score, XP, level) via `/finish`.
- The old bulk `/submit` endpoint no longer exists; nothing in the codebase still references it.
- `Student.total_xp` increases by exactly the sum of `xp_awarded` across that attempt's correct answers, exactly once per attempt (not duplicated if `/finish` is somehow called twice — guard against this if testing reveals it's an issue).
