"""Route tests for Issues #23 and #24 using FastAPI TestClient.

Tests cover:
- POST /api/cases/{process_number}/assess (Issue #23)
- GET  /api/cases/{process_number}/evaluations (Issue #23)
- GET  /api/cases/{process_number}/evaluations/{acao_id} (Issue #23)
- POST /api/cases/{process_number}/evaluations/{acao_id}/review (Issue #24)
- GET  /api/cases/{process_number}/evaluations/{acao_id}/review (Issue #24)
"""
from __future__ import annotations

import io
import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import evaluation._config as eval_cfg
from assessment import configure as assessment_configure, init_db as assessment_init_db
from assessment._config import _reset as assessment_reset
from assessment.api.app import create_app
from extraction import Chunk
from retrieval import configure as retrieval_configure
from retrieval._config import _reset as retrieval_reset
from retrieval.schema.ddl import init_db as retrieval_init_db

# ── helpers ───────────────────────────────────────────────────────────────────

class StubLLMClient:
    def __init__(self, response: str = "Evidência presente.\nSCORE: 3\nUNCERTAINTY: no"):
        self._response = response

    def complete(self, system: str, user: str) -> str:
        return self._response


def _make_chunks(filename: str = "EVTEA.pdf", n: int = 2) -> list[Chunk]:
    return [
        Chunk(
            filename=filename,
            page_number=1,
            chunk_index=i,
            char_offset=i * 50,
            text="Estudo de viabilidade técnica e econômica do projeto de concessão.",
            text_length=66,
            page_total=5,
            ocr_used=False,
            source_type="text",
        )
        for i in range(n)
    ]


def _fake_pdf_bytes() -> bytes:
    return b"fake pdf content for testing"


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def db_path(tmp_path) -> Path:
    path = tmp_path / "app.db"
    retrieval_configure(path)
    retrieval_init_db(path)
    assessment_configure(path)
    assessment_init_db(path)
    return path


@pytest.fixture(autouse=True)
def reset_modules(db_path):
    eval_cfg._client = StubLLMClient()
    eval_cfg._provider = "ollama"
    eval_cfg._model = "mistral"
    yield
    retrieval_reset()
    assessment_reset()
    eval_cfg._client = None
    eval_cfg._provider = None
    eval_cfg._model = None


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


def _upload_file(client: TestClient, process_number: str, force: bool = False) -> None:
    """Helper: POST /assess with a synthetic PDF upload."""
    url = f"/api/cases/{process_number}/assess"
    if force:
        url += "?force=true"
    with patch("assessment.service.extract_document", return_value=_make_chunks()):
        resp = client.post(
            url,
            files=[("files", ("EVTEA.pdf", io.BytesIO(_fake_pdf_bytes()), "application/pdf"))],
        )
    assert resp.status_code == 200, resp.text


# ── POST /assess ──────────────────────────────────────────────────────────────

def test_assess_returns_200_on_first_run(client):
    with patch("assessment.service.extract_document", return_value=_make_chunks()):
        resp = client.post(
            "/api/cases/P001/assess",
            files=[("files", ("EVTEA.pdf", io.BytesIO(_fake_pdf_bytes()), "application/pdf"))],
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["process_number"] == "P001"
    assert body["count"] >= 1
    assert "documents" in body
    assert body["documents"] == [{"filename": "EVTEA.pdf", "disposition": "new"}]


def test_assess_409_when_review_outcome_exists(client, db_path):
    _upload_file(client, "P001")

    # Insert a review outcome directly
    con = sqlite3.connect(str(db_path))
    con.execute(
        "INSERT INTO review_outcomes "
        "(acao_id, process_number, final_score, is_override, justification, evidence_references, created_at) "
        "VALUES (1, 'P001', 3, 0, NULL, NULL, '2026-06-02T00:00:00+00:00')"
    )
    con.commit()
    con.close()

    with patch("assessment.service.extract_document", return_value=_make_chunks()):
        resp = client.post(
            "/api/cases/P001/assess",
            files=[("files", ("EVTEA.pdf", io.BytesIO(_fake_pdf_bytes()), "application/pdf"))],
        )
    assert resp.status_code == 409


def test_assess_force_true_replaces_existing(client, db_path):
    _upload_file(client, "P001")

    # Add a review outcome
    con = sqlite3.connect(str(db_path))
    con.execute(
        "INSERT INTO review_outcomes "
        "(acao_id, process_number, final_score, is_override, justification, evidence_references, created_at) "
        "VALUES (1, 'P001', 3, 0, NULL, NULL, '2026-06-02T00:00:00+00:00')"
    )
    con.commit()
    con.close()

    with patch("assessment.service.extract_document", return_value=_make_chunks()):
        resp = client.post(
            "/api/cases/P001/assess?force=true",
            files=[("files", ("EVTEA.pdf", io.BytesIO(_fake_pdf_bytes()), "application/pdf"))],
        )
    assert resp.status_code == 200

    # review_outcomes must be gone
    con = sqlite3.connect(str(db_path))
    count = con.execute(
        "SELECT COUNT(*) FROM review_outcomes WHERE process_number='P001'"
    ).fetchone()[0]
    con.close()
    assert count == 0


# ── GET /evaluations ──────────────────────────────────────────────────────────

def test_list_evaluations_returns_all_results(client):
    _upload_file(client, "P001")
    resp = client.get("/api/cases/P001/evaluations")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) >= 1
    assert all("acao_id" in item for item in body)


def test_list_evaluations_empty_when_no_assessment(client):
    resp = client.get("/api/cases/UNKNOWN/evaluations")
    assert resp.status_code == 200
    assert resp.json() == []


# ── GET /evaluations/{acao_id} ────────────────────────────────────────────────

