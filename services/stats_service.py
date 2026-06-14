from __future__ import annotations

from collections import Counter
from datetime import date, timedelta

from services.level_service import get_level
from services.progress_service import (
    date_to_str,
    day_range_ending,
    get_entries_between,
    get_scores_in_period,
    get_total_solved,
    parse_date,
    today_for_user,
    validate_period,
)


def status_for_day(entry: dict | None, day: date, today: date, goal: int) -> dict:
    if entry is None:
        if day < today:
            return {"emoji": "❌", "name": "Missed", "key": "missed"}
        return {"emoji": "⭕", "name": "No data", "key": "no_data"}

    solved = int(entry.get("solved_problems") or 0)
    first_try = int(entry.get("first_try") or 0)

    if solved <= 0:
        if day < today:
            return {"emoji": "❌", "name": "Missed", "key": "missed"}
        return {"emoji": "⭕", "name": "No data", "key": "no_data"}

    if solved < goal:
        return {"emoji": "🟡", "name": "In progress", "key": "partial"}

    first_try_rate = first_try / solved if solved else 0
    if first_try_rate >= 0.8:
        return {"emoji": "⭐", "name": "High quality", "key": "high_quality"}

    if solved >= 1.5 * goal:
        return {"emoji": "🔥", "name": "Overachieved", "key": "overachieved"}

    return {"emoji": "✅", "name": "Completed", "key": "completed"}


def is_completed_status(status_key: str) -> bool:
    return status_key in {"completed", "overachieved", "high_quality"}


def period_entries(user: dict, days: int) -> list[dict]:
    validate_period(days)
    days_list = day_range_ending(user, days)
    start = date_to_str(days_list[0])
    end = date_to_str(days_list[-1])
    db_entries = get_entries_between(user["user_id"], start, end)
    by_date = {entry["date"]: entry for entry in db_entries}
    today = today_for_user(user)
    result = []
    for day in days_list:
        entry = by_date.get(date_to_str(day))
        status = status_for_day(entry, day, today, int(user["daily_goal"]))
        result.append(
            {
                "date": day,
                "date_str": date_to_str(day),
                "entry": entry,
                "status": status,
                "solved": int((entry or {}).get("solved_problems") or 0),
                "first_try": int((entry or {}).get("first_try") or 0),
                "after_explanation": int((entry or {}).get("after_explanation") or 0),
                "topic": (entry or {}).get("topic_of_day"),
                "sat_score": (entry or {}).get("sat_score"),
            }
        )
    return result


def current_streak(user: dict) -> int:
    today = today_for_user(user)
    lookback_days = 3650
    entries = get_entries_between(
        user["user_id"],
        date_to_str(today - timedelta(days=lookback_days)),
        date_to_str(today),
    )
    by_date = {entry["date"]: entry for entry in entries}
    streak = 0
    goal = int(user["daily_goal"])
    for offset in range(0, lookback_days + 1):
        day = today - timedelta(days=offset)
        status = status_for_day(by_date.get(date_to_str(day)), day, today, goal)
        if is_completed_status(status["key"]):
            streak += 1
        else:
            break
    return streak


def best_streak_for_entries(rows: list[dict]) -> int:
    best = 0
    current = 0
    for row in rows:
        if is_completed_status(row["status"]["key"]):
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def stats_for_period(user: dict, days: int) -> dict:
    rows = period_entries(user, days)
    solved_total = sum(row["solved"] for row in rows)
    first_total = sum(row["first_try"] for row in rows)
    after_total = sum(row["after_explanation"] for row in rows)
    completed_days = sum(1 for row in rows if is_completed_status(row["status"]["key"]))
    missed_days = sum(1 for row in rows if row["status"]["key"] == "missed")
    topics = [row["topic"] for row in rows if row["topic"]]
    most_common_topic = Counter(topics).most_common(1)[0][0] if topics else "—"

    scores = get_scores_in_period(user["user_id"], rows[0]["date_str"], rows[-1]["date_str"])
    latest_score = scores[-1]["score"] if scores else None
    highest_score = max([score["score"] for score in scores], default=None)
    score_improvement = None
    if len(scores) >= 2:
        score_improvement = int(scores[-1]["score"]) - int(scores[0]["score"])

    first_try_rate = first_total / solved_total if solved_total else 0
    after_rate = after_total / solved_total if solved_total else 0

    return {
        "days": days,
        "rows": rows,
        "total_solved": solved_total,
        "average_per_day": solved_total / days,
        "completed_days": completed_days,
        "missed_days": missed_days,
        "current_streak": current_streak(user),
        "best_streak": best_streak_for_entries(rows),
        "first_try_rate": first_try_rate,
        "after_explanation_rate": after_rate,
        "most_common_topic": most_common_topic,
        "latest_score": latest_score,
        "highest_score": highest_score,
        "score_improvement": score_improvement,
        "total_all_time": get_total_solved(user["user_id"]),
        "level": get_level(get_total_solved(user["user_id"])),
    }


