"""KanjiVG SVG stroke order data."""
import io
import zipfile
from pathlib import Path

import requests

from mnn import log
from mnn.paths import DATA_KANJIVG, DATA_KANJIVG_KANJI

logger = log.get(__name__)

URL = "https://github.com/KanjiVG/kanjivg/releases/download/r20240807/kanjivg-20240807-main.zip"


def fetch() -> None:
    DATA_KANJIVG.mkdir(parents=True, exist_ok=True)
    DATA_KANJIVG_KANJI.mkdir(parents=True, exist_ok=True)
    existing = len(list(DATA_KANJIVG_KANJI.glob("*.svg")))
    if existing > 5000:
        logger.info("kanjivg: skip (%d svgs present)", existing)
        return
    logger.info("downloading kanjivg release zip")
    r = requests.get(URL, timeout=180)
    r.raise_for_status()
    logger.info("extracting %d bytes", len(r.content))
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        for name in z.namelist():
            if not name.endswith(".svg") or "/" not in name:
                continue
            base = Path(name).name
            if "-" in base.replace(".svg", ""):
                continue
            with z.open(name) as f:
                (DATA_KANJIVG_KANJI / base).write_bytes(f.read())
    logger.info("kanjivg: %d svgs extracted", len(list(DATA_KANJIVG_KANJI.glob("*.svg"))))


def svg_path(cp: int) -> Path:
    return DATA_KANJIVG_KANJI / f"{cp:05x}.svg"
