"""Gate telemetry: a broken gate call must not masquerade as a rejection.

Until 2026-09-27 evidence_selection branched only on RelevanceVerdict.relevant,
so an unparseable or truncated gate response was recorded exactly like a
considered "not relevant" verdict — no log, no counter, no field. In the
2026-09-07 run 65% of (Ação, product) pairs rejected 100% of their candidates
and there was no way to tell how much of that was real judgement. These tests
pin the distinction down.
"""

from __future__ import annotations

import json

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
from evaluation.llm.llamacpp import LlamaCppTruncated

_YES = json.dumps({"relevant": True})
_NO = json.dumps({"relevant": False})


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
        text="texto de teste com tamanho suficiente para o gate",
        cascade_step="bm25",
        expected_product_ids=["1a"],
        bm25_score=-5.0,
        rank=1,
    )
    return RetrievedChunk(**{**defaults, **kwargs})


class StubGateClient:
    """Gate stub that can raise, plus optional provider/model labels."""

    def __init__(self, responder, provider_label=None, model_label=None):
        self._responder = responder
        self.calls = 0
        if provider_label is not None:
            self.provider_label = provider_label
        if model_label is not None:
            self.model_label = model_label

    def complete(self, system: str, user: str, schema: dict | None = None) -> str:
        self.calls += 1
        return self._responder(self.calls)


@pytest.fixture(autouse=True)
def _reset_gate_config():
    yield
    eval_cfg._reset()


def _set_gate(responder, **labels):
    eval_cfg._gate_client = StubGateClient(responder, **labels)
    return eval_cfg._gate_client


def _profile(product_id="1a", evidence_intent="evidência de X") -> RetrievalProfileStore:
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


@pytest.fixture(autouse=True)
def _install_profile(monkeypatch):
    import ingestion.retrieval_profile as _rp

    monkeypatch.setattr(_rp, "_store", _profile())
    monkeypatch.setattr(es, "fetch_neighbor_chunks", lambda *a, **k: (None, None))


# --- truncation is a failure, not a rejection --------------------------------

def test_truncated_gate_call_is_counted_as_failure_not_rejection():
    def responder(_n):
        raise LlamaCppTruncated("finish_reason=length (max_tokens=768)")

    _set_gate(responder)
    result = select_evidence(1, "P001", {"1a": [(0.05, make_chunk())]})

    assert result.accepted == []
    report = result.product_reports[0]
    assert report.n_gate_failures == 1
    assert report.n_rejected == 0, "a truncated call must not inflate the rejection count"
    assert report.n_examined == 1


def test_truncated_call_marks_the_rejected_chunk_as_gate_failed():
    def responder(_n):
        raise LlamaCppTruncated("finish_reason=length")

    _set_gate(responder)
    result = select_evidence(1, "P001", {"1a": [(0.05, make_chunk())]})

    assert len(result.rejected) == 1
    assert result.rejected[0].gate_failed is True
    assert result.rejected[0].gate_failure_reason == "truncated"


def test_unparseable_gate_response_marks_gate_failed():
    _set_gate(lambda _n: "isto não é JSON")
    result = select_evidence(1, "P001", {"1a": [(0.05, make_chunk())]})

    assert result.accepted == []
    assert result.rejected[0].gate_failed is True
    assert result.rejected[0].gate_failure_reason == "parse"
    assert result.product_reports[0].n_gate_failures == 1
    assert result.product_reports[0].n_rejected == 0


def test_genuine_rejection_is_not_marked_as_failure():
    _set_gate(lambda _n: _NO)
    result = select_evidence(1, "P001", {"1a": [(0.05, make_chunk())]})

    assert result.rejected[0].gate_failed is False
    assert result.rejected[0].gate_failure_reason is None
    report = result.product_reports[0]
    assert report.n_rejected == 1
    assert report.n_gate_failures == 0


# --- provider attribution ---------------------------------------------------

def test_provider_and_model_are_recorded_on_rejected_chunks():
    _set_gate(lambda _n: _NO, provider_label="llamacpp", model_label="gpt-oss-20b")
    result = select_evidence(1, "P001", {"1a": [(0.05, make_chunk())]})

    assert result.rejected[0].gate_provider == "llamacpp"
    assert result.rejected[0].gate_model == "gpt-oss-20b"


