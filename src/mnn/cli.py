"""Typer CLI entry point — all subcommands."""
from __future__ import annotations

import typer

from mnn import log
from mnn.paths import ensure_dirs

app = typer.Typer(
    name="mnn",
    help="Minna no Nihongo enriched Anki deck generator.",
    no_args_is_help=True,
    add_completion=False,
)
fetch_app = typer.Typer(help="Download external data sources.", no_args_is_help=True)
audio_app = typer.Typer(help="Generate edge-tts audio.", no_args_is_help=True)
enrich_app = typer.Typer(help="Per-source enrichment steps.", no_args_is_help=True)
app.add_typer(fetch_app, name="fetch")
app.add_typer(audio_app, name="audio")
app.add_typer(enrich_app, name="enrich")


@app.callback()
def _root(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="DEBUG logging."),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="WARN+ only."),
) -> None:
    log.setup(verbose=verbose, quiet=quiet)
    ensure_dirs()


@app.command()
def doctor() -> None:
    """Check environment, credentials, and data files."""
    from mnn.commands.doctor import run
    run()


@app.command()
def scrape(force: bool = typer.Option(False, "--force", help="Refetch even if cached.")) -> None:
    """Scrape vocabulary lists from learnjapaneseaz.com."""
    from mnn.commands.scrape import run
    run(force=force)


@fetch_app.command("tatoeba")
def fetch_tatoeba() -> None:
    """Download Tatoeba JP+EN sentence corpus."""
    from mnn.sources import tatoeba
    tatoeba.fetch()


@fetch_app.command("kanjivg")
def fetch_kanjivg() -> None:
    """Download KanjiVG SVGs."""
    from mnn.sources import kanjivg
    kanjivg.fetch()


@fetch_app.command("kanjium")
def fetch_kanjium() -> None:
    """Download kanjium pitch accent data."""
    from mnn.sources import kanjium
    kanjium.fetch()


@fetch_app.command("all")
def fetch_all() -> None:
    """Fetch all external data sources."""
    from mnn.sources import tatoeba, kanjivg, kanjium
    tatoeba.fetch()
    kanjivg.fetch()
    kanjium.fetch()


@app.command()
def clean(
    fill_kanji: bool = typer.Option(False, "--fill-kanji", help="Look up missing kanji via jisho."),
    force: bool = typer.Option(False, "--force", help="Re-clean even if cleaned cache exists."),
) -> None:
    """Validate scrape, write cleaned cache."""
    from mnn.enrich import clean as cln
    cln.run(force=force)
    if fill_kanji:
        from mnn.enrich import fill_kanji as fk
        import asyncio
        asyncio.run(fk.run())


@audio_app.command("words")
def audio_words() -> None:
    """edge-tts mp3 for every vocab kana."""
    from mnn.enrich import audio
    import asyncio
    asyncio.run(audio.run_words())


@audio_app.command("sentences")
def audio_sentences() -> None:
    """edge-tts mp3 for every Tatoeba sentence."""
    from mnn.enrich import audio
    import asyncio
    asyncio.run(audio.run_sentences())


@audio_app.command("all")
def audio_all() -> None:
    """Both word + sentence audio."""
    from mnn.enrich import audio
    import asyncio
    asyncio.run(audio.run_all())


@enrich_app.command("pitch")
def enrich_pitch() -> None:
    """Build pitch accent lookup from kanjium."""
    from mnn.enrich import pitch
    pitch.build_lookup()


@enrich_app.command("kanji-svg")
def enrich_kanji_svg() -> None:
    """Copy KanjiVG SVGs for kanji used + animate them."""
    from mnn.enrich import kanji_svg
    kanji_svg.run()


@enrich_app.command("sentences")
def enrich_sentences() -> None:
    """Match Tatoeba sentences to vocab."""
    from mnn.enrich import sentences
    sentences.run()


@enrich_app.command("mnemonics")
def enrich_mnemonics() -> None:
    """LLM-generated mnemonics."""
    from mnn.enrich import mnemonics
    import asyncio
    asyncio.run(mnemonics.run())


@enrich_app.command("quiz")
def enrich_quiz() -> None:
    """Multi-choice quiz cards per lesson."""
    from mnn.enrich import quiz
    quiz.run()


@enrich_app.command("meanings-bn")
def enrich_meanings_bn() -> None:
    """LLM-translate meanings to Bangladeshi modern Bengali."""
    from mnn.enrich import meanings_bn
    import asyncio
    asyncio.run(meanings_bn.run())


@enrich_app.command("mnemonics-bn")
def enrich_mnemonics_bn(
    lesson: list[int] = typer.Option(None, "--lesson", "-l", help="Only this lesson (repeatable). Default: all."),
    regen: bool = typer.Option(False, "--regen", help="Ignore cache, regenerate all."),
) -> None:
    """LLM Bangla mnemonics (Bangladeshi modern Bengali)."""
    from mnn.enrich import mnemonics_bn
    import asyncio
    asyncio.run(mnemonics_bn.run(lessons=lesson or None, regen=regen))


@enrich_app.command("sentences-bn")
def enrich_sentences_bn() -> None:
    """LLM-translate Tatoeba EN sentences to Bangladeshi modern Bengali."""
    from mnn.enrich import sentences_bn
    import asyncio
    asyncio.run(sentences_bn.run())


@enrich_app.command("bn-all")
def enrich_bn_all() -> None:
    """Run all Bangla enrichments (meanings + mnemonics + sentences)."""
    import asyncio
    from mnn.enrich import meanings_bn, mnemonics_bn, sentences_bn
    asyncio.run(meanings_bn.run())
    asyncio.run(sentences_bn.run())
    asyncio.run(mnemonics_bn.run())


@enrich_app.command("all")
def enrich_all() -> None:
    """Run all enrich steps."""
    from mnn.commands.enrich_all import run
    run()


@app.command()
def build() -> None:
    """Assemble .apkg from caches."""
    from mnn.deck import builder
    builder.run()


@app.command("all")
def all_pipeline(force: bool = typer.Option(False, "--force")) -> None:
    """Run full pipeline: scrape → fetch → clean → enrich → audio → build."""
    from mnn.commands.all_pipeline import run
    run(force=force)


@app.command()
def preview(target: str = typer.Argument(..., help="Lesson:row, e.g. 30:5")) -> None:
    """Render a single card preview to out_preview.html."""
    from mnn.verify import preview as pv
    n, idx = target.split(":")
    pv(int(n), int(idx))


@app.command("web")
def web_build() -> None:
    """Build static web site into docs/ (for GitHub Pages)."""
    from mnn.web import builder as web_builder
    web_builder.run()


@app.command("verify")
def verify() -> None:
    """Verify vocab against Jisho API for discrepancies."""
    from mnn.commands.verify_jisho import run
    run()


@app.command("serve")
def serve(
    port: int = typer.Option(None, "--port", "-p", help="Override default. Falls back to other ports if busy."),
    no_open: bool = typer.Option(False, "--no-open", help="Don't auto-open browser."),
) -> None:
    """Serve docs/ locally. Default port from SERVE_PORT env (8765); falls back to 8766, 8000, 3000, 5173, OS-assigned."""
    from mnn.commands.serve import run as serve_run
    serve_run(port=port, open_browser=not no_open)


@app.command("purge-cache")
def purge_cache(confirm: bool = typer.Option(False, "--confirm", help="Required to actually delete.")) -> None:
    """Wipe cache/ to force a clean rebuild."""
    from mnn.commands.purge import run
    run(confirm=confirm)
