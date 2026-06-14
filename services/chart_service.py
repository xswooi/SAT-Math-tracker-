from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from database import Database
from services.progress_service import date_range, status_for_entry, today_in_timezone


def _short_labels(days):
    return [d.strftime("%d %b") for d in days]


def _finish(path: Path) -> Path:
    plt.tight_layout()
    plt.savefig(path, dpi=160, bbox_inches="tight")
    plt.close()
    return path


async def generate_charts(db: Database, user: dict[str, Any], period_days: int, charts_dir: str) -> list[Path]:
    out_dir = Path(charts_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    today = today_in_timezone(user["timezone"])
    days = date_range(today, period_days)
    start = days[0].isoformat()
    end = days[-1].isoformat()
    entries = await db.list_entries(user["user_id"], start, end)
    by_date = {e["date"]: e for e in entries}
    scores = await db.list_sat_scores(user["user_id"], start, end)

    labels = _short_labels(days)
    solved = [int((by_date.get(d.isoformat()) or {}).get("solved_problems") or 0) for d in days]
    first_rates = []
    for d in days:
        e = by_date.get(d.isoformat())
        if e and int(e["solved_problems"] or 0) > 0:
            first_rates.append((int(e["first_try"] or 0) / int(e["solved_problems"] or 0)) * 100)
        else:
            first_rates.append(None)

    files: list[Path] = []
    token = uuid4().hex[:8]

    # 1. Problems solved per day.
    plt.figure(figsize=(max(7, period_days * 0.45), 4))
    plt.bar(labels, solved)
    plt.axhline(int(user["daily_goal"]), linestyle="--", linewidth=1, label="Daily goal")
    plt.title(f"Problems solved per day — last {period_days} days")
    plt.ylabel("Problems")
    plt.xticks(rotation=45, ha="right")
    plt.legend()
    files.append(_finish(out_dir / f"problems_{token}.png"))

    # 2. First try rate over time.
    plt.figure(figsize=(max(7, period_days * 0.45), 4))
    x = list(range(len(days)))
    y = [v if v is not None else float("nan") for v in first_rates]
    plt.plot(x, y, marker="o")
    plt.ylim(0, 105)
    plt.title(f"First try rate — last {period_days} days")
    plt.ylabel("First try rate (%)")
    plt.xticks(x, labels, rotation=45, ha="right")
    plt.grid(True, axis="y", linewidth=0.4)
    files.append(_finish(out_dir / f"first_try_rate_{token}.png"))

    # 3. SAT Math score over time.
    score_by_date: dict[str, int] = {}
    for s in scores:
        score_by_date[s["date"]] = int(s["score"])
    for e in entries:
        if e.get("sat_score") is not None:
            score_by_date[e["date"]] = int(e["sat_score"])

    plt.figure(figsize=(max(7, period_days * 0.45), 4))
    score_values = [score_by_date.get(d.isoformat(), float("nan")) for d in days]
    if any(v == v for v in score_values):
        plt.plot(x, score_values, marker="o")
        plt.ylim(190, 810)
        plt.ylabel("SAT Math score")
    else:
        plt.text(0.5, 0.5, "No SAT scores in this period", ha="center", va="center", fontsize=14)
        plt.axis("off")
    plt.title(f"SAT Math score — last {period_days} days")
    if plt.gca().has_data():
        plt.xticks(x, labels, rotation=45, ha="right")
        plt.grid(True, axis="y", linewidth=0.4)
    files.append(_finish(out_dir / f"sat_score_{token}.png"))

    # 4. Topic distribution.
    topics = [e["topic_of_day"] for e in entries if e.get("topic_of_day")]
    counter = Counter(topics)
    plt.figure(figsize=(7, 4))
    if counter:
        names = list(counter.keys())
        values = list(counter.values())
        plt.bar(names, values)
        plt.ylabel("Days")
        plt.xticks(rotation=25, ha="right")
    else:
        plt.text(0.5, 0.5, "No topics logged in this period", ha="center", va="center", fontsize=14)
        plt.axis("off")
    plt.title(f"Topic distribution — last {period_days} days")
    files.append(_finish(out_dir / f"topics_{token}.png"))

    # 5. Completion status heatmap/calendar-style chart.
    status_values = []
    status_emojis = []
    goal = int(user["daily_goal"])
    value_by_key = {"missed": 0, "no_data": 1, "partial": 2, "completed": 3, "overachieved": 4, "high_quality": 5}
    for d in days:
        st = status_for_entry(by_date.get(d.isoformat()), goal, d, today)
        status_values.append(value_by_key[st.key])
        status_emojis.append(st.emoji)

    weeks = (period_days + 6) // 7
    grid = [[float("nan") for _ in range(7)] for _ in range(weeks)]
    emoji_grid = [["" for _ in range(7)] for _ in range(weeks)]
    label_grid = [["" for _ in range(7)] for _ in range(weeks)]
    for idx, d in enumerate(days):
        r = idx // 7
        c = idx % 7
        grid[r][c] = status_values[idx]
        emoji_grid[r][c] = status_emojis[idx]
        label_grid[r][c] = d.strftime("%d")

    plt.figure(figsize=(8, max(2.2, weeks * 1.0)))
    plt.imshow(grid, aspect="auto")
    ax = plt.gca()
    ax.set_xticks(range(7))
    ax.set_xticklabels([(days[0] + timedelta(days=i)).strftime("%a") for i in range(7)])
    ax.set_yticks(range(weeks))
    ax.set_yticklabels([f"Week {i + 1}" for i in range(weeks)])
    for r in range(weeks):
        for c in range(7):
            if emoji_grid[r][c]:
                ax.text(c, r, f"{emoji_grid[r][c]}\n{label_grid[r][c]}", ha="center", va="center", fontsize=10)
    plt.title(f"Completion status — last {period_days} days")
    files.append(_finish(out_dir / f"heatmap_{token}.png"))

    return files
