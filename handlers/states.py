from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class ScoreStates(StatesGroup):
    waiting_for_score = State()


class SettingsStates(StatesGroup):
    waiting_for_daily_goal = State()
    waiting_for_timezone = State()
    waiting_for_default_stats_period = State()
    waiting_for_target_score = State()


class ImportStates(StatesGroup):
    waiting_for_json_file = State()
