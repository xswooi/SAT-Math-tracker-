from __future__ import annotations

import re

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from handlers.common import current_user
from services.progress_service import add_sat_score, date_to_str, today_for_user, validate_score
from services.stats_service import format_today
from services.progress_service import get_today_entry
from keyboards.progress_buttons import progress_keyboard


async def score(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = await current_user(update)
    if context.args:
        try:
            value = int(context.args[0])
            validate_score(value)
            entry = add_sat_score(user["user_id"], date_to_str(today_for_user(user)), value, notes="/score command")
            await update.effective_message.reply_text(f"SAT Math score saved: {value}\n\n" + format_today(user, entry))
        except ValueError:
            await update.effective_message.reply_text("SAT Math score must be between 200 and 800. Try /score 680.")
        return

    context.user_data["pending"] = "sat_score"
    await update.effective_message.reply_text("Enter SAT Math score from 200 to 800.")


async def score_ask_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await current_user(update)
    context.user_data["pending"] = "sat_score"
    await query.edit_message_text("Enter SAT Math score from 200 to 800.")


def register(app: Application) -> None:
    app.add_handler(CommandHandler("score", score))
    app.add_handler(CallbackQueryHandler(score_ask_callback, pattern=r"^score:ask$"))
