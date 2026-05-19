from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

# ── Model singleton ────────────────────────────────────────────────────────────
# Loaded once per process; reused across all calls with the same model_id.
_MODEL_CACHE: dict[str, "SentenceTransformer"] = {}


def _get_model(model_id: str) -> "SentenceTransformer":
    if model_id not in _MODEL_CACHE:
        from sentence_transformers import SentenceTransformer
        _MODEL_CACHE[model_id] = SentenceTransformer(model_id)
    return _MODEL_CACHE[model_id]


# ── Heading-path helpers ───────────────────────────────────────────────────────
_ACAO_RE = re.compile(r"Ação\s+(\d+)", re.IGNORECASE)
_SUBTASK_RE = re.compile(
    r">\s*(i{1,3}|iv|vi{0,3}|ix|xi{0,3}|xiv|xv)\.\s*$", re.IGNORECASE
)


def _extract_acao_num(heading_path: str | None) -> int | None:
    if not heading_path:
        return None
    m = _ACAO_RE.search(heading_path)
    return int(m.group(1)) if m else None


def _extract_subtask(heading_path: str | None) -> str | None:
    """Return the roman-numeral subtask label (e.g. 'iii.') from a heading path."""
    if not heading_path:
        return None
    m = _SUBTASK_RE.search(heading_path)
    return (m.group(1).lower() + ".") if m else None


# ── Data contract ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ReferenceHit:
    chunk_id:     str
    doc_id:       str
    ordinal:      int
    heading_path: str | None
    stage:        str | None  # M5D stage (e.g. "Proposta Inicial de Investimento")
    dimension:    str | None  # M5D dimension (e.g. "Estratégica")
    acao_num:     int | None  # extracted from heading_path
    subtask:      str | None  # extracted from heading_path (e.g. "i.", "iii.")
    text:         str
    distance:     float       # L2 distance on unit vectors — lower = more similar


# ── SQLite keyword search ──────────────────────────────────────────────────────

def search_reference_sqlite(
    *,
    sqlite_path: Path,
    query: str,
    limit: int,
    stage: str | None = None,
    dimension: str | None = None,
    acao_num: int | None = None,
    heading_contains: str | None = None,
) -> list[ReferenceHit]:
    """Keyword search in SQLite with optional hierarchy filters."""
    if limit <= 0:
        raise ValueError("limit must be > 0")

    conn = sqlite3.connect(str(sqlite_path))
    conn.row_factory = sqlite3.Row

    params: list[object] = [f"%{query}%"]
    where = ["text LIKE ?"]

    if stage:
        where.append("stage = ?")
        params.append(stage)
    if dimension:
        where.append("dimension = ?")
        params.append(dimension)
    if acao_num is not None:
        where.append("heading_path LIKE ?")
        params.append(f"%Ação {acao_num}:%")
    if heading_contains:
        where.append("heading_path LIKE ?")
        params.append(f"%{heading_contains}%")

    sql = f"""
      SELECT chunk_id, doc_id, ordinal, heading_path, stage, dimension, text
      FROM reference_chunks
      WHERE {' AND '.join(where)}
      ORDER BY doc_id, ordinal
      LIMIT ?
    """
    params.append(limit)

    rows = conn.execute(sql, params).fetchall()
    conn.close()

    return [
        ReferenceHit(
            chunk_id=r["chunk_id"],
            doc_id=r["doc_id"],
            ordinal=int(r["ordinal"]),
            heading_path=r["heading_path"],
            stage=r["stage"],
            dimension=r["dimension"],
            acao_num=_extract_acao_num(r["heading_path"]),
            subtask=_extract_subtask(r["heading_path"]),
            text=r["text"],
            distance=0.0,
        )
        for r in rows
    ]


# ── LanceDB semantic search ────────────────────────────────────────────────────

def search_reference_lancedb(
    *,
    lancedb_dir: Path,
    query: str,
    limit: int,
    model_id: str,
    stage: str | None = None,
    dimension: str | None = None,
    acao_num: int | None = None,
    content_only: bool = True,
    table: str = "reference_m5d_chunks",
) -> list[ReferenceHit]:
    """Semantic vector search with optional hierarchy filters.

    Parameters
    ----------
    stage:        Filter to a specific M5D stage.
    dimension:    Filter to a specific M5D dimension.
    acao_num:     Post-filter to a specific Ação number (applied in Python
                  after vector search since LanceDB has no LIKE operator).
    content_only: When True (default), exclude chunks without stage metadata
                  (front matter, annexes) from results.

    The model is loaded once per process and reused across calls.
    """
    if limit <= 0:
        raise ValueError("limit must be > 0")

    import lancedb

    db  = lancedb.connect(str(lancedb_dir))
    tbl = db.open_table(table)

    model = _get_model(model_id)
    vec   = model.encode([query], normalize_embeddings=True)[0]

    # Build WHERE clause for pre-filtering in LanceDB.
    where_parts: list[str] = []
    if content_only:
        where_parts.append("stage IS NOT NULL")
    if stage:
        escaped = stage.replace("'", "''")
        where_parts.append(f"stage = '{escaped}'")
    if dimension:
        escaped = dimension.replace("'", "''")
        where_parts.append(f"dimension = '{escaped}'")

    # Over-fetch when Ação post-filter is active so trimming doesn't starve results.
    fetch_limit = limit * 4 if acao_num is not None else limit

    search = tbl.search(vec).limit(fetch_limit)
    if where_parts:
        search = search.where(" AND ".join(where_parts))

    rows = search.to_list()

    # Post-filter by Ação number (heading_path LIKE match).
    if acao_num is not None:
        pattern = f"Ação {acao_num}:"
        rows = [r for r in rows if pattern in (r.get("heading_path") or "")]

    hits: list[ReferenceHit] = []
    for r in rows[:limit]:
        hp = r.get("heading_path")
        hits.append(
            ReferenceHit(
                chunk_id=r["chunk_id"],
                doc_id=r["doc_id"],
                ordinal=int(r["ordinal"]),
                heading_path=hp,
                stage=r.get("stage"),
                dimension=r.get("dimension"),
                acao_num=_extract_acao_num(hp),
                subtask=_extract_subtask(hp),
                text=r["text"],
                distance=float(r.get("_distance", 0.0)),
            )
        )
    return hits
