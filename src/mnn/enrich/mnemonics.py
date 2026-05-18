"""LLM-generated English mnemonics for vocab words."""
import asyncio

from mnn import log
from mnn.config import settings
from mnn.paths import CACHE, CACHE_MNEMONICS
from mnn.sources import llm
from mnn.util.io import read_json, write_json

logger = log.get(__name__)

SYSTEM = (
    "You write vivid English-language mnemonics for Japanese vocabulary learners. "
    "Output 2-3 short English sentences. Link the English meaning to the SOUND of "
    "the kana using English word associations. Be playful but never offensive. "
    "NEVER write Japanese script in your response. Plain English text only. "
    "No emoji. No markdown. No headings."
)


async def _one(client, sem, model, row, retries=3) -> str | None:
    word = row["kanji"] or row["kana"]
    user = f"Word: {word}\nReading: {row['kana']}\nMeaning: {row['meaning']}\n\nWrite the mnemonic."
    for attempt in range(retries):
        async with sem:
            try:
                resp = await client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": SYSTEM},
                        {"role": "user", "content": user},
                    ],
                    temperature=0.8,
                    max_tokens=300,
                )
                text = (resp.choices[0].message.content or "").strip()
                if text:
                    return text
            except Exception as e:
                logger.debug("mnem err %s att%d: %s", row["guid"], attempt, type(e).__name__)
                await asyncio.sleep(2 ** attempt)
    return None


async def run() -> None:
    s = settings()
    client = llm.async_client()
    sem = asyncio.Semaphore(s.llm_concurrency)
    grand_total = 0
    grand_hits = 0
    for n in range(1, 51):
        cleaned = CACHE / f"lesson_{n}.cleaned.json"
        if not cleaned.exists():
            continue
        sidecar = CACHE_MNEMONICS / f"lesson_{n}.json"
        cache: dict[str, str | None] = read_json(sidecar) if sidecar.exists() else {}
        rows = read_json(cleaned)
        todo = [r for r in rows if not cache.get(r["guid"])]
        if todo:
            logger.info("L%d: %d todo", n, len(todo))
            results = await asyncio.gather(*(_one(client, sem, s.llm_model, r) for r in todo))
            for r, text in zip(todo, results):
                cache[r["guid"]] = text
            write_json(sidecar, cache)
        hits = sum(1 for v in cache.values() if v)
        grand_total += len(rows)
        grand_hits += hits
        logger.info("L%d: %d/%d", n, hits, len(rows))
    logger.info("mnemonics total: %d/%d", grand_hits, grand_total)
