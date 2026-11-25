"""Tests for regex-based retrieval (ADR-0007, Issue #15)."""

import pytest

from extraction import Chunk
from retrieval import configure, index, retrieve_for_acao
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
        text="texto padrão.",
        text_length=13,
        page_total=5,
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
# Texts that match ação 01 law reference patterns (loaded from data/):
#   "11\.079"                    → Lei Federal 11.079/2004
#   "LC\s*n[oº]?\.?\s*105"       → LC nº 105/2009 (Rio PPP law)
#   "PPA\s+20(?:22|…|29)"        → PPA 2026
# ---------------------------------------------------------------------------

_LEI_11079   = "As contraprestações são reguladas pela Lei 11.079/2004."
_LC_105      = "O projeto cumpre os requisitos da LC nº 105/2009, art.10."
_PPA_2026    = "O empreendimento está previsto no PPA 2026-2029."
_NO_MATCH    = "Texto sem referências legais específicas a qualquer lei."


# ---------------------------------------------------------------------------
# Cascade: regex was removed from the cascade in ADR-0052.
# search_regex() is preserved as a utility but no longer called by
# retrieve_for_acao(). The tests below that verified cascade integration
# with regex were removed when Step D was dropped.
# ---------------------------------------------------------------------------

def test_cascade_does_not_include_regex_step(db, monkeypatch):
    """Cascade (Step C) returns only BM25/vector results — no regex step."""
    import ingestion.retrieval_profile as _rp
    from ingestion.retrieval_profile import RetrievalProfileStore
    monkeypatch.setattr(_rp, "_store", RetrievalProfileStore(acoes={}))

    law_only_chunk = make_chunk(
        page_number=2,
        text="11.079/2004",  # matches regex but no IPMP content terms
    )
    index("P001", [law_only_chunk])
    results = retrieve_for_acao(1, "P001")
    cascade_steps = {r.cascade_step for r in results}
    assert "regex" not in cascade_steps
