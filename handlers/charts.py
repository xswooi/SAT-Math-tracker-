from __future__ import annotations

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from handlers.common import current_user, parse_period_from_args
from keyboards.progress_buttons import period_keyboard
from services.chart_service import generate_charts
from services.progress_service import validate_period

MIN_MSG = "Minimum chart period is 5 days. Try /charts 5 or /charts 7."


async def charts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = await current_user(update)
    try:
        days = parse_period_from_args(context.args, int(user["default_stats_period"]))
        validate_period(days)
    except (ValueError, TypeError):
        await update.effective_message.reply_text(MIN_MSG)
        return

    await update.effective_message.reply_text(f"Generating charts for the last {days} days…")
    paths = generate_charts(user, days)
    for path in paths:
        await update.effective_message.reply_photo(photo=path.open("rb"))
    await update.effective_message.reply_text("Choose another chart period:", reply_markup=period_keyboard("charts"))


async def charts_period_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user = await current_user(update)
    try:
        days = int(query.data.split(":")[-1])
        validate_period(days)
    except ValueError:
        await query.edit_message_text(MIN_MSG, reply_markup=period_keyboard("charts"))
        return

    await query.edit_message_text(f"Generating charts for the last {days} days…")
    paths = generate_charts(user, days)
    for path in paths:
        await query.message.reply_photo(photo=path.open("rb"))
    await query.message.reply_text("Choose another chart period:", reply_markup=period_keyboard("charts"))


def register(app: Application) -> None:
    app.add_handler(CommandHandler("charts", charts))
    app.add_handler(CallbackQueryHandler(charts_period_callback, pattern=r"^charts:period:"))
