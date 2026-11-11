# Step 14 — Question Explanations & Answer Review

**Context:** builds on `13-leaderboard.md`. Extends the `Question` model, the admin question form (`05`), and the per-question flow (`/answer`, `/finish` from `10`–`11`). First step of the "improvement scope v2" batch (14–17) whose theme is **strengthening the educational side**.

**Goal:** after a question is graded, the student sees *why* the correct answer is correct, and can review all of their answers at the end of a quiz. Correct answers still only appear **after** grading — the existing design rule is untouched.

## Tasks

1. **Model change** — one nullable column on `Question` in `app/models.py`:

   ```python
   explanation = db.Column(db.Text, nullable=True)  # shown after grading
   ```

   `flask db migrate -m "add question explanation"` then `flask db upgrade`. Explanations are **optional** — existing questions stay valid with `NULL`.

2. **Admin form** (extend `app/admin/routes.py` + `app/templates/admin/question_form.html`)

   - Add an optional textarea `explanation` below the correct-choice selector, label *"Doğru cevabın açıklaması (isteğe bağlı)"*, placeholder suggesting a short "çünkü …" sentence.
   - Extend `_validate_question_form` to carry `explanation` into the returned `values` dict (no validation — it is optional; empty string means `NULL`).
   - In `question_new` and `question_edit`, set `question.explanation = values["explanation"].strip() or None`.
   - Keep the rest of the form flow (image handling, errors, redirects) exactly as is.

3. **Reveal the explanation in the per-question flow** (extend `POST /quizzes/<slug>/answer` in `app/public/routes.py`)

   Add to the JSON response:

   ```python
   "explanation": question.explanation,  # null when the question has none
   ```

   Grading logic does not change.

4. **Review payload in the finish summary** (extend `POST /quizzes/<slug>/finish`)

   Add `"review"` to the response — one entry per answered question, in answer order:

   ```python
   answers = (
       QuizAttemptAnswer.query.filter_by(attempt_id=attempt.id)
       .order_by(QuizAttemptAnswer.id)
       .all()
   )
   "review": [
       {
           "question_id": a.question_id,
           "question_text": a.question.text,
           "selected_choice": a.selected_choice,   # may be null (game over)
           "correct_choice": a.question.correct_choice,
           "is_correct": a.is_correct,
           "explanation": a.question.explanation,
       }
       for a in answers
   ]
   ```

5. **Frontend — inline explanation** (extend `app/static/js/quiz.js` and the quiz page template)

   - In `answerCard`'s success handler, if `data.explanation` is non-empty, render an explanation panel directly under the `.answer-feedback` box of the answered card:
     `"💡 Açıklama: " + data.explanation`.
   - Styling: a full-width box, e.g. `bg-blue-50 border border-blue-200 text-blue-900 rounded-lg p-3 mt-2 text-sm`. Add every new literal Tailwind class to the comment block at the top of `quiz.js` so the content scanner picks them up.
   - ⚠️ Per `AGENTS.md`: run `npm run build:css` and include the rebuilt `app/static/dist/output.css` in this change.

6. **Frontend — end-of-quiz review section**

   - In the quiz page template, add a hidden `<div id="answer-review" class="hidden">` below the score banner, titled *"Cevaplarını gözden geçir"*.
   - In `showSummary(data)`, render one compact row per review entry: result icon (✅/❌/⏳ for unanswered), question text, your choice letter vs. the correct letter (e.g. *"Senin cevabın: C — Doğru cevap: B"*), and the explanation if present.
   - Highlight the rows of **wrong** answers (e.g. red left border) — the point of the section is learning from mistakes, but still list all questions in order for context.

7. **Seed data** (optional but recommended): update the `flask seed-db` questions (or add a small `flask seed-explanations` command) so the seeded questions carry short Turkish explanations. This makes the feature demoable without hand-editing questions first.

8. **Update `docs/specs/00-overview.md`**: add step 14 to the build order and mention the `Question.explanation` column in the schema section.

## Acceptance criteria

- The admin question form accepts (and re-displays) an optional explanation; saving with an empty explanation stores `NULL`, not `""`.
- Answering a question with an explanation shows the explanation panel immediately after grading; a question without one shows nothing extra.
- The `/answer` response contains `explanation`; the quiz page HTML still never contains `correct_choice` or explanations **before** an answer is submitted (verify in page source).
- After finishing a quiz, the summary shows the review list with per-question result, chosen vs. correct letter, and explanations.
- A game-over attempt (some questions unanswered) renders `⏳` rows for unanswered questions and never leaks their answers as "chosen".
- `npm run build:css` was run; the committed `output.css` includes the new classes.
