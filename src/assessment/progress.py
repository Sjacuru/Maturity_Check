from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field

# Bounds memory for a pathologically chatty run; the frontend only ever
# needs recent events, and a Phase 1 assessment (ADR-0051) is scoped to a
# handful of Ações at most.
_MAX_EVENTS = 300

_lock = threading.Lock()


@dataclass
class ProgressEvent:
    seq: int
    stage: str
    message: str
    level: str
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "seq": self.seq,
            "stage": self.stage,
            "message": self.message,
            "level": self.level,
            "timestamp": self.timestamp,
        }


@dataclass
class _ProcessLog:
    events: list[ProgressEvent] = field(default_factory=list)
    next_seq: int = 0


_logs: dict[str, _ProcessLog] = {}


def start_run(process_number: str) -> None:
    """Clear any prior run's events for this process — a fresh assessment
    must not show stale progress left over from an earlier attempt."""
    with _lock:
        _logs[process_number] = _ProcessLog()


def emit(process_number: str, stage: str, message: str, level: str = "info") -> None:
    with _lock:
        log = _logs.setdefault(process_number, _ProcessLog())
        log.events.append(ProgressEvent(seq=log.next_seq, stage=stage, message=message, level=level))
        log.next_seq += 1
        if len(log.events) > _MAX_EVENTS:
            del log.events[: len(log.events) - _MAX_EVENTS]


def get_events(process_number: str, since: int = 0) -> list[dict]:
    with _lock:
        log = _logs.get(process_number)
        if log is None:
            return []
        return [e.to_dict() for e in log.events if e.seq >= since]


def make_reporter(process_number: str):
    """Build an evaluation.progress.ProgressCallback bound to this process_number."""

    def _reporter(stage: str, message: str, level: str = "info") -> None:
        emit(process_number, stage, message, level)

    return _reporter
