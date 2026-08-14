"""Integration tests for per-product hybrid BM25+vector retrieval (ADR-0049).

Vector ML dependencies are mocked at retrieval.query.vector.search_vector
(the attribute hybrid.py looks up via module reference) so these tests stay
fast and deterministic (ADR-0039 isolation pattern).
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from extraction import Chunk
from ingestion import get_ipmp_store
from ingestion.retrieval_profile import RetrievalProfileStore
from retrieval import configure, index
from retrieval.interfaces.contracts import RetrievedChunk
from retrieval.query.hybrid import retrieve_hybrid_for_acao
from retrieval.schema.ddl import init_db


def make_chunk(**kwargs) -> Chunk:
    defaults = dict(
        filename="doc.pdf",
        page_number=1,
        chunk_index=0,
        char_offset=0,
        text="texto padrão do fragmento.",
        text_length=26,
        page_total=10,
        ocr_used=False,
        source_type="text",
    )
    return Chunk(**{**defaults, **kwargs})


def make_vector_chunk(**kwargs) -> RetrievedChunk:
    defaults = dict(
        process_number="P001",
        filename="vector_only.pdf",
        page_number=1,
        chunk_index=0,
        char_offset=0,
        page_total=10,
        ocr_used=False,
        source_type="text",
        text="conteúdo relevante encontrado apenas por similaridade semântica",
        cascade_step="vector",
        expected_product_ids=[],
        bm25_score=None,
        rank=None,
        retrieval_mode="vector_fallback",
        retrieval_query="vector query",
    )
    return RetrievedChunk(**{**defaults, **kwargs})


@pytest.fixture
def db(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    configure(db_path)
    return db_path


@pytest.fixture(autouse=True)
def empty_profile(monkeypatch):
    """Force IPMP-text fallback for all products unless a test overrides this."""
    import ingestion.retrieval_profile as _rp
    monkeypatch.setattr(_rp, "_store", RetrievalProfileStore(acoes={}))


def test_vector_called_even_when_bm25_already_has_chunks(db):
    """Vector must run per-product regardless of how many BM25 hits exist."""
    index("P001", [make_chunk(text="projeto natureza finalidade contexto socioeconômico")])
    with patch("retrieval.query.vector.search_vector", return_value=[]) as mock_vector:
        retrieve_hybrid_for_acao(1, "P001")
    assert mock_vector.called


def test_vector_only_match_is_selected_when_not_found_by_bm25(db):
    """A chunk that BM25 never finds can still be selected via vector alone."""
    index("P001", [])
    vector_hit = make_vector_chunk()
    with patch("retrieval.query.vector.search_vector", return_value=[vector_hit]):
        results = retrieve_hybrid_for_acao(1, "P001")

    matches = [r for r in results if r.filename == "vector_only.pdf"]
    assert len(matches) == 1
    assert matches[0].cascade_step == "vector"
    assert matches[0].bm25_score is None
    assert matches[0].expected_product_ids  # attributed to whichever product claimed it


def test_rio_hints_does_not_trigger_extra_vector_calls(db):
    """rio_hints stays BM25-only — vector is called once per IPMP product, not once more for rio_hints."""
    index("P001", [make_chunk(text="conveniência e oportunidade do projeto")])
    with patch("retrieval.query.vector.search_vector", return_value=[]) as mock_vector:
        retrieve_hybrid_for_acao(1, "P001")

    acao = get_ipmp_store().acoes[1]
    n_products = sum(1 for p in acao.produtos_esperados if p.id[-1:].isalpha())
    assert mock_vector.call_count == n_products


def test_ipmp_product_lane_wins_over_rio_hints_on_conflict(db):
    """Same physical chunk claimed by both an IPMP product and rio_hints:
    the IPMP product lane wins regardless of either score (ADR-0049)."""
    # "conveniência e oportunidade" is a real Rio Manual primary_term for acao 1.
    # "projeto" + "natureza" are real IPMP 1a fallback vocabulary.
    shared_chunk = make_chunk(
        text="projeto natureza do problema, conveniência e oportunidade demonstrada claramente."
    )
    index("P001", [shared_chunk])
    with patch("retrieval.query.vector.search_vector", return_value=[]):
        results = retrieve_hybrid_for_acao(1, "P001")

    matches = [
        r for r in results
        if r.filename == "doc.pdf" and r.page_number == 1 and r.chunk_index == 0
    ]
    assert len(matches) == 1
    assert "rio_hints" not in matches[0].expected_product_ids


def test_unknown_acao_returns_empty(db):
    index("P001", [make_chunk()])
    with patch("retrieval.query.vector.search_vector", return_value=[]):
        results = retrieve_hybrid_for_acao(999, "P001")
    assert results == []
