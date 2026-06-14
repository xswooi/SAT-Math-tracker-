from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from services.progress_service import ensure_user, get_user


async def current_user(update: Update) -> dict:
    tg_user = update.effective_user
    if tg_user is None:
        raise RuntimeError("No Telegram user in update")
    return ensure_user(tg_user)


async def send_or_edit(update: Update, text: str, **kwargs) -> None:
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, **kwargs)
    elif update.effective_message:
        await update.effective_message.reply_text(text, **kwargs)


def parse_period_from_args(args: list[str], default: int) -> int:
    if not args:
        return default
    return int(args[0])
