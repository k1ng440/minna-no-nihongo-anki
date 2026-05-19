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
    "তুমি একজন বাংলাদেশী শিক্ষক। জাপানি শব্দ মুখস্থ করার জন্য keyword-link পদ্ধতিতে বাংলা mnemonic লেখো।\n\n"
    "নিয়ম:\n"
    "১. প্রতিটি mnemonic ১-২ বাক্য, সর্বোচ্চ ৪০ শব্দ। ছোট, পাঞ্চি, ছবি-ভিত্তিক।\n"
    "২. পদ্ধতি: জাপানি উচ্চারণের সাথে মিলে যায় এমন একটি বাংলা শব্দ/বাক্যাংশ বেছে নাও → একটি দৃশ্য কল্পনা করো → অর্থের সাথে যুক্ত করো।\n"
    "৩. কেবল বাংলা লেখো। ইংরেজি, রোমান হরফ (যেমন \"watashi\", \"I\", \"teacher\"), কোরিয়ান, হিন্দি, বা অন্য কোনো হরফ নয়। বন্ধনীতে রোমান উচ্চারণ লিখো না। জাপানি কানা/কাঞ্জি কেবল উদ্ধৃতিতে অনুমোদিত।\n"
    "৪. একটাই কণ্ঠস্বর: তুমি (informal-friendly)। আপনি/তুই মিশিও না।\n"
    "৫. জাপানি শব্দের ব্যুৎপত্তি বানিয়ো না — \"কা মানে X\", \"গাক মানে গান\" ধরনের ভুয়া etymology নিষিদ্ধ। শুধু উচ্চারণ-সাদৃশ্য কাজে লাগাও।\n"
    "৬. প্রমিত বাংলাদেশী বাংলা — কলকাতার সাহিত্যিক ভাষা না। স্কুল-অফিসের loanword বাংলা হরফে লেখো (যেমন \"অফিস\", \"স্কুল\", \"ইঞ্জিনিয়ার\")।\n"
    "৭. বাক্য অসম্পূর্ণ রেখো না। প্রতিটি বাক্যে দাঁড়ি (।) দাও।\n"
    "৮. বানোয়াট তথ্য বা ভুল অর্থ লেখো না।\n"
    "৯. দেশ/স্থানের নাম বাংলায় লেখো: কোরিয়া, থাইল্যান্ড, চীন, জার্মানি, জাপান, ফ্রান্স, ব্রাজিল, আমেরিকা, ইংল্যান্ড, ভারত, ইন্দোনেশিয়া, ভিয়েতনাম। ইংরেজি/রোমান বানান (Korea, Thailand, China) ব্যবহার নিষিদ্ধ।\n\n"
    "উদাহরণ:\n"
    "শব্দ: せんせい (sensei) — শিক্ষক\n"
    "ভালো: \"সেন-সেই শুনলে মনে করো ক্লাসে স্যার এসে বললেন 'সবাই সেই দিকে তাকাও!' সেন-সেই মানেই শিক্ষক।\"\n"
    "খারাপ (এড়িয়ে যাবে): \"sen মানে শব্দ, sei মানে বলা\" (বানোয়াট etymology), \"teacher\" (ইংরেজি)।\n\n"
    "ব্যবহারকারী JSON list এ একাধিক শব্দ দেবে। তুমি কেবল valid JSON object ফেরত দাও — "
    '{"results": [{"id": "<id>", "mnemonic": "<বাংলা>"}, ...]}। '
    "কোনো ব্যাখ্যা, markdown, code fence নয়। শুধু JSON।"
)

# Validation: reject mnemonics containing Latin/Hangul/Devanagari-letter/Georgian.
# Bangla daari (U+0964) is shared with Devanagari, so exclude it from the ban
# by listing Devanagari letter ranges explicitly (U+0904-U+0939, U+0958-U+095F).
BAD_SCRIPT_RE = re.compile(
    r"[A-Za-zऄ-हक़-य़ॲ-ॿႠ-ჿ가-힯ᄀ-ᇿ]"
)


