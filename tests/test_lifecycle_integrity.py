"""Lifecycle integrity regression suite (Issue #25).

Dedicated regression tests for the highest-risk orchestration behaviors.
Each test is labelled with the ADR or behavior it guards.

First-class regression targets:
  1. force=true replacement atomicity (ADR-0026)
  2. Fingerprint reuse correctness (ADR-0029)
  3. Stale extraction prevention (ADR-0029)
  4. Persistence consistency across re-runs (ADR-0026, ADR-0025)
  5. ReviewOutcome invalidation on force-replace (ADR-0026)
"""
from __future__ import annotations

import io
import json
import sqlite3
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

import evaluation._config as eval_cfg
from assessment import configure as assessment_configure, init_db as assessment_init_db
from assessment._config import _reset as assessment_reset
from assessment.api.app import create_app
from assessment.service import AssessmentService, _compute_sha256
from extraction import Chunk
from ingestion import get_ipmp_store
from retrieval import configure as retrieval_configure
from retrieval._config import _reset as retrieval_reset
from retrieval.schema.ddl import init_db as retrieval_init_db


# ── helpers ───────────────────────────────────────────────────────────────────

class StubLLMClient:
    def complete(self, system: str, user: str, schema: dict | None = None) -> str:
        return '{"reasoning": "Evidência confirmada.", "score": 3, "uncertainty": false}'


def _make_chunks(filename: str = "EVTEA.pdf", n: int = 2) -> list[Chunk]:
    return [
        Chunk(
            filename=filename,
            page_number=1,
            chunk_index=i,
            char_offset=i * 40,
            text="Estudo de viabilidade e análise de riscos do projeto.",
            text_length=54,
            page_total=5,
            ocr_used=False,
            source_type="text",
        )
        for i in range(n)
    ]


def _fake_bytes_v1() -> bytes:
    return b"pdf content version 1"


def _fake_bytes_v2() -> bytes:
    return b"pdf content version 2 - changed"


def _row_count(db_path: Path, table: str, process_number: str | None = None) -> int:
    con = sqlite3.connect(str(db_path))
    try:
        if process_number:
            return con.execute(
                f"SELECT COUNT(*) FROM {table} WHERE process_number = ?", (process_number,)
            ).fetchone()[0]
        return con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    finally:
        con.close()


def _get_sha256(db_path: Path, process_number: str, filename: str) -> str | None:
    con = sqlite3.connect(str(db_path))
    try:
        row = con.execute(
            "SELECT sha256 FROM document_fingerprints WHERE process_number=? AND filename=?",
            (process_number, filename),
        ).fetchone()
        return row[0] if row else None
    finally:
        con.close()


def _get_raw_json(db_path: Path, process_number: str, acao_id: int) -> str | None:
    con = sqlite3.connect(str(db_path))
    try:
        row = con.execute(
            "SELECT raw_json FROM evaluation_results WHERE process_number=? AND acao_id=?",
            (process_number, acao_id),
        ).fetchone()
        return row[0] if row else None
    finally:
        con.close()


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
    return TestClient(create_app())


@pytest.fixture
def pdf_file(tmp_path) -> Path:
    p = tmp_path / "EVTEA.pdf"
    p.write_bytes(_fake_bytes_v1())
    return p


def _assess(client: TestClient, process_number: str, content: bytes = None, force: bool = False):
    url = f"/api/cases/{process_number}/assess"
    if force:
        url += "?force=true"
    if content is None:
        content = _fake_bytes_v1()
    with patch("assessment.service.extract_document", return_value=_make_chunks()):
        resp = client.post(
            url,
            files=[("files", ("EVTEA.pdf", io.BytesIO(content), "application/pdf"))],
        )
    return resp


def _review(client: TestClient, process_number: str, acao_id: int = 1):
    return client.post(
        f"/api/cases/{process_number}/evaluations/{acao_id}/review",
        json={"final_score": 3, "is_override": False},
    )


# ── 1. force=true replacement atomicity (ADR-0026) ───────────────────────────

def test_force_replace_deletes_review_outcome_before_evaluation_adr0026(client, db_path):
    """force=true must delete the ReviewOutcome before inserting new EvaluationResult."""
    _assess(client, "P001")
    _review(client, "P001")

    assert _row_count(db_path, "review_outcomes", "P001") == 1

    _assess(client, "P001", force=True)

    # After force-replace: ReviewOutcome gone, new EvaluationResult present
    assert _row_count(db_path, "review_outcomes", "P001") == 0
    assert _row_count(db_path, "evaluation_results", "P001") >= 1


