"""Fill missing kanji on cleaned rows via jisho.org."""
import asyncio

import aiohttp

from mnn import log
from mnn.paths import CACHE
from mnn.sources.jisho import lookup
from mnn.util.io import read_json, write_json

logger = log.get(__name__)
CONCURRENCY = 5


async def run() -> None:
    async with aiohttp.ClientSession() as session:
        sem = asyncio.Semaphore(CONCURRENCY)
        filled = 0
        for n in range(1, 51):
            f = CACHE / f"lesson_{n}.cleaned.json"
            if not f.exists():
                continue
            rows = read_json(f)
            todo = [r for r in rows if not r["kanji"] and r["kana"]]
            if not todo:
                continue
            results = await asyncio.gather(*(lookup(session, sem, r["kana"]) for r in todo))
            n_filled = 0
            for r, kanji in zip(todo, results):
                if kanji:
                    r["kanji"] = kanji
                    n_filled += 1
            write_json(f, rows)
            filled += n_filled
            logger.info("L%d: filled %d/%d", n, n_filled, len(todo))
        logger.info("fill_kanji total: %d", filled)
