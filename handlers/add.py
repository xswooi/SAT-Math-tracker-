from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import Database
from handlers.common import ensure_callback_user, ensure_message_user
from handlers.states import ScoreStates
from keyboards.progress_buttons import progress_keyboard, topic_keyboard
from services.level_service import level_up_message
from services.progress_service import apply_delta, format_today_message, get_or_create_today_entry, set_topic, total_solved

router = Router()


@router.message(Command("add"))
@router.message(F.text == "Add Progress")
async def add_menu(message: Message, db: Database) -> None:
    user = await ensure_message_user(message, db)
    entry = await get_or_create_today_entry(db, user)
    await message.answer(format_today_message(entry, user), reply_markup=progress_keyboard())


@router.callback_query(F.data.startswith("delta:"))
async def delta_progress(callback: CallbackQuery, db: Database) -> None:
    user = await ensure_callback_user(callback, db)
    previous_total = await total_solved(db, user["user_id"])
    _, field, raw_delta = callback.data.split(":")  # type: ignore[union-attr]
    try:
        entry = await apply_delta(db, user, field, int(raw_delta))
    except ValueError as exc:
        await callback.answer(str(exc), show_alert=True)
        return
    await callback.message.edit_text(format_today_message(entry, user), reply_markup=progress_keyboard())  # type: ignore[union-attr]
    await callback.answer("Updated")
    new_total = await total_solved(db, user["user_id"])
    msg = level_up_message(previous_total, new_total)
    if msg and callback.message:
        await callback.message.answer(msg)


@router.callback_query(F.data == "topic_menu")
async def show_topics(callback: CallbackQuery) -> None:
    await callback.message.edit_text("Choose today’s topic:", reply_markup=topic_keyboard())  # type: ignore[union-attr]
    await callback.answer()


@router.callback_query(F.data == "back_progress")
async def back_to_progress(callback: CallbackQuery, db: Database) -> None:
    user = await ensure_callback_user(callback, db)
    entry = await get_or_create_today_entry(db, user)
    await callback.message.edit_text(format_today_message(entry, user), reply_markup=progress_keyboard())  # type: ignore[union-attr]
    await callback.answer()


@router.callback_query(F.data.startswith("topic:"))
async def choose_topic(callback: CallbackQuery, db: Database) -> None:
    user = await ensure_callback_user(callback, db)
    topic = callback.data.split(":", 1)[1]  # type: ignore[union-attr]
    try:
        entry = await set_topic(db, user, topic)
    except ValueError as exc:
        await callback.answer(str(exc), show_alert=True)
        return
    await callback.message.edit_text(format_today_message(entry, user), reply_markup=progress_keyboard())  # type: ignore[union-attr]
    await callback.answer(f"Topic set: {topic}")


@router.callback_query(F.data == "score_prompt")
async def score_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ScoreStates.waiting_for_score)
    await callback.message.answer("Send SAT Math score from 200 to 800.")  # type: ignore[union-attr]
    await callback.answer()
