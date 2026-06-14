from __future__ import annotations

LEVELS = [
    (1, "Beginner", 0),
    (2, "Consistent", 50),
    (3, "SAT Grinder", 150),
    (4, "700 Hunter", 300),
    (5, "Road to 800", 600),
    (6, "Final Boss", 1000),
]


def level_for_total(total_solved: int) -> tuple[int, str, int]:
    current = LEVELS[0]
    for level in LEVELS:
        if total_solved >= level[2]:
            current = level
        else:
            break
    return current


def next_level_for_total(total_solved: int) -> tuple[int, str, int] | None:
    for level in LEVELS:
        if total_solved < level[2]:
            return level
    return None


def format_level(total_solved: int) -> str:
    lvl, name, threshold = level_for_total(total_solved)
    next_level = next_level_for_total(total_solved)
    if next_level:
        need = next_level[2] - total_solved
        return f"Level {lvl}: {name} ({need} problems to {next_level[1]})"
    return f"Level {lvl}: {name}"


def level_up_message(previous_total: int, new_total: int) -> str | None:
    old_level = level_for_total(previous_total)
    new_level = level_for_total(new_total)
    if new_level[0] > old_level[0]:
        return (
            f"Level up! 🚀\n"
            f"You reached <b>Level {new_level[0]}: {new_level[1]}</b>.\n"
            f"Keep the road moving toward 800."
        )
    return None