def test_force_replace_review_gone_and_new_eval_present_adr0026(client, db_path):
    """After force=true, GET /review returns 404 and GET /evaluation returns new data."""
    _assess(client, "P001")
    _review(client, "P001")

    _assess(client, "P001", force=True)

    review_resp = client.get("/api/cases/P001/evaluations/1/review")
    assert review_resp.status_code == 404

    eval_resp = client.get("/api/cases/P001/evaluations/1")
    assert eval_resp.status_code == 200


def test_force_replace_is_atomic_partial_failure_leaves_no_stale_state_adr0026(db_path):
    """If the pipeline raises after deletion, no stale ReviewOutcome or EvaluationResult survives."""
    # raise_server_exceptions=False: uncaught route exceptions become 500 responses instead of
    # propagating through TestClient and preventing resp.status_code from being checked.
    failing_client = TestClient(create_app(), raise_server_exceptions=False)

    _assess(failing_client, "P001")
    _review(failing_client, "P001")

    prior_eval_raw = _get_raw_json(db_path, "P001", 1)
    assert prior_eval_raw is not None

    def raising_extract(path):
        raise RuntimeError("simulated extraction failure")

    # force=true triggers deletion, then pipeline fails
    url = "/api/cases/P001/assess?force=true"
    with patch("assessment.service.extract_document", side_effect=raising_extract):
        resp = failing_client.post(
            url,
            files=[("files", ("EVTEA.pdf", io.BytesIO(_fake_bytes_v2()), "application/pdf"))],
        )
    assert resp.status_code == 500

    # After failure: ReviewOutcome deleted (force deleted it before pipeline ran)
    # EvaluationResult also deleted (force deleted it before pipeline ran)
    # No stale data from the prior run survives — the deletion was committed
    assert _row_count(db_path, "review_outcomes", "P001") == 0
    assert _row_count(db_path, "evaluation_results", "P001") == 0


# ── 2. Fingerprint reuse correctness (ADR-0029) ──────────────────────────────

def test_fingerprint_reuse_skips_extraction_adr0029(client):
    """Same SHA-256 on re-submit must not call extract_document again."""
    content = _fake_bytes_v1()
    url = "/api/cases/P001/assess"

    # Inline HTTP calls so the outer mock is not overridden by _assess's internal patch.
    with patch("assessment.service.extract_document", return_value=_make_chunks()) as m:
        client.post(url, files=[("files", ("EVTEA.pdf", io.BytesIO(content), "application/pdf"))])
        first_count = m.call_count

    with patch("assessment.service.extract_document", return_value=_make_chunks()) as m:
        client.post(url, files=[("files", ("EVTEA.pdf", io.BytesIO(content), "application/pdf"))])
        second_count = m.call_count

    assert first_count == 1
    assert second_count == 0  # fingerprint matched — extraction skipped


def test_fingerprint_stored_after_first_index_adr0029(client, db_path):
    """A fingerprint row must exist in document_fingerprints after first assessment."""
    _assess(client, "P001")
    sha = _get_sha256(db_path, "P001", "EVTEA.pdf")
    assert sha is not None
    expected = _compute_sha256.__module__  # just checking it's accessible
    # verify SHA matches the bytes we uploaded
    import hashlib
    h = hashlib.sha256(_fake_bytes_v1())
    assert sha == h.hexdigest()


def test_different_sha256_triggers_reextraction_adr0029(client, db_path):
    """Different file content → extraction called on second run."""
    url = "/api/cases/P001/assess"

    with patch("assessment.service.extract_document", return_value=_make_chunks()) as m:
        client.post(url, files=[("files", ("EVTEA.pdf", io.BytesIO(_fake_bytes_v1()), "application/pdf"))])
        first_count = m.call_count

    with patch("assessment.service.extract_document", return_value=_make_chunks()) as m:
        client.post(url, files=[("files", ("EVTEA.pdf", io.BytesIO(_fake_bytes_v2()), "application/pdf"))])
        second_count = m.call_count

    assert first_count == 1
    assert second_count == 1  # new content → extraction ran again


# ── 3. Stale extraction prevention (ADR-0029) ────────────────────────────────

def test_stale_chunks_replaced_after_fingerprint_mismatch_adr0029(client, db_path):
    """After fingerprint mismatch, only new chunks survive — none from prior extraction."""
    url = "/api/cases/P001/assess"

    with patch("assessment.service.extract_document", return_value=_make_chunks(n=4)):
        client.post(url, files=[("files", ("EVTEA.pdf", io.BytesIO(_fake_bytes_v1()), "application/pdf"))])

    count_v1 = _row_count(db_path, "chunks", "P001")

    with patch("assessment.service.extract_document", return_value=_make_chunks(n=1)):
        client.post(url, files=[("files", ("EVTEA.pdf", io.BytesIO(_fake_bytes_v2()), "application/pdf"))])

    count_v2 = _row_count(db_path, "chunks", "P001")

    assert count_v1 == 4
    assert count_v2 == 1  # exactly 1 chunk — no v1 chunks survive