def test_get_evaluation_returns_full_result(client):
    _upload_file(client, "P001")
    resp = client.get("/api/cases/P001/evaluations/1")
    assert resp.status_code == 200
    body = resp.json()
    assert body["acao_id"] == 1
    assert body["process_number"] == "P001"
    assert "retrieved_chunks" in body
    assert "proposed_score" in body
    assert "uncertainty_flag" in body
    assert "parse_failed" in body
    assert "no_evidence_found" in body
    assert "system_prompt" in body
    assert "reasoning" in body


def test_get_evaluation_404_when_missing(client):
    resp = client.get("/api/cases/UNKNOWN/evaluations/1")
    assert resp.status_code == 404


# ── POST /review ──────────────────────────────────────────────────────────────

def test_submit_review_accept(client):
    _upload_file(client, "P001")
    resp = client.post(
        "/api/cases/P001/evaluations/1/review",
        json={"final_score": 3, "is_override": False, "justification": None},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["final_score"] == 3
    assert body["is_override"] is False
    assert body["justification"] is None
    assert "created_at" in body


def test_submit_review_override_with_justification(client):
    _upload_file(client, "P001")
    resp = client.post(
        "/api/cases/P001/evaluations/1/review",
        json={
            "final_score": 1,
            "is_override": True,
            "justification": "Produto parcialmente evidenciado na página 5.",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["final_score"] == 1
    assert body["is_override"] is True
    assert "Produto parcialmente" in body["justification"]


def test_submit_review_override_missing_justification_422(client):
    _upload_file(client, "P001")
    resp = client.post(
        "/api/cases/P001/evaluations/1/review",
        json={"final_score": 1, "is_override": True, "justification": None},
    )
    assert resp.status_code == 422


def test_submit_review_invalid_score_422(client):
    _upload_file(client, "P001")
    resp = client.post(
        "/api/cases/P001/evaluations/1/review",
        json={"final_score": 2, "is_override": False},
    )
    assert resp.status_code == 422


def test_submit_review_404_when_no_evaluation(client):
    resp = client.post(
        "/api/cases/UNKNOWN/evaluations/1/review",
        json={"final_score": 3, "is_override": False},
    )
    assert resp.status_code == 404


def test_submit_review_409_on_duplicate(client):
    _upload_file(client, "P001")
    payload = {"final_score": 3, "is_override": False}
    client.post("/api/cases/P001/evaluations/1/review", json=payload)
    resp = client.post("/api/cases/P001/evaluations/1/review", json=payload)
    assert resp.status_code == 409


def test_created_at_is_server_side(client):
    _upload_file(client, "P001")
    resp = client.post(
        "/api/cases/P001/evaluations/1/review",
        json={"final_score": 3, "is_override": False},
    )
    assert resp.status_code == 201
    body = resp.json()
    # created_at must be present and parseable — value is set server-side
    from datetime import datetime
    dt = datetime.fromisoformat(body["created_at"])
    assert dt is not None


def test_evidence_references_none_vs_empty(client):
    _upload_file(client, "P001")
    resp = client.post(
        "/api/cases/P001/evaluations/1/review",
        json={"final_score": 3, "is_override": False, "evidence_references": None},
    )
    assert resp.status_code == 201
    assert resp.json()["evidence_references"] is None


# ── GET /review ───────────────────────────────────────────────────────────────

def test_get_review_returns_stored_outcome(client):
    _upload_file(client, "P001")
    client.post(
        "/api/cases/P001/evaluations/1/review",
        json={"final_score": 3, "is_override": False},
    )
    resp = client.get("/api/cases/P001/evaluations/1/review")
    assert resp.status_code == 200
    body = resp.json()
    assert body["acao_id"] == 1
    assert body["process_number"] == "P001"
    assert body["final_score"] == 3


def test_get_review_404_when_missing(client):
    resp = client.get("/api/cases/UNKNOWN/evaluations/1/review")
    assert resp.status_code == 404


# ── /api prefix — Issue #29 ───────────────────────────────────────────────────

def test_assess_reused_disposition_on_second_identical_upload(client):
    with patch("assessment.service.extract_document", return_value=_make_chunks()):
        resp1 = client.post(
            "/api/cases/P001/assess",
            files=[("files", ("EVTEA.pdf", io.BytesIO(_fake_pdf_bytes()), "application/pdf"))],
        )
    assert resp1.status_code == 200
    assert resp1.json()["documents"][0]["disposition"] == "new"

    with patch("assessment.service.extract_document", return_value=_make_chunks()):
        resp2 = client.post(
            "/api/cases/P001/assess",
            files=[("files", ("EVTEA.pdf", io.BytesIO(_fake_pdf_bytes()), "application/pdf"))],
        )
    assert resp2.status_code == 200
    assert resp2.json()["documents"][0]["disposition"] == "reused"


def test_assess_replaced_disposition_when_content_changes(client):
    with patch("assessment.service.extract_document", return_value=_make_chunks()):
        client.post(
            "/api/cases/P001/assess",
            files=[("files", ("EVTEA.pdf", io.BytesIO(b"version 1"), "application/pdf"))],
        )
    with patch("assessment.service.extract_document", return_value=_make_chunks()):
        resp = client.post(
            "/api/cases/P001/assess",
            files=[("files", ("EVTEA.pdf", io.BytesIO(b"version 2 different content"), "application/pdf"))],
        )
    assert resp.status_code == 200
    assert resp.json()["documents"][0]["disposition"] == "replaced"


def test_old_path_without_api_prefix_returns_404(client):
    with patch("assessment.service.extract_document", return_value=_make_chunks()):
        resp = client.post(
            "/cases/P001/assess",
            files=[("files", ("EVTEA.pdf", io.BytesIO(_fake_pdf_bytes()), "application/pdf"))],
        )
    assert resp.status_code == 404
