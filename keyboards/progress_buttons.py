from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from services.progress_service import TOPICS
from services.stats_service import ALLOWED_PERIODS


def progress_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="+1 solved", callback_data="delta:solved_problems:1"),
                InlineKeyboardButton(text="-1 solved", callback_data="delta:solved_problems:-1"),
            ],
            [
                InlineKeyboardButton(text="+1 first try", callback_data="delta:first_try:1"),
                InlineKeyboardButton(text="-1 first try", callback_data="delta:first_try:-1"),
            ],
            [
                InlineKeyboardButton(text="+1 after expl.", callback_data="delta:after_explanation:1"),
                InlineKeyboardButton(text="-1 after expl.", callback_data="delta:after_explanation:-1"),
            ],
            [InlineKeyboardButton(text="Choose topic", callback_data="topic_menu")],
            [InlineKeyboardButton(text="Add SAT score", callback_data="score_prompt")],
        ]
    )


def topic_keyboard() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=topic, callback_data=f"topic:{topic}")] for topic in TOPICS]
    rows.append([InlineKeyboardButton(text="Back", callback_data="back_progress")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def period_keyboard(prefix: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{p} days", callback_data=f"{prefix}:{p}") for p in ALLOWED_PERIODS[:3]],
            [InlineKeyboardButton(text=f"{p} days", callback_data=f"{prefix}:{p}") for p in ALLOWED_PERIODS[3:]],
        ]
    )


def reset_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Yes, reset", callback_data="reset_confirm"),
                InlineKeyboardButton(text="Cancel", callback_data="reset_cancel"),
            ]
        ]
    )
