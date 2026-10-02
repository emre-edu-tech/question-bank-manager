# Step 6 — Admin: Quiz Builder

**Goal:** the admin assembles named, publishable quizzes by hand-picking and ordering questions from the bank built in Step 5.

## Tasks

1. **Quiz list** (`/admin/quizzes`)
   - Table of existing quizzes: title, slug, question count, a copy-able public link (`/quizzes/<slug>`), edit/delete actions.

2. **Slug generation**
   - On create, auto-generate a slug from the title (lowercase, ASCII-transliterated, hyphenated — handle Turkish characters sensibly, e.g. "ı"→"i", "ş"→"s", "ğ"→"g", "ü"→"u", "ö"→"o", "ç"→"c").
   - Let the admin override the slug in the form if they want a specific one.
   - On collision, append `-2`, `-3`, etc. until unique.

3. **Quiz builder form** (add/edit)
   - Title input (required), slug input (pre-filled from title, editable).
   - A two-pane picker:
     - Left: all questions in the bank, searchable/filterable by topic, each with a checkbox to add it to the quiz.
     - Right: the questions currently selected for this quiz, in order, each with simple **up/down buttons** to reorder (skip drag-and-drop — up/down arrows are enough and far less to get wrong with vanilla JS).
   - Require at least one question selected before allowing save.

4. **Save logic**
   - On create: insert the `Quiz` row, then insert `QuizQuestion` rows for each selected question with the correct `order` value.
   - On edit: reconcile the selected set against existing `QuizQuestion` rows — delete removed ones, insert newly added ones, update `order` for everything to match the current arrangement.

5. **Delete quiz**
   - Confirm, then delete the `Quiz` row and its `QuizQuestion` rows. Underlying `Question`/`Topic` rows are untouched.

6. **Public link visibility**
   - On the quiz list and edit page, show the full public URL prominently with a "copy link" button (vanilla JS `navigator.clipboard.writeText`), since this is what the admin will actually hand to students.

## Acceptance criteria

- Admin can create a new quiz, pick a subset of questions from different topics, reorder them, and save.
- The quiz is immediately visible and correctly ordered at its public URL.
- Editing a quiz to remove one question and add another correctly updates what's live, without leaving orphaned `QuizQuestion` rows.
- Deleting a quiz removes it from `/quizzes` and its old URL now 404s, while its questions remain in the bank untouched.
