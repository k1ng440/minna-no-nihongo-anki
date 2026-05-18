"""Render a single card preview to out_preview.html."""
import json
import re

from mnn import log
from mnn.deck import info
from mnn.deck.models import VOCAB_MODEL
from mnn.deck.templates import CSS
from mnn.deck.themes import THEMES
from mnn.deck.builder import _cloze_sentence, _kanji_svg_html, _load_mascot, _progress_bar
from mnn.enrich.pitch import render_or_plain
from mnn.paths import CACHE, CACHE_MNEMONICS, CACHE_PIXABAY, CACHE_SENTENCES, ROOT
from mnn.util.io import read_json

logger = log.get(__name__)


def _expand(tmpl: str, fields: dict[str, str]) -> str:
    def cond_show(m):
        v = fields.get(m.group(1), "")
        return m.group(2) if v and v.strip() else ""

    def cond_hide(m):
        v = fields.get(m.group(1), "")
        return m.group(2) if not (v and v.strip()) else ""

    tmpl = re.sub(r"\{\{#(\w+)\}\}(.*?)\{\{/\1\}\}", cond_show, tmpl, flags=re.DOTALL)
    tmpl = re.sub(r"\{\{\^(\w+)\}\}(.*?)\{\{/\1\}\}", cond_hide, tmpl, flags=re.DOTALL)
    for k, v in fields.items():
        tmpl = tmpl.replace("{{" + k + "}}", v)
    return tmpl


def preview(n: int, idx: int) -> None:
    rows = read_json(CACHE / f"lesson_{n}.cleaned.json")
    row = rows[idx]
    sents = read_json(CACHE_SENTENCES / f"lesson_{n}.json") if (CACHE_SENTENCES / f"lesson_{n}.json").exists() else {}
    mnem_f = CACHE_MNEMONICS / f"lesson_{n}.json"
    mnem = read_json(mnem_f) if mnem_f.exists() else {}
    pix_f = CACHE_PIXABAY / f"lesson_{n}.json"
    pix = read_json(pix_f) if pix_f.exists() else {}
    svg_map = read_json(CACHE / "kanji_svg_map.json")

    logger.info("preview: L%d #%s %s %s = %s", n, row["no"], row["kanji"], row["kana"], row["meaning"])

    sent = sents.get(row["kana"]) or {}
    fields = dict.fromkeys([f["name"] for f in VOCAB_MODEL.fields], "")
    fields.update({
        "Kanji": row["kanji"],
        "Kana": row["kana"],
        "Meaning": row["meaning"],
        "Lesson": str(n),
        "KanaPitch": render_or_plain(row["kanji"], row["kana"]),
        "SentenceJP": sent.get("jp", ""),
        "SentenceEN": sent.get("en", ""),
        "SentenceCloze": _cloze_sentence(sent.get("jp", ""), [row["kanji"], row["kana"]]) or "",
        "KanjiSVG": _kanji_svg_html(row["kanji"], svg_map),
        "Mnemonic": mnem.get(row["guid"]) or "",
        "Image": f'<img src="images/{pix.get(row["meaning"])}">' if pix.get(row["meaning"]) else "",
        "Mascot": _load_mascot(n),
        "LessonTheme": THEMES[n]["color"],
        "LessonEmoji": THEMES[n]["emoji"],
        "ProgressBar": _progress_bar(n, THEMES[n]["color"]),
    })

    out = [f"<!doctype html><html><head><meta charset=utf-8><style>{CSS}</style></head><body>"]
    for tmpl in VOCAB_MODEL.templates:
        out.append(f'<h3>{tmpl["name"]}</h3>')
        front = _expand(tmpl["qfmt"], fields)
        back = _expand(tmpl["afmt"].replace("{{FrontSide}}", front), fields)
        out.append(f'<div class="card">{back}</div><hr>')
    out.append('<h3>Info (Start Here)</h3>')
    out.append(f'<div class="card">{info.build()}</div>')
    out.append("</body></html>")
    dst = ROOT / "out_preview.html"
    dst.write_text("\n".join(out))
    logger.info("wrote %s", dst)
