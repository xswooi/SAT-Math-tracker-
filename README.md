# SAT Road to 800

A Telegram bot for tracking SAT Math preparation with simple daily logging, a Duolingo-style progress road, statistics, charts, JSON export/import, and motivational levels.

## Features

- Natural language input in English, Ukrainian, and simple mixed phrases
- Button-based daily editing
- SQLite persistent storage
- Multi-user support
- Daily upsert: sending progress twice on the same day updates that date instead of duplicating it
- Progress road with day statuses
- Statistics for 5/7/14/30/90 days
- Matplotlib charts sent as Telegram images
- SAT Math score tracking
- JSON export/import
- User settings

## Project structure

```text
sat_road_to_800/
  main.py
  config.py
  database.py
  requirements.txt
  .env.example
  handlers/
    start.py
    today.py
    add.py
    road.py
    stats.py
    charts.py
    score.py
    settings.py
    export_import.py
    messages.py
  services/
    progress_service.py
    stats_service.py
    chart_service.py
    parser_service.py
    level_service.py
    export_service.py
  keyboards/
    main_menu.py
    progress_buttons.py
    settings_buttons.py
  models/
    user.py
    daily_entry.py
    sat_score.py
```

## Create a Telegram bot with BotFather

1. Open Telegram and search for `@BotFather`.
2. Send `/newbot`.
3. Choose the display name, for example `SAT Road to 800`.
4. Choose a unique username ending in `bot`, for example `sat_road_to_800_bot`.
5. Copy the token. Treat it like a password.

## Install locally

Python 3.10+ is recommended.

```bash
cd sat_road_to_800
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## Add token to `.env`

```bash
cp .env.example .env
```

Then edit `.env`:

```env
BOT_TOKEN=123456789:your_real_token_here
DB_PATH=sat_road_to_800.sqlite3
DEFAULT_TIMEZONE=Europe/Kyiv
```

## Run the bot

```bash
python main.py
```

Then open your bot in Telegram and send `/start`.

## Natural language examples

```text
today 10 problems, 7 first try, 3 after explanation, topic geometry
10 задач, 6 з першого разу, 4 після пояснення, тема algebra
SAT score 680
сьогодні SAT 720
```

## Commands

- `/start` — intro and main menu
- `/today` — today’s progress
- `/day` — edit today with buttons
- `/add` — quick add/subtract buttons
- `/road` — Duolingo-style road
- `/stats` — default period statistics
- `/stats 5`, `/stats 7`, `/stats 14`, `/stats 30`, `/stats 90`
- `/charts` — default period charts
- `/charts 5`, `/charts 7`, `/charts 14`, `/charts 30`, `/charts 90`
- `/score` or `/score 680` — add SAT Math score
- `/settings` — daily goal, timezone, language, default stats period, target score
- `/export` — export JSON
- `/import` — import JSON
- `/reset` — reset all data after confirmation

## Validation rules

- `solved_problems >= 0`
- `first_try >= 0`
- `after_explanation >= 0`
- `first_try + after_explanation <= solved_problems`
- SAT Math score must be between 200 and 800
- statistics and chart periods must be at least 5 days

## Notes

This bot uses long polling, which is easiest for local development. For deployment, you can run the same code on a VPS, Railway, Render, Fly.io, or similar service. Keep the `.env` file private and never commit the real bot token.
