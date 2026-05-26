from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_DATA_FILE = Path(__file__).parent.parent.parent / "data" / "acronyms" / "acronyms.json"

_store: dict[str, str] | None = None


def get_acronym_store() -> dict[str, str]:
    global _store
    if _store is None:
        _store = _load()
    return _store


def _load() -> dict[str, str]:
    if not _DATA_FILE.exists():
        raise RuntimeError(f"Acronym file not found: {_DATA_FILE}")

    try:
        raw = json.loads(_DATA_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise RuntimeError(f"Cannot read {_DATA_FILE.name}: {exc}") from exc

    if not isinstance(raw, dict):
        raise RuntimeError(f"Expected a JSON object in {_DATA_FILE.name}, got {type(raw).__name__}")

    result: dict[str, str] = {}
    skipped = 0
    for key, value in raw.items():
        if not isinstance(key, str) or not key.strip():
            logger.warning("Skipping acronym entry — invalid key: %r", key)
            skipped += 1
            continue
        if not isinstance(value, str) or not value.strip():
            logger.warning("Skipping acronym entry %r — invalid value: %r", key, value)
            skipped += 1
            continue
        result[key] = value

    logger.info(
        "Loaded %d acronyms. Skipped: %d",
        len(result),
        skipped,
    )
    return result
