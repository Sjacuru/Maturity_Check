from __future__ import annotations

import sqlite3
from pathlib import Path


_CREATE_EVALUATION_RESULTS = """
CREATE TABLE IF NOT EXISTS evaluation_results (
    id              INTEGER PRIMARY KEY,
    acao_id         INTEGER NOT NULL,
    process_number  TEXT    NOT NULL,
    proposed_score  INTEGER,
    uncertainty_flag INTEGER NOT NULL DEFAULT 0,
    parse_failed    INTEGER NOT NULL DEFAULT 0,
    no_evidence_found INTEGER NOT NULL DEFAULT 0,
    provider        TEXT    NOT NULL,
    model           TEXT    NOT NULL,
    created_at      TEXT    NOT NULL,
    raw_json        TEXT    NOT NULL,
    UNIQUE (acao_id, process_number)
);
"""

# final_score is NULL exactly when the auditor marked the Ação not applicable
# (ADR-0076): no score, out of the nota's denominator. The CHECK says so with an
# explicit IS NOT NULL, because SQLite lets a CHECK that evaluates to NULL pass.
_REVIEW_OUTCOMES_COLUMNS = """
    id                  INTEGER PRIMARY KEY,
    acao_id             INTEGER NOT NULL,
    process_number      TEXT    NOT NULL,
    final_score         INTEGER,
    is_override         INTEGER NOT NULL,
    justification       TEXT,
    evidence_references TEXT,
    created_at          TEXT    NOT NULL,
    not_applicable      INTEGER NOT NULL DEFAULT 0,
    UNIQUE (acao_id, process_number),
    CHECK ((not_applicable = 0 AND final_score IS NOT NULL AND final_score IN (0, 1, 3))
        OR (not_applicable = 1 AND final_score IS NULL))
"""

_CREATE_REVIEW_OUTCOMES = (
    f"CREATE TABLE IF NOT EXISTS review_outcomes ({_REVIEW_OUTCOMES_COLUMNS});"
)

_CREATE_DOCUMENT_FINGERPRINTS = """
CREATE TABLE IF NOT EXISTS document_fingerprints (
    process_number  TEXT NOT NULL,
    filename        TEXT NOT NULL,
    sha256          TEXT NOT NULL,
    indexed_at      TEXT NOT NULL,
    PRIMARY KEY (process_number, filename)
);
"""


def init_db(db_path: str | Path) -> None:
    con = sqlite3.connect(str(db_path))
    try:
        con.execute("PRAGMA journal_mode=WAL;")
        con.execute(_CREATE_EVALUATION_RESULTS)
        con.execute(_CREATE_REVIEW_OUTCOMES)
        con.execute(_CREATE_DOCUMENT_FINGERPRINTS)
        con.commit()
        _migrate_review_outcomes(con)
    finally:
        con.close()


def _migrate_review_outcomes(con: sqlite3.Connection) -> None:
    """A database created before ADR-0076 has final_score NOT NULL and no
    not_applicable column. SQLite cannot drop a NOT NULL in place, so the table
    is rebuilt and its rows copied, in one transaction (sqlite.org/lang_altertable,
    "Making Other Kinds Of Table Schema Changes")."""
    columns = {row[1] for row in con.execute("PRAGMA table_info(review_outcomes)")}
    if "not_applicable" in columns:
        return
    try:
        con.execute("BEGIN")
        con.execute(f"CREATE TABLE review_outcomes_new ({_REVIEW_OUTCOMES_COLUMNS})")
        con.execute(
            "INSERT INTO review_outcomes_new (id, acao_id, process_number, final_score, "
            "is_override, justification, evidence_references, created_at) "
            "SELECT id, acao_id, process_number, final_score, is_override, justification, "
            "evidence_references, created_at FROM review_outcomes"
        )
        con.execute("DROP TABLE review_outcomes")
        con.execute("ALTER TABLE review_outcomes_new RENAME TO review_outcomes")
        con.commit()
    except BaseException:
        con.rollback()
        raise
