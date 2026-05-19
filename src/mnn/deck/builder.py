"""Assemble enriched .apkg from caches. No network."""
import html
import json
import re

import genanki

from mnn import log
from mnn.config import settings
from mnn.deck import info
from mnn.deck.models import INFO_MODEL, QUIZ_MODEL, VOCAB_MODEL
from mnn.deck.themes import THEMES, tier
from mnn.enrich.pitch import render_or_plain
from mnn.paths import ASSETS, AUDIO, AUDIO_SENT, CACHE, CACHE_MNEMONICS, CACHE_QUIZ, CACHE_SENTENCES, IMAGES, SVG

BN_MEANINGS = CACHE / "meanings_bn"
BN_MNEMONICS = CACHE / "mnemonics_bn"
BN_SENTENCES = CACHE / "sentences_bn"
from mnn.util.io import read_json

logger = log.get(__name__)

INFO_NOTE_GUID = "mnn-info-start-here-v6"


def _kanji_svg_html(kanji: str, svg_map: dict[str, str]) -> str:
    """Inline SVG (Anki webview blocks <img src=*.svg> on some platforms)."""
    out = []
    for ch in kanji:
        if ch not in svg_map:
            continue
        svg_path = SVG / svg_map[ch]
        if not svg_path.exists():
            continue
        svg_text = svg_path.read_text()
        # strip XML decl + comments — Anki cards expect HTML fragments
        svg_text = re.sub(r"<\?xml[^>]*\?>", "", svg_text)
        svg_text = re.sub(r"<!--.*?-->", "", svg_text, flags=re.DOTALL)
        out.append(f'<span class="kanji-svg">{svg_text.strip()}</span>')
    return "".join(out)


def _cloze_sentence(jp: str, headwords: list[str]) -> str | None:
    for hw in headwords:
        if hw and hw in jp:
            return jp.replace(hw, f'<span class="cloze-blank">{hw}</span>', 1)
    return None


def _progress_bar(n: int, color: str) -> str:
    pct = n * 2
    return f'<div class="prog"><div class="prog-fill" style="width:{pct}%;background:{color}"></div></div>'


def _load_mascot(n: int) -> str:
    f = ASSETS / f"mascot_t{tier(n)}.svg"
    return f.read_text() if f.exists() else ""


