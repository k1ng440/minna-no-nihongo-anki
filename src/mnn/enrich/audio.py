"""edge-tts MP3 generator for word kana + Tatoeba sentences."""
import asyncio
import json
from pathlib import Path

import edge_tts

from mnn import log
from mnn.config import settings
from mnn.paths import AUDIO, AUDIO_SENT, CACHE, CACHE_SENTENCES

logger = log.get(__name__)


async def _tts_one(sem, voice, text, path: Path):
    if path.exists() and path.stat().st_size > 0:
        return
    async with sem:
        try:
            await edge_tts.Communicate(text, voice).save(str(path))
        except Exception as e:
            logger.warning("tts err %s: %s", path.name, e)


async def _run_batch(work: dict[str, str], out_dir: Path, label: str) -> None:
    s = settings()
    out_dir.mkdir(parents=True, exist_ok=True)
    logger.info("%s: %d unique items", label, len(work))
    sem = asyncio.Semaphore(s.tts_concurrency)
    tasks = [_tts_one(sem, s.tts_voice, t, out_dir / fn) for t, fn in work.items()]
    done = 0
    for fut in asyncio.as_completed(tasks):
        await fut
        done += 1
        if done % 100 == 0:
            logger.info("%s: %d/%d", label, done, len(tasks))
    logger.info("%s done", label)


async def run_words() -> None:
    work: dict[str, str] = {}
    for n in range(1, 51):
        f = CACHE / f"lesson_{n}.cleaned.json"
        if not f.exists():
            continue
        for row in json.loads(f.read_text()):
            kana = row["kana"].strip()
            audio = row.get("audio", "")
            if kana and audio:
                work[kana] = audio
    await _run_batch(work, AUDIO, "audio.words")


async def run_sentences() -> None:
    work: dict[str, str] = {}
    for f in sorted(CACHE_SENTENCES.glob("lesson_*.json")):
        for v in json.loads(f.read_text()).values():
            if v:
                work[v["jp"]] = v["audio"]
    await _run_batch(work, AUDIO_SENT, "audio.sentences")


async def run_all() -> None:
    await run_words()
    await run_sentences()
