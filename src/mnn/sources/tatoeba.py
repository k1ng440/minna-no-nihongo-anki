"""Tatoeba sentence corpus + JP-EN indices (CC-BY 2.0 FR)."""
import bz2

import requests

from mnn import log
from mnn.paths import DATA_TATOEBA
from mnn.util.io import skip_if_present

logger = log.get(__name__)

URLS: dict[str, tuple[str, bool]] = {
    "jpn_sentences.tsv": (
        "https://downloads.tatoeba.org/exports/per_language/jpn/jpn_sentences.tsv.bz2",
        True,
    ),
    "eng_sentences.tsv": (
        "https://downloads.tatoeba.org/exports/per_language/eng/eng_sentences.tsv.bz2",
        True,
    ),
    "jpn_indices.csv": (
        "https://downloads.tatoeba.org/exports/jpn_indices.csv",
        False,
    ),
}


def fetch() -> None:
    DATA_TATOEBA.mkdir(parents=True, exist_ok=True)
    for name, (url, is_bz2) in URLS.items():
        dst = DATA_TATOEBA / name
        if skip_if_present(dst, min_size=1000):
            logger.info("skip %s (%d bytes)", name, dst.stat().st_size)
            continue
        logger.info("downloading %s", url)
        r = requests.get(url, timeout=300)
        r.raise_for_status()
        data = bz2.decompress(r.content) if is_bz2 else r.content
        dst.write_bytes(data)
        logger.info("wrote %s (%d bytes)", dst, len(data))


def load_sentences(path, lang: str) -> dict[int, str]:
    out: dict[int, str] = {}
    with path.open() as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 3 and parts[1] == lang:
                try:
                    out[int(parts[0])] = parts[2]
                except ValueError:
                    pass
    return out


def load_jp_eng_links() -> dict[int, list[int]]:
    """jp_indices.csv: jp_id\\teng_id\\twords → {jp_id: [eng_id, ...]}."""
    from collections import defaultdict
    out: dict[int, list[int]] = defaultdict(list)
    with (DATA_TATOEBA / "jpn_indices.csv").open() as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 2:
                try:
                    jp = int(parts[0])
                    en = int(parts[1])
                    if en > 0:
                        out[jp].append(en)
                except ValueError:
                    pass
    return out