def run() -> None:
    s = settings()
    svg_map = read_json(CACHE / "kanji_svg_map.json")

    info_body = info.build()

    parent = genanki.Deck(2000000000, s.parent_deck_name)
    parent.description = info_body
    decks = [parent]

    info_deck = genanki.Deck(2000000999, f"{s.parent_deck_name}::00 📖 Start Here")
    info_deck.description = info_body
    info_deck.add_note(
        genanki.Note(
            model=INFO_MODEL,
            fields=["Minna no Nihongo I + II", info_body],
            guid=genanki.guid_for(INFO_NOTE_GUID),
        )
    )
    decks.append(info_deck)

    media: set[str] = set()
    media.add(str(ASSETS / "cover.png"))

    all_vocab = all_quiz = 0
    for n in range(1, 51):
        cleaned_f = CACHE / f"lesson_{n}.cleaned.json"
        if not cleaned_f.exists():
            continue
        rows = read_json(cleaned_f)
        sents = read_json(CACHE_SENTENCES / f"lesson_{n}.json") if (CACHE_SENTENCES / f"lesson_{n}.json").exists() else {}
        mnem = read_json(CACHE_MNEMONICS / f"lesson_{n}.json") if (CACHE_MNEMONICS / f"lesson_{n}.json").exists() else {}
        bn_meanings = read_json(BN_MEANINGS / f"lesson_{n}.json") if (BN_MEANINGS / f"lesson_{n}.json").exists() else {}
        bn_mnem = read_json(BN_MNEMONICS / f"lesson_{n}.json") if (BN_MNEMONICS / f"lesson_{n}.json").exists() else {}
        bn_sents = read_json(BN_SENTENCES / f"lesson_{n}.json") if (BN_SENTENCES / f"lesson_{n}.json").exists() else {}
        theme = THEMES[n]
        mascot_svg = _load_mascot(n)
        progress = _progress_bar(n, theme["color"])

        vocab_deck = genanki.Deck(2000000000 + n, f"{s.parent_deck_name}::Lesson {n:02d}")
        quiz_deck = genanki.Deck(2000001000 + n, f"{s.parent_deck_name}::Quiz::Lesson {n:02d}")

        for row in rows:
            kanji = row["kanji"]
            kana = row["kana"]
            meaning = row["meaning"]
            audio_fn = row.get("audio", "")
            audio_field = ""
            if kana and audio_fn and (AUDIO / audio_fn).exists():
                audio_field = f"[sound:{audio_fn}]"
                media.add(str(AUDIO / audio_fn))
            kana_pitch = render_or_plain(kanji, kana)

            sent = sents.get(kana)
            sent_jp = sent_en = sent_audio = sent_cloze = sent_bn = ""
            if sent:
                sent_jp = html.escape(sent["jp"])
                sent_en = html.escape(sent["en"])
                snt_fn = sent["audio"]
                if (AUDIO_SENT / snt_fn).exists():
                    sent_audio = f"[sound:{snt_fn}]"
                    media.add(str(AUDIO_SENT / snt_fn))
                cz = _cloze_sentence(sent["jp"], [kanji, kana])
                if cz:
                    sent_cloze = cz
                bn_translated = bn_sents.get(sent["en"])
                if bn_translated:
                    sent_bn = html.escape(bn_translated)

            kanji_html = _kanji_svg_html(kanji, svg_map)
            for ch in kanji:
                if ch in svg_map:
                    media.add(str(SVG / svg_map[ch]))

            note = genanki.Note(
                model=VOCAB_MODEL,
                fields=[
                    html.escape(kanji), html.escape(kana), html.escape(meaning),
                    audio_field, str(n),
                    kana_pitch, sent_jp, sent_en, sent_audio, sent_cloze,
                    kanji_html, html.escape(mnem.get(row["guid"]) or ""), "",
                    mascot_svg, theme["color"], theme["emoji"], progress,
                    html.escape(bn_meanings.get(meaning) or ""),
                    html.escape(bn_mnem.get(row["guid"]) or ""),
                    sent_bn,
                ],
                guid=genanki.guid_for(row["guid"]),
            )
            vocab_deck.add_note(note)
            all_vocab += 1

        quiz_f = CACHE_QUIZ / f"lesson_{n}.json"
        if quiz_f.exists():
            for q in read_json(quiz_f):
                choices = q["choices"]
                while len(choices) < 4:
                    choices.append("")
                quiz_deck.add_note(
                    genanki.Note(
                        model=QUIZ_MODEL,
                        fields=[
                            html.escape(q["prompt"]),
                            html.escape(choices[0]), html.escape(choices[1]),
                            html.escape(choices[2]), html.escape(choices[3]),
                            q["correct_class"], str(n), q["direction"], theme["color"],
                        ],
                        guid=genanki.guid_for(q["guid"]),
                    )
                )
                all_quiz += 1

        decks.append(vocab_deck)
        decks.append(quiz_deck)
        logger.info("L%d: vocab=%d quiz=%d", n, len(rows), len(read_json(quiz_f)) if quiz_f.exists() else 0)

    out = s.output_apkg
    out.parent.mkdir(parents=True, exist_ok=True)
    pkg = genanki.Package(decks)
    pkg.media_files = sorted(media)
    pkg.write_to_file(out)
    size_mb = out.stat().st_size / 1024 / 1024
    logger.info("wrote %s (%.1f MB) — vocab=%d quiz=%d media=%d",
                out, size_mb, all_vocab, all_quiz, len(media))
