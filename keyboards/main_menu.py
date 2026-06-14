from __future__ import annotations

from telegram import KeyboardButton, ReplyKeyboardMarkup


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("Today"), KeyboardButton("Add Progress")],
            [KeyboardButton("Road"), KeyboardButton("Stats"), KeyboardButton("Charts")],
            [KeyboardButton("Add SAT Score"), KeyboardButton("Settings")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Send progress or choose an action",
    )
