"""LLM-translate matched English Tatoeba sentences to Bangladeshi modern Bengali."""
import asyncio

from mnn import log
from mnn.config import settings
from mnn.paths import CACHE, CACHE_SENTENCES
from mnn.sources import llm
from mnn.util.io import read_json, write_json

logger = log.get(__name__)
OUT_DIR = CACHE / "sentences_bn"

SYSTEM = (
    "তুমি একজন অভিজ্ঞ অনুবাদক। ইংরেজি বাক্যকে প্রমিত বাংলায় (Bangladeshi modern Bengali) অনুবাদ করো। "
    "Kolkata/সাহিত্যিক বাংলা নয় — দৈনন্দিন ব্যবহারের ভাষা। প্রয়োজনে ইংরেজি loanword ব্যবহার করো। "
    "শুধু অনুবাদ লেখো, ব্যাখ্যা নয়, quote মার্ক নয়।"
)


async def _one(client, sem, model, en_text: str, retries=3) -> str | None:
    for attempt in range(retries):
        async with sem:
            try:
                resp = await client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": SYSTEM},
                        {"role": "user", "content": en_text},
                    ],
                    temperature=0.3,
                    max_tokens=200,
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
        src = CACHE_SENTENCES / f"lesson_{n}.json"
        if not src.exists():
            continue
        sents = read_json(src)
        sidecar = OUT_DIR / f"lesson_{n}.json"
        cache: dict[str, str | None] = read_json(sidecar) if sidecar.exists() else {}
        todo_keys = [k for k, v in sents.items() if v and v.get("en") and not cache.get(v["en"])]
        if todo_keys:
            logger.info("L%d: %d todo", n, len(todo_keys))
            en_list = [sents[k]["en"] for k in todo_keys]
            results = await asyncio.gather(*(_one(client, sem, s.llm_model, e) for e in en_list))
            for en, bn in zip(en_list, results):
                cache[en] = bn
            write_json(sidecar, cache)
        hits = sum(1 for v in sents.values() if v and cache.get(v.get("en", "")))
        grand_total += sum(1 for v in sents.values() if v)
        grand_hits += hits
        logger.info("L%d: %d sentence translations", n, hits)
    logger.info("sentences_bn total: %d/%d", grand_hits, grand_total)
