from __future__ import annotations

import re

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from database import Database
from handlers.common import ensure_message_user
from handlers.states import ScoreStates
from services.level_service import level_up_message
from services.progress_service import format_today_message, get_or_create_today_entry, today_in_timezone, total_solved

router = Router()


def extract_score(text: str | None) -> int | None:
    if not text:
        return None
    m = re.search(r"\b(\d{3})\b", text)
    if not m:
        return None
    score = int(m.group(1))
    if 200 <= score <= 800:
        return score
    return None


@router.message(Command("score"))
@router.message(F.text == "Add SAT Score")
async def score_command(message: Message, db: Database, state: FSMContext) -> None:
    user = await ensure_message_user(message, db)
    score = extract_score(message.text)
    if score is None and message.text and message.text.startswith("/score") and len(message.text.split()) > 1:
        await message.answer("SAT Math score must be between 200 and 800. Try: /score 680")
        return
    if score is None:
        await state.set_state(ScoreStates.waiting_for_score)
        await message.answer("Send SAT Math score from 200 to 800.")
        return
    previous_total = await total_solved(db, user["user_id"])
    day = today_in_timezone(user["timezone"]).isoformat()
    await db.add_sat_score(user["user_id"], day, score)
    entry = await get_or_create_today_entry(db, user)
    await message.answer(f"SAT Math score saved: <b>{score}</b>\n\n" + format_today_message(entry, user))
    msg = level_up_message(previous_total, await total_solved(db, user["user_id"]))
    if msg:
        await message.answer(msg)


@router.message(ScoreStates.waiting_for_score)
async def score_state(message: Message, db: Database, state: FSMContext) -> None:
    user = await ensure_message_user(message, db)
    score = extract_score(message.text)
    if score is None:
        await message.answer("Invalid score. Enter a SAT Math score between 200 and 800, for example: 720")
        return
    day = today_in_timezone(user["timezone"]).isoformat()
    await db.add_sat_score(user["user_id"], day, score)
    await state.clear()
    entry = await get_or_create_today_entry(db, user)
    await message.answer(f"SAT Math score saved: <b>{score}</b>\n\n" + format_today_message(entry, user))
