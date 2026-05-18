"""Canonical project directories."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "cache"
DATA = ROOT / "data"
AUDIO = ROOT / "audio"
AUDIO_SENT = ROOT / "audio_sent"
SVG = ROOT / "svg"
IMAGES = ROOT / "images"
ASSETS = ROOT / "assets"
DIST = ROOT / "dist"

CACHE_SENTENCES = CACHE / "sentences"
CACHE_MNEMONICS = CACHE / "mnemonics"
CACHE_QUIZ = CACHE / "quiz"
CACHE_PIXABAY = CACHE / "pixabay"

DATA_TATOEBA = DATA / "tatoeba"
DATA_KANJIVG = DATA / "kanjivg"
DATA_KANJIVG_KANJI = DATA_KANJIVG / "kanji"
DATA_KANJIUM = DATA / "kanjium"


def ensure_dirs() -> None:
    for d in (CACHE, DATA, AUDIO, AUDIO_SENT, SVG, IMAGES, ASSETS, DIST,
              CACHE_SENTENCES, CACHE_MNEMONICS, CACHE_QUIZ, CACHE_PIXABAY,
              DATA_TATOEBA, DATA_KANJIVG, DATA_KANJIVG_KANJI, DATA_KANJIUM):
        d.mkdir(parents=True, exist_ok=True)
