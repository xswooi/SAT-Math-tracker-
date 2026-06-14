from __future__ import annotations

import re
from dataclasses import dataclass

from services.progress_service import normalize_topic


@dataclass(slots=True)
class ParsedProgress:
    solved_problems: int | None = None
    first_try: int | None = None
    after_explanation: int | None = None
    topic_of_day: str | None = None
    sat_score: int | None = None

    @property
    def has_anything(self) -> bool:
        return any(
            value is not None
            for value in [
                self.solved_problems,
                self.first_try,
                self.after_explanation,
                self.topic_of_day,
                self.sat_score,
            ]
        )


SCORE_RE = re.compile(r"(?:sat\s*(?:math\s*)?(?:score)?|score|бал|результат|sat)\D{0,10}(\d{3})", re.I)
SOLVED_RE = re.compile(
    r"(\d{1,3})\s*(?:problems?|tasks?|examples?|задач(?:і|а|)?|приклад(?:ів|и|)?|реш(?:ив|ено)?|solved)",
    re.I,
)
FIRST_RE = re.compile(
    r"(\d{1,3})\s*(?:first\s*try|on\s*the\s*first\s*try|з\s*перш(?:ого|ої)\s*раз(?:у|а)|с\s*перв(?:ого|ой)\s*раз(?:а|у))",
    re.I,
)
AFTER_RE = re.compile(
    r"(\d{1,3})\s*(?:after\s*(?:explanation|hint|help)|після\s*пояснення|после\s*объяснения|з\s*поясненням|with\s*explanation)",
    re.I,
)
TOPIC_RE = re.compile(r"(?:topic|тема)\s*[:\-]?\s*([A-Za-zА-Яа-яІіЇїЄєҐґ ]+)", re.I)


def parse_progress_text(text: str) -> ParsedProgress:
    text = text.strip()
    parsed = ParsedProgress()

    # SAT scores are multiples of 10 from 200 to 800, but accept any integer in that range.
    score_match = SCORE_RE.search(text)
    if score_match:
        score = int(score_match.group(1))
        if 200 <= score <= 800:
            parsed.sat_score = score

    solved_match = SOLVED_RE.search(text)
    if solved_match:
        parsed.solved_problems = int(solved_match.group(1))
    else:
        # Common compact input: "10 задач, 6 з першого, 4 після...".
        if re.search(r"\b(today|сьогодні|сегодня)\b", text, re.I):
            first_number = re.search(r"\b(\d{1,3})\b", text)
            if first_number and not parsed.sat_score:
                parsed.solved_problems = int(first_number.group(1))

    first_match = FIRST_RE.search(text)
    if first_match:
        parsed.first_try = int(first_match.group(1))

    after_match = AFTER_RE.search(text)
    if after_match:
        parsed.after_explanation = int(after_match.group(1))

    topic_match = TOPIC_RE.search(text)
    if topic_match:
        topic = normalize_topic(topic_match.group(1).strip())
        if topic:
            parsed.topic_of_day = topic
    else:
        for possible in [
            "algebra",
            "geometry",
            "functions",
            "data analysis",
            "mixed",
            "other",
            "алгебра",
            "геометрія",
            "функції",
            "аналіз даних",
            "змішане",
            "інше",
        ]:
            if possible in text.lower():
                parsed.topic_of_day = normalize_topic(possible)
                break

    return parsed
