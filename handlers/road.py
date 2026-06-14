from __future__ import annotations

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from handlers.common import current_user
from services.stats_service import format_road


async def road(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = await current_user(update)
    text = format_road(user, days=14)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text)
    else:
        await update.effective_message.reply_text(text)


def register(app: Application) -> None:
    app.add_handler(CommandHandler("road", road))
    app.add_handler(CallbackQueryHandler(road, pattern=r"^nav:road$"))
