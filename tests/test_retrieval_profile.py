"""Tests for retrieval profile store loading, build_query_from_terms, and cascade integration."""

import json
from pathlib import Path

import pytest

from extraction import Chunk
from ingestion.retrieval_profile import (
    AcaoRetrievalProfile,
    ExpectedProductProfile,
    NearQueryTerm,
    PhraseQueryTerm,
    RetrievalProfileStore,
    get_retrieval_profile_store,
)
from retrieval import configure, index
from retrieval.query.cascade import retrieve_bm25_for_acao
from retrieval.query.query_builder import build_query_from_terms
from retrieval.schema.ddl import init_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_profile(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data), encoding="utf-8")


def _minimal_valid_profile(acao_id: int = 1) -> dict:
    return {
        "acao_id": acao_id,
        "profile_maturity": "seed",
        "expected_products": {},
    }


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


@pytest.fixture
def profile_dir(tmp_path):
    """Return a fresh temp directory with the _store singleton reset."""
    return tmp_path / "profiles"


# ---------------------------------------------------------------------------
# Store loading — no directory
# ---------------------------------------------------------------------------

def test_empty_store_when_no_directory(monkeypatch, tmp_path):
    monkeypatch.setattr("ingestion.retrieval_profile._DATA_DIR", tmp_path / "nonexistent")
    monkeypatch.setattr("ingestion.retrieval_profile._store", None)
    store = get_retrieval_profile_store()
    assert store.acoes == {}


# ---------------------------------------------------------------------------
# Store loading — empty directory
# ---------------------------------------------------------------------------

def test_empty_store_when_no_files(monkeypatch, tmp_path):
    (tmp_path / "profiles").mkdir()
    monkeypatch.setattr("ingestion.retrieval_profile._DATA_DIR", tmp_path / "profiles")
    monkeypatch.setattr("ingestion.retrieval_profile._store", None)
    store = get_retrieval_profile_store()
    assert store.acoes == {}


# ---------------------------------------------------------------------------
# Store loading — valid file
# ---------------------------------------------------------------------------

def test_loads_valid_profile(monkeypatch, tmp_path):
    d = tmp_path / "profiles"
    d.mkdir()
    _write_profile(d / "acao_01.json", _minimal_valid_profile(1))
    monkeypatch.setattr("ingestion.retrieval_profile._DATA_DIR", d)
    monkeypatch.setattr("ingestion.retrieval_profile._store", None)
    store = get_retrieval_profile_store()
    assert 1 in store.acoes
    assert store.acoes[1].profile_maturity == "seed"


def test_loads_profile_with_expected_products(monkeypatch, tmp_path):
    d = tmp_path / "profiles"
    d.mkdir()
    data = {
        "acao_id": 1,
        "profile_maturity": "observed",
        "expected_products": {
            "1a": {
                "evidence_intent": "test intent",
                "retrieval_signal_concepts": [],
                "query_terms": [
                    {
                        "encoding": "phrase",
                        "text": "interesse público",
                        "type": "A",
                        "provenance": "canonical",
                    }
                ],
            }
        },
    }
    _write_profile(d / "acao_01.json", data)
    monkeypatch.setattr("ingestion.retrieval_profile._DATA_DIR", d)
    monkeypatch.setattr("ingestion.retrieval_profile._store", None)
    store = get_retrieval_profile_store()
    product = store.acoes[1].expected_products["1a"]
    assert product.evidence_intent == "test intent"
    assert len(product.query_terms) == 1
    assert product.query_terms[0].encoding == "phrase"


# ---------------------------------------------------------------------------
# Store loading — error cases
# ---------------------------------------------------------------------------

def test_raises_on_malformed_json(monkeypatch, tmp_path):
    d = tmp_path / "profiles"
    d.mkdir()
    (d / "acao_01.json").write_text("{not valid json", encoding="utf-8")
    monkeypatch.setattr("ingestion.retrieval_profile._DATA_DIR", d)
    monkeypatch.setattr("ingestion.retrieval_profile._store", None)
    with pytest.raises(RuntimeError, match="Cannot read"):
        get_retrieval_profile_store()


def test_raises_on_acao_id_mismatch(monkeypatch, tmp_path):
    d = tmp_path / "profiles"
    d.mkdir()
    # filename says 01, acao_id says 2
    _write_profile(d / "acao_01.json", _minimal_valid_profile(2))
    monkeypatch.setattr("ingestion.retrieval_profile._DATA_DIR", d)
    monkeypatch.setattr("ingestion.retrieval_profile._store", None)
    with pytest.raises(RuntimeError, match="mismatch"):
        get_retrieval_profile_store()


def test_skips_invalid_profile_and_loads_valid(monkeypatch, tmp_path):
    d = tmp_path / "profiles"
    d.mkdir()
    # acao_02.json has invalid profile_maturity — will be skipped
    invalid = {"acao_id": 2, "profile_maturity": "invalid_value", "expected_products": {}}
    _write_profile(d / "acao_02.json", invalid)
    # acao_01.json is valid
    _write_profile(d / "acao_01.json", _minimal_valid_profile(1))
    monkeypatch.setattr("ingestion.retrieval_profile._DATA_DIR", d)
    monkeypatch.setattr("ingestion.retrieval_profile._store", None)
    store = get_retrieval_profile_store()
    assert 1 in store.acoes
    assert 2 not in store.acoes


# ---------------------------------------------------------------------------
# Model validation — NearQueryTerm invariants
# ---------------------------------------------------------------------------

