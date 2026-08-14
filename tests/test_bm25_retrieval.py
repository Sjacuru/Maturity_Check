import sqlite3
from pathlib import Path

import pytest

from extraction import Chunk
from ingestion.retrieval_profile import RetrievalProfileStore
from retrieval import configure, index
from retrieval.query.bm25 import MAX_CHUNKS_PER_ACAO, search_bm25
from retrieval.query.hybrid import retrieve_hybrid_for_acao
from retrieval.query.query_builder import build_bm25_query
from retrieval.schema.ddl import init_db


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

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


@pytest.fixture
def db(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    configure(db_path)
    return db_path


# ---------------------------------------------------------------------------
# query_builder unit tests
# ---------------------------------------------------------------------------

def test_build_bm25_query_extracts_significant_words():
    q = build_bm25_query("Descrição do projeto necessário")
    assert '"projeto"' in q
    assert '"descrição"' in q
    assert '"necessário"' in q


def test_build_bm25_query_skips_short_words():
    q = build_bm25_query("o que é de")
    assert q == ""


def test_build_bm25_query_minimum_5_chars():
    q = build_bm25_query("abcd abcde")  # 4 chars skipped, 5 chars included
    assert '"abcde"' in q
    assert '"abcd"' not in q


def test_build_bm25_query_is_deterministic():
    q1 = build_bm25_query("projeto contexto viabilidade")
    q2 = build_bm25_query("projeto contexto viabilidade")
    assert q1 == q2


def test_build_bm25_query_output_is_sorted():
    q = build_bm25_query("viabilidade projeto natureza")
    terms = [t.strip('"') for t in q.split(" OR ")]
    assert terms == sorted(terms)


def test_build_bm25_query_acronym_expansion_adds_terms():
    q = build_bm25_query(
        "EVTEA do projeto",
        acronym_map={"EVTEA": "Estudo de Viabilidade"},
    )
    assert '"viabilidade"' in q
    assert '"estudo"' in q


def test_build_bm25_query_acronym_not_in_text_is_ignored():
    q = build_bm25_query(
        "projeto contexto",
        acronym_map={"EVTEA": "Estudo de Viabilidade"},
    )
    assert '"viabilidade"' not in q
    assert '"estudo"' not in q


def test_build_bm25_query_deduplicates_words():
    q = build_bm25_query("projeto projeto projeto")
    assert q.count('"projeto"') == 1


def test_build_bm25_query_terms_are_quoted():
    q = build_bm25_query("viabilidade projeto")
    for term in q.split(" OR "):
        assert term.startswith('"') and term.endswith('"')


# ---------------------------------------------------------------------------
# search_bm25 integration tests
# ---------------------------------------------------------------------------

def test_search_bm25_returns_matching_chunk(db):
    index("P001", [make_chunk(text="O projeto tem viabilidade econômica necessária")])
    results = search_bm25({"1a": '"projeto" OR "viabilidade"'}, "P001")
    assert len(results) == 1
    assert results[0].cascade_step == "bm25"
    assert results[0].rank == 1
    assert results[0].bm25_score < 0  # FTS5 BM25 score is negative


def test_search_bm25_respects_process_number(db):
    index("P001", [make_chunk(text="viabilidade do projeto")])
    index("P002", [make_chunk(text="viabilidade do projeto", page_number=2)])
    results = search_bm25({"1a": '"viabilidade"'}, "P001")
    assert len(results) == 1
    assert results[0].process_number == "P001"


def test_search_bm25_no_match_returns_empty(db):
    index("P001", [make_chunk(text="texto qualquer sem termos relevantes")])
    results = search_bm25({"1a": '"saneamento"'}, "P001")
    assert results == []


def test_search_bm25_no_chunks_for_process_returns_empty(db):
    results = search_bm25({"1a": '"projeto"'}, "P999")
    assert results == []


def test_search_bm25_deduplicates_multi_product_hits(db):
    index("P001", [make_chunk(text="projeto viabilidade contexto econômico")])
    results = search_bm25(
        {
            "1a": '"projeto" OR "viabilidade"',
            "1b": '"contexto" OR "econômico"',
        },
        "P001",
    )
    assert len(results) == 1


def test_search_bm25_assigns_expected_product_id(db):
    index("P001", [make_chunk(text="projeto viabilidade")])
    results = search_bm25({"1a": '"projeto"'}, "P001")
    assert results[0].expected_product_ids == ["1a"]


def test_search_bm25_caps_at_max_chunks_per_acao(db):
    # _PER_PRODUCT_TARGET=5 limits a single product's contribution, so the
    # global cap requires multiple non-overlapping products to actually exercise
    # it: 5 products x 5 exclusive chunks each = 25 candidates, capped to 20.
    markers = ["grupoa", "grupob", "grupoc", "grupod", "grupoe"]
    chunks = [
        make_chunk(page_number=i * 5 + j, chunk_index=0, text=f"viabilidade projeto {marker}")
        for i, marker in enumerate(markers)
        for j in range(5)
    ]
    index("P001", chunks)
    queries = {f"1{letter}": f'"{marker}"' for letter, marker in zip("abcde", markers)}
    results = search_bm25(queries, "P001")
    assert len(results) == MAX_CHUNKS_PER_ACAO


def test_search_bm25_ranks_are_sequential(db):
    chunks = [
        make_chunk(page_number=i, text=f"viabilidade econômica projeto {i}")
        for i in range(1, 4)
    ]
    index("P001", chunks)
    results = search_bm25({"1a": '"viabilidade"'}, "P001")
    assert [r.rank for r in results] == list(range(1, len(results) + 1))


def test_search_bm25_empty_query_value_returns_empty(db):
    index("P001", [make_chunk(text="viabilidade")])
    results = search_bm25({"1a": ""}, "P001")
    assert results == []


def test_search_bm25_all_empty_queries_returns_empty(db):
    index("P001", [make_chunk(text="viabilidade")])
    results = search_bm25({"1a": "", "1b": ""}, "P001")
    assert results == []


def test_search_bm25_without_init_db_raises(tmp_path):
    from retrieval import _config as _cfg
    original = _cfg._db_path
    try:
        configure(tmp_path / "never_init.db")
        with pytest.raises(RuntimeError, match="not initialised"):
            search_bm25({"1a": '"projeto"'}, "P001")
    finally:
        _cfg._db_path = original


def test_search_bm25_best_score_wins_dedup(db):
    # Two chunks: one is a better match (more term hits)
    chunk_strong = make_chunk(
        page_number=1,
        text="viabilidade projeto natureza contexto econômico",
    )
    chunk_weak = make_chunk(
        page_number=2,
        text="viabilidade apenas",
    )
    index("P001", [chunk_strong, chunk_weak])
    results = search_bm25({"1a": '"viabilidade" OR "projeto" OR "natureza"'}, "P001")
    assert results[0].page_number == 1  # stronger match is rank 1


# ---------------------------------------------------------------------------
# cascade integration tests (uses real IPMP data from data/ipmp/)
# ---------------------------------------------------------------------------

def test_retrieve_hybrid_for_acao_returns_relevant_chunks(db, monkeypatch):
    # Patch profile to empty so cascade uses IPMP fallback queries.
    # "projeto" and "natureza" appear in produto 1a IPMP text.
    import ingestion.retrieval_profile as _rp
    monkeypatch.setattr(_rp, "_store", RetrievalProfileStore(acoes={}))
    chunk = make_chunk(text="O projeto revela a natureza do problema e sua finalidade socioeconômica")
    index("P001", [chunk])
    results = retrieve_hybrid_for_acao(1, "P001")
    assert len(results) >= 1
    assert all(r.cascade_step == "bm25" for r in results)


def test_retrieve_hybrid_for_unknown_acao_returns_empty(db):
    index("P001", [make_chunk()])
    results = retrieve_hybrid_for_acao(999, "P001")
    assert results == []


def test_retrieve_for_acao_public_api(db, monkeypatch):
    # Patch profile to empty so cascade uses IPMP fallback queries.
    import ingestion.retrieval_profile as _rp
    from retrieval import retrieve_for_acao
    monkeypatch.setattr(_rp, "_store", RetrievalProfileStore(acoes={}))
    chunk = make_chunk(text="projeto viabilidade natureza finalidade")
    index("P001", [chunk])
    results = retrieve_for_acao(1, "P001")
    assert isinstance(results, list)
    assert all(r.cascade_step == "bm25" for r in results)
