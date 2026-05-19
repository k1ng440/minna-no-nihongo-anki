# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Anki review history is preserved across upgrades within the same major version.
See [`RELEASING.md`](RELEASING.md) for the stable-ID contract and what counts as
a breaking change.

## [Unreleased]

## [1.1.0] — 2026-05-20

GUIDs, note model IDs, and deck IDs are unchanged — review history is preserved.

### Added

- Bangladeshi Bengali (Bangla) localization for word meanings and example
  sentence translations. Renders alongside the English fields on every card.
- Live web demo: <https://k1ng440.github.io/minna-no-nihongo-anki/>. Build via
  `mnn web`, serve locally via `mnn serve`.
- `mnn enrich mnemonics-bn` gains `--lesson N` (repeatable) and `--regen` flags
  for targeted regeneration.

### Fixed

- **251 wrong English meanings** auto-detected across 46 lessons via an LLM
  audit and patched. Notable: `イギリス` was labelled "Brother", `ドイツ` was
  labelled "Virtue", a Vietnamese fragment had leaked into one entry, and an
  Excel auto-format had turned `1/4` into `4-Jan`. Affected Bangla meanings
  re-translated.
- KanjiVG SVGs now embed inline in cards (Anki webviews on some platforms
  block `<img src=*.svg>`); DOCTYPE + internal subset stripped before
  embedding.
- Stroke-order animation replay now uses `setTimeout` instead of the
  `offsetWidth` reflow trick, which was unreliable inside Anki's constrained
  webview.
- Multi-kanji words now animate sequentially with per-kanji delays derived
  from stroke counts, instead of all kanji firing at once.
- Card `onclick` handlers switched from ES6 arrow syntax to traditional
  `function` for compatibility with older Anki clients.
- Web build now ships `docs/data`, `docs/audio`, and `docs/svg` so the GitHub
  Pages demo loads on a fresh clone.

### Changed

- The Bangla mnemonic field is suppressed in the deck and web build for this
  release while the generation pipeline matures. The cache, prompt, validator,
  and mustache template are kept in place — re-enabling is a one-line revert
  in `src/mnn/deck/builder.py` and `src/mnn/web/builder.py` once mnemonic
  quality is uniformly acceptable across all 50 lessons.
- Bangla mnemonic generation pipeline (still cached, not rendered) now uses a
  strict keyword-link prompt with category-spanning few-shots, a per-row
  script/length/punctuation validator, a meaning-accuracy check against
  `cache/meanings_bn/` with Bangla synonym groups, and a soft-fail accumulator
  across retries so paraphrase doesn't yield a `null`.

## [1.0.0] — 2026-05-18

Initial public release.

### Deck contents

- **2,156 vocabulary words** spanning all 50 lessons of Minna no Nihongo
  Shokyu I + II (Second Edition).
- **50 per-lesson sub-decks** (`Lesson 01` … `Lesson 50`) plus a `Start Here`
  introduction deck pinned to the top of the deck list.
- **4,310 quiz cards** — 4-option multiple-choice reviews, one set per lesson,
  in optional `Quiz :: Lesson NN` sub-decks.
- **Per-lesson seasonal themes** with an evolving mascot that advances every
  10 lessons.

### Card features

- Native Japanese audio for every word and example sentence, generated with
  Microsoft Edge TTS (`ja-JP-NanamiNeural`).
- Pitch-accent coloring and contour overlays sourced from `kanjium`.
- Stroke-order SVG animations for each kanji, processed from `KanjiVG` and
  rendered with `currentColor` so they adapt to Anki's light/dark themes.
- Example sentences with English translations matched from the Tatoeba corpus
  (~85% hit rate across the deck).
- LLM-generated English mnemonics for each word (~98% coverage; uses local
  Ollama by default, OpenAI-compatible endpoints supported).
- Furigana over kanji, with a clean fallback for kana-only entries.

### Generator (`mnn` CLI)

- Production Python package (`src-layout`) installable via `uv sync`.
- Unified Typer CLI with 12 commands across 4 groups (`fetch`, `enrich`,
  `audio`, top-level).
- Centralized configuration via `.env` and a frozen `Settings` dataclass.
- Idempotent pipeline stages — every stage skips already-completed work on
  re-run. Use `--force` (where supported) or `mnn purge-cache --confirm` to
  start fresh.
- `mnn doctor` for environment + endpoint sanity checks.
- `mnn preview L:N` to render a single card to HTML before rebuilding.

### Data sources

- `learnjapaneseaz.com` — vocabulary list scrape.
- `tatoeba.org` — example sentences (CC BY 2.0 FR).
- `KanjiVG` — kanji stroke vectors (CC BY-SA 3.0).
- `kanjium` — pitch accent data (CC0).
- `JMdict` via Jisho.org — readings, glosses, parts of speech (CC BY-SA 4.0).
- Microsoft Edge TTS — spoken audio.

Full attribution and licensing in [`ATTRIBUTIONS.md`](ATTRIBUTIONS.md).

### Licensing

- Source code: MIT.
- Generated deck and bundled media: CC BY-SA 4.0 (inherited from KanjiVG and
  JMdict ShareAlike terms).

### Known limitations

- Tatoeba sentence coverage is partial (~85%); some vocab entries have no
  example sentence.
- Mnemonic quality depends on the LLM model used. The default local
  `gemma4:e4b` produces serviceable mnemonics; smaller models degrade fast.
- Pixabay image enrichment is disabled by default — image quality for
  vocabulary search is unreliable.

[Unreleased]: https://github.com/k1ng440/minna-no-nihongo-anki/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/k1ng440/minna-no-nihongo-anki/releases/tag/v1.0.0