def test_per_file_replacement_no_contamination_adr0029(client, db_path, tmp_path):
    """Replacing file A must not delete chunks from file B in the same Case."""
    pdf_a = tmp_path / "DocA.pdf"
    pdf_a.write_bytes(b"doc a v1")
    pdf_b = tmp_path / "DocB.pdf"
    pdf_b.write_bytes(b"doc b stable")

    chunks_a = _make_chunks("DocA.pdf", n=2)
    chunks_b = _make_chunks("DocB.pdf", n=3)

    def side_first(path):
        return _make_chunks(path.name, n=2 if "DocA" in path.name else 3)

    with patch("assessment.service.extract_document", side_effect=side_first):
        client.post(
            "/api/cases/P001/assess",
            files=[
                ("files", ("DocA.pdf", io.BytesIO(b"doc a v1"), "application/pdf")),
                ("files", ("DocB.pdf", io.BytesIO(b"doc b stable"), "application/pdf")),
            ],
        )

    total_after_first = _row_count(db_path, "chunks", "P001")
    assert total_after_first == 5  # 2 + 3

    chunks_a_v2 = _make_chunks("DocA.pdf", n=1)

    def side_second(path):
        return chunks_a_v2  # only DocA is re-extracted (DocB fingerprint matches)

    with patch("assessment.service.extract_document", side_effect=side_second):
        client.post(
            "/api/cases/P001/assess",
            files=[
                ("files", ("DocA.pdf", io.BytesIO(b"doc a v2 changed"), "application/pdf")),
                ("files", ("DocB.pdf", io.BytesIO(b"doc b stable"), "application/pdf")),
            ],
        )

    total_after_second = _row_count(db_path, "chunks", "P001")
    # DocA: 1 new chunk; DocB: 3 unchanged chunks
    assert total_after_second == 4


# ── 4. Persistence consistency across re-runs (ADR-0025, ADR-0026) ───────────

def test_raw_json_reflects_latest_evaluation_adr0025(client, db_path):
    """raw_json in evaluation_results must be from the most recent evaluation."""
    import json

    # First run with score-3 response
    eval_cfg._client = StubLLMClient()
    _assess(client, "P001", content=_fake_bytes_v1())
    raw_v1 = _get_raw_json(db_path, "P001", 1)
    assert raw_v1 is not None
    data_v1 = json.loads(raw_v1)

    # Force re-run with score-0 response
    class ZeroStub:
        def complete(self, system, user, schema=None):
            return '{"reasoning": "Nenhuma evidência.", "score": 0, "uncertainty": false}'

    eval_cfg._client = ZeroStub()
    _assess(client, "P001", content=_fake_bytes_v2(), force=True)
    raw_v2 = _get_raw_json(db_path, "P001", 1)
    assert raw_v2 is not None
    data_v2 = json.loads(raw_v2)

    # Exactly one row per (acao_id, process_number), total matching store actions
    num_acoes = len(get_ipmp_store().acoes)
    assert _row_count(db_path, "evaluation_results", "P001") == num_acoes
    # The stored data is from the latest run
    assert data_v2["proposed_score"] == 0


def test_get_evaluation_returns_latest_after_force_rerun_adr0026(client, db_path):
    """GET /evaluation must return new data after force=true re-run."""
    _assess(client, "P001")
    before = client.get("/api/cases/P001/evaluations/1").json()

    class ZeroStub:
        def complete(self, system, user, schema=None):
            return '{"reasoning": "Sem produto.", "score": 0, "uncertainty": false}'

    eval_cfg._client = ZeroStub()
    _assess(client, "P001", content=_fake_bytes_v2(), force=True)
    after = client.get("/api/cases/P001/evaluations/1").json()

    assert after["proposed_score"] == 0
    # Confirm results match loaded store actions (one per action)
    all_results = client.get("/api/cases/P001/evaluations").json()
    assert len(all_results) == len(get_ipmp_store().acoes)


# ── 6. new per-product fields round-trip, old rows still read (2026-09-27) ────

