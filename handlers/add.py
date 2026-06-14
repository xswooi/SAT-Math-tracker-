from __future__ import annotations

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from handlers.common import current_user
from keyboards.progress_buttons import progress_keyboard, topic_keyboard
from services.progress_service import increment_today, set_today_topic, get_today_entry
from services.stats_service import format_today


async def add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = await current_user(update)
    entry = get_today_entry(user)
    text = format_today(user, entry) + "\n\nUse buttons to edit today quickly."
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=progress_keyboard())
    else:
        await update.effective_message.reply_text(text, reply_markup=progress_keyboard())


async def add_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user = await current_user(update)
    _, field, delta_raw = query.data.split(":")
    try:
        entry, level_message = increment_today(user, field, int(delta_raw))
        text = format_today(user, entry)
        if level_message:
            text += f"\n\n{level_message}"
        await query.edit_message_text(text, reply_markup=progress_keyboard())
    except ValueError as exc:
        await query.edit_message_text(f"Cannot update progress: {exc}", reply_markup=progress_keyboard())


async def topic_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Choose today’s topic:", reply_markup=topic_keyboard())


async def topic_set_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user = await current_user(update)
    topic = query.data.split(":", 2)[2]
    try:
        entry = set_today_topic(user, topic)
        await query.edit_message_text(format_today(user, entry), reply_markup=progress_keyboard())
    except ValueError as exc:
        await query.edit_message_text(f"Cannot set topic: {exc}", reply_markup=topic_keyboard())


def register(app: Application) -> None:
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("day", add))
    app.add_handler(CallbackQueryHandler(add, pattern=r"^nav:add$"))
    app.add_handler(CallbackQueryHandler(add_callback, pattern=r"^add:"))
    app.add_handler(CallbackQueryHandler(topic_menu_callback, pattern=r"^topic:menu$"))
    app.add_handler(CallbackQueryHandler(topic_set_callback, pattern=r"^topic:set:"))
