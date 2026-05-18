"""Rich-backed logging."""
import logging

from rich.logging import RichHandler

_LOG_INIT = False


def setup(verbose: bool = False, quiet: bool = False) -> None:
    global _LOG_INIT
    level = logging.DEBUG if verbose else (logging.WARNING if quiet else logging.INFO)
    if _LOG_INIT:
        logging.getLogger().setLevel(level)
        return
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, show_path=False, markup=False)],
    )
    _LOG_INIT = True


def get(name: str) -> logging.Logger:
    return logging.getLogger(name)
