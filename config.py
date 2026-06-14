from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "sat_road_to_800.sqlite3"))
DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE", "Europe/Kyiv")
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "English")
DEFAULT_DAILY_GOAL = int(os.getenv("DEFAULT_DAILY_GOAL", "10"))
DEFAULT_STATS_PERIOD = int(os.getenv("DEFAULT_STATS_PERIOD", "7"))
DEFAULT_TARGET_SCORE = int(os.getenv("DEFAULT_TARGET_SCORE", "800"))

CHART_DIR = BASE_DIR / "charts"
EXPORT_DIR = BASE_DIR / "exports"
IMPORT_DIR = BASE_DIR / "imports"

ALLOWED_TOPICS = ["Algebra", "Geometry", "Functions", "Data Analysis", "Mixed", "Other"]
ALLOWED_LANGUAGES = ["English", "Ukrainian"]
MIN_STATS_PERIOD = 5
ALLOWED_PERIODS = [5, 7, 14, 30, 90]

CHART_DIR.mkdir(exist_ok=True)
EXPORT_DIR.mkdir(exist_ok=True)
IMPORT_DIR.mkdir(exist_ok=True)
