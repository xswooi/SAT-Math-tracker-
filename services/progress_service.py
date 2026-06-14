from __future__ import annotations

from datetime import datetime, date, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from typing import Any

from config import (
    ALLOWED_TOPICS,
    DEFAULT_DAILY_GOAL,
    DEFAULT_LANGUAGE,
    DEFAULT_STATS_PERIOD,
    DEFAULT_TARGET_SCORE,
    DEFAULT_TIMEZONE,
    MIN_STATS_PERIOD,
)
from database import get_db


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def safe_zoneinfo(tz_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        return ZoneInfo(DEFAULT_TIMEZONE)


def today_for_user(user: dict) -> date:
    tz = safe_zoneinfo(user.get("timezone") or DEFAULT_TIMEZONE)
    return datetime.now(tz).date()


def date_to_str(d: date) -> str:
    return d.isoformat()


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def ensure_user(telegram_user: Any) -> dict:
    user_id = int(telegram_user.id)
    username = telegram_user.username
    now = utc_now_iso()
    with get_db() as db:
        existing = db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if existing:
            if existing.get("username") != username:
                db.execute("UPDATE users SET username = ? WHERE user_id = ?", (username, user_id))
                existing["username"] = username
            return existing
        db.execute(
            """
            INSERT INTO users(user_id, username, language, timezone, daily_goal, target_score, default_stats_period, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                username,
                DEFAULT_LANGUAGE,
                DEFAULT_TIMEZONE,
                DEFAULT_DAILY_GOAL,
                DEFAULT_TARGET_SCORE,
                DEFAULT_STATS_PERIOD,
                now,
            ),
        )
        return db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()


def get_user(user_id: int) -> dict | None:
    with get_db() as db:
        return db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()


def update_user_setting(user_id: int, field: str, value: Any) -> dict:
    allowed = {"language", "timezone", "daily_goal", "target_score", "default_stats_period"}
    if field not in allowed:
        raise ValueError("Unknown setting.")
    with get_db() as db:
        db.execute(f"UPDATE users SET {field} = ? WHERE user_id = ?", (value, user_id))
        return db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()


def validate_score(score: int) -> None:
    if not 200 <= score <= 800:
        raise ValueError("SAT Math score must be between 200 and 800.")


def validate_counts(solved: int, first_try: int, after_explanation: int) -> None:
    if solved < 0:
        raise ValueError("Solved problems cannot be negative.")
    if first_try < 0:
        raise ValueError("First try cannot be negative.")
    if after_explanation < 0:
        raise ValueError("After explanation cannot be negative.")
    if first_try + after_explanation > solved:
        raise ValueError("First try + after explanation cannot exceed solved problems.")


def get_entry(user_id: int, entry_date: str) -> dict | None:
    with get_db() as db:
        return db.execute(
            "SELECT * FROM daily_entries WHERE user_id = ? AND date = ?",
            (user_id, entry_date),
        ).fetchone()


def get_or_create_entry(user_id: int, entry_date: str) -> dict:
    now = utc_now_iso()
    with get_db() as db:
        entry = db.execute(
            "SELECT * FROM daily_entries WHERE user_id = ? AND date = ?",
            (user_id, entry_date),
        ).fetchone()
        if entry:
            return entry
        db.execute(
            """
            INSERT INTO daily_entries(user_id, date, solved_problems, first_try, after_explanation, topic_of_day, sat_score, created_at, updated_at)
            VALUES (?, ?, 0, 0, 0, NULL, NULL, ?, ?)
            """,
            (user_id, entry_date, now, now),
        )
        return db.execute(
            "SELECT * FROM daily_entries WHERE user_id = ? AND date = ?",
            (user_id, entry_date),
        ).fetchone()


def get_today_entry(user: dict) -> dict:
    return get_or_create_entry(user["user_id"], date_to_str(today_for_user(user)))


def upsert_entry(
    user_id: int,
    entry_date: str,
    solved_problems: int | None = None,
    first_try: int | None = None,
    after_explanation: int | None = None,
    topic_of_day: str | None = None,
    sat_score: int | None = None,
) -> dict:
    entry = get_or_create_entry(user_id, entry_date)
    solved = entry["solved_problems"] if solved_problems is None else int(solved_problems)
    first = entry["first_try"] if first_try is None else int(first_try)
    after = entry["after_explanation"] if after_explanation is None else int(after_explanation)

    if topic_of_day is not None and topic_of_day not in ALLOWED_TOPICS:
        raise ValueError(f"Topic must be one of: {', '.join(ALLOWED_TOPICS)}")
    if sat_score is not None:
        validate_score(int(sat_score))
    validate_counts(solved, first, after)

    now = utc_now_iso()
    with get_db() as db:
        db.execute(
            """
            UPDATE daily_entries
            SET solved_problems = ?, first_try = ?, after_explanation = ?,
                topic_of_day = COALESCE(?, topic_of_day),
                sat_score = COALESCE(?, sat_score),
                updated_at = ?
            WHERE user_id = ? AND date = ?
            """,
            (solved, first, after, topic_of_day, sat_score, now, user_id, entry_date),
        )
        return db.execute(
            "SELECT * FROM daily_entries WHERE user_id = ? AND date = ?",
            (user_id, entry_date),
        ).fetchone()


def update_entry_from_parsed(user: dict, parsed: dict) -> tuple[dict, str | None]:
    from services.level_service import level_up_message

    user_id = user["user_id"]
    entry_date = date_to_str(today_for_user(user))
    old_total = get_total_solved(user_id)

    score = parsed.get("sat_score")
    if score is not None:
        add_sat_score(user_id, entry_date, int(score), notes="Natural language input")

    entry = upsert_entry(
        user_id=user_id,
        entry_date=entry_date,
        solved_problems=parsed.get("solved_problems"),
        first_try=parsed.get("first_try"),
        after_explanation=parsed.get("after_explanation"),
        topic_of_day=parsed.get("topic_of_day"),
        sat_score=score,
    )

    new_total = get_total_solved(user_id)
    return entry, level_up_message(old_total, new_total)


def increment_today(user: dict, field: str, delta: int) -> tuple[dict, str | None]:
    from services.level_service import level_up_message

    if field not in {"solved_problems", "first_try", "after_explanation"}:
        raise ValueError("Unknown progress field.")
    entry_date = date_to_str(today_for_user(user))
    entry = get_or_create_entry(user["user_id"], entry_date)
    old_total = get_total_solved(user["user_id"])

    solved = entry["solved_problems"]
    first = entry["first_try"]
    after = entry["after_explanation"]

    if field == "solved_problems":
        solved += delta
        if solved < first + after:
            # Keep the entry valid when the user lowers solved problems.
            overflow = first + after - solved
            reduce_after = min(after, overflow)
            after -= reduce_after
            overflow -= reduce_after
            if overflow:
                first = max(0, first - overflow)
    elif field == "first_try":
        first += delta
    elif field == "after_explanation":
        after += delta

    validate_counts(solved, first, after)
    updated = upsert_entry(user["user_id"], entry_date, solved, first, after)
    new_total = get_total_solved(user["user_id"])
    return updated, level_up_message(old_total, new_total)


def set_today_topic(user: dict, topic: str) -> dict:
    if topic not in ALLOWED_TOPICS:
        raise ValueError("Invalid topic.")
    return upsert_entry(
        user_id=user["user_id"],
        entry_date=date_to_str(today_for_user(user)),
        topic_of_day=topic,
    )


def add_sat_score(user_id: int, entry_date: str, score: int, notes: str | None = None) -> dict:
    validate_score(score)
    now = utc_now_iso()
    with get_db() as db:
        db.execute(
            "INSERT INTO sat_scores(user_id, date, score, notes, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, entry_date, score, notes, now),
        )
    return upsert_entry(user_id=user_id, entry_date=entry_date, sat_score=score)


def get_scores_in_period(user_id: int, start_date: str, end_date: str) -> list[dict]:
    with get_db() as db:
        return db.execute(
            """
            SELECT * FROM sat_scores
            WHERE user_id = ? AND date BETWEEN ? AND ?
            ORDER BY date ASC, id ASC
            """,
            (user_id, start_date, end_date),
        ).fetchall()


def get_all_entries(user_id: int) -> list[dict]:
    with get_db() as db:
        return db.execute(
            "SELECT * FROM daily_entries WHERE user_id = ? ORDER BY date ASC",
            (user_id,),
        ).fetchall()


def get_entries_between(user_id: int, start_date: str, end_date: str) -> list[dict]:
    with get_db() as db:
        return db.execute(
            """
            SELECT * FROM daily_entries
            WHERE user_id = ? AND date BETWEEN ? AND ?
            ORDER BY date ASC
            """,
            (user_id, start_date, end_date),
        ).fetchall()


def get_total_solved(user_id: int) -> int:
    with get_db() as db:
        row = db.execute(
            "SELECT COALESCE(SUM(solved_problems), 0) AS total FROM daily_entries WHERE user_id = ?",
            (user_id,),
        ).fetchone()
    return int(row["total"] or 0)


def day_range_ending(user: dict, days: int) -> list[date]:
    today = today_for_user(user)
    return [today - timedelta(days=offset) for offset in range(days - 1, -1, -1)]


def validate_period(period: int) -> int:
    period = int(period)
    if period < MIN_STATS_PERIOD:
        raise ValueError("Minimum statistics period is 5 days. Try /stats 5 or /stats 7.")
    return period


def validate_timezone_name(tz_name: str) -> str:
    ZoneInfo(tz_name)  # raises ZoneInfoNotFoundError if invalid
    return tz_name
