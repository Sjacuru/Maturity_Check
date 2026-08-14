"""Vector retrieval tests — Issue #27 and #28.

All ML dependencies (sentence_transformers, lancedb) are patched at the
vector.py import path so the main suite never loads the ML stack (ADR-0039).

Tests validate:
- Lazy initialization: model not loaded on module import
- Index lifecycle: create on first call, reuse on second, invalidate on replacement
- Provenance tagging: returned chunks carry retrieval_mode="vector_fallback"
- LanceDB boundary: ensure_vector_index_exists, search_vector, invalidate_vector_index

search_vector() now runs unconditionally per Expected Product, fused with BM25
via RRF (ADR-0049, superseding ADR-0033's zero-results-only trigger). See
tests/test_hybrid_retrieval.py for fusion-behavior coverage.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

import retrieval.query.vector as vector_mod
from retrieval import configure as retrieval_configure, RetrievedChunk
from retrieval._config import _reset as retrieval_reset
from retrieval.schema.ddl import init_db as retrieval_init_db
from retrieval.query.vector import (
    _table_name,
    ensure_vector_index_exists,
    invalidate_vector_index,
    search_vector,
)


# ── helpers ───────────────────────────────────────────────────────────────────

FAKE_EMBEDDING = np.zeros(384, dtype=np.float32)


def _make_stub_model(embedding=None):
    """Return a mock SentenceTransformer that produces fixed-dim embeddings."""
    stub = MagicMock()
    vec = embedding if embedding is not None else FAKE_EMBEDDING
    stub.encode.return_value = np.stack([vec])
    return stub


def _make_stub_db(table_exists: bool = False, table: MagicMock | None = None):
    """Return a mock lancedb DB.

    When table_exists=True, open_table() returns the provided table mock.
    When table_exists=False, open_table() raises (table absent).
    """
    stub_db = MagicMock()
    if table_exists and table is not None:
        stub_db.open_table.return_value = table
    elif table_exists:
        stub_db.open_table.return_value = MagicMock()
    else:
        stub_db.open_table.side_effect = Exception("table not found")
    stub_db.create_table.return_value = MagicMock()
    return stub_db


def _make_stub_table(hits: list[dict] | None = None) -> MagicMock:
    stub = MagicMock()
    stub.search.return_value.limit.return_value.to_list.return_value = hits or []
    return stub


def _seed_chunks(db_path: Path, process_number: str, n: int = 2) -> None:
    """Insert n synthetic chunks into the SQLite chunks table."""
    con = sqlite3.connect(str(db_path))
    try:
        for i in range(n):
            cur = con.execute(
                """
                INSERT OR IGNORE INTO chunks
                    (process_number, filename, page_number, chunk_index,
                     char_offset, text, text_length, page_total, ocr_used, source_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (process_number, "doc.pdf", 1, i, i * 10,
                 f"Chunk text {i}", 12, 5, 0, "text"),
            )
            con.execute(
                "INSERT INTO chunks_fts(rowid, text) VALUES (?, ?)",
                (cur.lastrowid, f"Chunk text {i}"),
            )
        con.commit()
    finally:
        con.close()


def _make_lancedb_hit(chunk_index=0, filename="doc.pdf", page_number=1,
                      char_offset=0, page_total=5, ocr_used=0,
                      source_type="text", text="sample text"):
    return {
        "chunk_index": chunk_index,
        "filename": filename,
        "page_number": page_number,
        "char_offset": char_offset,
        "page_total": page_total,
        "ocr_used": ocr_used,
        "source_type": source_type,
        "text": text,
        "_distance": 0.1,
    }


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def db_path(tmp_path) -> Path:
    path = tmp_path / "app.db"
    retrieval_configure(path)
    retrieval_init_db(path)
    return path


@pytest.fixture(autouse=True)
def reset_vector_state():
    yield
    retrieval_reset()
    vector_mod._reset()


# ── table_name sanitization ───────────────────────────────────────────────────

def test_table_name_alphanumeric_unchanged():
    assert _table_name("P001") == "P001"


