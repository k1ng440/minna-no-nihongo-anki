# Attributions

The Minna no Nihongo vocab deck is assembled from multiple third-party data
sources. This file lists every source, its license, and how it is used in this
project. Please respect the upstream licenses when redistributing the deck or
forking the generator.

## Summary

| Source | Used for | License | Attribution required |
|--------|----------|---------|----------------------|
| KanjiVG | Kanji stroke-order SVG animations | CC BY-SA 3.0 | Yes |
| Tatoeba | Example sentences (JP + translations) | CC BY 2.0 FR | Yes |
| JMdict / Jisho.org | Word definitions, readings, parts of speech | CC BY-SA 4.0 (EDRDG) | Yes |
| kanjium | Pitch accent data | Public domain / CC0 | Recommended |
| Pixabay | Mnemonic / illustrative images | Pixabay Content License | Not required, appreciated |
| Microsoft Edge TTS (via `edge-tts`) | Spoken audio for words and sentences | Microsoft service terms | N/A (service) |
| Minna no Nihongo (3A Corporation) | Source vocabulary list (ordering, lesson grouping) | Textbook © 3A Corporation | See note below |

## Detailed credits

### KanjiVG

- **Project:** KanjiVG — Kanji Vector Graphics
- **Author:** Ulrich Apel and contributors
- **URL:** https://kanjivg.tagaini.net/
- **License:** Creative Commons Attribution-ShareAlike 3.0 (CC BY-SA 3.0)
  https://creativecommons.org/licenses/by-sa/3.0/
- **Usage:** Per-kanji stroke-order SVG files are downloaded, post-processed
  (stroke-by-stroke animation classes, `currentColor` stroke, layout cleanup)
  and embedded as media in deck cards.
- **Obligation:** Attribution (above) plus ShareAlike — any redistribution of
  the derived SVGs or the deck as a whole must be under CC BY-SA 3.0 or a
  later compatible version. This is why the deck is licensed CC BY-SA 4.0.

### Tatoeba

- **Project:** Tatoeba Project
- **URL:** https://tatoeba.org/
- **License:** Creative Commons Attribution 2.0 France (CC BY 2.0 FR)
  https://creativecommons.org/licenses/by/2.0/fr/
- **Usage:** Japanese example sentences with English translations are matched
  to vocabulary words and embedded in cards. Individual sentence contributors
  are credited via Tatoeba's per-sentence attribution system; this deck
  attributes the corpus as a whole.
- **Obligation:** Attribution.

### JMdict / Jisho.org

- **Dictionary:** JMdict, maintained by the Electronic Dictionary Research and
  Development Group (EDRDG)
- **API frontend:** Jisho.org (https://jisho.org)
- **License:** Creative Commons Attribution-ShareAlike 4.0 (CC BY-SA 4.0)
  https://www.edrdg.org/edrdg/licence.html
- **Usage:** Word readings, English glosses, parts of speech, and kanji
  metadata are fetched via Jisho's API for vocabulary enrichment.
- **Obligation:** Attribution + ShareAlike. Compatible with the deck's
  CC BY-SA 4.0 license.

### kanjium

- **Project:** kanjium
- **Author:** Uros Ozvatic and contributors
- **URL:** https://github.com/mifunetoshiro/kanjium
- **License:** Public domain (per project README) — effectively CC0.
- **Usage:** Pitch accent data is consumed and rendered into pitch contour
  overlays on each word card.
- **Obligation:** None strictly required; credit given here in good faith.

### Pixabay

- **Service:** Pixabay (https://pixabay.com)
- **License:** Pixabay Content License
  https://pixabay.com/service/license-summary/
- **Usage:** Mnemonic / illustrative images are fetched per vocabulary word
  when the `pixabay` enrichment step is enabled.
- **Obligation:** Attribution not required by license, but acknowledged here.
  Note: the default deck build runs with Pixabay fetch **disabled**; users who
  enable it are responsible for complying with Pixabay's terms for any
  redistribution.

### Microsoft Edge TTS

- **Service:** Microsoft Edge online text-to-speech endpoints
- **Library:** `edge-tts` (Python) — MIT licensed, but unofficial
- **URL:** https://github.com/rany2/edge-tts
- **Usage:** Generates word-level and sentence-level audio (`.mp3`) embedded
  as media in deck cards.
- **Obligation:** Use is governed by Microsoft's service terms. Personal and
  educational use is permitted. Bulk redistribution of generated audio may be
  outside the spirit of Microsoft's intended use; included here under fair-use
  / educational reasoning. If Microsoft objects, audio media will be removed.

### Minna no Nihongo (textbook)

- **Publisher:** 3A Corporation
- **URL:** https://www.3anet.co.jp/np/en/
- **Usage:** This deck follows the vocabulary list, lesson order, and lesson
  grouping of the Minna no Nihongo textbook series (Shokyu I, II). No
  textbook text, illustrations, audio, or copyrighted prose are reproduced.
  Only the bare vocabulary (words and their standard dictionary readings /
  meanings, which are facts not subject to copyright) is referenced.
- **Note:** This deck is an unofficial study aid. It is not affiliated with,
  endorsed by, or licensed from 3A Corporation. Users are expected to own a
  copy of the textbook for full context, grammar explanations, and practice
  materials. If 3A Corporation requests changes, this project will comply.

## Deck license (downstream)

Because KanjiVG (CC BY-SA 3.0) and JMdict (CC BY-SA 4.0) impose ShareAlike
terms, the assembled deck and all bundled media are distributed under:

**Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)**
https://creativecommons.org/licenses/by-sa/4.0/

You are free to share and adapt the deck for any purpose, including
commercial, provided you give appropriate credit and distribute derivative
works under the same license.

The generator source code under `src/mnn/` is separately MIT-licensed — see
`LICENSE`.

## Reporting attribution issues

If you are a rights holder and believe your work is attributed incorrectly or
should not be included, open an issue on the GitHub repository or contact the
maintainer. Concerns will be addressed promptly.
