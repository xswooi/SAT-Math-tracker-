from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiosqlite

from config import Config


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class Database:
    def __init__(self, path: str, config: Config):
        self.path = path
        self.config = config
        Path(path).parent.mkdir(parents=True, exist_ok=True)

    async def connect(self) -> aiosqlite.Connection:
        db = await aiosqlite.connect(self.path)
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON")
        return db

    async def init_db(self) -> None:
        async with self.connect() as db:
            await db.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    language TEXT NOT NULL DEFAULT 'en',
                    timezone TEXT NOT NULL DEFAULT 'Europe/Kyiv',
                    daily_goal INTEGER NOT NULL DEFAULT 10,
                    target_score INTEGER NOT NULL DEFAULT 800,
                    default_stats_period INTEGER NOT NULL DEFAULT 7,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS daily_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    solved_problems INTEGER NOT NULL DEFAULT 0,
                    first_try INTEGER NOT NULL DEFAULT 0,
                    after_explanation INTEGER NOT NULL DEFAULT 0,
                    topic_of_day TEXT,
                    sat_score INTEGER,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(user_id, date),
                    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS sat_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_daily_entries_user_date
                    ON daily_entries(user_id, date);

                CREATE INDEX IF NOT EXISTS idx_sat_scores_user_date
                    ON sat_scores(user_id, date);
                """
            )
            await db.commit()

    async def ensure_user(self, user_id: int, username: str | None) -> dict[str, Any]:
        now = utc_now_iso()
        async with await self.connect() as db:
            await db.execute(
                """
                INSERT INTO users (user_id, username, language, timezone, daily_goal, target_score, default_stats_period, created_at)
                VALUES (?, ?, 'en', ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET username = excluded.username
                """,
                (
                    user_id,
                    username,
                    self.config.default_timezone,
                    self.config.default_daily_goal,
                    self.config.default_target_score,
                    self.config.default_stats_period,
                    now,
                ),
            )
            await db.commit()
        return await self.get_user(user_id)

    async def get_user(self, user_id: int) -> dict[str, Any]:
        async with await self.connect() as db:
            cur = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = await cur.fetchone()
            if row is None:
                raise ValueError(f"User {user_id} does not exist")
            return dict(row)

    async def update_user_setting(self, user_id: int, field: str, value: Any) -> None:
        allowed = {"language", "timezone", "daily_goal", "target_score", "default_stats_period"}
        if field not in allowed:
            raise ValueError(f"Invalid settings field: {field}")
        async with await self.connect() as db:
            await db.execute(f"UPDATE users SET {field} = ? WHERE user_id = ?", (value, user_id))
            await db.commit()

    async def get_entry(self, user_id: int, date: str) -> dict[str, Any] | None:
        async with await self.connect() as db:
            cur = await db.execute(
                "SELECT * FROM daily_entries WHERE user_id = ? AND date = ?",
                (user_id, date),
            )
            row = await cur.fetchone()
            return dict(row) if row else None

    async def upsert_entry(
        self,
        user_id: int,
        date: str,
        solved_problems: int | None = None,
        first_try: int | None = None,
        after_explanation: int | None = None,
        topic_of_day: str | None = None,
        sat_score: int | None = None,
    ) -> dict[str, Any]:
        old = await self.get_entry(user_id, date)
        now = utc_now_iso()

        if old is None:
            values = {
                "solved_problems": solved_problems if solved_problems is not None else 0,
                "first_try": first_try if first_try is not None else 0,
                "after_explanation": after_explanation if after_explanation is not None else 0,
                "topic_of_day": topic_of_day,
                "sat_score": sat_score,
            }
            async with await self.connect() as db:
                await db.execute(
                    """
                    INSERT INTO daily_entries
                    (user_id, date, solved_problems, first_try, after_explanation, topic_of_day, sat_score, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        date,
                        values["solved_problems"],
                        values["first_try"],
                        values["after_explanation"],
                        values["topic_of_day"],
                        values["sat_score"],
                        now,
                        now,
                    ),
                )
                await db.commit()
        else:
            values = {
                "solved_problems": old["solved_problems"] if solved_problems is None else solved_problems,
                "first_try": old["first_try"] if first_try is None else first_try,
                "after_explanation": old["after_explanation"] if after_explanation is None else after_explanation,
                "topic_of_day": old["topic_of_day"] if topic_of_day is None else topic_of_day,
                "sat_score": old["sat_score"] if sat_score is None else sat_score,
            }
            async with await self.connect() as db:
                await db.execute(
                    """
                    UPDATE daily_entries
                    SET solved_problems = ?, first_try = ?, after_explanation = ?, topic_of_day = ?, sat_score = ?, updated_at = ?
                    WHERE user_id = ? AND date = ?
                    """,
                    (
                        values["solved_problems"],
                        values["first_try"],
                        values["after_explanation"],
                        values["topic_of_day"],
                        values["sat_score"],
                        now,
                        user_id,
                        date,
                    ),
                )
                await db.commit()

        return await self.get_entry(user_id, date)  # type: ignore[return-value]

    async def list_entries(self, user_id: int, start_date: str, end_date: str) -> list[dict[str, Any]]:
        async with await self.connect() as db:
            cur = await db.execute(
                """
                SELECT * FROM daily_entries
                WHERE user_id = ? AND date BETWEEN ? AND ?
                ORDER BY date ASC
                """,
                (user_id, start_date, end_date),
            )
            rows = await cur.fetchall()
            return [dict(row) for row in rows]

    async def list_all_entries(self, user_id: int) -> list[dict[str, Any]]:
        async with await self.connect() as db:
            cur = await db.execute(
                "SELECT * FROM daily_entries WHERE user_id = ? ORDER BY date ASC",
                (user_id,),
            )
            return [dict(row) for row in await cur.fetchall()]

    async def add_sat_score(self, user_id: int, date: str, score: int, notes: str | None = None) -> dict[str, Any]:
        now = utc_now_iso()
        async with await self.connect() as db:
            cur = await db.execute(
                """
                INSERT INTO sat_scores (user_id, date, score, notes, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, date, score, notes, now),
            )
            await db.commit()
            score_id = cur.lastrowid
        await self.upsert_entry(user_id=user_id, date=date, sat_score=score)
        async with await self.connect() as db:
            cur = await db.execute("SELECT * FROM sat_scores WHERE id = ?", (score_id,))
            row = await cur.fetchone()
            return dict(row)

    async def list_sat_scores(self, user_id: int, start_date: str | None = None, end_date: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM sat_scores WHERE user_id = ?"
        params: list[Any] = [user_id]
        if start_date is not None and end_date is not None:
            query += " AND date BETWEEN ? AND ?"
            params.extend([start_date, end_date])
        query += " ORDER BY date ASC, id ASC"
        async with await self.connect() as db:
            cur = await db.execute(query, params)
            return [dict(row) for row in await cur.fetchall()]

    async def export_user_data(self, user_id: int) -> dict[str, Any]:
        return {
            "user": await self.get_user(user_id),
            "daily_entries": await self.list_all_entries(user_id),
            "sat_scores": await self.list_sat_scores(user_id),
        }

    async def import_user_data(self, user_id: int, data: dict[str, Any]) -> tuple[int, int]:
        daily_entries = data.get("daily_entries", [])
        sat_scores = data.get("sat_scores", [])
        imported_days = 0
        imported_scores = 0
        async with await self.connect() as db:
            for e in daily_entries:
                date = str(e.get("date", "")).strip()
                if not date:
                    continue
                solved = max(0, int(e.get("solved_problems", 0) or 0))
                first = max(0, int(e.get("first_try", 0) or 0))
                after = max(0, int(e.get("after_explanation", 0) or 0))
                if first + after > solved:
                    solved = first + after
                topic = e.get("topic_of_day")
                sat = e.get("sat_score")
                if sat is not None:
                    sat = int(sat)
                    if not (200 <= sat <= 800):
                        sat = None
                now = utc_now_iso()
                await db.execute(
                    """
                    INSERT INTO daily_entries
                    (user_id, date, solved_problems, first_try, after_explanation, topic_of_day, sat_score, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(user_id, date) DO UPDATE SET
                        solved_problems=excluded.solved_problems,
                        first_try=excluded.first_try,
                        after_explanation=excluded.after_explanation,
                        topic_of_day=excluded.topic_of_day,
                        sat_score=excluded.sat_score,
                        updated_at=excluded.updated_at
                    """,
                    (user_id, date, solved, first, after, topic, sat, now, now),
                )
                imported_days += 1

            for s in sat_scores:
                date = str(s.get("date", "")).strip()
                score = int(s.get("score", 0) or 0)
                if not date or not (200 <= score <= 800):
                    continue
                await db.execute(
                    "INSERT INTO sat_scores (user_id, date, score, notes, created_at) VALUES (?, ?, ?, ?, ?)",
                    (user_id, date, score, s.get("notes"), utc_now_iso()),
                )
                imported_scores += 1
            await db.commit()
        return imported_days, imported_scores

    async def reset_user_data(self, user_id: int) -> None:
        async with await self.connect() as db:
            await db.execute("DELETE FROM daily_entries WHERE user_id = ?", (user_id,))
            await db.execute("DELETE FROM sat_scores WHERE user_id = ?", (user_id,))
            await db.execute(
                """
                UPDATE users
                SET language = 'en', timezone = ?, daily_goal = ?, target_score = ?, default_stats_period = ?
                WHERE user_id = ?
                """,
                (
                    self.config.default_timezone,
                    self.config.default_daily_goal,
                    self.config.default_target_score,
                    self.config.default_stats_period,
                    user_id,
                ),
            )
            await db.commit()

    @staticmethod
    def dumps_pretty(data: dict[str, Any]) -> str:
        return json.dumps(data, indent=2, ensure_ascii=False, default=str)