def _validate(text: str) -> bool:
    """Return True if mnemonic passes quality gate."""
    if not text or len(text) < 20:
        return False
    if len(text) > 400:
        return False
    if BAD_SCRIPT_RE.search(text):
        return False
    # must end with Bangla daari or standard sentence terminator
    if not text.rstrip().endswith(("।", "?", "!", "।\"", "।'")):
        return False
    return True

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


async def _call_batch(client, sem, model, batch: list[dict], retries=4) -> dict[str, str]:
    user_payload = {"words": [
        {"id": r["guid"], "word": r["kanji"] or r["kana"], "reading": r["kana"], "meaning": r["meaning"]}
        for r in batch
    ]}
    user = (
        "নিচের প্রতিটি শব্দের জন্য একটি করে বাংলা mnemonic লেখো। "
        "প্রতিটি ফলাফলের id, ইনপুটের id এর সাথে মিলিয়ে দাও। "
        "মনে রাখবে: কেবল বাংলা হরফ, ১-২ পূর্ণ বাক্য, keyword-link পদ্ধতি, কোনো বানোয়াট etymology নয়।\n\n"
        f"{json.dumps(user_payload, ensure_ascii=False)}"
    )
    accumulated: dict[str, str] = {}
    pending = batch
    for attempt in range(retries):
        if not pending:
            break
        user_payload = {"words": [
            {"id": r["guid"], "word": r["kanji"] or r["kana"], "reading": r["kana"], "meaning": r["meaning"]}
            for r in pending
        ]}
        user = (
            "নিচের প্রতিটি শব্দের জন্য একটি করে বাংলা mnemonic লেখো। "
            "প্রতিটি ফলাফলের id, ইনপুটের id এর সাথে মিলিয়ে দাও। "
            "মনে রাখবে: কেবল বাংলা হরফ, ১-২ পূর্ণ বাক্য, keyword-link পদ্ধতি, কোনো বানোয়াট etymology নয়।\n\n"
            f"{json.dumps(user_payload, ensure_ascii=False)}"
        )
        async with sem:
            try:
                resp = await client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": SYSTEM},
                        {"role": "user", "content": user},
                    ],
                    temperature=0.5,
                    max_tokens=600 * len(pending) + 800,
                    response_format={"type": "json_object"},
                )
                text = (resp.choices[0].message.content or "").strip()
                parsed = _parse_batch_response(text)
                still_pending = []
                for r in pending:
                    m = parsed.get(r["guid"])
                    if m and _validate(m):
                        accumulated[r["guid"]] = m
                    else:
                        still_pending.append(r)
                if still_pending and len(still_pending) < len(pending):
                    logger.debug("partial: %d/%d ok att%d", len(pending) - len(still_pending), len(pending), attempt)
                pending = still_pending
            except Exception as e:
                logger.debug("batch err att%d: %s", attempt, type(e).__name__)
                await asyncio.sleep(2 ** attempt)
    if pending:
        logger.warning("gave up on %d items after %d attempts", len(pending), retries)
    return accumulated


async def _gen_for_rows(client, sem, model, rows: list[dict]) -> dict[str, str | None]:
    cache: dict[str, str | None] = {}
    batches = [rows[i:i + BATCH_SIZE] for i in range(0, len(rows), BATCH_SIZE)]
    results = await asyncio.gather(*(_call_batch(client, sem, model, b) for b in batches))
    for batch, got in zip(batches, results):
        for r in batch:
            cache[r["guid"]] = got.get(r["guid"]) or None
    return cache


async def run(lessons: list[int] | None = None, regen: bool = False) -> None:
    """Generate Bangla mnemonics.

    lessons: only process these lesson numbers (None = all 1..50).
    regen: ignore cached entries and re-generate.
    """
    s = settings()
    client = llm.async_client()
    sem = asyncio.Semaphore(s.llm_concurrency)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    grand_total = grand_hits = 0
    target = lessons if lessons else list(range(1, 51))
    for n in target:
        cleaned = CACHE / f"lesson_{n}.cleaned.json"
        if not cleaned.exists():
            continue
        sidecar = OUT_DIR / f"lesson_{n}.json"
        cache: dict[str, str | None] = read_json(sidecar) if sidecar.exists() else {}
        rows = read_json(cleaned)
        if regen:
            todo = rows
        else:
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
