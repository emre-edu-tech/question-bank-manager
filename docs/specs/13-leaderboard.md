# Step 13 — Leaderboard

**Context:** builds on `12-badges-and-achievements.md`. Adds one new public, read-only page. Doesn't modify any existing route.

**Goal:** a public leaderboard ranking students by total XP, so progress is visible and a little competitive — the final piece that ties XP, levels, and badges together into something students actually check.

## Tasks

1. **Leaderboard route**

   ```python
   @public_bp.route('/leaderboard')
   def leaderboard():
       class_code = request.args.get('class_code', '').strip().upper() or None

       query = Student.query
       if class_code:
           query = query.filter_by(class_code=class_code)

       students = query.order_by(Student.total_xp.desc()).limit(50).all()

       rows = []
       for rank, student in enumerate(students, start=1):
           level_number, level_name = calculate_level(student.total_xp)
           badge_count = len(student.student_badges)
           rows.append({
               "rank": rank,
               "nickname": student.nickname,
               "class_code": student.class_code,
               "total_xp": student.total_xp,
               "level_name": level_name,
               "badge_count": badge_count,
           })

       return render_template('public/leaderboard.html', rows=rows, class_code_filter=class_code)
   ```

2. **Template** (`app/templates/public/leaderboard.html`)

   - A table or styled card list: rank, nickname, class code, level name, total XP, badge count.
   - Top 3 get a visual highlight (e.g. a small medal emoji 🥇🥈🥉 or a colored border) — a nice, cheap touch for a 11–14 audience.
   - A simple text input + "Filtrele" button at the top to filter by class code (submits `?class_code=...` via a plain GET form, no AJAX needed).
   - A "Tüm Sınıflar" (all classes) link to clear the filter.
   - Empty state: if no students match, show "Henüz kimse quiz çözmedi!" instead of an empty table.

3. **Link it from navigation**

   Add a "Liderlik Tablosu" link to the public site's header/nav (`base.html` or the public layout), next to the existing `/quizzes` link, so students can find it without knowing the URL.

4. **No personal data beyond nickname + class code**

   Confirm the leaderboard never displays anything beyond what's already in `Student` (nickname, class_code, derived level/XP/badge count) — no IP addresses, no timestamps of when they played, nothing else.

## Acceptance criteria

- `/leaderboard` shows all students ranked by `total_xp` descending, correctly reflecting the actual contents of the `Student` table.
- `/leaderboard?class_code=7A` shows only students in that class, still correctly ranked.
- The top 3 rows are visually distinguished from the rest.
- An unfiltered leaderboard with zero students shows the empty-state message, not a broken/empty table.
- The nav link to the leaderboard is visible from the quiz listing and landing pages.
