"""Bangladeshi Bengali mnemonics via LLM."""
import asyncio

from mnn import log
from mnn.config import settings
from mnn.paths import CACHE
from mnn.sources import llm
from mnn.util.io import read_json, write_json

logger = log.get(__name__)
OUT_DIR = CACHE / "mnemonics_bn"

SYSTEM = (
    "তুমি একজন জাপানি ভাষা শিক্ষার্থীর জন্য মজার, স্মরণীয় mnemonic লেখো প্রমিত বাংলায় "
    "(Bangladeshi modern Bengali — Kolkata/সাহিত্যিক বাংলা নয়)। "
    "প্রতিটি mnemonic ২-৩টি ছোট বাক্যে কানা শব্দের উচ্চারণের সাথে বাংলা শব্দের সম্পর্ক তৈরি করবে। "
    "প্রয়োজনে ইংরেজি loanword ব্যবহার করো (স্কুল, অফিস, ইত্যাদি)। "
    "শুধু mnemonic লেখো — কোনো heading, markdown, emoji বা ইংরেজি ব্যাখ্যা নয়।"
)


async def _one(client, sem, model, row, retries=3):
    word = row["kanji"] or row["kana"]
    user = f"শব্দ: {word}\nReading (kana): {row['kana']}\nMeaning: {row['meaning']}\n\nবাংলা mnemonic লেখো।"
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
                    max_tokens=400,
                )
                text = (resp.choices[0].message.content or "").strip()
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
    logger.info("mnemonics_bn total: %d/%d", grand_hits, grand_total)
