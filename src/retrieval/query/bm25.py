from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from retrieval._config import get_db_path
from retrieval.interfaces.contracts import RetrievedChunk

MAX_CHUNKS_PER_ACAO = 20

# Each product gets up to this many best-scoring chunks before cross-product dedup.
# 5 products × 5 = 25 candidates, minus physical duplicates → capped at MAX_CHUNKS_PER_ACAO.
_PER_PRODUCT_TARGET = 5

_PER_QUERY_LIMIT = MAX_CHUNKS_PER_ACAO * 4

_SCHEMA_CHECK = "SELECT name FROM sqlite_master WHERE type='table' AND name='chunks'"

_SEARCH_SQL = """
    SELECT
        c.id,
        c.process_number, c.filename, c.page_number, c.chunk_index,
        c.char_offset, c.page_total, c.ocr_used, c.source_type, c.text,
        chunks_fts.rank
    FROM chunks_fts
    JOIN chunks c ON chunks_fts.rowid = c.id
    WHERE chunks_fts MATCH ?
      AND c.process_number = ?
    ORDER BY chunks_fts.rank
    LIMIT ?
"""


@dataclass(frozen=True)
class _Hit:
    chunk_id: int
    product_id: str | None
    score: float
    query_str: str
    row: tuple  # (process_number, filename, page_number, chunk_index,
    #              char_offset, page_total, ocr_used, source_type, text)


def search_bm25(
    queries: dict[str, str],
    process_number: str,
) -> list[RetrievedChunk]:
    """Run per-Expected-Product FTS5 BM25 queries, merge, dedup, rank, cap.

    queries: mapping from expected_product_id to FTS5 query string.
             Empty-string values are skipped.
    """
    non_empty = {pid: q for pid, q in queries.items() if q}
    if not non_empty:
        return []

    con = sqlite3.connect(str(get_db_path()))
    try:
        if not con.execute(_SCHEMA_CHECK).fetchone():
            raise RuntimeError(
                "Retrieval database schema not initialised. "
                "Call init_db(db_path) before search_bm25()."
            )
        hits = _run_queries(con, non_empty, process_number)
    finally:
        con.close()

    merged = _merge(hits)
    merged.sort(key=lambda h: h.score)  # most negative = best BM25 match
    top = merged[:MAX_CHUNKS_PER_ACAO]

    return [
        RetrievedChunk(
            process_number=h.row[0],
            filename=h.row[1],
            page_number=h.row[2],
            chunk_index=h.row[3],
            char_offset=h.row[4],
            page_total=h.row[5],
            ocr_used=bool(h.row[6]),
            source_type=h.row[7],
            text=h.row[8],
            cascade_step="bm25",
            expected_product_id=h.product_id,
            bm25_score=h.score,
            rank=i + 1,
            retrieval_query=h.query_str,
        )
        for i, h in enumerate(top)
    ]


def _run_queries(
    con: sqlite3.Connection,
    queries: dict[str, str],
    process_number: str,
) -> list[_Hit]:
    hits: list[_Hit] = []
    for product_id, query_str in queries.items():
        try:
            rows = con.execute(
                _SEARCH_SQL, (query_str, process_number, _PER_QUERY_LIMIT)
            ).fetchall()
        except sqlite3.OperationalError:
            continue
        for row in rows:
            hits.append(
                _Hit(
                    chunk_id=row[0],
                    product_id=product_id,
                    score=row[10],
                    query_str=query_str,
                    row=row[1:10],
                )
            )
    return hits


def fetch_bm25_candidates(
    query_str: str,
    process_number: str,
    expected_product_id: str | None,
    limit: int = 20,
) -> list[RetrievedChunk]:
    """Run a single FTS5 query and return up to `limit` ranked candidates.

    Unlike search_bm25(), this does not merge across products or apply the
    per-product/global caps — it's the raw per-product candidate list used as
    one input to RRF fusion against vector candidates (ADR-0049).
    Returns [] for an empty query_str.
    """
    if not query_str:
        return []

    con = sqlite3.connect(str(get_db_path()))
    try:
        if not con.execute(_SCHEMA_CHECK).fetchone():
            raise RuntimeError(
                "Retrieval database schema not initialised. "
                "Call init_db(db_path) before fetch_bm25_candidates()."
            )
        try:
            rows = con.execute(
                _SEARCH_SQL, (query_str, process_number, limit)
            ).fetchall()
        except sqlite3.OperationalError:
            return []
    finally:
        con.close()

    return [
        RetrievedChunk(
            process_number=row[1],
            filename=row[2],
            page_number=row[3],
            chunk_index=row[4],
            char_offset=row[5],
            page_total=row[6],
            ocr_used=bool(row[7]),
            source_type=row[8],
            text=row[9],
            cascade_step="bm25",
            expected_product_id=expected_product_id,
            bm25_score=row[10],
            rank=i + 1,
            retrieval_query=query_str,
        )
        for i, row in enumerate(rows)
    ]


def _merge(hits: list[_Hit]) -> list[_Hit]:
    """Fair per-product selection followed by cross-product physical deduplication.

    Step 1 — per product: keep the _PER_PRODUCT_TARGET best-scoring chunks so
    that no single product monopolises the final pool.
    Step 2 — cross-product: when the same physical chunk appears under multiple
    products, keep only the copy with the best (most negative) BM25 score,
    preserving that product's attribution.
    """
    # Step 1: collect best _PER_PRODUCT_TARGET hits per product_id
    per_product: dict[str | None, list[_Hit]] = {}
    for h in hits:
        per_product.setdefault(h.product_id, []).append(h)

    selected: list[_Hit] = []
    for phits in per_product.values():
        phits.sort(key=lambda h: h.score)   # most negative first
        selected.extend(phits[:_PER_PRODUCT_TARGET])

    # Step 2: deduplicate by physical chunk_id, keeping best score
    best: dict[int, _Hit] = {}
    for h in selected:
        if h.chunk_id not in best or h.score < best[h.chunk_id].score:
            best[h.chunk_id] = h
    return list(best.values())