def test_table_name_special_chars_replaced():
    name = _table_name("0023.001234/2024-01")
    assert "/" not in name
    assert "." not in name


def test_table_name_hyphen_and_underscore_preserved():
    assert _table_name("case_A-1") == "case_A-1"


# ── lazy ML loading ───────────────────────────────────────────────────────────

def test_importing_vector_module_does_not_load_ml():
    """The ML stack must not be loaded by merely importing the module."""
    assert vector_mod._model is None


def test_model_loaded_only_on_first_call(db_path):
    _seed_chunks(db_path, "P001")
    stub_model = _make_stub_model()
    stub_model.encode.return_value = np.zeros((2, 384), dtype=np.float32)
    stub_db = _make_stub_db(table_exists=False)

    with patch("sentence_transformers.SentenceTransformer", return_value=stub_model), \
         patch("lancedb.connect", return_value=stub_db):
        assert vector_mod._model is None
        ensure_vector_index_exists("P001")
        assert vector_mod._model is stub_model


# ── ensure_vector_index_exists ────────────────────────────────────────────────

def test_ensure_creates_table_when_absent(db_path):
    _seed_chunks(db_path, "P001", n=2)
    stub_model = _make_stub_model()
    stub_model.encode.return_value = np.zeros((2, 384), dtype=np.float32)
    stub_db = _make_stub_db(table_exists=False)

    with patch("sentence_transformers.SentenceTransformer", return_value=stub_model), \
         patch("lancedb.connect", return_value=stub_db):
        ensure_vector_index_exists("P001")

    stub_db.create_table.assert_called_once()
    tname = stub_db.create_table.call_args[0][0]
    assert tname == _table_name("P001")


def test_ensure_noop_when_table_exists(db_path):
    _seed_chunks(db_path, "P001")
    stub_model = _make_stub_model()
    stub_db = _make_stub_db(table_exists=True)

    with patch("sentence_transformers.SentenceTransformer", return_value=stub_model), \
         patch("lancedb.connect", return_value=stub_db):
        ensure_vector_index_exists("P001")

    stub_db.create_table.assert_not_called()
    stub_model.encode.assert_not_called()


def test_ensure_noop_when_no_chunks(db_path):
    stub_model = _make_stub_model()
    stub_db = _make_stub_db(table_exists=False)

    with patch("sentence_transformers.SentenceTransformer", return_value=stub_model), \
         patch("lancedb.connect", return_value=stub_db):
        ensure_vector_index_exists("P001")

    stub_db.create_table.assert_not_called()


def test_ensure_encodes_all_chunk_texts(db_path):
    _seed_chunks(db_path, "P001", n=3)
    stub_model = _make_stub_model()
    stub_model.encode.return_value = np.zeros((3, 384), dtype=np.float32)
    stub_db = _make_stub_db(table_exists=False)

    with patch("sentence_transformers.SentenceTransformer", return_value=stub_model), \
         patch("lancedb.connect", return_value=stub_db):
        ensure_vector_index_exists("P001")

    stub_model.encode.assert_called_once()
    encoded_texts = stub_model.encode.call_args[0][0]
    assert len(encoded_texts) == 3


# ── search_vector ─────────────────────────────────────────────────────────────

def test_search_returns_vector_fallback_chunks(db_path):
    _seed_chunks(db_path, "P001", n=2)
    stub_model = _make_stub_model()
    stub_model.encode.return_value = np.zeros((1, 384), dtype=np.float32)

    stub_table = _make_stub_table([
        _make_lancedb_hit(chunk_index=0, text="Chunk text 0"),
        _make_lancedb_hit(chunk_index=1, text="Chunk text 1"),
    ])
    stub_db = _make_stub_db(table_exists=True, table=stub_table)

    with patch("sentence_transformers.SentenceTransformer", return_value=stub_model), \
         patch("lancedb.connect", return_value=stub_db):
        results = search_vector("P001", "query about viability")

    assert len(results) == 2
    for r in results:
        assert isinstance(r, RetrievedChunk)
        assert r.retrieval_mode == "vector_fallback"
        assert r.cascade_step == "vector"
        assert r.expected_product_ids == []
        assert r.bm25_score is None
        assert r.rank is None
        assert r.process_number == "P001"


