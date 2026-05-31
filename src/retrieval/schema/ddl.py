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


def init_db(db_path: str | Path) -> None:
    con = sqlite3.connect(str(db_path))
    try:
        con.execute("PRAGMA journal_mode=WAL;")
        con.execute(_CREATE_CHUNKS)
        con.execute(_CREATE_CHUNKS_FTS)
        con.commit()
    finally:
        con.close()
