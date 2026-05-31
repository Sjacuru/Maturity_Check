from __future__ import annotations

import re
import sqlite3

from ingestion import get_rio_manual_store
from ingestion.rio_manual import AcaoRioManual
from retrieval._config import get_db_path
from retrieval.interfaces.contracts import RetrievedChunk


def _regex_match(pattern: str, text: str) -> int:
    """SQLite user-defined function: 1 if pattern matches text, else 0."""
    try:
        return 1 if re.search(pattern, text) else 0
    except re.error:
        return 0


def search_regex(
    acao_id: int,
    process_number: str,
) -> list[RetrievedChunk]:
    """Search all process chunks using Rio Manual law-reference regex patterns.

    Combines all regex_variants from law_references into a single OR expression,
    then runs one SQL scan via a Python-registered regex function (ADR-0007).
    Returns chunks with cascade_step="regex". The caller deduplicates against
    other result sets.
    """
    store = get_rio_manual_store()
    acao = store.acoes.get(acao_id)
    if acao is None:
        return []

    pattern = _build_combined_pattern(acao)
    if not pattern:
        return []

    con = sqlite3.connect(str(get_db_path()))
    con.create_function("regex_match", 2, _regex_match)
    try:
        rows = con.execute(
            """
            SELECT process_number, filename, page_number, chunk_index, char_offset,
                   page_total, ocr_used, source_type, text
            FROM chunks
            WHERE process_number = ?
              AND regex_match(?, text) = 1
            ORDER BY page_number, chunk_index
            """,
            (process_number, pattern),
        ).fetchall()
    except sqlite3.OperationalError:
        return []
    finally:
        con.close()

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
            cascade_step="regex",
            expected_product_id=None,
            bm25_score=None,
            rank=None,
        )
        for row in rows
    ]


def _build_combined_pattern(acao: AcaoRioManual) -> str:
    """Combine all valid law-reference regex_variants into a single OR expression."""
    seen: set[str] = set()
    valid: list[str] = []
    for law_ref in acao.law_references:
        for p in law_ref.regex_variants:
            if p not in seen:
                seen.add(p)
                try:
                    re.compile(p)
                    valid.append(p)
                except re.error:
                    pass
    if not valid:
        return ""
    return "|".join(f"(?:{p})" for p in valid)
