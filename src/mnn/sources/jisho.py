"""Jisho.org search API client (free, no key)."""
import re
from urllib.parse import quote

import aiohttp

CJK_RE = re.compile(r"[㐀-鿿々ヶ]")


async def lookup(session: aiohttp.ClientSession, sem, kana: str) -> str | None:
    url = f"https://jisho.org/api/v1/search/words?keyword={quote(kana)}"
    async with sem:
        try:
            async with session.get(url, timeout=20) as r:
                if r.status != 200:
                    return None
                data = await r.json()
        except Exception:
            return None
    for item in data.get("data", []):
        for j in item.get("japanese", []):
            word = j.get("word")
            reading = j.get("reading")
            if word and reading == kana and CJK_RE.search(word):
                return word
    return None
