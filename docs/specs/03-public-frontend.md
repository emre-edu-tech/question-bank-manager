# Step 3 — Public Frontend, Quiz-Taking & Grading

**Goal:** the entire student-facing experience, built and testable against the seeded data from Step 2 — no admin panel exists yet, and none is needed for this step.

This step includes grading. Grading is part of the quiz-taking experience, not a separate later task — build it here.

## Tasks

1. **Landing page** (`GET /`, `app/public/routes.py`)
    - Simple, appealing hero section: BilişimTest wordmark, a short description of the app, a clear call-to-action button linking to `/quizzes`.
   - Fully responsive; this is the page a student sees first, so it should look intentional, not like a placeholder.

2. **Quiz listing** (`GET /quizzes`)
   - Query all `Quiz` rows, render each as a card (title, link to `/quizzes/<slug>`).
   - Empty state: if there are no quizzes yet, show a friendly "no quizzes published yet" message instead of a blank page.

3. **Quiz-taking page** (`GET /quizzes/<slug>`)
   - Look up the `Quiz` by slug; 404 (styled, not Flask's default) if not found.
   - Render the quiz title and its questions **in `QuizQuestion.order`**, each with:
     - question text
     - the question image if `image_path` is set (skip the `<img>` tag entirely if it's null — no broken image icons)
     - the four choices as clickable, styled cards/buttons acting as a radio group (not raw unstyled `<input type="radio">` elements) — this needs to feel good for a 10–12 year old to use
   - A single "Submit" button at the bottom.
   - **Critical constraint:** nothing in this page's rendered HTML, inline JSON, or linked JS may reveal `correct_choice` for any question. View-source must not leak answers.

4. **Client-side JS** (`app/static/js/quiz.js` or similar, vanilla JS only)
   - On submit: collect selected choices into `{ "<question_id>": "A" | "B" | "C" | "D", ... }` for every question (validate all are answered client-side before allowing submit — highlight any unanswered ones).
   - `fetch(POST, /quizzes/<slug>/submit)` with that payload as JSON. Show a loading state while waiting.
   - Prevent double submission (disable the button after first click).

5. **Grading endpoint** (`POST /quizzes/<slug>/submit`)
   - Look up the quiz and its questions server-side.
   - Compare each submitted answer against that question's `correct_choice`.
   - Return JSON:
     ```json
     {
       "score": 4,
       "total": 6,
       "results": [
         {"question_id": 12, "selected": "B", "correct_choice": "A", "is_correct": false},
         ...
       ]
     }
     ```
   - If the payload is missing an answer for a question, treat it as incorrect (don't error out).

6. **Results reveal** (client JS, using the response above)
   - Show a prominent score banner (e.g. "4 / 6 doğru").
   - For each question, mark the student's selected choice green (correct) or red (incorrect); if incorrect, also highlight the actual correct choice.
   - Disable further interaction with the quiz's radio group after submission.

7. **Styling**
   - Tailwind components for question cards and choice buttons — favor larger touch targets and clear color feedback over dense text, given the age group.

## Acceptance criteria

- `/quizzes` lists the seeded "Örnek Quiz".
- Taking that quiz, answering all questions, and submitting shows the correct score and a correct per-question right/wrong reveal, including for the question with an image.
- Viewing page source of `/quizzes/ornek-quiz` before submitting contains no `correct_choice` values anywhere.
- Visiting a nonexistent slug shows a styled 404, not a stack trace.
- Trying to submit with unanswered questions is blocked client-side with a clear indicator of what's missing.
