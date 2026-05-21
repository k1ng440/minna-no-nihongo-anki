"""Verify vocab against Jisho API."""
import json
import time
from pathlib import Path

import requests

from mnn import log
from mnn.paths import CACHE
from mnn.util.io import read_json

logger = log.get(__name__)

JISHO_API = "https://jisho.org/api/v1/search/words"


def search_jisho(keyword: str) -> list[dict]:
    """Query Jisho API."""
    try:
        r = requests.get(JISHO_API, params={"keyword": keyword}, timeout=10)
        r.raise_for_status()
        return r.json().get("data", [])
    except Exception as e:
        logger.warning("Jisho API error for %s: %s", keyword, e)
        return []


def match_entry(kana: str, kanji: str, jisho_results: list[dict]) -> dict | None:
    """Find best matching Jisho entry."""
    for entry in jisho_results:
        for jpn in entry.get("japanese", []):
            j_reading = jpn.get("reading", "")
            j_word = jpn.get("word", "")
            # Match by reading first
            if j_reading == kana:
                # If we have kanji, check if it matches
                if kanji and j_word:
                    if kanji == j_word:
                        return entry
                elif not kanji and not j_word:
                    return entry
                elif not kanji and j_word:
                    # Kana-only word with kanji form in Jisho - ok
                    return entry
    return None


def run() -> None:
    """Verify all entries against Jisho."""
    discrepancies = []
    checked = 0
    not_found = []
    
    for n in range(1, 51):
        cleaned_f = CACHE / f"lesson_{n}.cleaned.json"
        if not cleaned_f.exists():
            continue
            
        rows = read_json(cleaned_f)
        for row in rows:
            kana = row["kana"]
            kanji = row.get("kanji", "")
            meaning = row.get("meaning", "")
            no = row.get("no", "?")
            
            checked += 1
            
            # Search by kana
            results = search_jisho(kana)
            time.sleep(0.5)  # Rate limit
            
            if not results:
                not_found.append({
                    "lesson": n,
                    "no": no,
                    "kana": kana,
                    "kanji": kanji,
                    "meaning": meaning,
                    "issue": "NOT_FOUND_IN_JISHO"
                })
                continue
            
            match = match_entry(kana, kanji, results)
            
            if not match:
                # Check if kanji is wrong
                issues = []
                
                # See if kanji exists in results with different reading
                for entry in results:
                    for jpn in entry.get("japanese", []):
                        if jpn.get("word") == kanji:
                            j_reading = jpn.get("reading", "")
                            if j_reading and j_reading != kana:
                                issues.append(f"KANJI_MISMATCH: {kanji} is read as '{j_reading}', not '{kana}'")
                                break
                
                if not issues:
                    # Check meanings
                    j_meanings = []
                    for sense in results[0].get("senses", [])[:3]:
                        j_meanings.extend(sense.get("english_definitions", []))
                    
                    # Simple check: does our meaning appear in Jisho?
                    our_meaning_clean = meaning.lower().replace("~", "").strip()
                    if our_meaning_clean and len(our_meaning_clean) > 3:
                        found = False
                        for jm in j_meanings:
                            if our_meaning_clean in jm.lower() or jm.lower() in our_meaning_clean:
                                found = True
                                break
                        if not found and j_meanings:
                            issues.append(f"MEANING_DIFFERENT: our='{meaning}' vs Jisho='{j_meanings[0]}'")
                
                if not issues:
                    issues.append("NO_EXACT_MATCH")
                
                if issues:
                    discrepancies.append({
                        "lesson": n,
                        "no": no,
                        "kana": kana,
                        "kanji": kanji,
                        "meaning": meaning,
                        "jisho_meanings": j_meanings[:3] if results else [],
                        "issues": issues
                    })
    
    # Output report
    report_path = CACHE / "verification_report.json"
    report = {
        "total_checked": checked,
        "discrepancies": discrepancies,
        "not_found": not_found,
        "summary": {
            "total_issues": len(discrepancies) + len(not_found),
            "discrepancy_count": len(discrepancies),
            "not_found_count": len(not_found)
        }
    }
    
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    logger.info("=" * 60)
    logger.info("VERIFICATION REPORT")
    logger.info("=" * 60)
    logger.info("Total entries checked: %d", checked)
    logger.info("Discrepancies found: %d", len(discrepancies))
    logger.info("Not found in Jisho: %d", len(not_found))
    logger.info("Report saved to: %s", report_path)
    
    if discrepancies:
        logger.info("\n--- Top Discrepancies ---")
        for d in discrepancies[:20]:
            logger.info("L%s #%s: %s (%s) - %s", 
                       d["lesson"], d["no"], d["kana"], d.get("kanji", ""), 
                       "; ".join(d["issues"]))
    
    if not_found:
        logger.info("\n--- Not Found in Jisho ---")
        for nf in not_found[:10]:
            logger.info("L%s #%s: %s (%s)", nf["lesson"], nf["no"], nf["kana"], nf.get("kanji", ""))


if __name__ == "__main__":
    run()
