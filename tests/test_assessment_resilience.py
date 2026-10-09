"""Run-level failure handling: fail fast on the server, isolate a bad Ação.

Two behaviours pinned here, both introduced 2026-09-27:

* The LLM wiring is GPU-only with no fallback (see main.py), so an unreachable
  inference server must stop the run before any Ação is attempted. Without the
  preflight, a switched-off server walked all 46 Ações, paid a connect timeout
  on each, and stored 46 evaluations flagged `no_evidence_found=True` — which is
  indistinguishable, in the audit trail, from "the documents genuinely lack this
  evidence".

* Any OTHER per-Ação exception must be recorded and the loop must continue. The
  loop previously had no try/except at all, so a single failing Ação discarded
  the other 45.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

import evaluation._config as eval_cfg
from assessment import configure as assessment_configure, init_db as assessment_init_db
from assessment._config import _reset as assessment_reset
from assessment.service import AssessmentService
from evaluation.llm.llamacpp import LlamaCppBusy, LlamaCppTimeout, LlamaCppUnavailable
from extraction import Chunk
from retrieval import configure as retrieval_configure
from retrieval._config import _reset as retrieval_reset
from retrieval.schema.ddl import init_db as retrieval_init_db


class StubLLMClient:
    def __init__(self, response: str = '{"reasoning": "ok", "score": 3, "uncertainty": false}'):
        self._response = response
        self.call_count = 0

    def complete(self, system: str, user: str, schema: dict | None = None) -> str:
        self.call_count += 1
        return self._response


class UnhealthyClient(StubLLMClient):
    """Exposes health_check() and fails it, like a real LlamaCppClient would
    against a server that is switched off."""

    def __init__(self, exc: Exception):
        super().__init__()
        self._exc = exc
        self.health_checks = 0

    def health_check(self, timeout: float | None = None) -> None:
        self.health_checks += 1
        raise self._exc


def _make_chunks(filename: str, n: int = 2) -> list[Chunk]:
    return [
        Chunk(
            filename=filename,
            page_number=1,
            chunk_index=i,
            char_offset=i * 50,
            text=f"Produto esperado {i}: estudo de viabilidade técnica e econômica.",
            text_length=60,
            page_total=3,
            ocr_used=False,
            source_type="text",
        )
        for i in range(n)
    ]


def _eval_count(db_path: Path) -> int:
    con = sqlite3.connect(str(db_path))
    try:
        return con.execute("SELECT COUNT(*) FROM evaluation_results").fetchone()[0]
    finally:
        con.close()


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
    stub = StubLLMClient()
    eval_cfg._client = stub
    eval_cfg._provider = "llamacpp"
    eval_cfg._model = "gpt-oss-20b"
    yield stub
    retrieval_reset()
    assessment_reset()
    eval_cfg._client = None
    eval_cfg._provider = None
    eval_cfg._model = None


@pytest.fixture
def dummy_pdf(tmp_path) -> Path:
    p = tmp_path / "EVTEA.pdf"
    p.write_bytes(b"fake pdf content v1")
    return p


# ── preflight: fail fast when the server is down ────────────────────────────

@pytest.mark.parametrize(
    "exc",
    [
        LlamaCppUnavailable("connection refused"),
        LlamaCppTimeout("timed out"),
        LlamaCppBusy("HTTP 503"),
    ],
)
def test_preflight_aborts_before_any_acao_when_server_is_down(db_path, dummy_pdf, exc):
    eval_cfg._client = UnhealthyClient(exc)
    svc = AssessmentService()

    with patch("assessment.service.extract_document", return_value=_make_chunks("EVTEA.pdf")):
        with pytest.raises(type(exc)):
            svc.run_assessment("P001", [dummy_pdf])

    assert _eval_count(db_path) == 0, "no Ação may be stored when the server is unreachable"


def test_preflight_probes_the_scorer_client(db_path, dummy_pdf):
    client = UnhealthyClient(LlamaCppUnavailable("refused"))
    eval_cfg._client = client
    svc = AssessmentService()

    with patch("assessment.service.extract_document", return_value=_make_chunks("EVTEA.pdf")):
        with pytest.raises(LlamaCppUnavailable):
            svc.run_assessment("P001", [dummy_pdf])

    assert client.health_checks == 1


def test_preflight_skips_clients_without_health_check(db_path, dummy_pdf):
    """A stub or an OllamaClient has no health_check(); that must not break the run."""
    assert not hasattr(eval_cfg._client, "health_check")
    svc = AssessmentService()

    with patch("assessment.service.extract_document", return_value=_make_chunks("EVTEA.pdf")):
        results, _ = svc.run_assessment("P001", [dummy_pdf])

    assert len(results) > 0


def test_documents_are_still_indexed_before_the_preflight_fires(db_path, dummy_pdf):
    """Extraction/indexing happens before the preflight, so an outage does not
    force a re-upload and re-extraction on the next attempt."""
    eval_cfg._client = UnhealthyClient(LlamaCppUnavailable("refused"))
    svc = AssessmentService()

    with patch("assessment.service.extract_document", return_value=_make_chunks("EVTEA.pdf")):
        with pytest.raises(LlamaCppUnavailable):
            svc.run_assessment("P001", [dummy_pdf])

    con = sqlite3.connect(str(db_path))
    try:
        indexed = con.execute(
            "SELECT COUNT(*) FROM chunks WHERE process_number = 'P001'"
        ).fetchone()[0]
    finally:
        con.close()
    assert indexed == 2


# ── mid-run infrastructure failure stops the loop ───────────────────────────

def test_infrastructure_failure_mid_run_stops_and_preserves_earlier_acoes(db_path, dummy_pdf):
    from ingestion import get_ipmp_store

    acao_ids = sorted(get_ipmp_store().acoes)
    fail_on = acao_ids[2]

    real_evaluate = None

    def flaky_evaluate(acao_id, process_number, chunks, **kwargs):
        if acao_id == fail_on:
            raise LlamaCppUnavailable("server vanished mid-run")
        return real_evaluate(acao_id, process_number, chunks, **kwargs)

    import assessment.service as svc_mod

    real_evaluate = svc_mod.evaluate
    svc = AssessmentService()

    with patch("assessment.service.extract_document", return_value=_make_chunks("EVTEA.pdf")):
        with patch.object(svc_mod, "evaluate", flaky_evaluate):
            with pytest.raises(LlamaCppUnavailable):
                svc.run_assessment("P001", [dummy_pdf])

    # The two Ações evaluated before the failure must survive.
    assert _eval_count(db_path) == 2


# ── a single bad Ação must not discard the rest ─────────────────────────────

def test_one_failing_acao_does_not_abort_the_run(db_path, dummy_pdf):
    from ingestion import get_ipmp_store

    acao_ids = sorted(get_ipmp_store().acoes)
    fail_on = acao_ids[1]

    import assessment.service as svc_mod

    real_evaluate = svc_mod.evaluate

    def flaky_evaluate(acao_id, process_number, chunks, **kwargs):
        if acao_id == fail_on:
            raise ValueError("defeito só desta Ação")
        return real_evaluate(acao_id, process_number, chunks, **kwargs)

    svc = AssessmentService()
    with patch("assessment.service.extract_document", return_value=_make_chunks("EVTEA.pdf")):
        with patch.object(svc_mod, "evaluate", flaky_evaluate):
            results, _ = svc.run_assessment("P001", [dummy_pdf])

    evaluated = {r.acao_id for r in results}
    assert fail_on not in evaluated
    assert len(evaluated) == len(acao_ids) - 1
    assert _eval_count(db_path) == len(acao_ids) - 1


def test_failing_acao_is_reported_in_progress(db_path, dummy_pdf):
    from assessment import progress
    from ingestion import get_ipmp_store

    acao_ids = sorted(get_ipmp_store().acoes)
    fail_on = acao_ids[0]

    import assessment.service as svc_mod

    real_evaluate = svc_mod.evaluate

    def flaky_evaluate(acao_id, process_number, chunks, **kwargs):
        if acao_id == fail_on:
            raise ValueError("boom")
        return real_evaluate(acao_id, process_number, chunks, **kwargs)

    svc = AssessmentService()
    with patch("assessment.service.extract_document", return_value=_make_chunks("EVTEA.pdf")):
        with patch.object(svc_mod, "evaluate", flaky_evaluate):
            svc.run_assessment("P001", [dummy_pdf])

    events = progress.get_events("P001")
    text = " ".join(e["message"] for e in events)
    assert f"Ação {fail_on} falhou" in text
    assert "seguindo para a próxima" in text
    # The run still reports completion, but flagged rather than clean.
    concluded = [e for e in events if e["stage"] == "concluido"]
    assert concluded and concluded[-1]["level"] == "warning"
    assert "com falha" in concluded[-1]["message"]
