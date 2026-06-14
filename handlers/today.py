from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from database import Database
from handlers.common import ensure_message_user
from keyboards.progress_buttons import progress_keyboard
from services.progress_service import format_today_message, get_or_create_today_entry

router = Router()


@router.message(Command("today"))
@router.message(F.text == "Today")
async def today(message: Message, db: Database) -> None:
    user = await ensure_message_user(message, db)
    entry = await get_or_create_today_entry(db, user)
    await message.answer(format_today_message(entry, user), reply_markup=progress_keyboard())


@router.message(Command("day"))
async def day(message: Message, db: Database) -> None:
    user = await ensure_message_user(message, db)
    entry = await get_or_create_today_entry(db, user)
    await message.answer(
        format_today_message(entry, user) + "\n\nUse the buttons below to edit today.",
        reply_markup=progress_keyboard(),
    )
