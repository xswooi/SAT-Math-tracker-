from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from config import EXPORT_DIR
from database import get_db
from services.progress_service import utc_now_iso


def export_user_data(user_id: int) -> Path:
    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        entries = db.execute(
            "SELECT * FROM daily_entries WHERE user_id = ? ORDER BY date ASC", (user_id,)
        ).fetchall()
        scores = db.execute(
            "SELECT * FROM sat_scores WHERE user_id = ? ORDER BY date ASC, id ASC", (user_id,)
        ).fetchall()
    payload = {
        "version": 1,
        "exported_at": utc_now_iso(),
        "user": user,
        "daily_entries": entries,
        "sat_scores": scores,
    }
    path = EXPORT_DIR / f"sat_road_to_800_export_{user_id}_{uuid4().hex[:8]}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def import_user_data(user_id: int, json_path: Path) -> dict:
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    entries = payload.get("daily_entries", [])
    scores = payload.get("sat_scores", [])
    imported_entries = 0
    imported_scores = 0

    with get_db() as db:
        for entry in entries:
            db.execute(
                """
                INSERT INTO daily_entries(user_id, date, solved_problems, first_try, after_explanation, topic_of_day, sat_score, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, date) DO UPDATE SET
                    solved_problems = excluded.solved_problems,
                    first_try = excluded.first_try,
                    after_explanation = excluded.after_explanation,
                    topic_of_day = excluded.topic_of_day,
                    sat_score = excluded.sat_score,
                    updated_at = excluded.updated_at
                """,
                (
                    user_id,
                    entry.get("date"),
                    int(entry.get("solved_problems") or 0),
                    int(entry.get("first_try") or 0),
                    int(entry.get("after_explanation") or 0),
                    entry.get("topic_of_day"),
                    entry.get("sat_score"),
                    entry.get("created_at") or utc_now_iso(),
                    entry.get("updated_at") or utc_now_iso(),
                ),
            )
            imported_entries += 1

        for score in scores:
            db.execute(
                "INSERT INTO sat_scores(user_id, date, score, notes, created_at) VALUES (?, ?, ?, ?, ?)",
                (
                    user_id,
                    score.get("date"),
                    int(score.get("score")),
                    score.get("notes"),
                    score.get("created_at") or utc_now_iso(),
                ),
            )
            imported_scores += 1

    return {"entries": imported_entries, "scores": imported_scores}


def reset_user_data(user_id: int) -> None:
    with get_db() as db:
        db.execute("DELETE FROM daily_entries WHERE user_id = ?", (user_id,))
        db.execute("DELETE FROM sat_scores WHERE user_id = ?", (user_id,))
