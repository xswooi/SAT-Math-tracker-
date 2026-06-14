from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class DailyEntry:
    id: int | None
    user_id: int
    date: str
    solved_problems: int
    first_try: int
    after_explanation: int
    topic_of_day: str | None
    sat_score: int | None
    created_at: str
    updated_at: str
