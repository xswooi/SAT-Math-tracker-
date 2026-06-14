from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Today"), KeyboardButton(text="Add Progress")],
            [KeyboardButton(text="Road"), KeyboardButton(text="Stats")],
            [KeyboardButton(text="Charts"), KeyboardButton(text="Add SAT Score")],
            [KeyboardButton(text="Settings")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Log progress: 10 problems, 7 first try...",
    )