def test_product_report_records_every_provider_that_served_it():
    _set_gate(lambda _n: _NO, provider_label="llamacpp", model_label="gpt-oss-20b")
    chunks = [(0.05, make_chunk(page_number=p)) for p in (1, 2, 3)]
    result = select_evidence(1, "P001", {"1a": chunks})

    report = result.product_reports[0]
    assert report.providers == ["llamacpp"]
    assert report.models == ["gpt-oss-20b"]


def test_missing_provider_labels_degrade_to_none():
    """A stub without provider_label must not break selection."""
    _set_gate(lambda _n: _NO)
    result = select_evidence(1, "P001", {"1a": [(0.05, make_chunk())]})

    assert result.rejected[0].gate_provider is None
    assert result.product_reports[0].providers == []


# --- report shape -----------------------------------------------------------

def test_report_counts_candidates_separately_from_examined(monkeypatch):
    """n_candidates is the pool offered; n_examined is what _MAX_EXAMINED allowed."""
    monkeypatch.setattr(es, "_MAX_EXAMINED", 2)
    _set_gate(lambda _n: _NO)
    chunks = [(0.05, make_chunk(page_number=p)) for p in range(1, 6)]
    result = select_evidence(1, "P001", {"1a": chunks})

    report = result.product_reports[0]
    assert report.n_candidates == 5
    assert report.n_examined == 2


def test_report_flags_no_evidence_when_nothing_accepted():
    _set_gate(lambda _n: _NO)
    result = select_evidence(1, "P001", {"1a": [(0.05, make_chunk())]})
    assert result.product_reports[0].no_evidence is True


def test_report_counts_accepted_anchors():
    _set_gate(lambda _n: _YES)
    chunks = [(0.05, make_chunk(page_number=p)) for p in (1, 2)]
    result = select_evidence(1, "P001", {"1a": chunks})

    report = result.product_reports[0]
    assert report.n_accepted == 2
    assert report.no_evidence is False


def test_one_report_per_examined_product():
    profile = RetrievalProfileStore(
        acoes={
            1: AcaoRetrievalProfile(
                acao_id=1,
                profile_maturity="seed",
                expected_products={
                    pid: ExpectedProductProfile(
                        evidence_intent=f"evidência de {pid}",
                        retrieval_signal_concepts=[],
                        query_terms=[],
                    )
                    for pid in ("1a", "1b")
                },
            )
        }
    )
    import ingestion.retrieval_profile as _rp

    _rp._store = profile
    _set_gate(lambda _n: _NO)
    result = select_evidence(
        1,
        "P001",
        {
            "1a": [(0.05, make_chunk(expected_product_ids=["1a"]))],
            "1b": [(0.04, make_chunk(page_number=2, expected_product_ids=["1b"]))],
        },
    )

    assert [r.expected_product_id for r in result.product_reports] == ["1a", "1b"]


def test_ungated_product_still_produces_a_report(monkeypatch):
    """A product with no evidence_intent passes through ungated — it must still
    report how many candidates went straight to the scorer."""
    import ingestion.retrieval_profile as _rp

    monkeypatch.setattr(_rp, "_store", RetrievalProfileStore(acoes={}))
    _set_gate(lambda _n: _NO)
    result = select_evidence(1, "P001", {"1a": [(0.05, make_chunk())]})

    assert len(result.accepted) == 1
    report = result.product_reports[0]
    assert report.n_examined == 0, "no gate call was made"
    assert report.n_accepted == 1
    assert report.n_candidates == 1


# --- transport failures must NOT be swallowed -------------------------------

def test_transport_failure_propagates_instead_of_becoming_a_rejection():
    """The wiring is GPU-only with no fallback, so an unreachable server must
    abort rather than silently yield an assessment where nothing is evidenced."""
    from evaluation.llm.llamacpp import LlamaCppUnavailable

    def responder(_n):
        raise LlamaCppUnavailable("connection refused")

    _set_gate(responder)
    with pytest.raises(LlamaCppUnavailable):
        select_evidence(1, "P001", {"1a": [(0.05, make_chunk())]})


