from __future__ import annotations

import re
import sqlite3
from pathlib import Path

from retrieval._config import get_db_path
from retrieval.interfaces.contracts import RetrievedChunk
from retrieval.query.bm25 import MAX_CHUNKS_PER_ACAO

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Module-level model cache. Populated lazily on first vector call.
_model = None


def _get_lancedb_path() -> Path:
    return get_db_path().parent / "lancedb"


def _table_name(process_number: str) -> str:
    """Sanitize process_number into a valid LanceDB table name."""
    return re.sub(r"[^a-zA-Z0-9_-]", "_", process_number)


def _get_model():
    global _model
    if _model is None:
        import sentence_transformers
        _model = sentence_transformers.SentenceTransformer(MODEL_NAME)
    return _model


def _fetch_chunks_from_sqlite(process_number: str) -> list[dict]:
    """Return all chunk rows for a process as plain dicts."""
    con = sqlite3.connect(str(get_db_path()))
    try:
        rows = con.execute(
            """
            SELECT process_number, filename, page_number, chunk_index,
                   char_offset, page_total, ocr_used, source_type, text
            FROM chunks
            WHERE process_number = ?
            ORDER BY filename, page_number, chunk_index
            """,
            (process_number,),
        ).fetchall()
    finally:
        con.close()

    return [
        {
            "process_number": r[0],
            "filename": r[1],
            "page_number": r[2],
            "chunk_index": r[3],
            "char_offset": r[4],
            "page_total": r[5],
            "ocr_used": r[6],
            "source_type": r[7],
            "text": r[8],
        }
        for r in rows
    ]


def ensure_vector_index_exists(process_number: str) -> None:
    """Populate the process-level LanceDB table from SQLite chunks if absent.

    No-op when the table already exists (reuse semantics, ADR-0035).
    No-op when there are no indexed chunks for the process.
    """
    import lancedb
    import numpy as np

    lancedb_path = _get_lancedb_path()
    db = lancedb.connect(str(lancedb_path))
    tname = _table_name(process_number)

    # Try opening the table first — avoids relying on list_tables() API which
    # varies across LanceDB versions and may lag behind in some backends.
    try:
        db.open_table(tname)
        return  # table exists — reuse semantics
    except Exception:
        pass

    chunk_rows = _fetch_chunks_from_sqlite(process_number)
    if not chunk_rows:
        return

    model = _get_model()
    texts = [r["text"] for r in chunk_rows]
    embeddings = model.encode(texts, convert_to_numpy=True)

    data = []
    for row, vec in zip(chunk_rows, embeddings):
        data.append({
            "chunk_index": row["chunk_index"],
            "filename": row["filename"],
            "page_number": row["page_number"],
            "char_offset": row["char_offset"],
            "page_total": row["page_total"],
            "ocr_used": row["ocr_used"],
            "source_type": row["source_type"],
            "text": row["text"],
            "vector": vec.astype(np.float32).tolist(),
        })

    db.create_table(tname, data=data)


def search_vector(
    process_number: str,
    query_text: str,
    k: int = MAX_CHUNKS_PER_ACAO,
) -> list[RetrievedChunk]:
    """Search the process-level LanceDB table for chunks similar to query_text.

    Returns [] when no vector index exists or can be built (no chunks indexed).
    All returned chunks carry retrieval_mode="vector_fallback".
    """
    import lancedb
    import numpy as np

    ensure_vector_index_exists(process_number)

    lancedb_path = _get_lancedb_path()
    db = lancedb.connect(str(lancedb_path))
    tname = _table_name(process_number)

    try:
        tbl = db.open_table(tname)
    except Exception:
        return []

    model = _get_model()
    query_vec = model.encode([query_text], convert_to_numpy=True)[0].astype(np.float32).tolist()

    hits = tbl.search(query_vec).limit(k).to_list()

    return [
        RetrievedChunk(
            process_number=process_number,
            filename=h["filename"],
            page_number=h["page_number"],
            chunk_index=h["chunk_index"],
            char_offset=h["char_offset"],
            page_total=h["page_total"],
            ocr_used=bool(h["ocr_used"]),
            source_type=h["source_type"],
            text=h["text"],
            cascade_step="vector",
            expected_product_id=None,
            bm25_score=None,
            rank=None,
            retrieval_mode="vector_fallback",
            retrieval_query=query_text,
        )
        for h in hits
    ]


def invalidate_vector_index(process_number: str) -> None:
    """Drop the process-level LanceDB table if it exists.

    Called during chunk replacement (fingerprint mismatch) so the vector index
    is rebuilt lazily from fresh chunks on the next fallback trigger (ADR-0040).
    """
    lancedb_path = _get_lancedb_path()
    if not lancedb_path.exists():
        return

    import lancedb

    db = lancedb.connect(str(lancedb_path))
    tname = _table_name(process_number)
    try:
        db.drop_table(tname)
    except Exception:
        pass  # table didn't exist — no-op


def _reset() -> None:
    """Reset module-level model cache. Used in tests for isolation."""
    global _model
    _model = None
