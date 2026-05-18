"""Generate 4-option multiple-choice quiz cards per lesson."""
import random

from mnn import log
from mnn.paths import CACHE, CACHE_QUIZ
from mnn.util.io import read_json, write_json

logger = log.get(__name__)


def _for_direction(rows: list[dict], direction: str) -> list[dict]:
    out = []
    for row in rows:
        rnd = random.Random(row["guid"] + direction)
        pool = [r for r in rows if r["guid"] != row["guid"] and r["meaning"] != row["meaning"]]
        if len(pool) < 3:
            continue
        distractors = rnd.sample(pool, 3)
        choices_data = distractors + [row]
        rnd.shuffle(choices_data)
        correct_idx = choices_data.index(row)
        if direction == "jp2en":
            prompt = row["kanji"] or row["kana"]
            choices = [c["meaning"] for c in choices_data]
        else:
            prompt = row["meaning"]
            choices = [(c["kanji"] or c["kana"]) for c in choices_data]
        out.append({
            "guid": f"quiz-{direction}-{row['guid']}",
            "prompt": prompt,
            "choices": choices,
            "correct_idx": correct_idx,
            "correct_class": f"correct-c{correct_idx + 1}",
            "lesson": row["lesson"],
            "direction": direction,
        })
    return out


def run() -> None:
    total = 0
    for n in range(1, 51):
        cleaned = CACHE / f"lesson_{n}.cleaned.json"
        if not cleaned.exists():
            continue
        rows = [r for r in read_json(cleaned) if r["meaning"].strip()]
        quiz = _for_direction(rows, "jp2en") + _for_direction(rows, "en2jp")
        write_json(CACHE_QUIZ / f"lesson_{n}.json", quiz)
        total += len(quiz)
        logger.info("L%d: %d quiz cards", n, len(quiz))
    logger.info("quiz total: %d", total)
