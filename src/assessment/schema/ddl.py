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

_CREATE_REVIEW_OUTCOMES = """
CREATE TABLE IF NOT EXISTS review_outcomes (
    id                  INTEGER PRIMARY KEY,
    acao_id             INTEGER NOT NULL,
    process_number      TEXT    NOT NULL,
    final_score         INTEGER NOT NULL,
    is_override         INTEGER NOT NULL,
    justification       TEXT,
    evidence_references TEXT,
    created_at          TEXT    NOT NULL,
    UNIQUE (acao_id, process_number)
);
"""

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
    finally:
        con.close()
