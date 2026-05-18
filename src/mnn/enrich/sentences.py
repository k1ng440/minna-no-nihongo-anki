"""Match shortest Tatoeba JP+EN sentence pair containing each headword."""
import re

from mnn import log
from mnn.paths import CACHE, CACHE_SENTENCES, DATA_TATOEBA
from mnn.sources import tatoeba
from mnn.util.hashing import sentence_audio_filename
from mnn.util.io import read_json, write_json

logger = log.get(__name__)

VERB_TAIL = re.compile(r"(ます|します|です|い|な)$")


def headword_variants(kanji: str, kana: str) -> list[str]:
    base = kanji if kanji else kana
    base = re.sub(r"[\[\]［］「」（）()\s〜~・,，、。.]", "", base).split("/")[0]
    out = [base]
    stripped = VERB_TAIL.sub("", base)
    if stripped and stripped != base and len(stripped) >= 1:
        out.append(stripped)
    if kanji and kana:
        kana_clean = re.sub(r"[\[\]［］「」（）()\s〜~・,，、。.]", "", kana).split("/")[0]
        out.append(kana_clean)
        s2 = VERB_TAIL.sub("", kana_clean)
        if s2 and s2 != kana_clean:
            out.append(s2)
    return [h for h in out if h]


def run() -> None:
    logger.info("loading Tatoeba sentences...")
    jp = tatoeba.load_sentences(DATA_TATOEBA / "jpn_sentences.tsv", "jpn")
    en = tatoeba.load_sentences(DATA_TATOEBA / "eng_sentences.tsv", "eng")
    links = tatoeba.load_jp_eng_links()
    logger.info("jp=%d en=%d linked=%d", len(jp), len(en), len(links))

    jp_sorted = sorted(((sid, txt) for sid, txt in jp.items() if sid in links), key=lambda x: len(x[1]))
    logger.info("searchable jp sentences: %d", len(jp_sorted))

    grand_total = 0
    grand_hits = 0
    for n in range(1, 51):
        cleaned_f = CACHE / f"lesson_{n}.cleaned.json"
        if not cleaned_f.exists():
            continue
        rows = read_json(cleaned_f)
        out: dict[str, dict | None] = {}
        hits = 0
        for row in rows:
            variants = headword_variants(row["kanji"], row["kana"])
            picked = None
            for variant in variants:
                if len(variant) < 1:
                    continue
                for sid, txt in jp_sorted:
                    if len(txt) > 30:
                        break
                    if variant in txt:
                        en_ids = links.get(sid, [])
                        eng_txt = next((en[i] for i in en_ids if i in en), None)
                        if eng_txt and len(eng_txt) < 80:
                            picked = {"jp": txt, "en": eng_txt, "audio": sentence_audio_filename(txt)}
                            break
                if picked:
                    break
            out[row["kana"]] = picked
            if picked:
                hits += 1
        write_json(CACHE_SENTENCES / f"lesson_{n}.json", out)
        grand_total += len(rows)
        grand_hits += hits
        logger.info("L%d: %d/%d", n, hits, len(rows))
    logger.info("sentences total: %d/%d (%d%%)", grand_hits, grand_total, grand_hits * 100 // max(1, grand_total))
