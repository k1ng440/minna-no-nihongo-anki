"""JSON read/write + skip-if-exists guard."""
import json
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def skip_if_present(path: Path, min_size: int = 1) -> bool:
    return path.exists() and path.stat().st_size >= min_size
