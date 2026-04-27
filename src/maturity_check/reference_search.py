from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ReferenceHit:
    chunk_id: str
    doc_id: str
    ordinal: int
    heading_path: str | None
    text: str


def search_reference_sqlite(
    *,
    sqlite_path: Path,
    query: str,
    heading_contains: str | None,
    limit: int,
) -> list[ReferenceHit]:
    if limit <= 0:
        raise ValueError("limit must be > 0")

    conn = sqlite3.connect(str(sqlite_path))
    conn.row_factory = sqlite3.Row

    q = f"%{query}%"
    params: list[object] = [q]
    where = ["text LIKE ?"]

    if heading_contains:
        where.append("(heading_path LIKE ?)")
        params.append(f"%{heading_contains}%")

    sql = f"""
      SELECT chunk_id, doc_id, ordinal, heading_path, text
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
            text=r["text"],
        )
        for r in rows
    ]


def search_reference_lancedb(
    *,
    lancedb_dir: Path,
    query: str,
    limit: int,
    model_id: str,
    table: str = "reference_m5d_chunks",
) -> list[ReferenceHit]:
    if limit <= 0:
        raise ValueError("limit must be > 0")

    import lancedb
    from sentence_transformers import SentenceTransformer

    db = lancedb.connect(str(lancedb_dir))
    tbl = db.open_table(table)

    model = SentenceTransformer(model_id)
    vec = model.encode([query], normalize_embeddings=True)[0]

    rows = tbl.search(vec).limit(limit).to_list()
    hits: list[ReferenceHit] = []
    for r in rows:
        hits.append(
            ReferenceHit(
                chunk_id=r["chunk_id"],
                doc_id=r["doc_id"],
                ordinal=int(r["ordinal"]),
                heading_path=r.get("heading_path"),
                text=r["text"],
            )
        )
    return hits

