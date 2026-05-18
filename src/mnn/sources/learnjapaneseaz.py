"""Scrape Minna no Nihongo vocab lessons from learnjapaneseaz.com."""
import re
import time
from typing import Iterator

import requests
from bs4 import BeautifulSoup

from mnn import log
from mnn.paths import CACHE
from mnn.util.io import skip_if_present, write_json

logger = log.get(__name__)

LESSON_URL = "https://learnjapaneseaz.com/minna-no-nihongo-lesson-{n}-vocabulary.html"
HEADERS = {"User-Agent": "Mozilla/5.0"}


def scrape_lesson(n: int) -> list[dict]:
    r = requests.get(LESSON_URL.format(n=n), headers=HEADERS, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    rows: list[dict] = []
    for table in soup.find_all("table"):
        for tr in table.find_all("tr"):
            cells = [c.get_text("", strip=True) for c in tr.find_all(["td", "th"])]
            if len(cells) < 4 or not re.match(r"^\d+$", cells[0]):
                continue
            rows.append({"no": cells[0], "kana": cells[1], "kanji": cells[2], "meaning": cells[3]})
    return rows


def scrape_all(force: bool = False, sleep: float = 0.3) -> Iterator[tuple[int, int]]:
    CACHE.mkdir(parents=True, exist_ok=True)
    for n in range(1, 51):
        dst = CACHE / f"lesson_{n}.json"
        if not force and skip_if_present(dst):
            logger.info("L%d: cached", n)
            yield n, 0
            continue
        try:
            rows = scrape_lesson(n)
        except Exception as e:
            logger.error("L%d failed: %s", n, e)
            time.sleep(2)
            continue
        write_json(dst, rows)
        logger.info("L%d: %d rows", n, len(rows))
        yield n, len(rows)
        time.sleep(sleep)
