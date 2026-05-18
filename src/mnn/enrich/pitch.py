"""Pitch accent lookup + HTML renderer."""
import json
from functools import lru_cache

from mnn import log
from mnn.paths import CACHE, DATA_KANJIUM

logger = log.get(__name__)

PITCH_FILE = CACHE / "pitch.json"
YOON_SMALL = set("ゃゅょャュョぁぃぅぇぉァィゥェォ")


def build_lookup() -> None:
    pitch: dict[str, int] = {}
    src = DATA_KANJIUM / "accents.txt"
    with src.open() as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 3:
                continue
            kanji, kana, pat = parts[0], parts[1], parts[2]
            patterns: list[int] = []
            for token in pat.split(","):
                t = token.strip()
                if not t:
                    continue
                m = ""
                for ch in t:
                    if ch.isdigit():
                        m += ch
                    else:
                        break
                if m:
                    patterns.append(int(m))
            if not patterns:
                continue
            drop = patterns[0]
            pitch[f"{kanji}|{kana}"] = drop
            pitch.setdefault(kana, drop)
            if kanji:
                pitch.setdefault(kanji, drop)
    PITCH_FILE.write_text(json.dumps(pitch, ensure_ascii=False))
    logger.info("pitch lookup: %d entries → %s", len(pitch), PITCH_FILE)


@lru_cache(maxsize=1)
def _lookup() -> dict[str, int]:
    return json.loads(PITCH_FILE.read_text())


def get(kanji: str, kana: str) -> int | None:
    table = _lookup()
    for k in (f"{kanji}|{kana}", kana, kanji):
        if k and k in table:
            return table[k]
    return None


def split_mora(kana: str) -> list[str]:
    out: list[str] = []
    for ch in kana:
        if ch in YOON_SMALL and out:
            out[-1] += ch
        else:
            out.append(ch)
    return out


def render(kana: str, drop: int) -> str:
    """drop: 0 = heiban (LHHHH), N>=1 = drop after Nth mora."""
    mora = split_mora(kana)
    if not mora:
        return kana
    spans: list[str] = []
    n = len(mora)
    if drop == 0:
        for i, m in enumerate(mora):
            cls = "lo" if i == 0 else "hi"
            spans.append(f'<span class="{cls}">{m}</span>')
    elif drop == 1:
        spans.append(f'<span class="hi drop">{mora[0]}</span>')
        for m in mora[1:]:
            spans.append(f'<span class="lo">{m}</span>')
    else:
        spans.append(f'<span class="lo">{mora[0]}</span>')
        for i in range(1, n):
            if i < drop:
                cls = "hi drop" if i == drop - 1 else "hi"
                spans.append(f'<span class="{cls}">{mora[i]}</span>')
            else:
                spans.append(f'<span class="lo">{mora[i]}</span>')
    return f'<span class="pitch">{"".join(spans)}</span>'


def render_or_plain(kanji: str, kana: str) -> str:
    drop = get(kanji, kana)
    if drop is None:
        import html
        return html.escape(kana)
    return render(kana, drop)
