"""Bangladeshi Bengali mnemonics via LLM — batched (N items per call)."""
import asyncio
import json
import re

from mnn import log
from mnn.config import settings
from mnn.paths import CACHE
from mnn.sources import llm
from mnn.util.io import read_json, write_json

logger = log.get(__name__)
OUT_DIR = CACHE / "mnemonics_bn"

BATCH_SIZE = 5

SYSTEM = (
    "তুমি প্রমিত বাংলায় (Bangladeshi modern Bengali) জাপানি শব্দের জন্য মজার, স্মরণীয় mnemonic লেখো। "
    "প্রতিটি mnemonic ২-৩টি ছোট বাক্যে কানা শব্দের উচ্চারণের সাথে বাংলা শব্দের সম্পর্ক তৈরি করবে। "
    "Kolkata/সাহিত্যিক বাংলা ব্যবহার করো না। প্রয়োজনে ইংরেজি loanword ব্যবহার করো (স্কুল, অফিস, ইত্যাদি)। "
    "ব্যবহারকারী তোমাকে JSON list এ একাধিক শব্দ দেবে। তুমি কেবল valid JSON object ফেরত দাও — "
    'যেমন: {"results": [{"id": "<id>", "mnemonic": "<বাংলা টেক্সট>"}, ...]}। '
    "কোনো ব্যাখ্যা, markdown, code fence, বা অতিরিক্ত পাঠ্য নয়। শুধু JSON।"
)

JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


def _parse_batch_response(text: str) -> dict[str, str]:
    """Extract {id: mnemonic} from possibly-fenced JSON response."""
    text = text.strip()
    # strip code fences
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    m = JSON_RE.search(text)
    if not m:
        return {}
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return {}
    results = data.get("results") or data.get("data") or []
    if isinstance(results, dict):
        return {str(k): str(v).strip() for k, v in results.items() if v}
    out = {}
    for item in results:
        if not isinstance(item, dict):
            continue
        i = item.get("id") or item.get("guid")
        m = item.get("mnemonic") or item.get("text") or item.get("result")
        if i and m:
            out[str(i)] = str(m).strip()
    return out


async def _call_batch(client, sem, model, batch: list[dict], retries=3) -> dict[str, str]:
    user_payload = {"words": [
        {"id": r["guid"], "word": r["kanji"] or r["kana"], "reading": r["kana"], "meaning": r["meaning"]}
        for r in batch
    ]}
    user = (
        "নিচের প্রতিটি শব্দের জন্য একটি করে বাংলা mnemonic লেখো। "
        "প্রতিটি ফলাফলের id, ইনপুটের id এর সাথে মিলিয়ে দাও।\n\n"
        f"{json.dumps(user_payload, ensure_ascii=False)}"
    )
    for attempt in range(retries):
        async with sem:
            try:
                resp = await client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": SYSTEM},
                        {"role": "user", "content": user},
                    ],
                    temperature=0.7,
                    max_tokens=300 * len(batch) + 200,
                    response_format={"type": "json_object"},
                )
                text = (resp.choices[0].message.content or "").strip()
                parsed = _parse_batch_response(text)
                if parsed:
                    return parsed
            except Exception as e:
                logger.debug("batch err att%d: %s", attempt, type(e).__name__)
                await asyncio.sleep(2 ** attempt)
    return {}


async def _gen_for_rows(client, sem, model, rows: list[dict]) -> dict[str, str | None]:
    cache: dict[str, str | None] = {}
    batches = [rows[i:i + BATCH_SIZE] for i in range(0, len(rows), BATCH_SIZE)]
    results = await asyncio.gather(*(_call_batch(client, sem, model, b) for b in batches))
    for batch, got in zip(batches, results):
        for r in batch:
            cache[r["guid"]] = got.get(r["guid"]) or None
    return cache


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
            logger.info("L%d: %d todo (%d batches)", n, len(todo), (len(todo) + BATCH_SIZE - 1) // BATCH_SIZE)
            got = await _gen_for_rows(client, sem, s.llm_model, todo)
            for guid, text in got.items():
                cache[guid] = text
            write_json(sidecar, cache)
        hits = sum(1 for v in cache.values() if v)
        grand_total += len(rows)
        grand_hits += hits
        logger.info("L%d: %d/%d", n, hits, len(rows))
    logger.info("mnemonics_bn total: %d/%d", grand_hits, grand_total)
