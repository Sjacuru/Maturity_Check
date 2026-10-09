"""Gate verdict ledger — the relevance gate's verdicts, frozen by construction.

ADR-0067. After ADR-0058–0065 the gate's remaining non-determinism is a handful
of borderline chunks whose verdict depends on what the server computed just
before them (Ação 3's p.161, Ação 22's p.145 — stable in isolation, not in a
run). No engine setting removes that residue without touching server internals,
so it is removed at the application layer: the FIRST verdict the model gives for
a (model, reasoning effort, system prompt, user prompt) tuple is recorded here,
and every later identical call is answered from the record instead of being
re-asked. Same input → same verdict, which is the reproducibility the project
owes its reviewers (CLAUDE.md Decision 7).

The key is a SHA-256 over exactly those four strings. The system prompt carries
the Ação's identity block, the product's criterion, concepts, negative patterns
and the sibling list; the user prompt carries the chunk text. Any profile
correction, prompt-builder change, model swap or re-extraction therefore changes
the key for exactly the calls it affects, and those are re-judged; nothing else
moves. Process number is deliberately NOT part of the key: the same criterion
applied to the same text is the same question whichever case it appears in.

The auditor can overturn a recorded verdict (`override`); the row then answers
with source="auditor" and keeps the justification. Failed calls (truncation,
unparseable output) are never recorded — a broken call is not a verdict
(ADR-0060).

Measurement runs (scripts/diagnostics/reproducibility.py) switch the ledger off:
with it on, a repeated run would trivially agree with itself and measure nothing.
"""

from __future__ import annotations

import hashlib
import logging
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

SOURCE_MODEL = "model"
SOURCE_AUDITOR = "auditor"

_DDL = """
CREATE TABLE IF NOT EXISTS gate_verdicts (
    prompt_hash           TEXT PRIMARY KEY,
    relevant              INTEGER NOT NULL,
    source                TEXT NOT NULL,
    reasoning             TEXT,
    model                 TEXT,
    reasoning_effort      TEXT,
    acao_id               INTEGER,
    product_id            TEXT,
    process_number        TEXT,
    filename              TEXT,
    page_number           INTEGER,
    chunk_index           INTEGER,
    created_at            TEXT NOT NULL,
    overridden_at         TEXT,
    override_justification TEXT
);
CREATE INDEX IF NOT EXISTS idx_gate_verdicts_acao ON gate_verdicts (acao_id, product_id);
"""


@dataclass(frozen=True)
class LedgerEntry:
    prompt_hash: str
    relevant: bool
    source: str                   # "model" | "auditor"
    reasoning: str | None
    model: str | None
    reasoning_effort: str | None
    acao_id: int | None
    product_id: str | None
    created_at: str
    overridden_at: str | None = None
    override_justification: str | None = None


def prompt_hash(model: str | None, reasoning_effort: str | None, system: str, user: str) -> str:
    """The ledger key. Field separator 0x1f keeps "ab"+"c" and "a"+"bc" apart."""
    h = hashlib.sha256()
    for part in (model or "", reasoning_effort or "", system, user):
        h.update(part.encode("utf-8"))
        h.update(b"\x1f")
    return h.hexdigest()


class GateLedger:
    """SQLite-backed ledger. One table in the shared app DB (ADR-0024: the
    evaluation module owns `gate_verdicts`). Thread-safe for the serial gate
    and for the pool mode alike — one lock around each statement."""

    def __init__(self, db_path: Path | str) -> None:
        self._db_path = str(db_path)
        self._lock = threading.Lock()
        with self._tx() as con:
            con.executescript(_DDL)

    @contextmanager
    def _tx(self):
        """One short-lived connection per statement: commit on success, always
        closed (the gate makes thousands of calls per run; `with con:` alone
        commits but never closes)."""
        con = sqlite3.connect(self._db_path, timeout=30)
        try:
            con.execute("PRAGMA journal_mode=WAL")
            with con:
                yield con
        finally:
            con.close()

    # -- reads ---------------------------------------------------------------

    def lookup(self, key: str) -> LedgerEntry | None:
        with self._lock, self._tx() as con:
            row = con.execute(
                "SELECT prompt_hash, relevant, source, reasoning, model, reasoning_effort, "
                "acao_id, product_id, created_at, overridden_at, override_justification "
                "FROM gate_verdicts WHERE prompt_hash = ?",
                (key,),
            ).fetchone()
        return _to_entry(row) if row else None

    def count(self) -> int:
        with self._lock, self._tx() as con:
            return con.execute("SELECT COUNT(*) FROM gate_verdicts").fetchone()[0]

    # -- writes --------------------------------------------------------------

    def record(
        self,
        key: str,
        *,
        relevant: bool,
        reasoning: str | None,
        model: str | None,
        reasoning_effort: str | None,
        acao_id: int | None = None,
        product_id: str | None = None,
        process_number: str | None = None,
        filename: str | None = None,
        page_number: int | None = None,
        chunk_index: int | None = None,
    ) -> None:
        """First verdict wins: an existing row (model or auditor) is left alone."""
        with self._lock, self._tx() as con:
            con.execute(
                "INSERT OR IGNORE INTO gate_verdicts (prompt_hash, relevant, source, reasoning, "
                "model, reasoning_effort, acao_id, product_id, process_number, filename, "
                "page_number, chunk_index, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    key, int(relevant), SOURCE_MODEL, reasoning, model, reasoning_effort,
                    acao_id, product_id, process_number, filename, page_number, chunk_index,
                    _now(),
                ),
            )

    def override(self, key: str, *, relevant: bool, justification: str) -> LedgerEntry:
        """The auditor's verdict replaces the recorded one for every later call
        with the same key. Requires a justification; raises KeyError when the
        key was never judged (there is nothing to overturn)."""
        if not justification or not justification.strip():
            raise ValueError("an override requires a non-empty justification")
        with self._lock, self._tx() as con:
            cur = con.execute(
                "UPDATE gate_verdicts SET relevant = ?, source = ?, overridden_at = ?, "
                "override_justification = ? WHERE prompt_hash = ?",
                (int(relevant), SOURCE_AUDITOR, _now(), justification.strip(), key),
            )
            if cur.rowcount == 0:
                raise KeyError(key)
        entry = self.lookup(key)
        assert entry is not None
        logger.info(
            "Gate verdict overridden by auditor: %s (acao %s, product %s) -> relevant=%s",
            key[:12], entry.acao_id, entry.product_id, relevant,
        )
        return entry


def _to_entry(row: tuple) -> LedgerEntry:
    return LedgerEntry(
        prompt_hash=row[0], relevant=bool(row[1]), source=row[2], reasoning=row[3],
        model=row[4], reasoning_effort=row[5], acao_id=row[6], product_id=row[7],
        created_at=row[8], overridden_at=row[9], override_justification=row[10],
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
