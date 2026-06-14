# SAT Road to 800

A Telegram bot for tracking SAT Math preparation with daily progress, a Duolingo-style road, statistics, charts, JSON export/import, and settings.

## Features

- Natural language progress logging in English, Ukrainian, and simple mixed phrases.
- Button-based progress updates.
- One daily entry per user per date; repeated entries update the same day.
- SQLite persistent storage.
- Progress road with statuses: ⭕ 🟡 ✅ 🔥 ⭐ ❌.
- Statistics for 5+ days.
- Matplotlib charts sent as Telegram images.
- Multi-user support.
- JSON export/import.

## Project structure

```text
sat_road_to_800/
├── main.py
├── config.py
├── database.py
├── requirements.txt
├── .env.example
├── handlers/
├── services/
├── keyboards/
└── models/
```

## Create a Telegram bot with BotFather

1. Open Telegram.
2. Search for `@BotFather`.
3. Send `/newbot`.
4. Follow the instructions: choose a display name and a username ending in `bot`.
5. Copy the bot token.

## Configure environment

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env`:

```env
BOT_TOKEN=123456789:your_real_bot_token_here
```

## Install dependencies

Python 3.11+ is recommended.

```bash
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
# .venv\Scripts\activate       # Windows PowerShell
pip install -r requirements.txt
```

## Run locally

```bash
python main.py
```

Then open your bot in Telegram and send `/start`.

## Example inputs

```text
today 10 problems, 7 first try, 3 after explanation, topic geometry
10 задач, 6 з першого разу, 4 після пояснення, тема algebra
SAT score 680
сьогодні SAT 720
```

## Commands

- `/start` — main menu
- `/today` — today’s progress
- `/day` — edit today with buttons
- `/add` — quick button-based progress
- `/road` — recent-day SAT road
- `/stats` or `/stats 14` — statistics, minimum 5 days
- `/charts` or `/charts 30` — chart images, minimum 5 days
- `/score` — add SAT Math score
- `/settings` — daily goal, timezone, language, default period, target score
- `/export` — export JSON
- `/import` — import JSON
- `/reset` — reset after confirmation

## Notes

- The default timezone is `Europe/Kyiv`. Change it in `/settings` if needed.
- The default daily goal is 10 problems.
- The default target score is 800.
- The bot stores data in `data/sat_road.sqlite3`.
- Chart PNGs are generated into `charts/`.
