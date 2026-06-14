from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Message

from database import Database
from handlers.common import ensure_callback_user, ensure_message_user
from keyboards.progress_buttons import period_keyboard
from services.stats_service import calculate_stats, format_stats_message, parse_period

router = Router()


@router.message(Command("stats"))
async def stats_command(message: Message, db: Database, command: CommandObject) -> None:
    user = await ensure_message_user(message, db)
    period, error = parse_period(command.args, int(user["default_stats_period"]))
    if error:
        await message.answer(error)
        return
    assert period is not None
    stats = await calculate_stats(db, user, period)
    await message.answer(format_stats_message(stats), reply_markup=period_keyboard("stats_period"))


@router.message(F.text == "Stats")
async def stats_menu(message: Message, db: Database) -> None:
    user = await ensure_message_user(message, db)
    stats = await calculate_stats(db, user, int(user["default_stats_period"]))
    await message.answer(format_stats_message(stats), reply_markup=period_keyboard("stats_period"))


@router.callback_query(F.data.startswith("stats_period:"))
async def stats_period_callback(callback: CallbackQuery, db: Database) -> None:
    user = await ensure_callback_user(callback, db)
    days = int(callback.data.split(":", 1)[1])  # type: ignore[union-attr]
    stats = await calculate_stats(db, user, days)
    await callback.message.edit_text(format_stats_message(stats), reply_markup=period_keyboard("stats_period"))  # type: ignore[union-attr]
    await callback.answer()
