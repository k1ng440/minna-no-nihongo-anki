"""Validate scraped rows; write cleaned cache."""
import re
import time

import requests
from bs4 import BeautifulSoup

from mnn import log
from mnn.paths import CACHE
from mnn.util.hashing import audio_filename
from mnn.util.io import read_json, write_json

logger = log.get(__name__)

HIRAGANA = r"぀-ゟ"
KATAKANA = r"゠-ヿ"
CJK = r"㐀-鿿"

MANUAL_OVERRIDES: dict[tuple[int, str], dict] = {
    (30, "6"): {"kanji": "相談します", "kana": "そうだんします", "meaning": "consult"},
    (2, "13"): {"kanji": "名刺", "kana": "めいし", "meaning": "business card"},
}


def looks_corrupt(kanji: str, kana: str) -> bool:
    if not kanji:
        return False
    m = re.search(rf"([{HIRAGANA}]+)$", kanji)
    okuri = m.group(1) if m else ""
    if okuri and not kana.endswith(okuri):
        return True
    body = re.sub(rf"[{HIRAGANA}{KATAKANA}]", "", kanji)
    if len(body) > 5:
        return True
    if body and not re.fullmatch(rf"[{CJK}]+", body):
        return True
    return False


def _rescrape(n: int) -> list[dict]:
    url = f"https://learnjapaneseaz.com/minna-no-nihongo-lesson-{n}-vocabulary.html"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    rows = []
    for table in soup.find_all("table"):
        for tr in table.find_all("tr"):
            cells = [c.get_text("", strip=True) for c in tr.find_all(["td", "th"])]
            if len(cells) < 4 or not re.match(r"^\d+$", cells[0]):
                continue
            rows.append({"no": cells[0], "kana": cells[1], "kanji": cells[2], "meaning": cells[3]})
    return rows


def run(force: bool = False) -> None:
    flagged = 0
    total = 0
    for n in range(1, 51):
        src = CACHE / f"lesson_{n}.json"
        if not src.exists():
            continue
        dst = CACHE / f"lesson_{n}.cleaned.json"
        if dst.exists() and not force:
            existing = read_json(dst)
            total += len(existing)
            logger.info("L%d: cached cleaned (%d rows)", n, len(existing))
            continue
        rows = read_json(src)
        rescrape_cache: list[dict] | None = None
        cleaned = []
        for row in rows:
            kana = row["kana"].strip()
            kanji = row["kanji"].strip()
            meaning = row["meaning"].strip()
            no = row["no"]

            override = MANUAL_OVERRIDES.get((n, no))
            if override:
                flagged += 1
                kanji = override.get("kanji", kanji)
                kana = override.get("kana", kana)
                meaning = override.get("meaning", meaning)
            elif looks_corrupt(kanji, kana):
                flagged += 1
                if rescrape_cache is None:
                    logger.info("rescraping L%d", n)
                    try:
                        rescrape_cache = _rescrape(n)
                    except Exception as e:
                        logger.warning("rescrape failed: %s", e)
                        rescrape_cache = []
                    time.sleep(0.3)
                for r2 in rescrape_cache:
                    if r2["no"] == no and not looks_corrupt(r2["kanji"].strip(), r2["kana"].strip()):
                        kanji = r2["kanji"].strip()
                        kana = r2["kana"].strip()
                        meaning = r2["meaning"].strip()
                        break

            cleaned.append({
                "no": no,
                "lesson": n,
                "kana": kana,
                "kanji": kanji,
                "meaning": meaning,
                "audio": audio_filename(kana) if kana else "",
                "guid": f"mnn-l{n}-{no}-{kana}",
            })
            total += 1
        write_json(dst, cleaned)
    logger.info("clean done: %d rows total, %d flagged/overridden", total, flagged)
