from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database import Database
from handlers.common import ensure_message_user
from keyboards.main_menu import main_menu_keyboard

router = Router()

START_TEXT = """
<b>SAT Road to 800</b>

Track SAT Math prep in seconds:
• daily solved problems
• first-try answers
• solved after explanation
• optional topic
• optional SAT Math score

Send text like:
<code>today 10 problems, 7 first try, 3 after explanation, topic geometry</code>
<code>10 задач, 6 з першого разу, 4 після пояснення, тема algebra</code>
<code>SAT score 680</code>

Daily goal is 10 problems by default. Use /settings to change it.
""".strip()


@router.message(Command("start"))
async def start(message: Message, db: Database) -> None:
    await ensure_message_user(message, db)
    await message.answer(START_TEXT, reply_markup=main_menu_keyboard())
