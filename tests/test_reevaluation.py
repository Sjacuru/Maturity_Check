"""Re-evaluation of selected Ações after gate overrides (ADR-0078).

The auditor marks gate verdicts (ADR-0067) and then re-evaluates the Ações
they belong to, or all of them, from the documents already indexed. Only those
Ações run the gate and the scorer again; their reviews are deleted; the Ações
that cite them with effect (ADR-0070) have the cap recalculated without the
model, and lose their review only when their score changes.
"""

from __future__ import annotations

import io
import json
import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import evaluation._config as eval_cfg
from assessment import configure as assessment_configure, init_db as assessment_init_db
from assessment._config import _reset as assessment_reset
from assessment.api.app import create_app
from assessment.service import (
    AssessmentService,
    _persist_evaluation_result,
    pending_gate_overrides,
    reviews_at_stake,
)
from evaluation import GateLedger, evaluate, recompute_dependency_cap
from evaluation.interfaces.contracts import EvaluationResult
from evaluation.llm.llamacpp import LlamaCppUnavailable
from extraction import Chunk
from ingestion import get_dependency_store, get_ipmp_store
from retrieval import RetrievedChunk
from retrieval import configure as retrieval_configure
from retrieval._config import _reset as retrieval_reset
from retrieval.schema.ddl import init_db as retrieval_init_db

P = "P078"


# ── helpers ───────────────────────────────────────────────────────────────────

class _Stub:
    """Scorer stub: every listed product gets the given verdict."""

    def __init__(self, products: dict[str, bool]) -> None:
        self._products = products
        self.calls = 0

    def complete(self, system: str, user: str, schema: dict | None = None) -> str:
        self.calls += 1
        return json.dumps({
            "reasoning": "ok", "score": 3, "uncertainty": False,
            "products": [{"product_id": p, "evidenced": e, "justificativa": "j"}
                         for p, e in self._products.items()],
        })


class _DownStub(_Stub):
    def health_check(self) -> None:
        raise LlamaCppUnavailable("server down")


def _products(acao_id: int) -> list[str]:
    return [p.id for p in get_ipmp_store().acoes[acao_id].produtos_esperados if p.scored]


def _chunk(product_ids: list[str], page: int = 158) -> RetrievedChunk:
    return RetrievedChunk(
        process_number=P, filename="ETP.pdf", page_number=page, chunk_index=0,
        char_offset=0, page_total=10, ocr_used=False, source_type="text",
        text="Divisão do objeto em quatro lotes com quantitativos.",
        cascade_step="bm25", expected_product_ids=product_ids, bm25_score=3.5, rank=1,
    )


def _plain(acao_id: int, score: int) -> EvaluationResult:
    return EvaluationResult(
        acao_id=acao_id, process_number=P, provider="llamacpp", model="m",
        retrieved_chunks=[], evidence_char_count=10, system_prompt="s",
        user_prompt="u", raw_llm_response="{}", reasoning="r",
        proposed_score=score, uncertainty_flag=False, parse_failed=False,
        no_evidence_found=False,
    )


def _wire(stub) -> None:
    eval_cfg._client = stub
    eval_cfg._provider = "llamacpp"
    eval_cfg._model = "stub"


def _review(db: Path, acao_id: int, score: int = 1) -> None:
    con = sqlite3.connect(str(db))
    con.execute(
        "INSERT INTO review_outcomes (acao_id, process_number, final_score, is_override, "
        "justification, evidence_references, created_at) VALUES (?, ?, ?, 0, NULL, NULL, ?)",
        (acao_id, P, score, "2026-10-01T00:00:00+00:00"),
    )
    con.commit()
    con.close()


def _row(db: Path, acao_id: int) -> tuple | None:
    con = sqlite3.connect(str(db))
    try:
        return con.execute(
            "SELECT proposed_score, created_at, raw_json FROM evaluation_results "
            "WHERE process_number = ? AND acao_id = ?", (P, acao_id),
        ).fetchone()
    finally:
        con.close()


def _has_review(db: Path, acao_id: int) -> bool:
    con = sqlite3.connect(str(db))
    try:
        return con.execute(
            "SELECT 1 FROM review_outcomes WHERE process_number = ? AND acao_id = ?",
            (P, acao_id),
        ).fetchone() is not None
    finally:
        con.close()


