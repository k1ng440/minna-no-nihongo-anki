"""Kanjium pitch accent dataset."""
import requests

from mnn import log
from mnn.paths import DATA_KANJIUM
from mnn.util.io import skip_if_present

logger = log.get(__name__)

URL = "https://raw.githubusercontent.com/mifunetoshiro/kanjium/master/data/source_files/raw/accents.txt"


def fetch() -> None:
    DATA_KANJIUM.mkdir(parents=True, exist_ok=True)
    dst = DATA_KANJIUM / "accents.txt"
    if skip_if_present(dst, min_size=100_000):
        logger.info("kanjium: skip (%d bytes)", dst.stat().st_size)
        return
    logger.info("downloading kanjium accents")
    r = requests.get(URL, timeout=60)
    r.raise_for_status()
    dst.write_bytes(r.content)
    logger.info("kanjium: wrote %d bytes", len(r.content))