def test_near_term_requires_at_least_two_tokens():
    with pytest.raises(ValueError, match="at least 2 tokens"):
        NearQueryTerm(
            encoding="near",
            tokens=["único"],
            distance=5,
            type="C",
            provenance="real_world",
        )


def test_near_term_requires_positive_distance():
    with pytest.raises(ValueError, match="distance must be"):
        NearQueryTerm(
            encoding="near",
            tokens=["tok1", "tok2"],
            distance=0,
            type="C",
            provenance="real_world",
        )


# ---------------------------------------------------------------------------
# build_query_from_terms — unit tests
# ---------------------------------------------------------------------------

def test_empty_list_returns_empty_string():
    assert build_query_from_terms([]) == ""


def test_phrase_term_produces_quoted_string():
    term = PhraseQueryTerm(
        encoding="phrase",
        text="interesse público",
        type="A",
        provenance="canonical",
    )
    result = build_query_from_terms([term])
    assert result == '"interesse público"'


def test_near_term_produces_near_syntax():
    term = NearQueryTerm(
        encoding="near",
        tokens=["contrato", "vencimento"],
        distance=5,
        type="C",
        provenance="real_world",
    )
    result = build_query_from_terms([term])
    assert result == 'NEAR("contrato" "vencimento", 5)'


def test_near_term_with_three_tokens():
    term = NearQueryTerm(
        encoding="near",
        tokens=["concessão", "serviço", "público"],
        distance=5,
        type="C",
        provenance="real_world",
    )
    result = build_query_from_terms([term])
    assert result == 'NEAR("concessão" "serviço" "público", 5)'


def test_multiple_phrase_terms_are_or_joined():
    terms = [
        PhraseQueryTerm(encoding="phrase", text="interesse público", type="A", provenance="canonical"),
        PhraseQueryTerm(encoding="phrase", text="plano estratégico", type="A", provenance="canonical"),
    ]
    result = build_query_from_terms(terms)
    assert result == '"interesse público" OR "plano estratégico"'


def test_mixed_phrase_and_near_are_or_joined():
    terms = [
        PhraseQueryTerm(encoding="phrase", text="efetivo interesse público", type="A", provenance="canonical"),
        NearQueryTerm(encoding="near", tokens=["contrato", "vencimento"], distance=5, type="C", provenance="real_world"),
    ]
    result = build_query_from_terms(terms)
    assert result == '"efetivo interesse público" OR NEAR("contrato" "vencimento", 5)'


# ---------------------------------------------------------------------------
# Cascade integration — profile store interaction
# ---------------------------------------------------------------------------

def _make_profile_with_1a_term(phrase: str) -> RetrievalProfileStore:
    """Return a RetrievalProfileStore with a single phrase term for product 1a."""
    return RetrievalProfileStore(
        acoes={
            1: AcaoRetrievalProfile(
                acao_id=1,
                profile_maturity="observed",
                expected_products={
                    "1a": ExpectedProductProfile(
                        evidence_intent="test",
                        retrieval_signal_concepts=[],
                        query_terms=[
                            PhraseQueryTerm(
                                encoding="phrase",
                                text=phrase,
                                type="B",
                                provenance="real_world",
                            )
                        ],
                    )
                },
            )
        }
    )


def test_cascade_uses_profile_term_to_retrieve_chunk(db, monkeypatch):
    """Profile phrase term is used; a chunk containing that term is retrieved."""
    import ingestion.retrieval_profile as _rp

    profile_phrase = "continuidade das atividades"
    monkeypatch.setattr(_rp, "_store", _make_profile_with_1a_term(profile_phrase))

    index("P001", [make_chunk(text=f"documento descreve a {profile_phrase} de forma detalhada")])
    results = retrieve_bm25_for_acao(1, "P001")
    assert any(profile_phrase in r.text for r in results)


def test_cascade_falls_back_when_no_profile_for_acao(db, monkeypatch):
    """When the profile store is empty, falls back to build_bm25_query for all products."""
    import ingestion.retrieval_profile as _rp

    monkeypatch.setattr(_rp, "_store", RetrievalProfileStore(acoes={}))

    # Words from IPMP 1a text that pass the 5-char filter
    index("P001", [make_chunk(text="projeto natureza finalidade contexto socioeconômico")])
    results = retrieve_bm25_for_acao(1, "P001")
    assert len(results) >= 1


def test_cascade_falls_back_per_product_when_missing_from_profile(db, monkeypatch):
    """Products not in the profile use build_bm25_query as fallback."""
    import ingestion.retrieval_profile as _rp

    # Profile only covers 1a — 1b/1c/1d must fall back to build_bm25_query
    monkeypatch.setattr(_rp, "_store", _make_profile_with_1a_term("termoexclusivo"))

    # "panorama" from IPMP 1b text — only reachable via build_bm25_query fallback for 1b
    index("P001", [make_chunk(text="panorama econômico social ambiental relevante do projeto")])
    results = retrieve_bm25_for_acao(1, "P001")
    assert len(results) >= 1


def test_cascade_rio_hints_unchanged_by_profile(db, monkeypatch):
    """rio_hints query is built from Rio Manual regardless of profile presence."""
    import ingestion.retrieval_profile as _rp

    # Empty profile — ensures any retrieval is via rio_hints or fallback, not profile
    monkeypatch.setattr(_rp, "_store", RetrievalProfileStore(acoes={}))

    # "conveniência e oportunidade" is a Rio Manual primary_term for acao 1
    index("P001", [make_chunk(text="conveniência e oportunidade do projeto está demonstrada")])
    results = retrieve_bm25_for_acao(1, "P001")
    assert len(results) >= 1
