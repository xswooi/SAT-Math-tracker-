from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from config import DB_PATH


def dict_factory(cursor: sqlite3.Cursor, row: sqlite3.Row) -> dict:
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


@contextmanager
def get_db() -> Iterator[sqlite3.Connection]:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = dict_factory
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with get_db() as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                language TEXT NOT NULL DEFAULT 'English',
                timezone TEXT NOT NULL DEFAULT 'Europe/Kyiv',
                daily_goal INTEGER NOT NULL DEFAULT 10,
                target_score INTEGER NOT NULL DEFAULT 800,
                default_stats_period INTEGER NOT NULL DEFAULT 7,
                created_at TEXT NOT NULL
            )
            """
        )

        db.execute(
            """
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
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                UNIQUE(user_id, date)
            )
            """
        )

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS sat_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                score INTEGER NOT NULL,
                notes TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
            """
        )

        db.execute("CREATE INDEX IF NOT EXISTS idx_daily_entries_user_date ON daily_entries(user_id, date)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_sat_scores_user_date ON sat_scores(user_id, date)")
