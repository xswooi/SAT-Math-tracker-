from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from database import Database
from services.progress_service import (
    COMPLETED_KEYS,
    best_streak,
    current_streak,
    date_range,
    status_for_entry,
    today_in_timezone,
)

MIN_PERIOD = 5
ALLOWED_PERIODS = [5, 7, 14, 30, 90]


@dataclass(slots=True)
class Stats:
    days: int
    total_solved: int
    average_solved: float
    completed_days: int
    missed_days: int
    current_streak: int
    best_streak: int
    first_try_rate: float
    after_explanation_rate: float
    most_common_topic: str | None
    latest_score: int | None
    highest_score: int | None
    score_improvement: int | None


def parse_period(arg_text: str | None, default: int) -> tuple[int | None, str | None]:
    if not arg_text or not arg_text.strip():
        return default, None
    parts = arg_text.strip().split()
    for p in parts:
        if p.isdigit():
            days = int(p)
            if days < MIN_PERIOD:
                return None, "Minimum statistics period is 5 days. Try /stats 5 or /stats 7."
            return days, None
    return default, None


def period_bounds(user: dict[str, Any], days: int) -> tuple[date, date, list[date]]:
    end = today_in_timezone(user["timezone"])
    days_list = date_range(end, days)
    return days_list[0], days_list[-1], days_list


async def calculate_stats(db: Database, user: dict[str, Any], days: int) -> Stats:
    start, end, days_list = period_bounds(user, days)
    rows = await db.list_entries(user["user_id"], start.isoformat(), end.isoformat())
    by_date = {row["date"]: row for row in rows}
    today = today_in_timezone(user["timezone"])
    goal = int(user["daily_goal"])

    total_solved = 0
    first_try = 0
    after = 0
    completed = 0
    missed = 0
    topics: list[str] = []

    for d in days_list:
        entry = by_date.get(d.isoformat())
        status = status_for_entry(entry, goal, d, today)
        if entry:
            solved = int(entry["solved_problems"] or 0)
            total_solved += solved
            first_try += int(entry["first_try"] or 0)
            after += int(entry["after_explanation"] or 0)
            if entry.get("topic_of_day"):
                topics.append(entry["topic_of_day"])
        if status.key in COMPLETED_KEYS:
            completed += 1
        if status.key == "missed":
            missed += 1

    scores = await db.list_sat_scores(user["user_id"], start.isoformat(), end.isoformat())
    # Also include imported daily-entry SAT scores if no sat_scores rows exist for those dates.
    score_points = [(s["date"], int(s["score"])) for s in scores]
    seen = {(d, score) for d, score in score_points}
    for row in rows:
        if row.get("sat_score") is not None:
            tup = (row["date"], int(row["sat_score"]))
            if tup not in seen:
                score_points.append(tup)
    score_points.sort(key=lambda x: x[0])

    latest = score_points[-1][1] if score_points else None
    highest = max((score for _, score in score_points), default=None)
    improvement = None
    if len(score_points) >= 2:
        improvement = score_points[-1][1] - score_points[0][1]

    most_common_topic = Counter(topics).most_common(1)[0][0] if topics else None

    return Stats(
        days=days,
        total_solved=total_solved,
        average_solved=total_solved / days,
        completed_days=completed,
        missed_days=missed,
        current_streak=await current_streak(db, user),
        best_streak=await best_streak(db, user, start, end),
        first_try_rate=(first_try / total_solved) if total_solved else 0,
        after_explanation_rate=(after / total_solved) if total_solved else 0,
        most_common_topic=most_common_topic,
        latest_score=latest,
        highest_score=highest,
        score_improvement=improvement,
    )


def format_stats_message(stats: Stats) -> str:
    latest = stats.latest_score if stats.latest_score is not None else "—"
    highest = stats.highest_score if stats.highest_score is not None else "—"
    improvement = "—" if stats.score_improvement is None else f"{stats.score_improvement:+d}"
    topic = stats.most_common_topic or "—"
    return (
        f"<b>Stats — last {stats.days} days</b>\n\n"
        f"Solved total: <b>{stats.total_solved}</b>\n"
        f"Average per day: <b>{stats.average_solved:.1f}</b>\n"
        f"Completed days: <b>{stats.completed_days}</b>\n"
        f"Missed days: <b>{stats.missed_days}</b>\n"
        f"Current streak: <b>{stats.current_streak}</b> days\n"
        f"Best streak: <b>{stats.best_streak}</b> days\n\n"
        f"First try rate: <b>{stats.first_try_rate:.0%}</b>\n"
        f"After explanation rate: <b>{stats.after_explanation_rate:.0%}</b>\n"
        f"Most common topic: <b>{topic}</b>\n\n"
        f"Latest SAT Math score: <b>{latest}</b>\n"
        f"Highest SAT Math score: <b>{highest}</b>\n"
        f"Score improvement: <b>{improvement}</b>"
    )
