from __future__ import annotations

import sqlite3
from pathlib import Path


_CREATE_CHUNKS = """
CREATE TABLE IF NOT EXISTS chunks (
    id             INTEGER PRIMARY KEY,
    process_number TEXT    NOT NULL,
    filename       TEXT    NOT NULL,
    page_number    INTEGER NOT NULL,
    chunk_index    INTEGER NOT NULL,
    char_offset    INTEGER NOT NULL,
    text           TEXT    NOT NULL,
    text_length    INTEGER NOT NULL,
    page_total     INTEGER NOT NULL,
    ocr_used       INTEGER NOT NULL,
    source_type    TEXT    NOT NULL,
    UNIQUE (process_number, filename, page_number, chunk_index)
);
"""

_CREATE_CHUNKS_FTS = """
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts
USING fts5(
    text,
    content='chunks',
    content_rowid='id',
    tokenize='unicode61 remove_diacritics 2'
);
"""


# Canonical document index (ADR-0074): where each document starts and ends
# inside each file, and the genre every chunk inherits from its document.
# Derived data, rebuilt from the chunks whenever they or the rules change.
_CREATE_DOCUMENT_INDEX = """
CREATE TABLE IF NOT EXISTS document_index (
    process_number      TEXT    NOT NULL,
    filename            TEXT    NOT NULL,
    segment_index       INTEGER NOT NULL,
    page_start          INTEGER NOT NULL,
    page_end            INTEGER NOT NULL,
    start_reason        TEXT    NOT NULL,
    doc_type            TEXT,
    title               TEXT,
    genre               TEXT    NOT NULL,
    genre_basis         TEXT    NOT NULL,
    n_chunks            INTEGER NOT NULL,
    n_chunks_instrument INTEGER NOT NULL,
    rules_version       TEXT    NOT NULL,
    PRIMARY KEY (process_number, filename, segment_index)
);
"""

_CREATE_CHUNK_GENRE = """
CREATE TABLE IF NOT EXISTS chunk_genre (
    process_number TEXT    NOT NULL,
    filename       TEXT    NOT NULL,
    page_number    INTEGER NOT NULL,
    chunk_index    INTEGER NOT NULL,
    segment_index  INTEGER NOT NULL,
    chunk_label    TEXT    NOT NULL,
    genre          TEXT    NOT NULL,
    narrative_section TEXT,
    rules_version  TEXT    NOT NULL,
    PRIMARY KEY (process_number, filename, page_number, chunk_index)
);
"""

_CREATE_DOCUMENT_INDEX_STATE = """
CREATE TABLE IF NOT EXISTS document_index_state (
    process_number TEXT PRIMARY KEY,
    rules_version  TEXT    NOT NULL,
    chunk_count    INTEGER NOT NULL,
    chunk_checksum TEXT    NOT NULL,
    built_at       TEXT    NOT NULL
);
"""

GENRE_TABLES_DDL = (_CREATE_DOCUMENT_INDEX, _CREATE_CHUNK_GENRE, _CREATE_DOCUMENT_INDEX_STATE)


def create_genre_tables(con: sqlite3.Connection) -> None:
    """Create the document-index tables. They hold derived data only, so a
    chunk_genre table of an older shape (before the narrative_section column,
    ADR-0077) is dropped with its state and rebuilt on the next read."""
    columns = {row[1] for row in con.execute("PRAGMA table_info(chunk_genre)")}
    if columns and "narrative_section" not in columns:
        for table in ("document_index_state", "chunk_genre", "document_index"):
            con.execute(f"DROP TABLE IF EXISTS {table}")
    for ddl in GENRE_TABLES_DDL:
        con.execute(ddl)


def init_db(db_path: str | Path) -> None:
    con = sqlite3.connect(str(db_path))
    try:
        con.execute("PRAGMA journal_mode=WAL;")
        con.execute(_CREATE_CHUNKS)
        con.execute(_CREATE_CHUNKS_FTS)
        create_genre_tables(con)
        con.commit()
    finally:
        con.close()
