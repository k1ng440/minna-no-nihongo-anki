"""Stable MD5-based filename helpers (16 hex chars)."""
import hashlib


def _h(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()[:16]


def audio_filename(text: str) -> str:
    return f"mnn_{_h(text)}.mp3"


def sentence_audio_filename(text: str) -> str:
    return f"snt_{_h(text)}.mp3"


def image_filename(text: str) -> str:
    return f"img_{_h(text)}.jpg"