def format_progress_bar(solved: int, goal: int, blocks: int = 10) -> str:
    if goal <= 0:
        percent = 0
    else:
        percent = min(solved / goal, 1)
    filled = round(percent * blocks)
    return "█" * filled + "░" * (blocks - filled)


def format_today(user: dict, entry: dict) -> str:
    today = today_for_user(user)
    status = status_for_day(entry, today, today, int(user["daily_goal"]))
    solved = int(entry.get("solved_problems") or 0)
    goal = int(user["daily_goal"])
    percent = int(min(solved / goal, 1) * 100) if goal else 0
    topic = entry.get("topic_of_day") or "—"
    score = entry.get("sat_score") or "—"
    return (
        f"Today — {today.strftime('%d %B')}\n\n"
        f"Goal: {goal} problems\n"
        f"Solved: {solved}/{goal}\n"
        f"First try: {entry.get('first_try') or 0}\n"
        f"After explanation: {entry.get('after_explanation') or 0}\n"
        f"Topic: {topic}\n"
        f"SAT Math score: {score}\n\n"
        f"Progress:\n"
        f"{format_progress_bar(solved, goal)} {percent}%\n\n"
        f"Status: {status['name']} {status['emoji']}"
    )


def format_stats(user: dict, stats: dict) -> str:
    latest = stats["latest_score"] if stats["latest_score"] is not None else "—"
    highest = stats["highest_score"] if stats["highest_score"] is not None else "—"
    improvement = stats["score_improvement"]
    improvement_text = "—" if improvement is None else f"{improvement:+d}"
    return (
        f"Stats — last {stats['days']} days\n\n"
        f"Total solved: {stats['total_solved']} problems\n"
        f"Average/day: {stats['average_per_day']:.1f}\n"
        f"Completed days: {stats['completed_days']}\n"
        f"Missed days: {stats['missed_days']}\n"
        f"Current streak: {stats['current_streak']} days\n"
        f"Best streak: {stats['best_streak']} days\n\n"
        f"First try rate: {stats['first_try_rate']:.0%}\n"
        f"After explanation rate: {stats['after_explanation_rate']:.0%}\n"
        f"Most common topic: {stats['most_common_topic']}\n\n"
        f"Latest SAT Math score: {latest}\n"
        f"Highest SAT Math score: {highest}\n"
        f"Score improvement: {improvement_text}\n\n"
        f"Level: {stats['level']['name']}"
    )


def road_for_period(user: dict, days: int = 14) -> dict:
    rows = period_entries(user, days)
    total = get_total_solved(user["user_id"])
    level = get_level(total)
    return {
        "path": " → ".join(row["status"]["emoji"] for row in rows),
        "current_streak": current_streak(user),
        "total_solved": total,
        "level": level,
        "rows": rows,
    }


def format_road(user: dict, days: int = 14) -> str:
    road = road_for_period(user, days)
    next_level = road["level"].get("next")
    next_text = "Max level reached" if not next_level else f"{next_level['remaining']} problems to {next_level['name']}"
    return (
        "SAT Road to 800\n\n"
        f"{road['path']}\n\n"
        f"Current streak: {road['current_streak']} days\n"
        f"Total solved: {road['total_solved']} problems\n"
        f"Level: {road['level']['name']}\n"
        f"Next: {next_text}"
    )
