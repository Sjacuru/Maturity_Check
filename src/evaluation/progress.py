from __future__ import annotations

from typing import Callable

# (stage, message, level) -> None. level is one of:
# "info" | "waiting" | "warning" | "error" | "success"
ProgressCallback = Callable[[str, str, str], None]

# Module-level global, not a contextvar: Phase 1 scope (ADR-0027) runs
# exactly one assessment at a time, so a single global reporter is correct
# and avoids fighting contextvar propagation across the per-product
# ThreadPoolExecutor in evidence_selection.py (plain concurrent.futures
# workers do not inherit the submitting thread's contextvars automatically —
# only asyncio's own executor integration does that). Revisit if concurrent
# assessments are ever supported (ADR-0055).
_reporter: ProgressCallback | None = None


def set_reporter(reporter: ProgressCallback | None) -> None:
    global _reporter
    _reporter = reporter


def report(stage: str, message: str, level: str = "info") -> None:
    """No-op when no reporter is registered (e.g. in tests, or callers that
    don't go through AssessmentService). Never raises — a progress-reporting
    failure must not interrupt the actual assessment."""
    if _reporter is None:
        return
    try:
        _reporter(stage, message, level)
    except Exception:  # noqa: BLE001 - progress reporting must never break the run
        pass