def _age(db: Path, acao_id: int) -> None:
    """Date an evaluation well before any override the test records."""
    con = sqlite3.connect(str(db))
    con.execute(
        "UPDATE evaluation_results SET created_at = ? WHERE process_number = ? AND acao_id = ?",
        ("2026-01-01T00:00:00+00:00", P, acao_id),
    )
    con.commit()
    con.close()


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def db(tmp_path) -> Path:
    path = tmp_path / "app.db"
    retrieval_configure(path)
    retrieval_init_db(path)
    assessment_configure(path)
    assessment_init_db(path)
    yield path
    retrieval_reset()
    assessment_reset()


@pytest.fixture(autouse=True)
def _llm_state():
    yield
    eval_cfg._client = None
    eval_cfg._provider = None
    eval_cfg._model = None
    eval_cfg._gate_ledger = None


@pytest.fixture
def client(db) -> TestClient:
    return TestClient(create_app())


def _seed_2_and_3(db: Path) -> None:
    """Ação 2 came out 0, so Ação 3's counted 3 is capped to 1 (ADR-0070)."""
    _persist_evaluation_result(db, _plain(2, 0))
    _wire(_Stub({"3a": True}))
    capped = evaluate(3, P, [_chunk(["3a"])], prior_results={2: _plain(2, 0)})
    assert capped.proposed_score == 1 and capped.dependency_cap.applied
    _persist_evaluation_result(db, capped)


# ── recompute_dependency_cap ─────────────────────────────────────────────────

def test_lifting_the_prerequisite_removes_the_cap_exactly_as_a_fresh_evaluation():
    _wire(_Stub({"3a": True}))
    capped = evaluate(3, P, [_chunk(["3a"])], prior_results={2: _plain(2, 0)})
    fresh = evaluate(3, P, [_chunk(["3a"])], prior_results={2: _plain(2, 1)})
    again = recompute_dependency_cap(capped, {2: _plain(2, 1)}, get_dependency_store())
    assert again.proposed_score == 3
    assert again.model_dump() == fresh.model_dump()


def test_lowering_the_prerequisite_applies_the_cap_exactly_as_a_fresh_evaluation():
    _wire(_Stub({"3a": True}))
    open_ = evaluate(3, P, [_chunk(["3a"])], prior_results={2: _plain(2, 1)})
    fresh = evaluate(3, P, [_chunk(["3a"])], prior_results={2: _plain(2, 0)})
    again = recompute_dependency_cap(open_, {2: _plain(2, 0)}, get_dependency_store())
    assert again.proposed_score == 1
    assert again.model_dump() == fresh.model_dump()


def test_a_no_evidence_result_is_returned_unchanged():
    _wire(_Stub({"3a": True}))
    empty = evaluate(3, P, [], prior_results={2: _plain(2, 0)})
    assert recompute_dependency_cap(empty, {2: _plain(2, 1)}, get_dependency_store()) is empty


# ── the service ──────────────────────────────────────────────────────────────

def test_reevaluating_a_prerequisite_recalculates_its_dependent(db):
    _seed_2_and_3(db)
    _review(db, 2)
    _review(db, 3)
    created_3 = _row(db, 3)[1]
    _wire(_Stub({p: True for p in _products(2)}))
    with patch(
        "assessment.service._retrieve_and_select",
        return_value=([_chunk(_products(2))], [], []),
    ):
        report = AssessmentService().run_reevaluation(P, [2])

    assert report["reevaluated"] == [
        {"acao_id": 2, "before": "0", "after": "3", "review_deleted": True}
    ]
    assert report["dependents"] == [
        {"acao_id": 3, "before": "1", "after": "3", "review_deleted": True}
    ]
    assert report["interrupted"] is None and report["failed"] == []
    assert _row(db, 2)[0] == 3 and _row(db, 3)[0] == 3
    stored_3 = EvaluationResult.model_validate_json(_row(db, 3)[2])
    assert not stored_3.dependency_cap.applied
    # the dependent was not run again: same row date, so an override recorded
    # on it would still read as pending
    assert _row(db, 3)[1] == created_3
    assert not _has_review(db, 2) and not _has_review(db, 3)


def test_a_dependent_whose_score_does_not_change_keeps_its_review(db):
    _seed_2_and_3(db)
    _review(db, 3)
    _wire(_Stub({p: False for p in _products(2)}))  # Ação 2 stays at 0
    with patch(
        "assessment.service._retrieve_and_select",
        return_value=([_chunk(_products(2))], [], []),
    ):
        report = AssessmentService().run_reevaluation(P, [2])
    assert report["dependents"] == []
    assert _row(db, 3)[0] == 1
    assert _has_review(db, 3)


