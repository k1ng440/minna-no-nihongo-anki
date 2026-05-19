"""Bangladeshi Bengali mnemonics via LLM — batched (N items per call)."""
import asyncio
import json
import re
import unicodedata

from mnn import log
from mnn.config import settings
from mnn.paths import CACHE
from mnn.sources import llm
from mnn.util.io import read_json, write_json

logger = log.get(__name__)
OUT_DIR = CACHE / "mnemonics_bn"
MEANINGS_BN_DIR = CACHE / "meanings_bn"

BATCH_SIZE = 5

# Bangla synonym groups — if mnemonic contains any token from a group, treat
# any other token in the same group as effectively present. Catches paraphrase
# (e.g. মানুষ ≈ লোক ≈ নাগরিক). Conservative list — only obvious synonyms.
BN_SYNONYMS = [
    {"মানুষ", "লোক", "নাগরিক", "জন", "ব্যক্তি"},
    {"ডাক্তার", "চিকিৎসক"},
    {"বিদ্যুৎ", "কারেন্ট", "ইলেকট্রিসিটি", "ইলেক্ট্রিসিটি"},
    {"হাসপাতাল", "ক্লিনিক"},
    {"বিশ্ববিদ্যালয়", "ইউনিভার্সিটি", "কলেজ", "ভার্সিটি"},
    {"কর্মচারী", "চাকুরিজীবী", "কর্মী", "এমপ্লয়ি", "কর্মকর্তা"},
    {"ছাত্র", "ছাত্রী", "শিক্ষার্থী", "স্টুডেন্ট"},
    {"শিক্ষক", "স্যার", "শিক্ষিকা", "টিচার", "শিক্ষকতা", "শিক্ষকত্ব"},
    {"হ্যাঁ", "জি", "হা", "জ্বি"},
    {"না", "নয়", "নাহ", "নো"},
    {"কে", "কারা", "কোন"},
    {"বছর", "বয়স", "বয়সী", "বয়সে"},
    {"প্রথম", "প্রথমবার", "নতুন", "সাক্ষাত"},
    {"কোম্পানি", "অফিস", "প্রতিষ্ঠান"},
    {"ব্যাংক", "ব্যাঙ্ক"},
    {"গবেষক", "রিসার্চার"},
    {"ইঞ্জিনিয়ার", "প্রকৌশলী"},
    {"আদর", "আদুরে", "ভালোবাসা", "স্নেহ", "প্রিয়", "ডাকনাম"},
    {"সম্মান", "সম্মানসূচক", "শ্রদ্ধা", "জনাব", "জনাবা", "মিস্টার"},
    {"ভাই", "ভাইরা", "বোন", "বোনেরা", "সবাই"},
    {"নাম", "ডাকনাম"},
    {"টেলার", "ক্যাশিয়ার", "কর্মচারী"},
    {"স্নাতকোত্তর", "মাস্টার্স", "পোস্টগ্র্যাজুয়েট", "গবেষক"},
    {"মাফ", "ক্ষমা", "দুঃখিত", "সরি"},
    {"অন্যটা", "অন্য", "অন্যটি", "সম্মানীয়", "ওই"},
    {"এঁরা", "এঁকে", "ইনি", "ইনিই"},
]


def _synonym_set(token: str) -> set[str]:
    """Return set containing token + its synonyms (or just {token} if none)."""
    for grp in BN_SYNONYMS:
        if token in grp:
            return grp
    return {token}


def _extract_meaning_keywords(bn_meaning: str | None) -> list[set[str]]:
    """Extract Bangla content tokens (with synonyms) from meaning string.

    Returns list of synonym sets — mnemonic must contain at least one token
    from at least one set to pass accuracy check.
    """
    if not bn_meaning:
        return []
    parts = re.split(r"[,/]", bn_meaning)
    out = []
    for p in parts:
        p = re.sub(r"\([^)]*\)", "", p).strip()
        if not p:
            continue
        toks = [t for t in p.split() if len(t) >= 2]
        if not toks:
            continue
        # use longest token as keyword
        longest = max(toks, key=len)
        out.append(_synonym_set(longest))
    return out


