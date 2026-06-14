from __future__ import annotations

import io
import json
from datetime import datetime
from pathlib import Path

from aiogram import F, Bot, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

from database import Database
from handlers.common import ensure_callback_user, ensure_message_user
from handlers.states import ImportStates
from keyboards.progress_buttons import reset_confirm_keyboard
from keyboards.main_menu import main_menu_keyboard

router = Router()


@router.message(Command("export"))
async def export_data(message: Message, db: Database) -> None:
    user = await ensure_message_user(message, db)
    data = await db.export_user_data(user["user_id"])
    out_dir = Path(db.config.exports_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = out_dir / f"sat_road_export_{user['user_id']}_{stamp}.json"
    path.write_text(Database.dumps_pretty(data), encoding="utf-8")
    await message.answer_document(FSInputFile(path), caption="Your SAT Road to 800 data export.")


@router.message(Command("import"))
async def import_data(message: Message, db: Database, state: FSMContext) -> None:
    await ensure_message_user(message, db)
    await state.set_state(ImportStates.waiting_for_json_file)
    await message.answer("Send a JSON export file. Existing days with the same date will be updated.")


@router.message(ImportStates.waiting_for_json_file, F.document)
async def import_json_file(message: Message, bot: Bot, db: Database, state: FSMContext) -> None:
    user = await ensure_message_user(message, db)
    document = message.document
    if document is None:
        await message.answer("Please send a JSON file.")
        return
    if document.file_name and not document.file_name.lower().endswith(".json"):
        await message.answer("Please send a .json file.")
        return

    buffer = io.BytesIO()
    tg_file = await bot.get_file(document.file_id)
    await bot.download_file(tg_file.file_path, destination=buffer)  # type: ignore[arg-type]
    buffer.seek(0)

    try:
        data = json.loads(buffer.read().decode("utf-8"))
    except Exception:
        await message.answer("Could not read this JSON file. Please check the export format.")
        return

    imported_days, imported_scores = await db.import_user_data(user["user_id"], data)
    await state.clear()
    await message.answer(
        f"Import completed.\nDays imported/updated: <b>{imported_days}</b>\nSAT scores imported: <b>{imported_scores}</b>",
        reply_markup=main_menu_keyboard(),
    )


@router.message(ImportStates.waiting_for_json_file)
async def import_waiting_fallback(message: Message) -> None:
    await message.answer("Send the export as a JSON document, or use /start to return to the menu.")


@router.message(Command("reset"))
async def reset(message: Message, db: Database) -> None:
    await ensure_message_user(message, db)
    await message.answer(
        "This will delete all SAT Road progress, SAT scores, and reset settings. Are you sure?",
        reply_markup=reset_confirm_keyboard(),
    )


@router.callback_query(F.data == "reset_confirm")
async def reset_confirm(callback: CallbackQuery, db: Database) -> None:
    user = await ensure_callback_user(callback, db)
    await db.reset_user_data(user["user_id"])
    await callback.message.edit_text("All data has been reset.")  # type: ignore[union-attr]
    await callback.message.answer("Main menu:", reply_markup=main_menu_keyboard())  # type: ignore[union-attr]
    await callback.answer()


@router.callback_query(F.data == "reset_cancel")
async def reset_cancel(callback: CallbackQuery) -> None:
    await callback.message.edit_text("Reset cancelled.")  # type: ignore[union-attr]
    await callback.answer()
