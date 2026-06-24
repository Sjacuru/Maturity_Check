"""Tests for evaluation.evidence_selection.select_evidence (ADR-0050)."""

from __future__ import annotations

import pytest

from ingestion.retrieval_profile import (
    AcaoRetrievalProfile,
    ExpectedProductProfile,
    RetrievalProfileStore,
)
from retrieval.interfaces.contracts import RetrievedChunk

import evaluation._config as eval_cfg
import evaluation.evidence_selection as es
from evaluation.evidence_selection import select_evidence


def make_chunk(**kwargs) -> RetrievedChunk:
    defaults = dict(
        process_number="P001",
        filename="doc.pdf",
        page_number=1,
        chunk_index=0,
        char_offset=0,
        page_total=10,
        ocr_used=False,
        source_type="text",
        text="texto padrão",
        cascade_step="bm25",
        expected_product_id="1a",
        bm25_score=-5.0,
        rank=1,
    )
    return RetrievedChunk(**{**defaults, **kwargs})


class StubGateClient:
    def __init__(self, responder):
        self._responder = responder
        self.calls: list[tuple[str, str]] = []

    def complete(self, system: str, user: str) -> str:
        self.calls.append((system, user))
        return self._responder(system, user)


@pytest.fixture(autouse=True)
def _reset_gate_config():
    yield
    eval_cfg._reset()


def _set_gate(responder):
    eval_cfg._gate_client = StubGateClient(responder)


def _profile_with_evidence_intent(product_id: str, evidence_intent: str) -> RetrievalProfileStore:
    return RetrievalProfileStore(
        acoes={
            1: AcaoRetrievalProfile(
                acao_id=1,
                profile_maturity="seed",
                expected_products={
                    product_id: ExpectedProductProfile(
                        evidence_intent=evidence_intent,
                        retrieval_signal_concepts=[],
                        query_terms=[],
                    )
                },
            )
        }
    )


def _no_neighbors(monkeypatch):
    monkeypatch.setattr(es, "fetch_neighbor_chunks", lambda *a, **k: (None, None))


def test_relevant_chunk_is_accepted_as_anchor(monkeypatch):
    import ingestion.retrieval_profile as _rp
    monkeypatch.setattr(_rp, "_store", _profile_with_evidence_intent("1a", "evidência de X"))
    _no_neighbors(monkeypatch)
    _set_gate(lambda system, user: "RELEVANT: yes\nCLEANED:\ntexto padrão")

    chunk = make_chunk()
    result = select_evidence(1, "P001", {"1a": [(0.05, chunk)]})

    assert len(result.accepted) == 1
    assert result.accepted[0].text == "texto padrão"
    assert result.rejected == []


def test_irrelevant_chunk_is_rejected(monkeypatch):
    import ingestion.retrieval_profile as _rp
    monkeypatch.setattr(_rp, "_store", _profile_with_evidence_intent("1a", "evidência de X"))
    _no_neighbors(monkeypatch)
    _set_gate(lambda system, user: "RELEVANT: no")

    chunk = make_chunk()
    result = select_evidence(1, "P001", {"1a": [(0.05, chunk)]})

    assert result.accepted == []
    assert len(result.rejected) == 1
    assert result.rejected[0].expected_product_id == "1a"
    assert result.rejected[0].filename == chunk.filename


def test_product_without_evidence_intent_passes_through_ungated(monkeypatch):
    import ingestion.retrieval_profile as _rp
    monkeypatch.setattr(_rp, "_store", RetrievalProfileStore(acoes={}))

    def _boom(system, user):
        raise AssertionError("gate must not be called when no evidence_intent exists")

    _set_gate(_boom)

    chunk = make_chunk()
    result = select_evidence(1, "P001", {"1a": [(0.05, chunk)]})

    assert result.accepted == [chunk]
    assert result.rejected == []


def test_anchor_target_caps_at_five(monkeypatch):
    import ingestion.retrieval_profile as _rp
    monkeypatch.setattr(_rp, "_store", _profile_with_evidence_intent("1a", "evidência de X"))
    _no_neighbors(monkeypatch)
    _set_gate(lambda system, user: "RELEVANT: yes\nCLEANED:\ntexto")

    chunks = [
        (1.0 - i * 0.01, make_chunk(page_number=i, chunk_index=0, text="texto"))
        for i in range(10)
    ]
    result = select_evidence(1, "P001", {"1a": chunks})

    assert len(result.accepted) == 5


def test_cleaning_violation_falls_back_to_original_text(monkeypatch):
    import ingestion.retrieval_profile as _rp
    monkeypatch.setattr(_rp, "_store", _profile_with_evidence_intent("1a", "evidência de X"))
    _no_neighbors(monkeypatch)
    # Cleaned text inserts a word not present in the original — violates deletion-only.
    _set_gate(lambda system, user: "RELEVANT: yes\nCLEANED:\ntexto INSERIDO padrão")

    chunk = make_chunk(text="texto padrão")
    result = select_evidence(1, "P001", {"1a": [(0.05, chunk)]})

    assert result.accepted[0].text == "texto padrão"


