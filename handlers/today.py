from __future__ import annotations

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from handlers.common import current_user
from keyboards.progress_buttons import progress_keyboard
from services.progress_service import get_today_entry
from services.stats_service import format_today


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = await current_user(update)
    entry = get_today_entry(user)
    text = format_today(user, entry)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=progress_keyboard())
    else:
        await update.effective_message.reply_text(text, reply_markup=progress_keyboard())


def register(app: Application) -> None:
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CallbackQueryHandler(today, pattern=r"^nav:today$"))
