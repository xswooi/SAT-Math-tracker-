from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class User:
    user_id: int
    username: str | None
    language: str
    timezone: str
    daily_goal: int
    target_score: int
    default_stats_period: int
    created_at: str