def test_valid_deletion_only_cleaning_is_applied(monkeypatch):
    import ingestion.retrieval_profile as _rp
    monkeypatch.setattr(_rp, "_store", _profile_with_evidence_intent("1a", "evidência de X"))
    _no_neighbors(monkeypatch)
    _set_gate(lambda system, user: "RELEVANT: yes\nCLEANED:\npadrão")  # valid subsequence

    chunk = make_chunk(text="texto padrão")
    result = select_evidence(1, "P001", {"1a": [(0.05, chunk)]})

    assert result.accepted[0].text == "padrão"


def test_relevant_anchor_triggers_neighbor_expansion(monkeypatch):
    import ingestion.retrieval_profile as _rp
    monkeypatch.setattr(_rp, "_store", _profile_with_evidence_intent("1a", "evidência de X"))

    prev_chunk = make_chunk(page_number=1, chunk_index=0, text="anterior")
    next_chunk = make_chunk(page_number=1, chunk_index=2, text="seguinte")
    monkeypatch.setattr(es, "fetch_neighbor_chunks", lambda *a, **k: (prev_chunk, next_chunk))
    _set_gate(lambda system, user: "RELEVANT: yes\nCLEANED:\n" + user.split("\n", 1)[-1])

    anchor = make_chunk(page_number=1, chunk_index=1, text="ancora")
    result = select_evidence(1, "P001", {"1a": [(0.05, anchor)]})

    texts = {c.text for c in result.accepted}
    assert "anterior" in texts
    assert "seguinte" in texts


def test_rejected_neighbor_is_recorded(monkeypatch):
    import ingestion.retrieval_profile as _rp
    monkeypatch.setattr(_rp, "_store", _profile_with_evidence_intent("1a", "evidência de X"))

    prev_chunk = make_chunk(page_number=1, chunk_index=0, text="anterior irrelevante")
    monkeypatch.setattr(es, "fetch_neighbor_chunks", lambda *a, **k: (prev_chunk, None))

    calls = {"n": 0}

    def responder(system, user):
        calls["n"] += 1
        if calls["n"] == 1:
            return "RELEVANT: yes\nCLEANED:\nancora"
        return "RELEVANT: no"

    _set_gate(responder)

    anchor = make_chunk(page_number=1, chunk_index=1, text="ancora")
    result = select_evidence(1, "P001", {"1a": [(0.05, anchor)]})

    assert any(r.page_number == 1 and r.chunk_index == 0 for r in result.rejected)


def test_expansion_target_caps_at_five_per_product(monkeypatch):
    import ingestion.retrieval_profile as _rp
    monkeypatch.setattr(_rp, "_store", _profile_with_evidence_intent("1a", "evidência de X"))

    # Each anchor contributes up to 2 neighbors (prev+next); 5 anchors -> up to
    # 10 candidate neighbors, but expansion must cap at 5 total for the product.
    neighbor_counter = {"n": 0}

    def fake_neighbors(process_number, filename, page_number, chunk_index):
        neighbor_counter["n"] += 1
        prev = make_chunk(page_number=page_number, chunk_index=-1, text=f"prev{neighbor_counter['n']}")
        nxt = make_chunk(page_number=page_number, chunk_index=999, text=f"next{neighbor_counter['n']}")
        return prev, nxt

    monkeypatch.setattr(es, "fetch_neighbor_chunks", fake_neighbors)
    _set_gate(lambda system, user: "RELEVANT: yes\nCLEANED:\n" + user.split("\n", 1)[-1])

    anchors = [
        (1.0 - i * 0.01, make_chunk(page_number=i, chunk_index=0, text=f"anchor{i}"))
        for i in range(5)
    ]
    result = select_evidence(1, "P001", {"1a": anchors})

    expansion_texts = [c.text for c in result.accepted if c.text.startswith(("prev", "next"))]
    assert len(expansion_texts) == 5


def test_trim_expansions_drops_weakest_anchor_score_first(monkeypatch):
    monkeypatch.setattr(es, "_EVIDENCE_BUDGET_CHARS", 600)

    anchors = [(0.5, make_chunk(text="a" * 100))]
    strong_expansion = make_chunk(page_number=2, text="b" * 500)
    weak_expansion = make_chunk(page_number=3, text="c" * 500)
    expansions = [(0.9, strong_expansion), (0.1, weak_expansion)]

    kept = es._trim_expansions_to_budget(anchors, expansions)

    assert weak_expansion not in kept
    assert strong_expansion in kept


def test_is_verbatim_subsequence_allows_pure_deletion():
    assert es._is_verbatim_subsequence("projeto necessário", "o projeto é necessário aqui")


def test_is_verbatim_subsequence_rejects_insertion():
    assert not es._is_verbatim_subsequence("projeto urgente necessário", "o projeto é necessário aqui")


def test_is_verbatim_subsequence_rejects_reordering():
    assert not es._is_verbatim_subsequence("necessário projeto", "o projeto é necessário aqui")


def test_is_verbatim_subsequence_ignores_whitespace_differences():
    assert es._is_verbatim_subsequence("projeto\nnecessário", "projeto   necessário")
