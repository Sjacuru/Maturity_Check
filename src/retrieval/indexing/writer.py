from __future__ import annotations

import sqlite3

from extraction import Chunk
from retrieval._config import get_db_path


def index(process_number: str, chunks: list[Chunk]) -> None:
    if not chunks:
        return

    con = sqlite3.connect(str(get_db_path()))
    try:
        _check_schema(con)
        for chunk in chunks:
            _insert_chunk(con, process_number, chunk)
        con.commit()
    finally:
        con.close()


def _check_schema(con: sqlite3.Connection) -> None:
    row = con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='chunks'"
    ).fetchone()
    if not row:
        raise RuntimeError(
            "Retrieval database schema not initialised. Call init_db(db_path) before index()."
        )


def _insert_chunk(con: sqlite3.Connection, process_number: str, chunk: Chunk) -> None:
    prev = con.total_changes
    cur = con.execute(
        """
        INSERT OR IGNORE INTO chunks
            (process_number, filename, page_number, chunk_index, char_offset,
             text, text_length, page_total, ocr_used, source_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            process_number,
            chunk.filename,
            chunk.page_number,
            chunk.chunk_index,
            chunk.char_offset,
            chunk.text,
            chunk.text_length,
            chunk.page_total,
            int(chunk.ocr_used),
            chunk.source_type,
        ),
    )
    if con.total_changes > prev:
        con.execute(
            "INSERT INTO chunks_fts(rowid, text) VALUES (?, ?)",
            (cur.lastrowid, chunk.text),
        )
