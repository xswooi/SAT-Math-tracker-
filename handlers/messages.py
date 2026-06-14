from __future__ import annotations

import re

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from handlers.common import current_user
from handlers.settings import format_settings, handle_pending_setting
from keyboards.main_menu import main_menu_keyboard
from keyboards.progress_buttons import period_keyboard, progress_keyboard
from keyboards.settings_buttons import settings_keyboard
from services.chart_service import generate_charts
from services.parser_service import parse_progress_text
from services.progress_service import (
    add_sat_score,
    date_to_str,
    get_today_entry,
    today_for_user,
    update_entry_from_parsed,
    validate_score,
)
from services.stats_service import format_road, format_stats, format_today, stats_for_period


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = await current_user(update)
    text = (update.effective_message.text or "").strip()
    lowered = text.lower()

    pending = context.user_data.get("pending")
    if pending == "sat_score":
        match = re.search(r"\d{3}", text)
        if not match:
            await update.effective_message.reply_text("Enter a valid SAT Math score from 200 to 800.")
            return
        try:
            score = int(match.group(0))
            validate_score(score)
            entry = add_sat_score(user["user_id"], date_to_str(today_for_user(user)), score, notes="Manual score input")
            context.user_data.pop("pending", None)
            await update.effective_message.reply_text(f"SAT Math score saved: {score}\n\n" + format_today(user, entry))
        except ValueError:
            await update.effective_message.reply_text("SAT Math score must be between 200 and 800.")
        return

    if isinstance(pending, str) and pending.startswith("setting:"):
        setting = pending.split(":", 1)[1]
        handled = await handle_pending_setting(update, context, user, setting, text)
        if handled:
            return

    if lowered in {"today", "сьогодні", "сегодня"}:
        entry = get_today_entry(user)
        await update.effective_message.reply_text(format_today(user, entry), reply_markup=progress_keyboard())
        return

    if lowered in {"add progress", "add", "додати", "прогрес"}:
        entry = get_today_entry(user)
        await update.effective_message.reply_text(format_today(user, entry), reply_markup=progress_keyboard())
        return

    if lowered in {"road", "дорога", "шлях"}:
        await update.effective_message.reply_text(format_road(user, days=14))
        return

    if lowered in {"stats", "statistics", "статистика"}:
        stats = stats_for_period(user, int(user["default_stats_period"]))
        await update.effective_message.reply_text(format_stats(user, stats), reply_markup=period_keyboard("stats"))
        return

    if lowered in {"charts", "chart", "графіки", "графики"}:
        days = int(user["default_stats_period"])
        await update.effective_message.reply_text(f"Generating charts for the last {days} days…")
        for path in generate_charts(user, days):
            await update.effective_message.reply_photo(photo=path.open("rb"))
        await update.effective_message.reply_text("Choose another chart period:", reply_markup=period_keyboard("charts"))
        return

    if lowered in {"add sat score", "score", "sat score", "додати sat", "бал sat"}:
        context.user_data["pending"] = "sat_score"
        await update.effective_message.reply_text("Enter SAT Math score from 200 to 800.")
        return

    if lowered in {"settings", "налаштування", "настройки"}:
        await update.effective_message.reply_text(format_settings(user), reply_markup=settings_keyboard())
        return

    parsed = parse_progress_text(text)
    if parsed:
        try:
            entry, level_message = update_entry_from_parsed(user, parsed)
            reply = "Progress saved for today.\n\n" + format_today(user, entry)
            if level_message:
                reply += f"\n\n{level_message}"
            await update.effective_message.reply_text(reply, reply_markup=main_menu_keyboard())
        except ValueError as exc:
            await update.effective_message.reply_text(f"Could not save progress: {exc}")
        return

    await update.effective_message.reply_text(
        "I did not understand that yet. Try: 10 problems, 7 first try, 3 after explanation, topic geometry",
        reply_markup=main_menu_keyboard(),
    )


def register(app: Application) -> None:
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
