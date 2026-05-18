"""mnn web build — generate static site into docs/."""
import json
import shutil
from pathlib import Path

from mnn import log
from mnn.deck import info
from mnn.deck.themes import THEMES
from mnn.enrich.pitch import render_or_plain
from mnn.paths import (
    ASSETS,
    AUDIO,
    AUDIO_SENT,
    CACHE,
    CACHE_MNEMONICS,
    CACHE_SENTENCES,
    ROOT,
    SVG,
)
from mnn.util.io import read_json

logger = log.get(__name__)

STATIC = Path(__file__).parent / "static"
DOCS = ROOT / "docs"


def _gather() -> dict:
    svg_map = read_json(CACHE / "kanji_svg_map.json")
    lessons_meta: list[dict] = []
    cards: list[dict] = []

    for n in range(1, 51):
        cleaned_f = CACHE / f"lesson_{n}.cleaned.json"
        if not cleaned_f.exists():
            continue
        rows = read_json(cleaned_f)
        sents = read_json(CACHE_SENTENCES / f"lesson_{n}.json") if (CACHE_SENTENCES / f"lesson_{n}.json").exists() else {}
        mnem = read_json(CACHE_MNEMONICS / f"lesson_{n}.json") if (CACHE_MNEMONICS / f"lesson_{n}.json").exists() else {}
        theme = THEMES[n]
        lessons_meta.append({"n": n, "count": len(rows), "color": theme["color"], "emoji": theme["emoji"]})

        for row in rows:
            kana = row["kana"]
            kanji = row["kanji"]
            sent = sents.get(kana) or {}
            cards.append({
                "guid": row["guid"],
                "lesson": n,
                "kanji": kanji,
                "kana": kana,
                "kana_pitch": render_or_plain(kanji, kana),
                "meaning": row["meaning"],
                "audio": row.get("audio") if (AUDIO / row.get("audio", "")).exists() else "",
                "sentence_jp": sent.get("jp", ""),
                "sentence_en": sent.get("en", ""),
                "sentence_audio": sent.get("audio", "") if sent and (AUDIO_SENT / sent.get("audio", "")).exists() else "",
                "kanji_svgs": [svg_map[c] for c in kanji if c in svg_map],
                "mnemonic": mnem.get(row["guid"]) or "",
                "theme": theme["color"],
                "emoji": theme["emoji"],
            })

    return {
        "lessons": lessons_meta,
        "cards": cards,
        "intro_html": info.build(),
    }


def _copy_tree(src: Path, dst: Path) -> int:
    dst.mkdir(parents=True, exist_ok=True)
    count = 0
    for f in src.iterdir():
        if f.is_file():
            target = dst / f.name
            if not target.exists() or target.stat().st_size != f.stat().st_size:
                shutil.copy2(f, target)
            count += 1
    return count


def run() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)

    for name in ("index.html", "style.css", "app.js"):
        shutil.copy2(STATIC / name, DOCS / name)

    (DOCS / "data").mkdir(exist_ok=True)
    payload = _gather()
    (DOCS / "data" / "vocab.json").write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    size = (DOCS / "data" / "vocab.json").stat().st_size
    logger.info("vocab.json: %d cards, %d KB", len(payload["cards"]), size // 1024)

    shutil.copy2(ASSETS / "cover.png", DOCS / "cover.png")

    n_audio = _copy_tree(AUDIO, DOCS / "audio")
    n_sent = _copy_tree(AUDIO_SENT, DOCS / "audio_sent")
    n_svg = _copy_tree(SVG, DOCS / "svg")
    logger.info("media: audio=%d sentence_audio=%d svg=%d", n_audio, n_sent, n_svg)

    nojekyll = DOCS / ".nojekyll"
    if not nojekyll.exists():
        nojekyll.touch()

    total_mb = sum(p.stat().st_size for p in DOCS.rglob("*") if p.is_file()) / 1024 / 1024
    logger.info("docs/ ready: %.1f MB", total_mb)
