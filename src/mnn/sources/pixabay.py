"""Pixabay image API (free key required). Disabled by default — quality was poor in MNN context."""
import asyncio
import re

import aiohttp

from mnn import log
from mnn.config import settings
from mnn.paths import CACHE_PIXABAY, IMAGES
from mnn.util.hashing import image_filename
from mnn.util.io import read_json, write_json

logger = log.get(__name__)

CONCURRENCY = 5
SLEEP = 0.6
ENDPOINT = "https://pixabay.com/api/"


def _clean_query(meaning: str) -> str:
    m = re.sub(r"\([^)]*\)", "", meaning)
    m = m.split(",")[0].split(";")[0].split("/")[0].strip()
    m = re.sub(r"\s+", " ", m).strip(" .")
    return " ".join(m.split()[:3])


async def _fetch_one(session, sem, key, meaning, dst):
    if dst.exists() and dst.stat().st_size > 0:
        return True
    q = _clean_query(meaning)
    if not q:
        return False
    params = {"key": key, "q": q, "image_type": "photo", "safesearch": "true",
              "per_page": "3", "lang": "en"}
    for attempt in range(3):
        try:
            async with sem:
                async with session.get(ENDPOINT, params=params, timeout=30) as r:
                    if r.status == 429:
                        await asyncio.sleep(30)
                        continue
                    if r.status != 200:
                        return False
                    data = await r.json()
                await asyncio.sleep(SLEEP)
                hits = data.get("hits", [])
                if not hits and " " in q:
                    params["q"] = q.split()[0]
                    continue
                if not hits:
                    return False
                img_url = hits[0].get("webformatURL")
                if not img_url:
                    return False
                async with session.get(img_url, timeout=60) as ir:
                    if ir.status != 200:
                        return False
                    dst.write_bytes(await ir.read())
                    return True
        except Exception as e:
            logger.warning("pixabay err %r att%d: %s", q, attempt, type(e).__name__)
            await asyncio.sleep(3 * (attempt + 1))
    return False


async def run() -> None:
    s = settings()
    if not s.pixabay_enabled:
        logger.info("pixabay disabled (set PIXABAY_ENABLED=1)")
        return
    if not s.pixabay_key:
        logger.error("PIXABAY_API_KEY not set")
        return
    IMAGES.mkdir(exist_ok=True)
    async with aiohttp.ClientSession() as session:
        sem = asyncio.Semaphore(CONCURRENCY)
        for n in range(1, 51):
            cleaned = CACHE_PIXABAY.parent / f"lesson_{n}.cleaned.json"
            if not cleaned.exists():
                continue
            sidecar = CACHE_PIXABAY / f"lesson_{n}.json"
            mapping = read_json(sidecar) if sidecar.exists() else {}
            tasks = []
            for row in read_json(cleaned):
                meaning = row["meaning"]
                if not meaning or (meaning in mapping and mapping[meaning]):
                    continue
                fn = image_filename(meaning)
                tasks.append((meaning, fn, _fetch_one(session, sem, s.pixabay_key, meaning, IMAGES / fn)))
            if not tasks:
                logger.info("L%d: cached", n)
                continue
            results = await asyncio.gather(*(t[2] for t in tasks), return_exceptions=True)
            for (meaning, fn, _), ok in zip(tasks, results):
                if isinstance(ok, Exception):
                    continue
                mapping[meaning] = fn if ok else None
            write_json(sidecar, mapping)
            hits = sum(1 for v in mapping.values() if v)
            logger.info("L%d: %d/%d images", n, hits, len(mapping))