def _validate_accuracy(text: str, keyword_sets: list[set[str]]) -> bool:
    """Mnemonic must contain at least one token from any synonym set.

    Bengali has NFC vs NFD codepoint differences for characters like য় (U+09DF
    vs U+09AF+U+09BC) — normalize both sides to NFC before substring check.
    """
    if not keyword_sets:
        return True  # no reference data, skip
    text_nfc = unicodedata.normalize("NFC", text)
    for grp in keyword_sets:
        for tok in grp:
            if unicodedata.normalize("NFC", tok) in text_nfc:
                return True
    return False

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
    "উদাহরণ:\n\n"
    "[ব্যক্তি/পেশা] せんせい (sensei) → শিক্ষক\n"
    "ভালো: \"সেন-সেই শুনলে মনে করো ক্লাসে স্যার এসে বললেন 'সবাই সেই দিকে তাকাও!' সেন-সেই মানেই শিক্ষক।\"\n"
    "খারাপ: \"sen মানে শব্দ, sei মানে বলা\" (বানোয়াট ব্যুৎপত্তি)।\n\n"
    "[দেশের নাম] ドイツ (doitsu) → জার্মানি\n"
    "ভালো: \"ডোইৎসু শুনলে মনে করো জার্মানিতে গিয়ে তুমি বাটিতে মিষ্টি দই খাচ্ছ। দই থেকে মনে রাখো ডোইৎসু মানেই জার্মানি।\"\n"
    "খারাপ: \"ডোইৎসু মানে গুণ\" (ভুল অর্থ), \"Germany\" (ইংরেজি)।\n\n"
    "[প্রত্যয়/particle] ～じん (-jin) → কোনো দেশের নাগরিক\n"
    "ভালো: \"কল্পনা করো বোতলের জিন একেক দেশের পোশাক পরে বের হচ্ছে। দেশের নামের শেষে জিন যোগ করলেই সেই দেশের নাগরিক বোঝায়, যেমন নিহন-জিন মানে জাপানি।\"\n"
    "খারাপ: কেবল ব্যাখ্যা, কোনো কীওয়ার্ড-লিংক নেই।\n\n"
    "[বিদ্যুৎ/বস্তু] でんき (denki) → বিদ্যুৎ\n"
    "ভালো: \"দেন-কি শুনলে মনে করো বিদ্যুৎ চলে যাওয়ায় তুমি চিৎকার করছ, 'কারেন্ট দেন কি দেন না?' দেন-কি মানে বিদ্যুৎ।\"\n"
    "খারাপ: \"দেন মানে দেওয়া, কি মানে কী\" (বানোয়াট কাঞ্জি ব্যুৎপত্তি)।\n\n"
    "[অভিবাদন/phrase] はじめまして (hajimemashite) → প্রথম সাক্ষাতের অভিবাদন\n"
    "ভালো: \"হাজিমে শুনলে মনে করো 'হাজি সাহেবের মেয়ে'র সাথে প্রথমবার দেখা। হাজিমেমাশিতে মানে প্রথম পরিচয়ের অভিবাদন।\"\n"
    "খারাপ: \"hajime means start, mashite means meeting\" (ইংরেজি + বানোয়াট ব্যুৎপত্তি)।\n\n"
    "[direct cognate] エンジニア (enjinia) → ইঞ্জিনিয়ার\n"
    "ভালো: \"এনজিনিয়া শুনতে হুবহু ইঞ্জিনিয়ার শব্দের মতো — কঠিন কিছু মনে রাখার দরকার নেই।\"\n"
    "খারাপ: জোর করে অপ্রাসঙ্গিক imagery বসানো।\n\n"
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


async def _call_batch(client, sem, model, batch: list[dict], retries=4, accuracy_keywords: dict[str, list[set[str]]] | None = None) -> dict[str, str]:
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
    soft_fail: dict[str, str] = {}
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
                    if not m or not _validate(m):
                        still_pending.append(r)
                        continue
                    kw = (accuracy_keywords or {}).get(r["guid"], [])
                    if not _validate_accuracy(m, kw):
                        # passes script/length but misses meaning — retry
                        soft_fail[r["guid"]] = m
                        still_pending.append(r)
                        continue
                    accumulated[r["guid"]] = m
                if still_pending and len(still_pending) < len(pending):
                    logger.debug("partial: %d/%d ok att%d", len(pending) - len(still_pending), len(pending), attempt)
                pending = still_pending
            except Exception as e:
                logger.debug("batch err att%d: %s", attempt, type(e).__name__)
                await asyncio.sleep(2 ** attempt)
    # Accept soft-fail candidates (passed _validate but missed accuracy keyword)
    if pending and soft_fail:
        for r in list(pending):
            if r["guid"] in soft_fail:
                accumulated[r["guid"]] = soft_fail[r["guid"]]
                pending.remove(r)
                logger.debug("soft-fail accepted: %s", r["guid"])
    if pending:
        logger.warning("gave up on %d items after %d attempts", len(pending), retries)
    return accumulated


async def _gen_for_rows(client, sem, model, rows: list[dict], accuracy_keywords: dict[str, list[set[str]]] | None = None) -> dict[str, str | None]:
    cache: dict[str, str | None] = {}
    batches = [rows[i:i + BATCH_SIZE] for i in range(0, len(rows), BATCH_SIZE)]
    results = await asyncio.gather(*(
        _call_batch(client, sem, model, b, accuracy_keywords=accuracy_keywords)
        for b in batches
    ))
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
        bn_map_path = MEANINGS_BN_DIR / f"lesson_{n}.json"
        bn_map: dict[str, str | None] = read_json(bn_map_path) if bn_map_path.exists() else {}
        accuracy_kw = {
            r["guid"]: _extract_meaning_keywords(bn_map.get(r["meaning"]))
            for r in rows
        }
        if regen:
            todo = rows
        else:
            todo = [r for r in rows if not cache.get(r["guid"])]
        if todo:
            logger.info("L%d: %d todo (%d batches)", n, len(todo), (len(todo) + BATCH_SIZE - 1) // BATCH_SIZE)
            got = await _gen_for_rows(client, sem, s.llm_model, todo, accuracy_keywords=accuracy_kw)
            for guid, text in got.items():
                cache[guid] = text
            write_json(sidecar, cache)
        hits = sum(1 for v in cache.values() if v)
        grand_total += len(rows)
        grand_hits += hits
        logger.info("L%d: %d/%d", n, hits, len(rows))
    logger.info("mnemonics_bn total: %d/%d", grand_hits, grand_total)
