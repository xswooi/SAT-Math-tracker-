from __future__ import annotations

from . import add, charts, export_import, natural_language, road, score, settings, start, stats, today

routers = [
    start.router,
    today.router,
    add.router,
    road.router,
    stats.router,
    charts.router,
    score.router,
    settings.router,
    export_import.router,
    natural_language.router,
]
