from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, FSInputFile, Message

from database import Database
from handlers.common import ensure_callback_user, ensure_message_user
from keyboards.progress_buttons import period_keyboard
from services.chart_service import generate_charts
from services.stats_service import MIN_PERIOD

router = Router()


def parse_chart_period(args: str | None, default: int) -> tuple[int | None, str | None]:
    if not args:
        return default, None
    for part in args.split():
        if part.isdigit():
            days = int(part)
            if days < MIN_PERIOD:
                return None, "Minimum chart period is 5 days. Try /charts 5 or /charts 7."
            return days, None
    return default, None


async def send_charts(message: Message, db: Database, user: dict, days: int) -> None:
    await message.answer(f"Charts — last <b>{days}</b> days", reply_markup=period_keyboard("charts_period"))
    files = await generate_charts(db, user, days, db.config.charts_dir)
    captions = [
        "Problems solved per day",
        "First try rate over time",
        "SAT Math score over time",
        "Topic distribution",
        "Completion status",
    ]
    for path, caption in zip(files, captions, strict=False):
        await message.answer_photo(FSInputFile(path), caption=caption)


@router.message(Command("charts"))
async def charts_command(message: Message, db: Database, command: CommandObject) -> None:
    user = await ensure_message_user(message, db)
    period, error = parse_chart_period(command.args, int(user["default_stats_period"]))
    if error:
        await message.answer(error)
        return
    assert period is not None
    await send_charts(message, db, user, period)


@router.message(F.text == "Charts")
async def charts_menu(message: Message, db: Database) -> None:
    user = await ensure_message_user(message, db)
    await send_charts(message, db, user, int(user["default_stats_period"]))


@router.callback_query(F.data.startswith("charts_period:"))
async def charts_period_callback(callback: CallbackQuery, db: Database) -> None:
    user = await ensure_callback_user(callback, db)
    days = int(callback.data.split(":", 1)[1])  # type: ignore[union-attr]
    await callback.answer("Generating charts")
    if callback.message:
        await send_charts(callback.message, db, user, days)
