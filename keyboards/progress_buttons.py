from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import ALLOWED_TOPICS, ALLOWED_PERIODS


def progress_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("+1 solved", callback_data="add:solved_problems:1"),
                InlineKeyboardButton("-1 solved", callback_data="add:solved_problems:-1"),
            ],
            [
                InlineKeyboardButton("+1 first try", callback_data="add:first_try:1"),
                InlineKeyboardButton("-1 first try", callback_data="add:first_try:-1"),
            ],
            [
                InlineKeyboardButton("+1 after explanation", callback_data="add:after_explanation:1"),
                InlineKeyboardButton("-1 after explanation", callback_data="add:after_explanation:-1"),
            ],
            [
                InlineKeyboardButton("Choose topic", callback_data="topic:menu"),
                InlineKeyboardButton("Add SAT score", callback_data="score:ask"),
            ],
            [InlineKeyboardButton("Refresh today", callback_data="nav:today")],
        ]
    )


def topic_keyboard() -> InlineKeyboardMarkup:
    rows = []
    for i in range(0, len(ALLOWED_TOPICS), 2):
        rows.append([
            InlineKeyboardButton(topic, callback_data=f"topic:set:{topic}")
            for topic in ALLOWED_TOPICS[i:i + 2]
        ])
    rows.append([InlineKeyboardButton("Back", callback_data="nav:add")])
    return InlineKeyboardMarkup(rows)


def period_keyboard(prefix: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(str(period), callback_data=f"{prefix}:period:{period}") for period in ALLOWED_PERIODS]]
    )
