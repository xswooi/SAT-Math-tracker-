from __future__ import annotations

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from keyboards.main_menu import main_menu_keyboard
from services.progress_service import ensure_user

START_TEXT = """SAT Road to 800

Track SAT Math practice without logging every problem separately.

You can send progress naturally, for example:
10 problems, 7 first try, 3 after explanation, topic geometry
10 задач, 6 з першого разу, 4 після пояснення, тема algebra
SAT score 680

Main commands:
/today — today’s progress
/add — quick buttons
/road — progress road
/stats — statistics
/charts — charts
/score — add SAT Math score
/settings — change preferences
/export — export JSON
/import — import JSON
/reset — reset data
"""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ensure_user(update.effective_user)
    await update.effective_message.reply_text(START_TEXT, reply_markup=main_menu_keyboard())


def register(app: Application) -> None:
    app.add_handler(CommandHandler("start", start))
