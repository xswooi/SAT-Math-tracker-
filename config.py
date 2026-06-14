from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class Config:
    bot_token: str
    database_path: str = str(BASE_DIR / "data" / "sat_road.sqlite3")
    charts_dir: str = str(BASE_DIR / "charts")
    exports_dir: str = str(BASE_DIR / "exports")
    default_timezone: str = "Europe/Kyiv"
    default_daily_goal: int = 10
    default_stats_period: int = 7
    default_target_score: int = 800


def load_config() -> Config:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError(
            "BOT_TOKEN is missing. Create a .env file with BOT_TOKEN=your_telegram_bot_token"
        )
    return Config(bot_token=token)
