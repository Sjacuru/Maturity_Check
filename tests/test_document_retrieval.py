"""Tests for document-focused retrieval: filename_match (Step A) + variant_match (Step B)."""

import pytest

from extraction import Chunk
from retrieval import configure, index
from retrieval.query.cascade import retrieve_for_acao
from retrieval.query.document import retrieve_document_focused
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
# Filenames derived from real acao_01.json canonical names
#   Canonical: "Relatório de Pré-Análise"         → stem normalises to "relatorio de pre analise"
#   Canonical: "Relatório Geral de Avaliação"     → stem normalises to "relatorio geral de avaliacao"
#   Variant:   "Relatório de Pré-Análise de Projetos"  (variant of pre_analysis_report)
#   Variant:   "Relatório de Avaliação"                (variant of general_evaluation_report)
# ---------------------------------------------------------------------------

_CANONICAL_FILENAME = "Relatório de Pré-Análise.pdf"
_VARIANT_FILENAME   = "Relatório de Pré-Análise de Projetos.pdf"
_SECOND_CANONICAL   = "Relatório Geral de Avaliação.pdf"


# ---------------------------------------------------------------------------
# Step A — filename match
# ---------------------------------------------------------------------------

def test_filename_match_exact_canonical(db):
    index("P001", [make_chunk(filename=_CANONICAL_FILENAME)])
    results = retrieve_document_focused(1, "P001")
    assert results is not None
    assert len(results) == 1
    assert results[0].cascade_step == "filename_match"


def test_filename_match_variant_name(db):
    index("P001", [make_chunk(filename=_VARIANT_FILENAME)])
    results = retrieve_document_focused(1, "P001")
    assert results is not None
    assert results[0].cascade_step == "filename_match"


def test_filename_match_second_canonical(db):
    index("P001", [make_chunk(filename=_SECOND_CANONICAL)])
    results = retrieve_document_focused(1, "P001")
    assert results is not None
    assert results[0].cascade_step == "filename_match"


def test_filename_match_case_insensitive_diacritics(db):
    # Lower-case, no-diacritic version should still match after normalisation
    index("P001", [make_chunk(filename="relatorio de pre-analise.pdf")])
    results = retrieve_document_focused(1, "P001")
    assert results is not None
    assert results[0].cascade_step == "filename_match"


def test_filename_no_match_returns_none(db):
    index("P001", [make_chunk(filename="contrato_obra.pdf")])
    results = retrieve_document_focused(1, "P001")
    assert results is None


# ---------------------------------------------------------------------------
# Step B — variant match (content search)
# ---------------------------------------------------------------------------

def test_variant_match_canonical_in_header(db):
    # First chunk text contains the canonical document name
    chunk = make_chunk(
        filename="estudo_viabilidade.pdf",
        text="Relatório de Pré-Análise da concessão de saneamento básico",
    )
    index("P001", [chunk])
    results = retrieve_document_focused(1, "P001")
    assert results is not None
    assert results[0].cascade_step == "variant_match"


def test_variant_match_variant_name_in_header(db):
    chunk = make_chunk(
        filename="avaliacao_projeto.pdf",
        text="Relatório Geral de Avaliação do Projeto de PPP municipal",
    )
    index("P001", [chunk])
    results = retrieve_document_focused(1, "P001")
    assert results is not None
    assert results[0].cascade_step == "variant_match"


def test_variant_match_only_inspects_header_chunks(db):
    # Canonical name appears only in a late chunk — should NOT match
    chunks = [
        make_chunk(filename="contrato.pdf", page_number=1, text="Introdução geral do estudo."),
        make_chunk(filename="contrato.pdf", page_number=2, text="Análise técnica detalhada."),
        make_chunk(filename="contrato.pdf", page_number=3,
                   text="Relatório de Pré-Análise referenciado aqui."),
    ]
    index("P001", chunks)
    results = retrieve_document_focused(1, "P001")
    # First 2 chunks have no match, late chunk is not inspected
    assert results is None


def test_variant_match_no_match_returns_none(db):
    chunk = make_chunk(
        filename="contrato.pdf",
        text="Cláusulas contratuais gerais para a concessão de infraestrutura.",
    )
    index("P001", [chunk])
    results = retrieve_document_focused(1, "P001")
    assert results is None


# ---------------------------------------------------------------------------
# Return shape — document-focused result
# ---------------------------------------------------------------------------

