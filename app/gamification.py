XP_PER_CORRECT_ANSWER = 10

LEVEL_THRESHOLDS = [
    (0, 1, "Çaylak"),
    (50, 2, "Kaşif"),
    (150, 3, "Uzman"),
    (300, 4, "Usta"),
    (500, 5, "Efsane"),
]


def calculate_level(total_xp: int):
    """Returns (level_number, level_name) for a given XP total."""
    current = LEVEL_THRESHOLDS[0]
    for threshold_xp, level_number, level_name in LEVEL_THRESHOLDS:
        if total_xp >= threshold_xp:
            current = (threshold_xp, level_number, level_name)
    return current[1], current[2]
