# Step 12 — Badges & Achievements

**Context:** builds on `11-speed-bonus.md`. Extends `app/models.py` and the `POST /quizzes/<slug>/finish` route from Step 10. Badges are **admin-seeded, not admin-CRUD** — keep this one simple, no management UI.

**Goal:** students unlock badges for specific milestones, shown at the moment they're earned.

## Tasks

1. **Models**

   ```python
   class Badge(db.Model):
       id = db.Column(db.Integer, primary_key=True)
       code = db.Column(db.String(30), unique=True, nullable=False)
       name = db.Column(db.String(50), nullable=False)
       description = db.Column(db.String(200), nullable=False)

   class StudentBadge(db.Model):
       id = db.Column(db.Integer, primary_key=True)
       student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
       badge_id = db.Column(db.Integer, db.ForeignKey('badge.id'), nullable=False)
       earned_at = db.Column(db.DateTime, default=datetime.utcnow)

       student = db.relationship('Student', backref='student_badges')
       badge = db.relationship('Badge')

       __table_args__ = (db.UniqueConstraint('student_id', 'badge_id', name='uq_student_badge'),)
   ```

   `flask db migrate -m "add badges"` then `flask db upgrade`.

2. **Seed the badge list** (extend the `flask seed-db` command from Step 02, or add a new `flask seed-badges` command — guard against duplicates either way)

   | code | name | description |
   |---|---|---|
   | `ilk-adim` | İlk Adım | İlk quizini tamamladın |
   | `mukemmel-skor` | Mükemmel Skor | Bir quizde tüm soruları doğru bildin |
   | `hiz-ustasi` | Hız Ustası | Bir denemede 3 veya daha fazla hız bonusu kazandın |
   | `azimli` | Azimli | Toplam 5 quiz tamamladın |
   | `hayatta-kalan` | Hayatta Kalan | Hiç can kaybetmeden bir quizi bitirdin |
   | `seviye-5` | Seviye 5 | Efsane seviyesine ulaştın |

3. **Badge rule evaluation** (new function, e.g. in `app/gamification.py`)

   ```python
   def check_and_award_badges(student, attempt):
       """Checks all badge rules against the student's current state and
       awards any newly-earned badges. Returns the list of newly-awarded Badge objects."""
       newly_awarded = []
       already_earned_codes = {sb.badge.code for sb in student.student_badges}

       def award(code):
           if code in already_earned_codes:
               return
           badge = Badge.query.filter_by(code=code).first()
           if badge:
               db.session.add(StudentBadge(student_id=student.id, badge_id=badge.id))
               newly_awarded.append(badge)

       completed_attempts = QuizAttempt.query.filter_by(student_id=student.id, completed=True).count()

       if completed_attempts >= 1:
           award('ilk-adim')
       if attempt.score == attempt.total_questions:
           award('mukemmel-skor')
       speed_bonus_count = sum(1 for a in attempt.answers if a.xp_awarded > XP_PER_CORRECT_ANSWER)
       if speed_bonus_count >= 3:
           award('hiz-ustasi')
       if completed_attempts >= 5:
           award('azimli')
       if attempt.lives_remaining == STARTING_LIVES:
           award('hayatta-kalan')
       level_number, _ = calculate_level(student.total_xp)
       if level_number >= 5:
           award('seviye-5')

       return newly_awarded
   ```

4. **Wire into `/finish`** (extend the route from Step 10)

   Right before returning the JSON response in `finish_attempt`, call:
   ```python
   newly_awarded = check_and_award_badges(student, attempt)
   db.session.commit()
   ```
   Add `"new_badges": [{"code": b.code, "name": b.name, "description": b.description} for b in newly_awarded]` to the response JSON.

5. **Display newly-earned badges**

   On the finish summary screen (client JS), if `new_badges` is non-empty, show a small celebratory callout per badge: name + description. Keep it simple — a styled card per badge is enough, no animation required.

6. **Badge case page** (`GET /my-badges`, `@student_required`)

   Lists every `Badge` in the system, visually distinguishing ones the student has earned (name, description, earned date) from ones they haven't (greyed out, description only — don't hide unearned badges, showing what's still achievable is part of the motivation).

## Acceptance criteria

- Seeding runs cleanly and populates exactly the 6 badges above, with no duplicates on a second run.
- Completing a first-ever quiz awards `ilk-adim` and it appears in that attempt's `/finish` response.
- Scoring 100% on a quiz awards `mukemmel-skor`; finishing with all 3 lives intact awards `hayatta-kalan`.
- A badge is never awarded twice to the same student (verify by completing a qualifying action a second time — `new_badges` should be empty the second time).
- `/my-badges` correctly distinguishes earned vs. unearned badges for the current student.
