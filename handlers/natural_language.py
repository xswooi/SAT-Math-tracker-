from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from database import Database
from handlers.common import ensure_message_user
from keyboards.main_menu import main_menu_keyboard
from keyboards.progress_buttons import progress_keyboard
from services.level_service import level_up_message
from services.parser_service import parse_progress_text
from services.progress_service import format_today_message, get_or_create_today_entry, set_today_entry, today_in_timezone, total_solved

router = Router()


@router.message(F.text)
async def natural_language(message: Message, db: Database) -> None:
    text = (message.text or "").strip()
    if not text or text.startswith("/"):
        return

    user = await ensure_message_user(message, db)
    parsed = parse_progress_text(text)
    if not parsed.has_anything:
        await message.answer(
            "I could not parse that yet. Try:\n"
            "<code>today 10 problems, 7 first try, 3 after explanation, topic geometry</code>\n"
            "or use the buttons below.",
            reply_markup=main_menu_keyboard(),
        )
        return

    old_entry = await get_or_create_today_entry(db, user)
    solved = parsed.solved_problems
    first = parsed.first_try
    after = parsed.after_explanation

    # If the user only gives quality split, infer solved = first + after.
    if solved is None and (first is not None or after is not None):
        inferred = (first if first is not None else old_entry["first_try"] or 0) + (
            after if after is not None else old_entry["after_explanation"] or 0
        )
        solved = max(int(old_entry["solved_problems"] or 0), int(inferred))

    try:
        previous_total = await total_solved(db, user["user_id"])
        if parsed.sat_score is not None:
            if not (200 <= parsed.sat_score <= 800):
                await message.answer("SAT Math score must be between 200 and 800.")
                return
            day = today_in_timezone(user["timezone"]).isoformat()
            await db.add_sat_score(user["user_id"], day, parsed.sat_score)

        entry = await set_today_entry(
            db=db,
            user=user,
            solved_problems=solved,
            first_try=first,
            after_explanation=after,
            topic_of_day=parsed.topic_of_day,
            sat_score=parsed.sat_score,
        )
    except ValueError as exc:
        await message.answer(str(exc))
        return

    await message.answer("Saved.\n\n" + format_today_message(entry, user), reply_markup=progress_keyboard())
    msg = level_up_message(previous_total, await total_solved(db, user["user_id"]))
    if msg:
        await message.answer(msg)