def test_document_match_returns_all_chunks_from_document(db):
    chunks = [
        make_chunk(filename=_CANONICAL_FILENAME, page_number=1, text="Capítulo 1."),
        make_chunk(filename=_CANONICAL_FILENAME, page_number=2, text="Capítulo 2."),
        make_chunk(filename=_CANONICAL_FILENAME, page_number=3, text="Capítulo 3."),
    ]
    # Extra document that should not be included
    index("P001", chunks + [make_chunk(filename="outro.pdf", text="outro documento")])
    results = retrieve_document_focused(1, "P001")
    assert results is not None
    assert len(results) == 3
    assert all(r.filename == _CANONICAL_FILENAME for r in results)


def test_document_match_expected_product_id_is_none(db):
    index("P001", [make_chunk(filename=_CANONICAL_FILENAME)])
    results = retrieve_document_focused(1, "P001")
    assert results is not None
    assert all(r.expected_product_id is None for r in results)


def test_document_match_bm25_score_and_rank_are_none(db):
    index("P001", [make_chunk(filename=_CANONICAL_FILENAME)])
    results = retrieve_document_focused(1, "P001")
    assert results is not None
    assert all(r.bm25_score is None for r in results)
    assert all(r.rank is None for r in results)


def test_document_match_chunks_ordered_by_page_then_chunk(db):
    chunks = [
        make_chunk(filename=_CANONICAL_FILENAME, page_number=2, chunk_index=1, text="c"),
        make_chunk(filename=_CANONICAL_FILENAME, page_number=1, chunk_index=0, text="a"),
        make_chunk(filename=_CANONICAL_FILENAME, page_number=2, chunk_index=0, text="b"),
    ]
    index("P001", chunks)
    results = retrieve_document_focused(1, "P001")
    assert results is not None
    assert [(r.page_number, r.chunk_index) for r in results] == [(1, 0), (2, 0), (2, 1)]


def test_document_match_unknown_acao_in_rio_manual_returns_none(db):
    # acao_id 999 is not in the Rio Manual store
    index("P001", [make_chunk(filename=_CANONICAL_FILENAME)])
    results = retrieve_document_focused(999, "P001")
    assert results is None


def test_document_match_process_with_no_chunks_returns_empty_list(db):
    # acao_id 1 is in the Rio Manual store; no chunks indexed for P999
    index("P001", [make_chunk(filename=_CANONICAL_FILENAME)])
    results = retrieve_document_focused(1, "P999")
    # No filenames for P999 → no match → falls through to None
    assert results is None


# ---------------------------------------------------------------------------
# Full cascade: document path preferred over BM25
# ---------------------------------------------------------------------------

def test_cascade_uses_filename_match_when_available(db):
    index("P001", [make_chunk(filename=_CANONICAL_FILENAME, text="projeto estratégico")])
    results = retrieve_for_acao(1, "P001")
    assert len(results) >= 1
    assert results[0].cascade_step == "filename_match"


def test_cascade_falls_back_to_bm25_when_no_document_match(db, monkeypatch):
    # Patch profile to empty so cascade uses IPMP fallback queries.
    import ingestion.retrieval_profile as _rp
    from ingestion.retrieval_profile import RetrievalProfileStore
    monkeypatch.setattr(_rp, "_store", RetrievalProfileStore(acoes={}))
    index("P001", [make_chunk(filename="doc.pdf", text="projeto natureza finalidade estratégico")])
    results = retrieve_for_acao(1, "P001")
    assert isinstance(results, list)
    # With no filename/variant match, BM25 runs — step may be "bm25" or []
    assert all(r.cascade_step == "bm25" for r in results)


def test_cascade_variant_match_preferred_over_bm25(db):
    chunk = make_chunk(
        filename="relatorio_customizado.pdf",
        text="Relatório Geral de Avaliação do projeto de infraestrutura.",
    )
    index("P001", [chunk])
    results = retrieve_for_acao(1, "P001")
    assert len(results) >= 1
    assert results[0].cascade_step == "variant_match"


def test_cascade_filename_match_takes_priority_over_variant_match(db):
    # File with a matching canonical filename AND matching content in another file
    canonical_chunk = make_chunk(filename=_CANONICAL_FILENAME, text="conteúdo A")
    variant_content_chunk = make_chunk(
        filename="outro.pdf",
        text="Relatório Geral de Avaliação referenciado aqui",
    )
    index("P001", [canonical_chunk, variant_content_chunk])
    results = retrieve_for_acao(1, "P001")
    # filename_match runs first and finds a match → that document is returned
    assert results[0].cascade_step == "filename_match"
    assert all(r.filename == _CANONICAL_FILENAME for r in results)
