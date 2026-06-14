from __future__ import annotations

from pathlib import Path

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from config import IMPORT_DIR
from handlers.common import current_user
from keyboards.settings_buttons import reset_confirm_keyboard
from services.export_service import export_user_data, import_user_data, reset_user_data


async def export_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = await current_user(update)
    path = export_user_data(user["user_id"])
    await update.effective_message.reply_document(document=path.open("rb"), filename=path.name)


async def import_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await current_user(update)
    context.user_data["pending"] = "import_json"
    await update.effective_message.reply_text("Send a JSON export file from this bot. Existing days with the same date will be updated.")


async def import_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get("pending") != "import_json":
        return
    user = await current_user(update)
    document = update.effective_message.document
    if not document or not (document.file_name or "").lower().endswith(".json"):
        await update.effective_message.reply_text("Please send a .json file exported from this bot.")
        return

    tg_file = await document.get_file()
    path = IMPORT_DIR / f"import_{user['user_id']}_{document.file_unique_id}.json"
    await tg_file.download_to_drive(custom_path=path)
    try:
        result = import_user_data(user["user_id"], Path(path))
        await update.effective_message.reply_text(
            f"Import complete.\nEntries imported: {result['entries']}\nSAT scores imported: {result['scores']}"
        )
    except Exception as exc:
        await update.effective_message.reply_text(f"Import failed: {exc}")
    finally:
        context.user_data.pop("pending", None)


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await current_user(update)
    await update.effective_message.reply_text(
        "This will delete all daily entries and SAT scores for your account. Are you sure?",
        reply_markup=reset_confirm_keyboard(),
    )


async def reset_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user = await current_user(update)
    action = query.data.split(":")[-1]
    if action == "confirm":
        reset_user_data(user["user_id"])
        await query.edit_message_text("All progress data has been reset.")
    else:
        await query.edit_message_text("Reset cancelled.")


def register(app: Application) -> None:
    app.add_handler(CommandHandler("export", export_data))
    app.add_handler(CommandHandler("import", import_data))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CallbackQueryHandler(reset_callback, pattern=r"^reset:"))
    app.add_handler(MessageHandler(filters.Document.FileExtension("json"), import_document))
