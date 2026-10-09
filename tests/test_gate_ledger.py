"""Gate verdict ledger (ADR-0067): first verdict wins, identical calls are
answered from the record, the auditor can overturn, failures are never frozen,
and measurement runs can switch it off."""

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
from evaluation._config import configure_gate_ledger, get_gate_ledger
from evaluation.evidence_selection import select_evidence
from evaluation.gate_ledger import GateLedger, prompt_hash
from evaluation.llm.llamacpp import LlamaCppTruncated

_YES = json.dumps({"relevant": True})
_NO = json.dumps({"relevant": False})


def make_chunk(**kwargs) -> RetrievedChunk:
    defaults = dict(
        process_number="P001", filename="doc.pdf", page_number=1, chunk_index=0,
        char_offset=0, page_total=10, ocr_used=False, source_type="text",
        text="texto de teste com tamanho suficiente para o gate",
        cascade_step="bm25", expected_product_ids=["1a"], bm25_score=-5.0, rank=1,
    )
    return RetrievedChunk(**{**defaults, **kwargs})


class _Completion:
    def __init__(self, content, reasoning):
        self.content, self.reasoning = content, reasoning


class CountingGateClient:
    """Answers from a list of (content, reasoning); counts real calls."""

    provider_label = "llamacpp"
    model_label = "gpt-oss-20b"
    reasoning_effort = "low"

    def __init__(self, answers):
        self._answers = list(answers)
        self.calls = 0

    def complete(self, system, user, schema=None):  # pragma: no cover
        raise AssertionError("gate should use complete_detailed")

    def complete_detailed(self, system, user, schema=None):
        self.calls += 1
        content, reasoning = self._answers.pop(0)
        if isinstance(content, Exception):
            raise content
        return _Completion(content, reasoning)


@pytest.fixture(autouse=True)
def _profile(monkeypatch):
    import ingestion.retrieval_profile as _rp

    monkeypatch.setattr(_rp, "_store", RetrievalProfileStore(acoes={1: AcaoRetrievalProfile(
        acao_id=1, profile_maturity="seed",
        expected_products={"1a": ExpectedProductProfile(
            evidence_intent="evidência de X", retrieval_signal_concepts=[], query_terms=[],
        )},
    )}))
    monkeypatch.setattr(es, "fetch_neighbor_chunks", lambda *a, **k: (None, None))
    yield
    eval_cfg._reset()


@pytest.fixture
def ledger(tmp_path) -> GateLedger:
    led = GateLedger(tmp_path / "ledger.db")
    configure_gate_ledger(led)
    return led


# --- the key -----------------------------------------------------------------

def test_prompt_hash_changes_with_any_of_its_four_inputs():
    base = prompt_hash("m", "low", "sys", "usr")
    assert base == prompt_hash("m", "low", "sys", "usr")
    assert base != prompt_hash("m2", "low", "sys", "usr")
    assert base != prompt_hash("m", "medium", "sys", "usr")
    assert base != prompt_hash("m", "low", "sys!", "usr")
    assert base != prompt_hash("m", "low", "sys", "usr!")


def test_prompt_hash_separates_fields():
    assert prompt_hash("ab", "c", "s", "u") != prompt_hash("a", "bc", "s", "u")


# --- first verdict wins, later identical calls are not re-asked ---------------

def test_second_identical_call_is_answered_from_the_ledger(ledger):
    client = CountingGateClient([(_YES, "porque sim")])
    eval_cfg._gate_client = client
    first = select_evidence(1, "P001", {"1a": [(0.9, make_chunk())]})
    assert client.calls == 1
    assert first.accepted[0].gate_source == {"1a": "model"}
    assert ledger.count() == 1

    # same prompt again: the model is NOT called, the stored verdict + reasoning come back
    second = select_evidence(1, "P001", {"1a": [(0.9, make_chunk())]})
    assert client.calls == 1
    assert [c.page_number for c in second.accepted] == [1]
    assert second.accepted[0].gate_source == {"1a": "ledger"}
    assert second.accepted[0].gate_reasoning == {"1a": "porque sim"}
    assert second.product_reports[0].n_ledger_hits == 1
    assert second.product_reports[0].providers == ["ledger"]


def test_a_changed_prompt_is_judged_again(ledger):
    client = CountingGateClient([(_NO, "r1"), (_YES, "r2")])
    eval_cfg._gate_client = client
    select_evidence(1, "P001", {"1a": [(0.9, make_chunk())]})
    # a different chunk text -> different user prompt -> new key
    select_evidence(1, "P001", {"1a": [(0.9, make_chunk(text="um texto totalmente diferente e longo"))]})
    assert client.calls == 2
    assert ledger.count() == 2


