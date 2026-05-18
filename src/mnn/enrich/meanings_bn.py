"""Translate vocab meanings to Bangladeshi modern Bengali via LLM."""
import asyncio

from mnn import log
from mnn.config import settings
from mnn.paths import CACHE
from mnn.sources import llm
from mnn.util.io import read_json, write_json

logger = log.get(__name__)

OUT_DIR = CACHE / "meanings_bn"

SYSTEM = (
    "You translate English vocabulary glosses to Bangladeshi modern Bengali "
    "(প্রমিত বাংলা used in Bangladesh, NOT Kolkata/West Bengal literary style). "
    "Prefer everyday colloquial Bangladeshi vocabulary and common English loanwords when natural "
    "(e.g. 'school' → 'স্কুল', not 'বিদ্যালয়'; 'office' → 'অফিস', not 'কার্যালয়'). "
    "Keep verbs in dictionary/infinitive form. "
    "Output ONLY the Bangla translation. No transliteration. No English. No explanation. No quotes."
)


async def _one(client, sem, model, meaning: str, retries=3) -> str | None:
    for attempt in range(retries):
        async with sem:
            try:
                resp = await client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": SYSTEM},
                        {"role": "user", "content": meaning},
                    ],
                    temperature=0.2,
                    max_tokens=120,
                )
                text = (resp.choices[0].message.content or "").strip().strip('"').strip("'")
                if text:
                    return text
            except Exception:
                await asyncio.sleep(2 ** attempt)
    return None


async def run() -> None:
    s = settings()
    client = llm.async_client()
    sem = asyncio.Semaphore(s.llm_concurrency)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    grand_total = grand_hits = 0
    for n in range(1, 51):
        cleaned = CACHE / f"lesson_{n}.cleaned.json"
        if not cleaned.exists():
            continue
        sidecar = OUT_DIR / f"lesson_{n}.json"
        cache: dict[str, str | None] = read_json(sidecar) if sidecar.exists() else {}
        rows = read_json(cleaned)
        todo = [r for r in rows if r["meaning"] and not cache.get(r["meaning"])]
        if todo:
            logger.info("L%d: %d todo", n, len(todo))
            results = await asyncio.gather(*(_one(client, sem, s.llm_model, r["meaning"]) for r in todo))
            for r, text in zip(todo, results):
                cache[r["meaning"]] = text
            write_json(sidecar, cache)
        hits = sum(1 for v in cache.values() if v)
        grand_total += len(rows)
        grand_hits += hits
        logger.info("L%d: %d/%d", n, hits, len(rows))
    logger.info("meanings_bn total: %d/%d", grand_hits, grand_total)
