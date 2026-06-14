from __future__ import annotations

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import Database
from handlers.common import ensure_callback_user, ensure_message_user
from handlers.states import SettingsStates
from keyboards.settings_buttons import language_keyboard, settings_keyboard

router = Router()


def settings_text(user: dict) -> str:
    return (
        "<b>Settings</b>\n\n"
        f"Daily goal: <b>{user['daily_goal']}</b> problems\n"
        f"Timezone: <b>{user['timezone']}</b>\n"
        f"Language: <b>{user['language']}</b>\n"
        f"Default stats period: <b>{user['default_stats_period']}</b> days\n"
        f"Target SAT score: <b>{user['target_score']}</b>"
    )


@router.message(Command("settings"))
@router.message(F.text == "Settings")
async def settings(message: Message, db: Database) -> None:
    user = await ensure_message_user(message, db)
    await message.answer(settings_text(user), reply_markup=settings_keyboard())


@router.callback_query(F.data.startswith("settings:"))
async def settings_choose(callback: CallbackQuery, db: Database, state: FSMContext) -> None:
    user = await ensure_callback_user(callback, db)
    field = callback.data.split(":", 1)[1]  # type: ignore[union-attr]

    if field == "daily_goal":
        await state.set_state(SettingsStates.waiting_for_daily_goal)
        await callback.message.answer("Enter new daily goal, for example: 10")  # type: ignore[union-attr]
    elif field == "timezone":
        await state.set_state(SettingsStates.waiting_for_timezone)
        await callback.message.answer("Enter timezone, for example: Europe/Kyiv, Europe/London, America/New_York")  # type: ignore[union-attr]
    elif field == "language":
        await callback.message.answer("Choose language:", reply_markup=language_keyboard())  # type: ignore[union-attr]
    elif field == "default_stats_period":
        await state.set_state(SettingsStates.waiting_for_default_stats_period)
        await callback.message.answer("Enter default stats period. Minimum is 5 days, for example: 7")  # type: ignore[union-attr]
    elif field == "target_score":
        await state.set_state(SettingsStates.waiting_for_target_score)
        await callback.message.answer("Enter target SAT Math score from 200 to 800, for example: 800")  # type: ignore[union-attr]
    else:
        await callback.answer("Unknown setting", show_alert=True)
        return
    await callback.answer()


@router.callback_query(F.data.startswith("language:"))
async def set_language(callback: CallbackQuery, db: Database) -> None:
    user = await ensure_callback_user(callback, db)
    lang = callback.data.split(":", 1)[1]  # type: ignore[union-attr]
    if lang not in {"en", "uk"}:
        await callback.answer("Unsupported language", show_alert=True)
        return
    await db.update_user_setting(user["user_id"], "language", lang)
    updated = await db.get_user(user["user_id"])
    await callback.message.answer("Language updated.\n\n" + settings_text(updated), reply_markup=settings_keyboard())  # type: ignore[union-attr]
    await callback.answer()


@router.message(SettingsStates.waiting_for_daily_goal)
async def set_daily_goal(message: Message, db: Database, state: FSMContext) -> None:
    user = await ensure_message_user(message, db)
    try:
        value = int((message.text or "").strip())
        if value <= 0 or value > 500:
            raise ValueError
    except ValueError:
        await message.answer("Enter a valid positive daily goal, for example: 10")
        return
    await db.update_user_setting(user["user_id"], "daily_goal", value)
    await state.clear()
    updated = await db.get_user(user["user_id"])
    await message.answer("Daily goal updated.\n\n" + settings_text(updated), reply_markup=settings_keyboard())


@router.message(SettingsStates.waiting_for_timezone)
async def set_timezone(message: Message, db: Database, state: FSMContext) -> None:
    user = await ensure_message_user(message, db)
    tz = (message.text or "").strip()
    try:
        ZoneInfo(tz)
    except ZoneInfoNotFoundError:
        await message.answer("Invalid timezone. Try an IANA timezone like Europe/Kyiv or Europe/London.")
        return
    await db.update_user_setting(user["user_id"], "timezone", tz)
    await state.clear()
    updated = await db.get_user(user["user_id"])
    await message.answer("Timezone updated.\n\n" + settings_text(updated), reply_markup=settings_keyboard())


@router.message(SettingsStates.waiting_for_default_stats_period)
async def set_default_stats_period(message: Message, db: Database, state: FSMContext) -> None:
    user = await ensure_message_user(message, db)
    try:
        value = int((message.text or "").strip())
        if value < 5 or value > 365:
            raise ValueError
    except ValueError:
        await message.answer("Minimum statistics period is 5 days. Try 5 or 7.")
        return
    await db.update_user_setting(user["user_id"], "default_stats_period", value)
    await state.clear()
    updated = await db.get_user(user["user_id"])
    await message.answer("Default stats period updated.\n\n" + settings_text(updated), reply_markup=settings_keyboard())


@router.message(SettingsStates.waiting_for_target_score)
async def set_target_score(message: Message, db: Database, state: FSMContext) -> None:
    user = await ensure_message_user(message, db)
    try:
        value = int((message.text or "").strip())
        if not (200 <= value <= 800):
            raise ValueError
    except ValueError:
        await message.answer("Target SAT Math score must be between 200 and 800.")
        return
    await db.update_user_setting(user["user_id"], "target_score", value)
    await state.clear()
    updated = await db.get_user(user["user_id"])
    await message.answer("Target score updated.\n\n" + settings_text(updated), reply_markup=settings_keyboard())
