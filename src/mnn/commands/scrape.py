"""mnn scrape — scrape learnjapaneseaz lessons 1-50."""
from mnn.sources.learnjapaneseaz import scrape_all


def run(force: bool = False) -> None:
    for _ in scrape_all(force=force):
        pass