def test_a_failing_acao_keeps_its_evaluation_and_review(db):
    _seed_2_and_3(db)
    _review(db, 2)
    before = _row(db, 2)
    _wire(_Stub({}))
    with patch("assessment.service._retrieve_and_select", side_effect=RuntimeError("boom")):
        report = AssessmentService().run_reevaluation(P, [2])
    assert report["failed"] == [2] and report["reevaluated"] == []
    assert _row(db, 2) == before
    assert _has_review(db, 2)


def test_reviews_at_stake_lists_targets_and_transitive_dependents(db):
    _seed_2_and_3(db)
    for a in (2, 3, 5):
        _review(db, a)
    targets, dependents = reviews_at_stake(db, P, [2])
    assert targets == [2]
    assert 3 in dependents and 5 not in dependents


# ── the routes ───────────────────────────────────────────────────────────────

def _assess(client: TestClient) -> None:
    chunks = [
        Chunk(filename="EVTEA.pdf", page_number=1, chunk_index=i, char_offset=i * 50,
              text="Estudo de viabilidade técnica e econômica do projeto de concessão.",
              text_length=66, page_total=5, ocr_used=False, source_type="text")
        for i in range(2)
    ]
    _wire(_Stub({}))
    with patch("assessment.service.extract_document", return_value=chunks):
        resp = client.post(
            f"/api/cases/{P}/assess",
            files=[("files", ("EVTEA.pdf", io.BytesIO(b"pdf"), "application/pdf"))],
        )
    assert resp.status_code == 200, resp.text


def test_route_refuses_an_empty_list_and_an_unknown_acao(client):
    _assess(client)
    assert client.post(f"/api/cases/{P}/reevaluate", json={"acao_ids": []}).status_code == 422
    assert client.post(f"/api/cases/{P}/reevaluate", json={"acao_ids": [999]}).status_code == 422


def test_route_404_for_an_acao_without_evaluation(client):
    assert client.post(f"/api/cases/{P}/reevaluate", json={"acao_ids": [1]}).status_code == 404


def test_route_409_names_the_reviews_until_confirmed(client, db):
    _assess(client)
    _review(db, 1)
    resp = client.post(f"/api/cases/{P}/reevaluate", json={"acao_ids": [1]})
    assert resp.status_code == 409
    assert resp.json()["detail"]["reviewed_targets"] == [1]
    assert _has_review(db, 1)

    resp = client.post(f"/api/cases/{P}/reevaluate", json={"acao_ids": [1], "delete_reviews": True})
    assert resp.status_code == 200, resp.text
    assert resp.json()["reevaluated"][0]["acao_id"] == 1
    assert not _has_review(db, 1)


def test_route_touches_only_the_requested_acoes(client, db):
    _assess(client)
    others = {a: _row(db, a) for a in get_ipmp_store().acoes if a not in (1, 2, 3, 4)}
    resp = client.post(f"/api/cases/{P}/reevaluate", json={"acao_ids": [1]})
    assert resp.status_code == 200, resp.text
    # Ações citing 1 may be recalculated; the rest stay byte for byte.
    cites_1 = {a for a in get_ipmp_store().acoes
               if any(d.citada == 1 for d in get_dependency_store().com_efeito(a))}
    for a, row in others.items():
        if a not in cites_1:
            assert _row(db, a) == row


def test_route_503_when_the_server_is_down_and_nothing_changes(client, db):
    _assess(client)
    before = _row(db, 1)
    _wire(_DownStub({}))
    resp = client.post(f"/api/cases/{P}/reevaluate", json={"acao_ids": [1]})
    assert resp.status_code == 503
    assert _row(db, 1) == before


def test_pending_lists_an_override_until_its_acao_is_reevaluated(client, db):
    _assess(client)
    _age(db, 1)
    ledger = GateLedger(db)
    eval_cfg._gate_ledger = ledger
    ledger.record("a" * 64, relevant=False, reasoning="r", model="m", reasoning_effort="low",
                  acao_id=1, product_id="1a", process_number=P, filename="EVTEA.pdf",
                  page_number=1, chunk_index=0)
    assert client.get(f"/api/cases/{P}/reevaluation/pending").json()["acao_ids"] == []

    ledger.override("a" * 64, relevant=True, justification="trecho trata do diagnóstico")
    body = client.get(f"/api/cases/{P}/reevaluation/pending").json()
    assert body["acao_ids"] == [1]
    assert body["overrides"][0]["justification"] == "trecho trata do diagnóstico"

    _wire(_Stub({}))
    assert client.post(f"/api/cases/{P}/reevaluate", json={"acao_ids": [1]}).status_code == 200
    assert pending_gate_overrides(db, P) == []
