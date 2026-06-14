from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Daily goal", callback_data="settings:daily_goal")],
            [InlineKeyboardButton(text="Timezone", callback_data="settings:timezone")],
            [InlineKeyboardButton(text="Language", callback_data="settings:language")],
            [InlineKeyboardButton(text="Default stats period", callback_data="settings:default_stats_period")],
            [InlineKeyboardButton(text="Target SAT score", callback_data="settings:target_score")],
        ]
    )


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="English", callback_data="language:en"),
                InlineKeyboardButton(text="Українська", callback_data="language:uk"),
            ]
        ]
    )
