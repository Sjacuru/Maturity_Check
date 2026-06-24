from __future__ import annotations

import sqlite3

from retrieval._config import get_db_path
from retrieval.interfaces.contracts import RetrievedChunk

_PREV_SQL = """
    SELECT process_number, filename, page_number, chunk_index, char_offset,
           page_total, ocr_used, source_type, text
    FROM chunks
    WHERE process_number = ? AND filename = ?
      AND (page_number < ? OR (page_number = ? AND chunk_index < ?))
    ORDER BY page_number DESC, chunk_index DESC
    LIMIT 1
"""

_NEXT_SQL = """
    SELECT process_number, filename, page_number, chunk_index, char_offset,
           page_total, ocr_used, source_type, text
    FROM chunks
    WHERE process_number = ? AND filename = ?
      AND (page_number > ? OR (page_number = ? AND chunk_index > ?))
    ORDER BY page_number ASC, chunk_index ASC
    LIMIT 1
"""


def _row_to_chunk(row: tuple) -> RetrievedChunk:
    return RetrievedChunk(
        process_number=row[0],
        filename=row[1],
        page_number=row[2],
        chunk_index=row[3],
        char_offset=row[4],
        page_total=row[5],
        ocr_used=bool(row[6]),
        source_type=row[7],
        text=row[8],
        cascade_step="bm25",
        expected_product_id=None,
        bm25_score=None,
        rank=None,
    )


def fetch_neighbor_chunks(
    process_number: str,
    filename: str,
    page_number: int,
    chunk_index: int,
) -> tuple[RetrievedChunk | None, RetrievedChunk | None]:
    """Fetch the immediate previous and next chunk in document reading order.

    Reading order is (page_number, chunk_index) ascending within the same
    (process_number, filename) — the document's natural linear sequence,
    crossing page boundaries when the anchor is first/last on its page
    (ADR-0050). Returns (None, None) components when no such neighbor exists
    (e.g. anchor is the first or last chunk of the document).
    """
    con = sqlite3.connect(str(get_db_path()))
    try:
        prev_row = con.execute(
            _PREV_SQL, (process_number, filename, page_number, page_number, chunk_index)
        ).fetchone()
        next_row = con.execute(
            _NEXT_SQL, (process_number, filename, page_number, page_number, chunk_index)
        ).fetchone()
    finally:
        con.close()

    prev_chunk = _row_to_chunk(prev_row) if prev_row else None
    next_chunk = _row_to_chunk(next_row) if next_row else None
    return prev_chunk, next_chunk
