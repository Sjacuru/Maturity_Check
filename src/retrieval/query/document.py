from __future__ import annotations

import re
import sqlite3
import unicodedata
from pathlib import Path as _Path

from ingestion import get_rio_manual_store
from ingestion.rio_manual import AcaoRioManual
from retrieval._config import get_db_path
from retrieval.interfaces.contracts import RetrievedChunk

_HEADER_CHUNK_COUNT = 2  # leading chunks inspected for variant match


def retrieve_document_focused(
    acao_id: int,
    process_number: str,
) -> list[RetrievedChunk] | None:
    """Try filename match (Step A) then variant match (Step B).

    Returns list[RetrievedChunk] with all chunks from the identified document,
    or None when neither step identifies a candidate (caller falls back to BM25).
    Returns None when acao_id is not present in the Rio Manual store.
    """
    store = get_rio_manual_store()
    acao = store.acoes.get(acao_id)
    if acao is None:
        return None

    con = sqlite3.connect(str(get_db_path()))
    try:
        result = _try_filename_match(con, process_number, acao)
        if result is None:
            result = _try_variant_match(con, process_number, acao)
    finally:
        con.close()

    return result


# ---------------------------------------------------------------------------
# Step A — filename match
# ---------------------------------------------------------------------------

def _try_filename_match(
    con: sqlite3.Connection,
    process_number: str,
    acao: AcaoRioManual,
) -> list[RetrievedChunk] | None:
    normalised = _build_normalised_doc_names(acao)
    for filename in _distinct_filenames(con, process_number):
        stem = _normalise(_Path(filename).stem)
        if stem in normalised:
            return _fetch_all_chunks(con, process_number, filename, "filename_match")
    return None


# ---------------------------------------------------------------------------
# Step B — variant match
# ---------------------------------------------------------------------------

def _try_variant_match(
    con: sqlite3.Connection,
    process_number: str,
    acao: AcaoRioManual,
) -> list[RetrievedChunk] | None:
    patterns = _build_variant_patterns(acao)
    if not patterns:
        return None

    for filename in _distinct_filenames(con, process_number):
        header = _header_text(con, process_number, filename)
        if header and _any_match(patterns, header):
            return _fetch_all_chunks(con, process_number, filename, "variant_match")
    return None


# ---------------------------------------------------------------------------
# SQL helpers
# ---------------------------------------------------------------------------

def _distinct_filenames(con: sqlite3.Connection, process_number: str) -> list[str]:
    rows = con.execute(
        "SELECT DISTINCT filename FROM chunks WHERE process_number = ? ORDER BY filename",
        (process_number,),
    ).fetchall()
    return [row[0] for row in rows]


def _header_text(
    con: sqlite3.Connection,
    process_number: str,
    filename: str,
) -> str:
    rows = con.execute(
        """
        SELECT text FROM chunks
        WHERE process_number = ? AND filename = ?
        ORDER BY page_number, chunk_index
        LIMIT ?
        """,
        (process_number, filename, _HEADER_CHUNK_COUNT),
    ).fetchall()
    return " ".join(row[0] for row in rows)


def _fetch_all_chunks(
    con: sqlite3.Connection,
    process_number: str,
    filename: str,
    cascade_step: str,
) -> list[RetrievedChunk]:
    rows = con.execute(
        """
        SELECT process_number, filename, page_number, chunk_index, char_offset,
               page_total, ocr_used, source_type, text
        FROM chunks
        WHERE process_number = ? AND filename = ?
        ORDER BY page_number, chunk_index
        """,
        (process_number, filename),
    ).fetchall()
    return [
        RetrievedChunk(
            process_number=row[0],
            filename=row[1],
            page_number=row[2],
            chunk_index=row[3],
            char_offset=row[4],
            page_total=row[5],
            ocr_used=bool(row[6]),
            source_type=row[7],
            text=row[8],
            cascade_step=cascade_step,  # type: ignore[arg-type]
            expected_product_id=None,
            bm25_score=None,
            rank=None,
            retrieval_query=filename,
        )
        for row in rows
    ]


# ---------------------------------------------------------------------------
# Pattern helpers
# ---------------------------------------------------------------------------

def _build_normalised_doc_names(acao: AcaoRioManual) -> set[str]:
    names: set[str] = set()
    for doc in acao.document_names:
        names.add(_normalise(doc.canonical))
        for v in doc.variants:
            names.add(_normalise(v))
    return names


def _build_variant_patterns(acao: AcaoRioManual) -> list[re.Pattern[str]]:
    patterns: list[re.Pattern[str]] = []
    for doc in acao.document_names:
        patterns.append(re.compile(re.escape(doc.canonical), re.IGNORECASE))
        for v in doc.variants:
            patterns.append(re.compile(re.escape(v), re.IGNORECASE))
    return patterns


def _any_match(patterns: list[re.Pattern[str]], text: str) -> bool:
    return any(p.search(text) for p in patterns)


def _normalise(name: str) -> str:
    """Lowercase, strip diacritics, collapse separators to single space."""
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_str = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[\s_\-]+", " ", ascii_str).lower().strip()
