"""mnn enrich all — pitch + kanji-svg + sentences + mnemonics + quiz."""
import asyncio

from mnn.enrich import kanji_svg, mnemonics, pitch, quiz, sentences


def run() -> None:
    pitch.build_lookup()
    kanji_svg.run()
    sentences.run()
    asyncio.run(mnemonics.run())
    quiz.run()
