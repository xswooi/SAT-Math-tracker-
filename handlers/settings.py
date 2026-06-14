from __future__ import annotations

from zoneinfo import ZoneInfoNotFoundError

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from config import MIN_STATS_PERIOD
from handlers.common import current_user
from keyboards.settings_buttons import language_keyboard, settings_keyboard
from services.progress_service import update_user_setting, validate_period, validate_score, validate_timezone_name


def format_settings(user: dict) -> str:
    return (
        "Settings\n\n"
        f"Daily goal: {user['daily_goal']} problems\n"
        f"Timezone: {user['timezone']}\n"
        f"Language: {user['language']}\n"
        f"Default stats period: {user['default_stats_period']} days\n"
        f"Target SAT score: {user['target_score']}"
    )


async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = await current_user(update)
    text = format_settings(user)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=settings_keyboard())
    else:
        await update.effective_message.reply_text(text, reply_markup=settings_keyboard())


async def settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await current_user(update)
    setting = query.data.split(":", 1)[1]

    if setting == "language":
        await query.edit_message_text("Choose language:", reply_markup=language_keyboard())
        return

    prompt_by_setting = {
        "daily_goal": "Enter new daily goal, for example: 10",
        "timezone": "Enter timezone, for example: Europe/Kyiv or Europe/Zaporozhye",
        "default_stats_period": "Enter default stats period. Minimum is 5 days.",
        "target_score": "Enter target SAT Math score from 200 to 800.",
    }
    if setting not in prompt_by_setting:
        await query.edit_message_text("Unknown setting.", reply_markup=settings_keyboard())
        return
    context.user_data["pending"] = f"setting:{setting}"
    await query.edit_message_text(prompt_by_setting[setting])


async def language_set_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user = await current_user(update)
    language = query.data.split(":")[-1]
    updated = update_user_setting(user["user_id"], "language", language)
    await query.edit_message_text(format_settings(updated), reply_markup=settings_keyboard())


async def handle_pending_setting(update: Update, context: ContextTypes.DEFAULT_TYPE, user: dict, setting: str, text: str) -> bool:
    try:
        if setting == "daily_goal":
            value = int(text)
            if value <= 0:
                raise ValueError("Daily goal must be positive.")
        elif setting == "timezone":
            value = validate_timezone_name(text.strip())
        elif setting == "default_stats_period":
            value = validate_period(int(text))
        elif setting == "target_score":
            value = int(text)
            validate_score(value)
        else:
            return False
    except (ValueError, ZoneInfoNotFoundError):
        await update.effective_message.reply_text("Invalid value. Open /settings and try again.")
        context.user_data.pop("pending", None)
        return True

    updated = update_user_setting(user["user_id"], setting, value)
    context.user_data.pop("pending", None)
    await update.effective_message.reply_text(format_settings(updated), reply_markup=settings_keyboard())
    return True


def register(app: Application) -> None:
    app.add_handler(CommandHandler("settings", settings))
    app.add_handler(CallbackQueryHandler(settings, pattern=r"^nav:settings$"))
    app.add_handler(CallbackQueryHandler(language_set_callback, pattern=r"^settings:language:set:"))
    app.add_handler(CallbackQueryHandler(settings_callback, pattern=r"^settings:"))
