# Step 5 — Admin: Topics & Questions

**Goal:** the admin can fully manage the question bank — Topics and Questions, including image upload — all behind the login gate from Step 4.

## Tasks

1. **Dashboard nav**
   - Update the `/admin` dashboard with links to Topics, Questions, and Quizzes (Quizzes gets built in Step 6 — link it now, build it next).

2. **Topics CRUD** (`/admin/topics`)
   - List all topics with question counts.
   - Add form: name only.
   - Edit: rename.
   - Delete: if the topic has any questions, block deletion and show a message like "Reassign or delete its questions first" — don't cascade-delete questions silently.

3. **Questions CRUD** (`/admin/questions`)
   - List: table of questions (truncated text, topic name, has-image indicator), filterable by topic via a dropdown, with edit/delete actions.
   - Add/Edit form:
     - Topic (select, required)
     - Question text (textarea, required)
     - Four choice text inputs (`choice_a`–`choice_d`, all required)
     - Correct-answer selector: instead of picking a bare letter, let the admin click/select which of the four typed choices is correct (label it dynamically, e.g. radio buttons next to each choice input) — store the corresponding letter in `correct_choice`.
     - Optional image upload (file input). Accept `.png`, `.jpg`, `.jpeg`, `.webp` only; reject others with a clear error. Cap file size (e.g. 2MB) and reject oversized files with a clear error.
     - On upload: generate a unique filename (e.g. `uuid4().hex` + original extension via `secure_filename`), save to `app/static/uploads/questions/`, store the relative path in `image_path`.
     - On edit: if a new image is uploaded, delete the old file from disk before saving the new path. Support removing an existing image entirely (checkbox "remove image").
   - Delete: confirm (a plain JS `confirm()` dialog is enough), then delete the row. If the question is used in any `QuizQuestion`, also remove those linking rows so quizzes don't break (note in the confirm message that it will be removed from any quizzes using it).

4. **Validation & feedback**
   - Server-side validation for all required fields; on error, re-render the form with entered values preserved and inline error messages (don't just flash a generic "error" and lose the form data).
   - Flash a success message on create/update/delete, styled consistently with a small Tailwind alert component.

## Acceptance criteria

- Admin can create a topic, then a question under it with all four choices, a marked correct answer, and an uploaded image.
- Editing that question to swap the image deletes the old file and saves the new one.
- Attempting to delete a topic that still has questions is blocked with a clear message.
- Deleting a question that's part of a quiz removes it from that quiz without error.
- All forms preserve entered data and show field-level errors on validation failure.
