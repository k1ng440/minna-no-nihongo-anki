"""mnn doctor — environment + data sanity checks."""
import socket
from urllib.parse import urlparse

import requests

from mnn import log
from mnn.config import settings
from mnn.paths import ASSETS, CACHE, DATA_KANJIUM, DATA_KANJIVG_KANJI, DATA_TATOEBA

logger = log.get(__name__)


def _check(label: str, ok: bool, detail: str = "") -> None:
    mark = "✓" if ok else "✗"
    logger.info("[%s] %s%s", mark, label, f" — {detail}" if detail else "")


def run() -> None:
    s = settings()
    _check(".env loaded", True, f"LLM_MODEL={s.llm_model}")

    try:
        host = urlparse(s.llm_api_url).hostname or "localhost"
        port = urlparse(s.llm_api_url).port or 11434
        with socket.create_connection((host, port), timeout=3):
            _check("LLM endpoint", True, s.llm_api_url)
    except Exception as e:
        _check("LLM endpoint", False, f"{s.llm_api_url} unreachable: {e}")

    try:
        import edge_tts  # noqa: F401
        _check("edge-tts", True)
    except Exception as e:
        _check("edge-tts", False, str(e))

    _check("KanjiVG", DATA_KANJIVG_KANJI.exists() and len(list(DATA_KANJIVG_KANJI.glob("*.svg"))) > 5000,
           f"{len(list(DATA_KANJIVG_KANJI.glob('*.svg'))) if DATA_KANJIVG_KANJI.exists() else 0} svgs")
    _check("kanjium accents", (DATA_KANJIUM / "accents.txt").exists())
    _check("Tatoeba jpn", (DATA_TATOEBA / "jpn_sentences.tsv").exists())
    _check("Tatoeba eng", (DATA_TATOEBA / "eng_sentences.tsv").exists())
    _check("Tatoeba indices", (DATA_TATOEBA / "jpn_indices.csv").exists())
    _check("Cleaned cache", len(list(CACHE.glob("lesson_*.cleaned.json"))) >= 50,
           f"{len(list(CACHE.glob('lesson_*.cleaned.json')))} lessons")
    _check("Cover asset", (ASSETS / "cover.png").exists())
    mascots = sum((ASSETS / f"mascot_t{i}.svg").exists() for i in range(1, 6))
    _check("Mascots", mascots == 5, f"{mascots}/5")
    _check("Pixabay enabled", s.pixabay_enabled, "set PIXABAY_ENABLED=1 to use")
