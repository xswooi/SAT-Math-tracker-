from __future__ import annotations

from collections import Counter
from pathlib import Path
from uuid import uuid4

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

from config import CHART_DIR
from services.progress_service import get_scores_in_period, validate_period
from services.stats_service import period_entries


def _save(fig, name: str) -> Path:
    path = CHART_DIR / f"{name}_{uuid4().hex[:8]}.png"
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return path


def _empty_chart(title: str, message: str) -> Path:
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.axis("off")
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.text(0.5, 0.5, message, ha="center", va="center", fontsize=12)
    return _save(fig, title.lower().replace(" ", "_"))


def problems_chart(rows: list[dict], goal: int) -> Path:
    labels = [row["date"].strftime("%d %b") for row in rows]
    values = [row["solved"] for row in rows]
    fig, ax = plt.subplots(figsize=(max(7, len(rows) * 0.45), 4))
    ax.bar(labels, values)
    ax.axhline(goal, linestyle="--", linewidth=1, label=f"Goal: {goal}")
    ax.set_title("Problems solved per day", fontsize=14, fontweight="bold")
    ax.set_ylabel("Problems")
    ax.tick_params(axis="x", rotation=45)
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    return _save(fig, "problems_solved")


def first_try_chart(rows: list[dict]) -> Path:
    labels = [row["date"].strftime("%d %b") for row in rows]
    values = [(row["first_try"] / row["solved"] * 100) if row["solved"] else None for row in rows]
    fig, ax = plt.subplots(figsize=(max(7, len(rows) * 0.45), 4))
    ax.plot(labels, values, marker="o")
    ax.set_title("First try rate over time", fontsize=14, fontweight="bold")
    ax.set_ylabel("First try rate (%)")
    ax.set_ylim(0, 105)
    ax.tick_params(axis="x", rotation=45)
    ax.grid(alpha=0.25)
    return _save(fig, "first_try_rate")


def sat_score_chart(user: dict, rows: list[dict]) -> Path:
    scores = get_scores_in_period(user["user_id"], rows[0]["date_str"], rows[-1]["date_str"])
    if not scores:
        return _empty_chart("SAT Math score over time", "No SAT Math scores in this period yet.")
    labels = [score["date"] for score in scores]
    values = [score["score"] for score in scores]
    fig, ax = plt.subplots(figsize=(max(7, len(labels) * 0.7), 4))
    ax.plot(labels, values, marker="o")
    ax.axhline(int(user["target_score"]), linestyle="--", linewidth=1, label=f"Target: {user['target_score']}")
    ax.set_title("SAT Math score over time", fontsize=14, fontweight="bold")
    ax.set_ylabel("Score")
    ax.set_ylim(180, 820)
    ax.tick_params(axis="x", rotation=45)
    ax.grid(alpha=0.25)
    ax.legend()
    return _save(fig, "sat_score")


def topic_distribution_chart(rows: list[dict]) -> Path:
    topics = [row["topic"] for row in rows if row["topic"]]
    if not topics:
        return _empty_chart("Topic distribution", "No topic data in this period yet.")
    counts = Counter(topics)
    labels = list(counts.keys())
    values = list(counts.values())
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(labels, values)
    ax.set_title("Topic distribution", fontsize=14, fontweight="bold")
    ax.set_ylabel("Days")
    ax.tick_params(axis="x", rotation=30)
    ax.grid(axis="y", alpha=0.25)
    return _save(fig, "topic_distribution")


def completion_heatmap(rows: list[dict]) -> Path:
    status_order = {"missed": 0, "no_data": 1, "partial": 2, "completed": 3, "overachieved": 4, "high_quality": 5}
    values = [status_order[row["status"]["key"]] for row in rows]
    labels = [row["date"].strftime("%d %b") for row in rows]

    fig_height = 2.8 if len(rows) <= 14 else 3.2
    fig, ax = plt.subplots(figsize=(max(7, len(rows) * 0.35), fig_height))
    cmap = ListedColormap(["#e74c3c", "#ecf0f1", "#f1c40f", "#2ecc71", "#e67e22", "#9b59b6"])
    ax.imshow([values], aspect="auto", cmap=cmap, vmin=0, vmax=5)
    ax.set_yticks([])
    ax.set_xticks(range(len(rows)))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_title("Completion status heatmap", fontsize=14, fontweight="bold")

    label_by_status = {
        "missed": "M",
        "no_data": "—",
        "partial": "P",
        "completed": "C",
        "overachieved": "O",
        "high_quality": "Q",
    }
    for i, row in enumerate(rows):
        ax.text(i, 0, label_by_status[row["status"]["key"]], ha="center", va="center", fontsize=12, fontweight="bold")

    legend = "M missed   — no data   P partial   C completed   O overachieved   Q high quality"
    fig.text(0.5, -0.04, legend, ha="center", fontsize=9)
    return _save(fig, "completion_heatmap")


def generate_charts(user: dict, days: int) -> list[Path]:
    validate_period(days)
    rows = period_entries(user, days)
    goal = int(user["daily_goal"])
    return [
        problems_chart(rows, goal),
        first_try_chart(rows),
        sat_score_chart(user, rows),
        topic_distribution_chart(rows),
        completion_heatmap(rows),
    ]
