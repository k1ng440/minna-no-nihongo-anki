"""Copy KanjiVG SVGs for kanji used in cleaned cache; inject CSS animation."""
import json
import re

from mnn import log
from mnn.paths import CACHE, SVG
from mnn.sources import kanjivg

logger = log.get(__name__)

CJK_RE = re.compile(r"[㐀-鿿]")
TEXT_RE = re.compile(r"<text[^>]*>.*?</text>", flags=re.DOTALL)

ANIM_CSS = """<style>
svg { cursor: pointer; }
svg path { fill: none; stroke: currentColor; stroke-width: 3; stroke-linecap: round;
stroke-dasharray: 200; stroke-dashoffset: 200; animation: draw 1.2s forwards; }
@keyframes draw { to { stroke-dashoffset: 0; } }
</style>"""

REPLAY_JS = (
    "var s=this;s.querySelectorAll('path').forEach(function(p){"
    "p.style.animation='none';});setTimeout(function(){"
    "s.querySelectorAll('path').forEach(function(p){p.style.animation='';});},20);"
)

MAP_FILE = CACHE / "kanji_svg_map.json"


def inject_animation(svg: str) -> str:
    svg = TEXT_RE.sub("", svg)
    # add onclick to <svg ...> tag for tap-to-replay
    svg = re.sub(
        r"<svg\b([^>]*)>",
        lambda m: f'<svg{m.group(1)} onclick="{REPLAY_JS}">',
        svg,
        count=1,
    )
    idx = svg.find(">", svg.find("<svg")) + 1
    svg = svg[:idx] + ANIM_CSS + svg[idx:]
    paths = re.findall(r'<path[^>]*id="kvg:[^"]*-s(\d+)"', svg)
    if paths:
        rules = "\n".join(
            f'svg path[id$="-s{i}"] {{ animation-delay: {(int(i) - 1) * 0.8:.2f}s; }}'
            for i in sorted(set(paths), key=int)
        )
        svg = svg.replace("</style>", rules + "</style>", 1)
    return svg


def run() -> None:
    SVG.mkdir(exist_ok=True)
    kanji_set: set[str] = set()
    for n in range(1, 51):
        f = CACHE / f"lesson_{n}.cleaned.json"
        if not f.exists():
            continue
        for row in json.loads(f.read_text()):
            for ch in CJK_RE.findall(row.get("kanji", "")):
                kanji_set.add(ch)

    mapping: dict[str, str] = {}
    missing = 0
    for ch in sorted(kanji_set):
        cp = ord(ch)
        src = kanjivg.svg_path(cp)
        if not src.exists():
            missing += 1
            continue
        dst_name = f"k_{cp:05x}.svg"
        dst = SVG / dst_name
        if not dst.exists():
            dst.write_text(inject_animation(src.read_text()))
        mapping[ch] = dst_name
    MAP_FILE.write_text(json.dumps(mapping, ensure_ascii=False, indent=2))
    logger.info("kanji: %d unique, %d copied, %d missing", len(kanji_set), len(mapping), missing)
