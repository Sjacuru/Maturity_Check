from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
from tqdm import tqdm

from maturity_check.db import connect_sqlite, init_framework_schema
from maturity_check.ingest.chunking import chunk_text, iter_markdown_blocks


def _sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _sha256_file_bytes(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def ingest_m5d(
    *,
    m5d_path: Path,
    sqlite_path: Path,
    lancedb_dir: Path,
    embed: bool,
    model_id: str,
    max_chars: int,
    overlap_chars: int,
) -> None:
    if not m5d_path.exists():
        raise FileNotFoundError(str(m5d_path))

    m5d_path = m5d_path.resolve()
    doc_id = "m5d_md_v1"
    source = "M5D"
    title = "M5D (markdown reference)"

    content_hash = _sha256_file_bytes(m5d_path)
    md = m5d_path.read_text(encoding="utf-8")

    conn = connect_sqlite(sqlite_path)
    init_framework_schema(conn)

    # Upsert doc record
    conn.execute(
        """
        INSERT INTO reference_documents (doc_id, source, title, path, content_hash)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(doc_id) DO UPDATE SET
          source=excluded.source,
          title=excluded.title,
          path=excluded.path,
          content_hash=excluded.content_hash
        """,
        (doc_id, source, title, str(m5d_path), content_hash),
    )

    # Replace all chunks (simple, safe v0 behavior)
    conn.execute("DELETE FROM reference_chunks WHERE doc_id = ?", (doc_id,))

    # Build chunks
    chunk_rows: list[dict[str, Any]] = []
    ordinal = 0

    for block_start, heading_path, block in iter_markdown_blocks(md):
        windows = chunk_text(block, max_chars=max_chars, overlap_chars=overlap_chars)
        for start_rel, end_rel, ctext in windows:
            start_char = block_start + start_rel
            end_char = block_start + end_rel
            chunk_id = f"{doc_id}:{ordinal}"
            row = {
                "chunk_id": chunk_id,
                "doc_id": doc_id,
                "ordinal": ordinal,
                "heading_path": heading_path,
                "start_char": start_char,
                "end_char": end_char,
                "text": ctext,
                "text_hash": _sha256_text(ctext),
            }
            chunk_rows.append(row)
            ordinal += 1

    # Insert chunks
    conn.executemany(
        """
        INSERT INTO reference_chunks
          (chunk_id, doc_id, ordinal, heading_path, start_char, end_char, text, text_hash)
        VALUES
          (:chunk_id, :doc_id, :ordinal, :heading_path, :start_char, :end_char, :text, :text_hash)
        """,
        chunk_rows,
    )
    conn.commit()
    conn.close()

    # Optional embeddings into LanceDB (reference index)
    if embed:
        import lancedb
        from sentence_transformers import SentenceTransformer

        lancedb_dir.mkdir(parents=True, exist_ok=True)
        db = lancedb.connect(str(lancedb_dir))

        model = SentenceTransformer(model_id)

        # Minimal schema for LanceDB table: include ids + metadata + vector
        tbl_name = "reference_m5d_chunks"
        try:
            tbl = db.open_table(tbl_name)
            tbl.drop()
        except Exception:
            pass

        batch_size = 64
        vectors_dim = None

        rows_for_table: list[dict[str, Any]] = []
        for i in tqdm(range(0, len(chunk_rows), batch_size), desc="Embedding M5D chunks"):
            batch = chunk_rows[i : i + batch_size]
            texts = [r["text"] for r in batch]
            emb = model.encode(texts, normalize_embeddings=True)
            emb = np.asarray(emb, dtype=np.float32)
            if vectors_dim is None:
                vectors_dim = int(emb.shape[1])
            for r, v in zip(batch, emb, strict=True):
                rows_for_table.append(
                    {
                        "chunk_id": r["chunk_id"],
                        "doc_id": r["doc_id"],
                        "ordinal": r["ordinal"],
                        "heading_path": r["heading_path"],
                        "text": r["text"],
                        "text_hash": r["text_hash"],
                        "vector": v,
                    }
                )

        if not rows_for_table:
            raise RuntimeError("No chunks to embed; rows_for_table is empty.")

        # Create table from first batch (provides schema including vector dim)
        tbl = db.create_table(tbl_name, data=rows_for_table[:1], mode="overwrite")
        if len(rows_for_table) > 1:
            tbl.add(rows_for_table[1:])

        # Write a small manifest for reproducibility/audit
        manifest = {
            "doc_id": doc_id,
            "source": source,
            "path": str(m5d_path),
            "content_hash": content_hash,
            "model_id": model_id,
            "table": tbl_name,
            "num_chunks": len(chunk_rows),
            "max_chars": max_chars,
            "overlap_chars": overlap_chars,
            "vector_dim": vectors_dim,
        }
        (lancedb_dir / "reference_m5d_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    print(f"Ingested {len(chunk_rows)} chunks from {m5d_path} into {sqlite_path}.")