def test_search_returns_empty_when_no_table(db_path):
    stub_model = _make_stub_model()
    stub_db = _make_stub_db(table_exists=False)

    with patch("sentence_transformers.SentenceTransformer", return_value=stub_model), \
         patch("lancedb.connect", return_value=stub_db):
        results = search_vector("P001", "some query")

    assert results == []


def test_search_reuses_existing_index(db_path):
    _seed_chunks(db_path, "P001")
    stub_model = _make_stub_model()
    stub_model.encode.return_value = np.zeros((1, 384), dtype=np.float32)

    stub_table = _make_stub_table([])
    # Table already exists — create_table must NOT be called
    stub_db = _make_stub_db(table_exists=True, table=stub_table)

    with patch("sentence_transformers.SentenceTransformer", return_value=stub_model), \
         patch("lancedb.connect", return_value=stub_db):
        search_vector("P001", "query")
        search_vector("P001", "query again")

    stub_db.create_table.assert_not_called()


# ── invalidate_vector_index ───────────────────────────────────────────────────

def test_invalidate_drops_existing_table(db_path):
    tname = _table_name("P001")
    stub_db = _make_stub_db(table_exists=True)

    lancedb_path = db_path.parent / "lancedb"
    lancedb_path.mkdir()

    with patch("lancedb.connect", return_value=stub_db):
        invalidate_vector_index("P001")

    stub_db.drop_table.assert_called_once_with(tname)


def test_invalidate_noop_when_table_absent(db_path):
    """drop_table raises but no exception propagates — no-op semantics."""
    stub_db = _make_stub_db(table_exists=False)
    stub_db.drop_table.side_effect = Exception("table not found")

    lancedb_path = db_path.parent / "lancedb"
    lancedb_path.mkdir()

    with patch("lancedb.connect", return_value=stub_db):
        invalidate_vector_index("P001")  # must not raise


def test_invalidate_noop_when_lancedb_dir_absent(db_path):
    """No lancedb directory yet — must not raise or connect."""
    with patch("lancedb.connect") as mock_connect:
        invalidate_vector_index("P001")
    mock_connect.assert_not_called()


# ── cascade Step C integration (hybrid retrieval, ADR-0049) ───────────────────
#
# Vector is no longer a zero-results fallback (ADR-0033, superseded) — it now
# runs unconditionally per Expected Product, fused with BM25 via RRF. See
# tests/test_hybrid_retrieval.py for fusion-behavior coverage; the tests below
# only confirm cascade.py wires retrieve_hybrid_for_acao() correctly.

def _make_lexical_chunk(process_number: str = "P001") -> RetrievedChunk:
    return RetrievedChunk(
        process_number=process_number,
        filename="EVTEA.pdf",
        page_number=1,
        chunk_index=0,
        char_offset=0,
        page_total=5,
        ocr_used=False,
        source_type="text",
        text="Estudo de viabilidade técnica.",
        cascade_step="bm25",
        expected_product_ids=["1a"],
        bm25_score=-1.5,
        rank=1,
    )


def test_cascade_lexical_results_have_lexical_mode(db_path):
    """All hybrid-retrieved chunks must carry retrieval_mode='lexical' when sourced from BM25."""
    from retrieval.query.cascade import retrieve_for_acao

    lexical_chunk = _make_lexical_chunk()

    with patch("retrieval.query.cascade.retrieve_hybrid_for_acao", return_value=[lexical_chunk]), \
         patch("retrieval.query.regex_search.search_regex", return_value=[]), \
         patch("retrieval.query.document.retrieve_document_focused", return_value=None):
        result = retrieve_for_acao(1, "P001")

    for chunk in result:
        assert chunk.retrieval_mode == "lexical"
