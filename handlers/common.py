from __future__ import annotations

from aiogram.types import Message, CallbackQuery

from database import Database


async def ensure_message_user(message: Message, db: Database) -> dict:
    if message.from_user is None:
        raise ValueError("Message has no Telegram user.")
    return await db.ensure_user(message.from_user.id, message.from_user.username)


async def ensure_callback_user(callback: CallbackQuery, db: Database) -> dict:
    if callback.from_user is None:
        raise ValueError("Callback has no Telegram user.")
    return await db.ensure_user(callback.from_user.id, callback.from_user.username)
