from __future__ import annotations

from pathlib import Path

_db_path: Path | None = None


def configure(db_path: str | Path) -> None:
    global _db_path
    _db_path = Path(db_path)


def get_db_path() -> Path:
    if _db_path is None:
        raise RuntimeError(
            "Assessment module not configured. Call configure(db_path) before using the assessment module."
        )
    return _db_path


def _reset() -> None:
    global _db_path
    _db_path = None
