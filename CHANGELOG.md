# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Anki review history is preserved across upgrades within the same major version.
See [`RELEASING.md`](RELEASING.md) for the stable-ID contract and what counts as
a breaking change.

## [Unreleased]

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