def test_new_per_product_fields_survive_the_raw_json_round_trip(client, db_path):
    """product_verdicts / product_gate_reports / score_source must reach the API.

    raw_json is the canonical read path (ADR-0025/ADR-0031): the routes return
    json.loads(raw_json) verbatim, so anything the auditor is meant to see has to
    be inside that blob, not only on the in-memory model.
    """
    _assess(client, "P001")

    stored = json.loads(_get_raw_json(db_path, "P001", 1))
    assert "product_verdicts" in stored
    assert "product_gate_reports" in stored
    assert "score_source" in stored

    served = client.get("/api/cases/P001/evaluations/1").json()
    assert served["score_source"] == stored["score_source"]
    assert served["product_verdicts"] == stored["product_verdicts"]
    assert served["product_gate_reports"] == stored["product_gate_reports"]


def test_stub_without_products_is_recorded_as_a_model_sourced_score(client, db_path):
    """The lifecycle stub returns the pre-2026-09-27 shape, so the fallback path
    is what this suite exercises — it must be labelled, not silently accepted."""
    _assess(client, "P001")
    stored = json.loads(_get_raw_json(db_path, "P001", 1))
    assert stored["score_source"] == "model"
    assert stored["product_verdicts"] == []
    assert stored["uncertainty_flag"] is True


def test_evaluation_persisted_before_the_new_fields_still_reads_back(client, db_path):
    """A raw_json blob with none of the new keys must still be served as-is.

    Nothing migrates these rows and the read path does not re-validate them, so
    this guards the one way the change could break existing cases.
    """
    _assess(client, "P001")

    legacy = json.loads(_get_raw_json(db_path, "P001", 1))
    for key in ("product_verdicts", "product_gate_reports", "score_source",
                "score_margin", "dependency_cap"):
        legacy.pop(key, None)
    con = sqlite3.connect(str(db_path))
    try:
        con.execute(
            "UPDATE evaluation_results SET raw_json = ? "
            "WHERE process_number = ? AND acao_id = ?",
            (json.dumps(legacy), "P001", 1),
        )
        con.commit()
    finally:
        con.close()

    resp = client.get("/api/cases/P001/evaluations/1")
    assert resp.status_code == 200
    body = resp.json()
    assert "product_verdicts" not in body
    assert body["proposed_score"] == legacy["proposed_score"]

    listed = client.get("/api/cases/P001/evaluations")
    assert listed.status_code == 200
    assert len(listed.json()) >= 1


# ── gate verdict overrides (ADR-0067) ─────────────────────────────────────────

def _override(client: TestClient, process_number: str, acao_id: int, **body):
    payload = {"prompt_hash": "0" * 64, "relevant": True, "justification": "trata do critério"}
    payload.update(body)
    return client.post(
        f"/api/cases/{process_number}/evaluations/{acao_id}/gate-overrides", json=payload
    )


def test_gate_override_503_when_no_ledger_is_configured(client):
    from evaluation._config import configure_gate_ledger

    configure_gate_ledger(None)
    _assess(client, "P001")
    assert _override(client, "P001", 1).status_code == 503


def test_gate_override_404_for_unknown_hash_and_422_without_justification(client, db_path):
    from evaluation._config import configure_gate_ledger
    from evaluation.gate_ledger import GateLedger

    configure_gate_ledger(GateLedger(db_path))
    try:
        _assess(client, "P001")
        assert _override(client, "P001", 1).status_code == 404
        assert _override(client, "P001", 1, justification="  ").status_code == 422
        assert _override(client, "P001", 1, prompt_hash="xyz").status_code == 422
        assert _override(client, "P999", 1).status_code == 404  # no evaluation for that case
    finally:
        configure_gate_ledger(None)


def test_gate_override_flips_a_recorded_verdict(client, db_path):
    from evaluation._config import configure_gate_ledger
    from evaluation.gate_ledger import GateLedger, prompt_hash

    ledger = GateLedger(db_path)
    configure_gate_ledger(ledger)
    try:
        _assess(client, "P001")
        key = prompt_hash("m", "low", "sys", "usr")
        ledger.record(key, relevant=False, reasoning="r", model="m", reasoning_effort="low",
                      acao_id=1, product_id="1a", process_number="P001")
        resp = _override(client, "P001", 1, prompt_hash=key, justification="evidência direta")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["relevant"] is True and body["source"] == "auditor"
        assert body["override_justification"] == "evidência direta"
        assert ledger.lookup(key).source == "auditor"
        # a row recorded for another Ação cannot be overridden through this Ação's route
        other = prompt_hash("m", "low", "sys2", "usr2")
        ledger.record(other, relevant=False, reasoning=None, model="m", reasoning_effort="low", acao_id=2)
        assert _override(client, "P001", 1, prompt_hash=other).status_code == 404
    finally:
        configure_gate_ledger(None)
