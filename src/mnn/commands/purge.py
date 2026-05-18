"""mnn purge-cache — wipe cache/ to force a clean rebuild."""
import shutil

from mnn import log
from mnn.paths import CACHE

logger = log.get(__name__)


def run(confirm: bool = False) -> None:
    if not confirm:
        logger.warning("dry-run only — pass --confirm to actually delete %s", CACHE)
        return
    if CACHE.exists():
        shutil.rmtree(CACHE)
    CACHE.mkdir(parents=True, exist_ok=True)
    logger.info("cache wiped: %s", CACHE)