# --- gate reasoning persisted per call (2026-10-03) ---------------------------

class _Completion:
    def __init__(self, content, reasoning):
        self.content = content
        self.reasoning = reasoning


class DetailedStubGateClient:
    """A client with complete_detailed(), like LlamaCppClient: the gate must
    take the reasoning from it instead of falling back to complete()."""

    def __init__(self, responder):
        self._responder = responder
        self.calls = 0

    def complete(self, system: str, user: str, schema: dict | None = None) -> str:  # pragma: no cover
        raise AssertionError("the gate should prefer complete_detailed()")

    def complete_detailed(self, system: str, user: str, schema: dict | None = None):
        self.calls += 1
        content, reasoning = self._responder(self.calls, user)
        return _Completion(content, reasoning)


def test_rejected_chunk_keeps_the_gate_reasoning():
    eval_cfg._gate_client = DetailedStubGateClient(lambda n, u: (_NO, f"motivo {n}"))
    result = select_evidence(1, "P001", {"1a": [(0.05, make_chunk())]})
    assert result.rejected[0].gate_reasoning == "motivo 1"


def test_accepted_chunk_keeps_the_gate_reasoning_keyed_by_product():
    eval_cfg._gate_client = DetailedStubGateClient(lambda n, u: (_YES, "evidencia direta do criterio"))
    result = select_evidence(1, "P001", {"1a": [(0.05, make_chunk())]})
    assert result.accepted[0].gate_reasoning == {"1a": "evidencia direta do criterio"}


def test_reasoning_merges_when_two_products_accept_the_same_chunk(monkeypatch):
    import ingestion.retrieval_profile as _rp

    monkeypatch.setattr(
        _rp, "_store",
        RetrievalProfileStore(acoes={1: AcaoRetrievalProfile(
            acao_id=1, profile_maturity="seed",
            expected_products={
                "1a": ExpectedProductProfile(evidence_intent="A", retrieval_signal_concepts=[], query_terms=[]),
                "1b": ExpectedProductProfile(evidence_intent="B", retrieval_signal_concepts=[], query_terms=[]),
            },
        )}),
    )

    def responder(n, user):
        pid = "1a" if "Produto Esperado 1a" in user else "1b"
        return _YES, f"aceito para {pid}"

    eval_cfg._gate_client = DetailedStubGateClient(responder)
    same = make_chunk(page_number=7)
    result = select_evidence(1, "P001", {"1a": [(0.9, same)], "1b": [(0.8, same)]})

    assert len(result.accepted) == 1
    assert result.accepted[0].expected_product_ids == ["1a", "1b"]
    assert result.accepted[0].gate_reasoning == {"1a": "aceito para 1a", "1b": "aceito para 1b"}


def test_client_without_complete_detailed_still_works_with_no_reasoning():
    _set_gate(lambda _n: _NO)
    result = select_evidence(1, "P001", {"1a": [(0.05, make_chunk())]})
    assert result.rejected[0].gate_reasoning is None


def test_failed_gate_call_has_no_reasoning():
    def responder(n, user):
        raise LlamaCppTruncated("finish_reason=length")

    eval_cfg._gate_client = DetailedStubGateClient(responder)
    result = select_evidence(1, "P001", {"1a": [(0.05, make_chunk())]})
    assert result.rejected[0].gate_failed is True
    assert result.rejected[0].gate_reasoning is None


def test_rows_persisted_before_gate_reasoning_still_validate():
    """Older raw_json has no gate_reasoning on either chunk model; the read path
    does not re-validate (ADR-0031) but the models must accept such rows too."""
    from evaluation.interfaces.contracts import RejectedChunk

    old_rejected = RejectedChunk.model_validate(
        {"filename": "d.pdf", "page_number": 1, "chunk_index": 0, "expected_product_id": "1a"}
    )
    assert old_rejected.gate_reasoning is None
    old_accepted = make_chunk().model_dump()
    old_accepted.pop("gate_reasoning")
    assert RetrievedChunk.model_validate(old_accepted).gate_reasoning == {}
