from __future__ import annotations

LEVELS = [
    (1, "Beginner", 0),
    (2, "Consistent", 50),
    (3, "SAT Grinder", 150),
    (4, "700 Hunter", 300),
    (5, "Road to 800", 600),
    (6, "Final Boss", 1000),
]


def get_level(total_solved: int) -> dict:
    current = LEVELS[0]
    for level in LEVELS:
        if total_solved >= level[2]:
            current = level
        else:
            break
    next_level = next((level for level in LEVELS if level[2] > total_solved), None)
    return {
        "number": current[0],
        "name": current[1],
        "threshold": current[2],
        "next": None if next_level is None else {
            "number": next_level[0],
            "name": next_level[1],
            "threshold": next_level[2],
            "remaining": next_level[2] - total_solved,
        },
    }


def level_up_message(old_total: int, new_total: int) -> str | None:
    old_level = get_level(old_total)
    new_level = get_level(new_total)
    if new_level["number"] > old_level["number"]:
        return (
            f"Level up! ⭐\n"
            f"You reached Level {new_level['number']}: {new_level['name']}.\n"
            f"Total solved: {new_total} problems. Keep the road moving."
        )
    return None
