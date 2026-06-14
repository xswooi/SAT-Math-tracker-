from __future__ import annotations

import logging
import sys

from telegram.ext import ApplicationBuilder

from config import BOT_TOKEN
from database import init_db
from handlers import add, charts, export_import, messages, road, score, settings, start, stats, today


def build_application():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is missing. Create .env from .env.example and add your Telegram bot token.")

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Register more specific handlers before the generic text handler.
    start.register(application)
    today.register(application)
    add.register(application)
    road.register(application)
    stats.register(application)
    charts.register(application)
    score.register(application)
    settings.register(application)
    export_import.register(application)
    messages.register(application)

    return application


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    logging.info("Initializing SQLite database...")
    init_db()
    logging.info("Building Telegram application...")
    application = build_application()
    logging.info("SAT Road to 800 bot is running. Waiting for Telegram updates...")
    application.run_polling(allowed_updates=None)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
