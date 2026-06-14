from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Daily goal", callback_data="settings:daily_goal")],
            [InlineKeyboardButton("Timezone", callback_data="settings:timezone")],
            [InlineKeyboardButton("Language", callback_data="settings:language")],
            [InlineKeyboardButton("Default stats period", callback_data="settings:default_stats_period")],
            [InlineKeyboardButton("Target SAT score", callback_data="settings:target_score")],
        ]
    )


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("English", callback_data="settings:language:set:English")],
            [InlineKeyboardButton("Ukrainian", callback_data="settings:language:set:Ukrainian")],
            [InlineKeyboardButton("Back", callback_data="nav:settings")],
        ]
    )


def reset_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Yes, reset all data", callback_data="reset:confirm")],
            [InlineKeyboardButton("Cancel", callback_data="reset:cancel")],
        ]
    )
