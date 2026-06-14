from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from typing import Any

from database import Database

TOPICS = ["Algebra", "Geometry", "Functions", "Data Analysis", "Mixed", "Other"]


@dataclass(slots=True)
class Status:
    key: str
    emoji: str
    label: str


STATUSES = {
    "no_data": Status("no_data", "⭕", "No data"),
    "partial": Status("partial", "🟡", "In progress"),
    "completed": Status("completed", "✅", "Completed"),
    "overachieved": Status("overachieved", "🔥", "Overachieved"),
    "high_quality": Status("high_quality", "⭐", "High quality"),
    "missed": Status("missed", "❌", "Missed"),
}

COMPLETED_KEYS = {"completed", "overachieved", "high_quality"}


def safe_zoneinfo(tz_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def today_in_timezone(tz_name: str) -> date:
    return datetime.now(safe_zoneinfo(tz_name)).date()


def date_range(end: date, days: int) -> list[date]:
    start = end - timedelta(days=days - 1)
    return [start + timedelta(days=i) for i in range(days)]


def validate_entry_values(solved: int, first_try: int, after_explanation: int) -> None:
    if solved < 0:
        raise ValueError("Solved problems cannot be negative.")
    if first_try < 0:
        raise ValueError("First try cannot be negative.")
    if after_explanation < 0:
        raise ValueError("After explanation cannot be negative.")
    if first_try + after_explanation > solved:
        raise ValueError("First try + after explanation cannot exceed solved problems.")


def status_for_entry(entry: dict[str, Any] | None, goal: int, day: date, today: date) -> Status:
    if entry is None or int(entry.get("solved_problems") or 0) == 0:
        if day < today:
            return STATUSES["missed"]
        return STATUSES["no_data"]

    solved = int(entry.get("solved_problems") or 0)
    first = int(entry.get("first_try") or 0)

    if solved < goal:
        return STATUSES["partial"]

    first_try_rate = first / solved if solved else 0
    if first_try_rate >= 0.8:
        return STATUSES["high_quality"]
    if solved >= goal * 1.5:
        return STATUSES["overachieved"]
    return STATUSES["completed"]


def progress_bar(solved: int, goal: int, width: int = 10) -> str:
    if goal <= 0:
        goal = 1
    ratio = min(1.0, solved / goal)
    filled = round(ratio * width)
    return "█" * filled + "░" * (width - filled)


async def get_or_create_today_entry(db: Database, user: dict[str, Any]) -> dict[str, Any]:
    day = today_in_timezone(user["timezone"]).isoformat()
    entry = await db.get_entry(user["user_id"], day)
    if entry is None:
        entry = await db.upsert_entry(user["user_id"], day)
    return entry


async def set_today_entry(
    db: Database,
    user: dict[str, Any],
    solved_problems: int | None = None,
    first_try: int | None = None,
    after_explanation: int | None = None,
    topic_of_day: str | None = None,
    sat_score: int | None = None,
) -> dict[str, Any]:
    day = today_in_timezone(user["timezone"]).isoformat()
    old = await db.get_entry(user["user_id"], day)
    solved = old["solved_problems"] if old and solved_problems is None else (solved_problems or 0)
    first = old["first_try"] if old and first_try is None else (first_try or 0)
    after = old["after_explanation"] if old and after_explanation is None else (after_explanation or 0)
    validate_entry_values(int(solved), int(first), int(after))
    if sat_score is not None and not (200 <= int(sat_score) <= 800):
        raise ValueError("SAT Math score must be between 200 and 800.")
    return await db.upsert_entry(
        user_id=user["user_id"],
        date=day,
        solved_problems=int(solved) if solved_problems is not None else None,
        first_try=int(first) if first_try is not None else None,
        after_explanation=int(after) if after_explanation is not None else None,
        topic_of_day=topic_of_day,
        sat_score=int(sat_score) if sat_score is not None else None,
    )


async def apply_delta(db: Database, user: dict[str, Any], field: str, delta: int) -> dict[str, Any]:
    entry = await get_or_create_today_entry(db, user)
    solved = int(entry["solved_problems"] or 0)
    first = int(entry["first_try"] or 0)
    after = int(entry["after_explanation"] or 0)

    if field == "solved_problems":
        solved = max(0, solved + delta)
        if first + after > solved:
            overflow = first + after - solved
            reduce_after = min(after, overflow)
            after -= reduce_after
            overflow -= reduce_after
            if overflow:
                first = max(0, first - overflow)
    elif field == "first_try":
        first = max(0, first + delta)
        if first + after > solved:
            solved = first + after
    elif field == "after_explanation":
        after = max(0, after + delta)
        if first + after > solved:
            solved = first + after
    else:
        raise ValueError("Unsupported field")

    validate_entry_values(solved, first, after)
    return await db.upsert_entry(
        user["user_id"],
        entry["date"],
        solved_problems=solved,
        first_try=first,
        after_explanation=after,
    )


async def set_topic(db: Database, user: dict[str, Any], topic: str) -> dict[str, Any]:
    normalized = normalize_topic(topic)
    if normalized is None:
        raise ValueError("Unknown topic.")
    day = today_in_timezone(user["timezone"]).isoformat()
    return await db.upsert_entry(user["user_id"], day, topic_of_day=normalized)


def normalize_topic(topic: str | None) -> str | None:
    if not topic:
        return None
    raw = topic.strip().lower()
    mapping = {
        "algebra": "Algebra",
        "алгебра": "Algebra",
        "geometry": "Geometry",
        "геометрія": "Geometry",
        "геометрия": "Geometry",
        "functions": "Functions",
        "function": "Functions",
        "функції": "Functions",
        "функции": "Functions",
        "data": "Data Analysis",
        "data analysis": "Data Analysis",
        "statistics": "Data Analysis",
        "статистика": "Data Analysis",
        "аналіз даних": "Data Analysis",
        "анализ данных": "Data Analysis",
        "mixed": "Mixed",
        "мікс": "Mixed",
        "смешанное": "Mixed",
        "змішане": "Mixed",
        "other": "Other",
        "інше": "Other",
        "другое": "Other",
    }
    if raw in mapping:
        return mapping[raw]
    for key, value in mapping.items():
        if key in raw:
            return value
    return None


def format_date_human(iso_date: str) -> str:
    d = datetime.strptime(iso_date, "%Y-%m-%d").date()
    return d.strftime("%d %B").lstrip("0")


def format_today_message(entry: dict[str, Any], user: dict[str, Any]) -> str:
    goal = int(user["daily_goal"])
    solved = int(entry["solved_problems"] or 0)
    first = int(entry["first_try"] or 0)
    after = int(entry["after_explanation"] or 0)
    topic = entry.get("topic_of_day") or "—"
    score = entry.get("sat_score") or "—"
    today = today_in_timezone(user["timezone"])
    status = status_for_entry(entry, goal, datetime.strptime(entry["date"], "%Y-%m-%d").date(), today)
    pct = round(min(100, (solved / goal) * 100)) if goal else 0
    bar = progress_bar(solved, goal)

    return (
        f"<b>Today — {format_date_human(entry['date'])}</b>\n\n"
        f"Goal: <b>{goal}</b> problems\n"
        f"Solved: <b>{solved}/{goal}</b>\n"
        f"First try: <b>{first}</b>\n"
        f"After explanation: <b>{after}</b>\n"
        f"Topic: <b>{topic}</b>\n"
        f"SAT Math score: <b>{score}</b>\n\n"
        f"Progress:\n<code>{bar}</code> {pct}%\n\n"
        f"Status: <b>{status.label}</b> {status.emoji}"
    )


async def current_streak(db: Database, user: dict[str, Any]) -> int:
    today = today_in_timezone(user["timezone"])
    entries = await db.list_all_entries(user["user_id"])
    by_date = {e["date"]: e for e in entries}
    goal = int(user["daily_goal"])

    cursor = today
    if status_for_entry(by_date.get(cursor.isoformat()), goal, cursor, today).key not in COMPLETED_KEYS:
        cursor = today - timedelta(days=1)

    streak = 0
    while True:
        status = status_for_entry(by_date.get(cursor.isoformat()), goal, cursor, today)
        if status.key in COMPLETED_KEYS:
            streak += 1
            cursor -= timedelta(days=1)
        else:
            break
    return streak


async def best_streak(db: Database, user: dict[str, Any], start: date | None = None, end: date | None = None) -> int:
    today = today_in_timezone(user["timezone"])
    entries = await db.list_all_entries(user["user_id"])
    if not entries:
        return 0
    by_date = {e["date"]: e for e in entries}
    first_date = datetime.strptime(entries[0]["date"], "%Y-%m-%d").date()
    start = start or first_date
    end = end or today
    goal = int(user["daily_goal"])

    best = 0
    running = 0
    cursor = start
    while cursor <= end:
        st = status_for_entry(by_date.get(cursor.isoformat()), goal, cursor, today)
        if st.key in COMPLETED_KEYS:
            running += 1
            best = max(best, running)
        else:
            running = 0
        cursor += timedelta(days=1)
    return best


async def total_solved(db: Database, user_id: int) -> int:
    return sum(int(e["solved_problems"] or 0) for e in await db.list_all_entries(user_id))