def test_rejected_chunk_carries_source_and_hash(ledger):
    eval_cfg._gate_client = CountingGateClient([(_NO, "não trata do critério")])
    result = select_evidence(1, "P001", {"1a": [(0.9, make_chunk())]})
    rc = result.rejected[0]
    assert rc.gate_source == "model"
    assert rc.gate_prompt_hash and len(rc.gate_prompt_hash) == 64
    assert ledger.lookup(rc.gate_prompt_hash).relevant is False


# --- auditor override ----------------------------------------------------------

def test_auditor_override_wins_on_the_next_identical_call(ledger):
    eval_cfg._gate_client = CountingGateClient([(_NO, "modelo rejeitou")])
    first = select_evidence(1, "P001", {"1a": [(0.9, make_chunk())]})
    key = first.rejected[0].gate_prompt_hash

    entry = ledger.override(key, relevant=True, justification="trata diretamente do critério")
    assert entry.source == "auditor" and entry.relevant is True
    assert entry.override_justification == "trata diretamente do critério"

    again = select_evidence(1, "P001", {"1a": [(0.9, make_chunk())]})
    assert [c.page_number for c in again.accepted] == [1]
    assert again.accepted[0].gate_source == {"1a": "auditor"}


def test_override_requires_a_known_key_and_a_justification(ledger):
    with pytest.raises(KeyError):
        ledger.override("0" * 64, relevant=True, justification="x")
    eval_cfg._gate_client = CountingGateClient([(_NO, None)])
    key = select_evidence(1, "P001", {"1a": [(0.9, make_chunk())]}).rejected[0].gate_prompt_hash
    with pytest.raises(ValueError):
        ledger.override(key, relevant=True, justification="   ")


def test_record_never_replaces_an_existing_row(ledger):
    key = prompt_hash("m", "low", "s", "u")
    ledger.record(key, relevant=False, reasoning="a", model="m", reasoning_effort="low")
    ledger.record(key, relevant=True, reasoning="b", model="m", reasoning_effort="low")
    assert ledger.lookup(key).relevant is False
    assert ledger.lookup(key).reasoning == "a"


# --- failures are not frozen; off switch ----------------------------------------

def test_failed_gate_call_is_not_recorded(ledger):
    eval_cfg._gate_client = CountingGateClient([(LlamaCppTruncated("length"), None), (_YES, "ok")])
    first = select_evidence(1, "P001", {"1a": [(0.9, make_chunk())]})
    assert first.rejected[0].gate_failed is True
    assert ledger.count() == 0
    second = select_evidence(1, "P001", {"1a": [(0.9, make_chunk())]})
    assert [c.page_number for c in second.accepted] == [1]


def test_without_a_ledger_every_call_reaches_the_model():
    configure_gate_ledger(None)
    assert get_gate_ledger() is None
    client = CountingGateClient([(_NO, None), (_NO, None)])
    eval_cfg._gate_client = client
    select_evidence(1, "P001", {"1a": [(0.9, make_chunk())]})
    select_evidence(1, "P001", {"1a": [(0.9, make_chunk())]})
    assert client.calls == 2


def test_ledger_table_lives_in_the_shared_db(tmp_path):
    import sqlite3

    GateLedger(tmp_path / "app.db")
    con = sqlite3.connect(str(tmp_path / "app.db"))
    try:
        names = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    finally:
        con.close()
    assert "gate_verdicts" in names


class ServedNameGateClient(CountingGateClient):
    """Like the real LlamaCppClient: last_model_used is None before the first
    response and the server-reported name afterwards."""

    def __init__(self, answers):
        super().__init__(answers)
        self.last_model_used = None

    def complete_detailed(self, system, user, schema=None):
        out = super().complete_detailed(system, user, schema)
        self.last_model_used = "Served-Name"
        return out


def test_ledger_key_does_not_depend_on_the_served_model_name(ledger):
    """The key must be the same before and after the client learns the name the
    server reports (otherwise the first prompt of every process misses once)."""
    client = ServedNameGateClient([(_NO, "primeira"), (_YES, "nunca deve ser chamada")])
    eval_cfg._gate_client = client
    first = select_evidence(1, "P001", {"1a": [(0.9, make_chunk())]})
    assert client.calls == 1
    assert first.accepted == [] and first.rejected[0].gate_source == "model"
    second = select_evidence(1, "P001", {"1a": [(0.9, make_chunk())]})
    assert client.calls == 1, "identical prompt re-asked: key changed with last_model_used"
    assert second.rejected[0].gate_source == "ledger"
    assert second.rejected[0].gate_prompt_hash == first.rejected[0].gate_prompt_hash
    assert ledger.count() == 1
    # the row's model column is the string the key was hashed with (the configured label)
    assert ledger.lookup(first.rejected[0].gate_prompt_hash).model == "gpt-oss-20b"
