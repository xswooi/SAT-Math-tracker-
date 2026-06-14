from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SatScore:
    id: int | None
    user_id: int
    date: str
    score: int
    notes: str | None
    created_at: str | None
