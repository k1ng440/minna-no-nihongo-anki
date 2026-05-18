"""Rich progress wrapper for long async batches."""
from rich.progress import BarColumn, MofNCompleteColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn


def make_progress(description: str) -> Progress:
    return Progress(
        SpinnerColumn(),
        TextColumn(description),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        transient=False,
    )
