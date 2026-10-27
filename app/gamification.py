from app.extensions import db
from app.models import Badge, QuizAttempt, StudentBadge

XP_PER_CORRECT_ANSWER = 10
STARTING_LIVES = 3

LEVEL_THRESHOLDS = [
    (0, 1, "Çaylak"),
    (50, 2, "Kaşif"),
    (150, 3, "Uzman"),
    (300, 4, "Usta"),
    (500, 5, "Efsane"),
]


def calculate_speed_bonus(time_taken_seconds: float) -> int:
    if time_taken_seconds <= 10:
        return 5
    elif time_taken_seconds <= 20:
        return 2
    return 0


def calculate_level(total_xp: int):
    """Returns (level_number, level_name) for a given XP total."""
    current = LEVEL_THRESHOLDS[0]
    for threshold_xp, level_number, level_name in LEVEL_THRESHOLDS:
        if total_xp >= threshold_xp:
            current = (threshold_xp, level_number, level_name)
    return current[1], current[2]


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

    completed_attempts = QuizAttempt.query.filter_by(
        student_id=student.id, completed=True
    ).count()

    if completed_attempts >= 1:
        award('ilk-adim')
    if attempt.score == attempt.total_questions:
        award('mukemmel-skor')
    speed_bonus_count = sum(
        1 for a in attempt.answers if a.xp_awarded > XP_PER_CORRECT_ANSWER
    )
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
