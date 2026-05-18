"""mnn all — full pipeline orchestrator (resumable, idempotent)."""
import asyncio

from mnn import log
from mnn.commands import scrape as scrape_cmd
from mnn.deck import builder
from mnn.enrich import audio, clean, fill_kanji, kanji_svg, mnemonics, pitch, quiz, sentences
from mnn.sources import kanjium, kanjivg, tatoeba

logger = log.get(__name__)


def run(force: bool = False) -> None:
    logger.info("=== fetch ===")
    tatoeba.fetch()
    kanjivg.fetch()
    kanjium.fetch()

    logger.info("=== scrape ===")
    scrape_cmd.run(force=force)

    logger.info("=== clean ===")
    clean.run()
    asyncio.run(fill_kanji.run())

    logger.info("=== enrich ===")
    pitch.build_lookup()
    kanji_svg.run()
    sentences.run()
    asyncio.run(mnemonics.run())
    quiz.run()

    logger.info("=== audio ===")
    asyncio.run(audio.run_all())

    logger.info("=== build ===")
    builder.run()
