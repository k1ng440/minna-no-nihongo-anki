"""Runtime settings from .env / environment."""
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import os

from dotenv import load_dotenv

from mnn.paths import DIST, ROOT


@dataclass(frozen=True)
class Settings:
    root: Path
    llm_api_url: str
    llm_api_key: str
    llm_model: str
    llm_concurrency: int
    tts_voice: str
    tts_concurrency: int
    pixabay_key: str | None
    pixabay_enabled: bool
    parent_deck_name: str
    output_apkg: Path
    serve_port: int


@lru_cache(maxsize=1)
def settings() -> Settings:
    load_dotenv(ROOT / ".env")
    return Settings(
        root=ROOT,
        llm_api_url=os.environ.get("LLM_API_URL", "http://localhost:11434"),
        llm_api_key=os.environ.get("LLM_API_KEY", "ollama"),
        llm_model=os.environ.get("LLM_MODEL", "gemma4:e4b"),
        llm_concurrency=int(os.environ.get("LLM_CONCURRENCY", "8")),
        tts_voice=os.environ.get("TTS_VOICE", "ja-JP-NanamiNeural"),
        tts_concurrency=int(os.environ.get("TTS_CONCURRENCY", "16")),
        pixabay_key=os.environ.get("PIXABAY_API_KEY") or None,
        pixabay_enabled=os.environ.get("PIXABAY_ENABLED", "0") == "1",
        parent_deck_name=os.environ.get("PARENT_DECK", "Minna no Nihongo"),
        output_apkg=DIST / "MinnaNoNihongo_Vocab.apkg",
        serve_port=int(os.environ.get("SERVE_PORT", "8765")),
    )
