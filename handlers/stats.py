from __future__ import annotations

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from handlers.common import current_user, parse_period_from_args
from keyboards.progress_buttons import period_keyboard
from services.progress_service import MIN_STATS_PERIOD, validate_period
from services.stats_service import stats_for_period, format_stats

MIN_MSG = "Minimum statistics period is 5 days. Try /stats 5 or /stats 7."


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = await current_user(update)
    try:
        days = parse_period_from_args(context.args, int(user["default_stats_period"]))
        validate_period(days)
    except (ValueError, TypeError):
        await update.effective_message.reply_text(MIN_MSG)
        return
    data = stats_for_period(user, days)
    await update.effective_message.reply_text(format_stats(user, data), reply_markup=period_keyboard("stats"))


async def stats_period_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user = await current_user(update)
    try:
        days = int(query.data.split(":")[-1])
        validate_period(days)
        data = stats_for_period(user, days)
        await query.edit_message_text(format_stats(user, data), reply_markup=period_keyboard("stats"))
    except ValueError:
        await query.edit_message_text(MIN_MSG, reply_markup=period_keyboard("stats"))


def register(app: Application) -> None:
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CallbackQueryHandler(stats_period_callback, pattern=r"^stats:period:"))
