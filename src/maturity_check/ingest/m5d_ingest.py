from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import lancedb
import numpy as np
import pyarrow as pa
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

from maturity_check.db import connect_sqlite, init_framework_schema
from maturity_check.ingest.chunking import chunk_text, iter_markdown_blocks, normalize_pdf_headings

# ---------------------------------------------------------------------------
# M5D action metadata — stable mapping derived from M5D ToC (46 actions)
# ---------------------------------------------------------------------------

_PII1 = "Proposta Inicial de Investimento"
_PII2 = "Proposta Intermediária de Investimento"
_PCI  = "Proposta Completa de Investimento"

M5D_ACTION_METADATA: dict[int, dict[str, str]] = {
    # Stage 1 — Proposta Inicial de Investimento
    1:  {"stage": _PII1, "dimension": "Estratégica"},
    2:  {"stage": _PII1, "dimension": "Estratégica"},
    3:  {"stage": _PII1, "dimension": "Estratégica"},
    4:  {"stage": _PII1, "dimension": "Estratégica"},
    5:  {"stage": _PII1, "dimension": "Econômica"},
    6:  {"stage": _PII1, "dimension": "Econômica"},
    7:  {"stage": _PII1, "dimension": "Econômica"},
    8:  {"stage": _PII1, "dimension": "Comercial"},
    9:  {"stage": _PII1, "dimension": "Comercial"},
    10: {"stage": _PII1, "dimension": "Financeira"},
    11: {"stage": _PII1, "dimension": "Gerencial"},
    12: {"stage": _PII1, "dimension": "Gerencial"},
    13: {"stage": _PII1, "dimension": "Gerencial"},
    14: {"stage": _PII1, "dimension": "Gerencial"},
    15: {"stage": _PII1, "dimension": "Gerencial"},
    16: {"stage": _PII1, "dimension": "Ponto de Transição"},
    # Stage 2 — Proposta Intermediária de Investimento
    17: {"stage": _PII2, "dimension": "Estratégica"},
    18: {"stage": _PII2, "dimension": "Econômica"},
    19: {"stage": _PII2, "dimension": "Econômica"},
    20: {"stage": _PII2, "dimension": "Econômica"},
    21: {"stage": _PII2, "dimension": "Econômica"},
    22: {"stage": _PII2, "dimension": "Comercial"},
    23: {"stage": _PII2, "dimension": "Comercial"},
    24: {"stage": _PII2, "dimension": "Comercial"},
    25: {"stage": _PII2, "dimension": "Comercial"},
    26: {"stage": _PII2, "dimension": "Financeira"},
    27: {"stage": _PII2, "dimension": "Financeira"},
    28: {"stage": _PII2, "dimension": "Financeira"},
    29: {"stage": _PII2, "dimension": "Gerencial"},
    30: {"stage": _PII2, "dimension": "Gerencial"},
    31: {"stage": _PII2, "dimension": "Gerencial"},
    32: {"stage": _PII2, "dimension": "Gerencial"},
    33: {"stage": _PII2, "dimension": "Gerencial"},
    34: {"stage": _PII2, "dimension": "Gerencial"},
    35: {"stage": _PII2, "dimension": "Gerencial"},
    36: {"stage": _PII2, "dimension": "Gerencial"},
    37: {"stage": _PII2, "dimension": "Ponto de Transição"},
    38: {"stage": _PII2, "dimension": "Ponto de Transição"},
    # Stage 3 — Proposta Completa de Investimento
    39: {"stage": _PCI,  "dimension": "Estratégica"},
    40: {"stage": _PCI,  "dimension": "Econômica"},
    41: {"stage": _PCI,  "dimension": "Econômica"},
    42: {"stage": _PCI,  "dimension": "Comercial"},
    43: {"stage": _PCI,  "dimension": "Financeira"},
    44: {"stage": _PCI,  "dimension": "Gerencial"},
    45: {"stage": _PCI,  "dimension": "Ponto de Transição"},
    46: {"stage": _PCI,  "dimension": "Ponto de Transição"},
}

_ACAO_NUM_RE = re.compile(r"(?:^|>)\s*Ação\s+(\d+)(?:[:\s]|$)")


def get_action_metadata(heading_path: str | None) -> dict[str, str] | None:
    """Return {stage, dimension} for the action number found in heading_path, or None."""
    if not heading_path:
        return None
    m = _ACAO_NUM_RE.search(heading_path)
    if not m:
        return None
    return M5D_ACTION_METADATA.get(int(m.group(1)))


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
    md = normalize_pdf_headings(m5d_path.read_text(encoding="utf-8"))

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
        meta = get_action_metadata(heading_path)
        for start_rel, end_rel, ctext in windows:
            start_char = block_start + start_rel
            end_char = block_start + end_rel
            chunk_id = f"{doc_id}:{ordinal}"
            row = {
                "chunk_id": chunk_id,
                "doc_id": doc_id,
                "ordinal": ordinal,
                "heading_path": heading_path,
                "stage": meta["stage"] if meta else None,
                "dimension": meta["dimension"] if meta else None,
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
          (chunk_id, doc_id, ordinal, heading_path, stage, dimension,
           start_char, end_char, text, text_hash)
        VALUES
          (:chunk_id, :doc_id, :ordinal, :heading_path, :stage, :dimension,
           :start_char, :end_char, :text, :text_hash)
        """,
        chunk_rows,
    )
    conn.commit()
    conn.close()

    # Optional embeddings into LanceDB (reference index)
    if embed:
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
                        "stage": r["stage"],
                        "dimension": r["dimension"],
                        "text": r["text"],
                        "text_hash": r["text_hash"],
                        "vector": v,
                    }
                )

        if not rows_for_table:
            raise RuntimeError("No chunks to embed; rows_for_table is empty.")

        schema = pa.schema([
            pa.field("chunk_id", pa.string()),
            pa.field("doc_id", pa.string()),
            pa.field("ordinal", pa.int64()),
            pa.field("heading_path", pa.string()),
            pa.field("stage", pa.string()),
            pa.field("dimension", pa.string()),
            pa.field("text", pa.string()),
            pa.field("text_hash", pa.string()),
            pa.field("vector", pa.list_(pa.float32(), vectors_dim)),
        ])
        tbl = db.create_table(tbl_name, data=rows_for_table, schema=schema, mode="overwrite")

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

