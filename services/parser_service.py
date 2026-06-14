from __future__ import annotations

import re
from typing import Any

from config import ALLOWED_TOPICS

TOPIC_ALIASES = {
    "algebra": "Algebra",
    "алгебра": "Algebra",
    "geometry": "Geometry",
    "геометрія": "Geometry",
    "геометрия": "Geometry",
    "functions": "Functions",
    "function": "Functions",
    "функції": "Functions",
    "функции": "Functions",
    "data analysis": "Data Analysis",
    "data": "Data Analysis",
    "statistics": "Data Analysis",
    "статистика": "Data Analysis",
    "аналіз даних": "Data Analysis",
    "анализ данных": "Data Analysis",
    "mixed": "Mixed",
    "мікс": "Mixed",
    "змішана": "Mixed",
    "змішані": "Mixed",
    "микс": "Mixed",
    "other": "Other",
    "інше": "Other",
    "другое": "Other",
}

NUMBER = r"(?P<num>\d{1,4})"


def _find_number(patterns: list[str], text: str) -> int | None:
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.UNICODE)
        if match:
            return int(match.group("num"))
    return None


def parse_topic(text: str) -> str | None:
    lowered = text.lower()
    topic_match = re.search(r"(?:topic|тема)\s*[:\-]?\s*([a-zA-Zа-яА-ЯіїєґІЇЄҐ ]+)", lowered)
    if topic_match:
        raw = topic_match.group(1).strip().split(",")[0].strip()
        for alias, canonical in TOPIC_ALIASES.items():
            if alias in raw:
                return canonical

    # Fallback: topic name anywhere in the message.
    for alias, canonical in TOPIC_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", lowered, re.IGNORECASE | re.UNICODE):
            return canonical
    return None


def parse_sat_score(text: str) -> int | None:
    patterns = [
        r"(?:sat\s*(?:math)?\s*(?:score)?|score|бал|результат)\s*[:\-]?\s*(?P<num>\d{3})",
        r"(?P<num>\d{3})\s*(?:sat|балів|балла|score)",
    ]
    score = _find_number(patterns, text)
    if score is not None:
        return score
    return None


def parse_progress_text(text: str) -> dict[str, Any]:
    normalized = text.lower().replace("ё", "е")
    result: dict[str, Any] = {}

    solved_patterns = [
        rf"(?P<num>\d{{1,4}})\s*(?:math\s*)?(?:problems?|tasks?|questions?|задач(?:і|и|)?|приклад(?:ів|и|)?)",
        rf"(?:solved|розв(?:'|’)?язав|розв(?:'|’)?язано|решил|зробив)\s*(?P<num>\d{{1,4}})",
    ]
    first_try_patterns = [
        rf"(?P<num>\d{{1,4}})\s*(?:first\s*try|on\s*the\s*first\s*try|з\s*перш(?:ого|ої)\s*разу|з\s*першого|першого\s*разу|с\s*первого\s*раза)",
        rf"(?:first\s*try|з\s*перш(?:ого|ої)\s*разу|с\s*первого\s*раза)\s*(?P<num>\d{{1,4}})",
    ]
    after_patterns = [
        rf"(?P<num>\d{{1,4}})\s*(?:after\s*explanation|after\s*help|після\s*пояснення|після\s*підказки|после\s*объяснения|после\s*подсказки)",
        rf"(?:after\s*explanation|після\s*пояснення|после\s*объяснения)\s*(?P<num>\d{{1,4}})",
    ]

    solved = _find_number(solved_patterns, normalized)
    first_try = _find_number(first_try_patterns, normalized)
    after_explanation = _find_number(after_patterns, normalized)
    sat_score = parse_sat_score(normalized)
    topic = parse_topic(normalized)

    # Common compact input: "10, 7 first try, 3 after explanation".
    if solved is None and (first_try is not None or after_explanation is not None):
        first_number = re.search(r"(?P<num>\d{1,4})", normalized)
        if first_number:
            possible = int(first_number.group("num"))
            if possible not in {first_try, after_explanation, sat_score}:
                solved = possible

    if solved is not None:
        result["solved_problems"] = solved
    if first_try is not None:
        result["first_try"] = first_try
    if after_explanation is not None:
        result["after_explanation"] = after_explanation
    if topic is not None:
        result["topic_of_day"] = topic
    if sat_score is not None:
        result["sat_score"] = sat_score

    return result


def looks_like_progress(text: str) -> bool:
    return bool(parse_progress_text(text))
