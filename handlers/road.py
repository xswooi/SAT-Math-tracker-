from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from database import Database
from handlers.common import ensure_message_user
from services.level_service import format_level
from services.progress_service import current_streak, date_range, status_for_entry, today_in_timezone, total_solved

router = Router()


@router.message(Command("road"))
@router.message(F.text == "Road")
async def road(message: Message, db: Database) -> None:
    user = await ensure_message_user(message, db)
    today = today_in_timezone(user["timezone"])
    days = date_range(today, 7)
    entries = await db.list_entries(user["user_id"], days[0].isoformat(), days[-1].isoformat())
    by_date = {e["date"]: e for e in entries}
    goal = int(user["daily_goal"])
    nodes = [status_for_entry(by_date.get(d.isoformat()), goal, d, today).emoji for d in days]
    total = await total_solved(db, user["user_id"])
    streak = await current_streak(db, user)
    await message.answer(
        "<b>SAT Road to 800</b>\n\n"
        + " → ".join(nodes)
        + "\n\n"
        + f"Current streak: <b>{streak}</b> days\n"
        + f"Total solved: <b>{total}</b> problems\n"
        + f"Level: <b>{format_level(total)}</b>\n\n"
        + "Legend: ⭕ no data · 🟡 partial · ✅ completed · 🔥 overachieved · ⭐ high quality · ❌ missed"
    )
