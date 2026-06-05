"""Integration tests for AssessmentService (Issue #22).

All tests use:
- A temporary SQLite database (shared between retrieval and assessment)
- A StubLLMClient injected directly into evaluation._config
- A patched extract_document to avoid requiring real PDFs
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
from extraction import Chunk
from retrieval import configure as retrieval_configure
from retrieval._config import _reset as retrieval_reset
from retrieval.schema.ddl import init_db as retrieval_init_db


# ── helpers ──────────────────────────────────────────────────────────────────

class StubLLMClient:
    def __init__(self, response: str = "ok\nSCORE: 3\nUNCERTAINTY: no") -> None:
        self._response = response
        self.call_count = 0

    def complete(self, system: str, user: str) -> str:
        self.call_count += 1
        return self._response


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


def _chunk_count(db_path: Path, process_number: str | None = None) -> int:
    con = sqlite3.connect(str(db_path))
    try:
        if process_number:
            return con.execute(
                "SELECT COUNT(*) FROM chunks WHERE process_number = ?", (process_number,)
            ).fetchone()[0]
        return con.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    finally:
        con.close()


def _fingerprint_count(db_path: Path, process_number: str | None = None) -> int:
    con = sqlite3.connect(str(db_path))
    try:
        if process_number:
            return con.execute(
                "SELECT COUNT(*) FROM document_fingerprints WHERE process_number = ?",
                (process_number,),
            ).fetchone()[0]
        return con.execute("SELECT COUNT(*) FROM document_fingerprints").fetchone()[0]
    finally:
        con.close()


def _eval_result_count(db_path: Path, process_number: str | None = None) -> int:
    con = sqlite3.connect(str(db_path))
    try:
        if process_number:
            return con.execute(
                "SELECT COUNT(*) FROM evaluation_results WHERE process_number = ?",
                (process_number,),
            ).fetchone()[0]
        return con.execute("SELECT COUNT(*) FROM evaluation_results").fetchone()[0]
    finally:
        con.close()


# ── fixtures ─────────────────────────────────────────────────────────────────

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
    eval_cfg._provider = "ollama"
    eval_cfg._model = "mistral"
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



# ── guard conditions ──────────────────────────────────────────────────────────

def test_raises_before_configure_llm(db_path, dummy_pdf):
    eval_cfg._client = None
    eval_cfg._provider = None
    eval_cfg._model = None
    svc = AssessmentService()
    with pytest.raises(RuntimeError, match="configure_llm"):
        with patch("assessment.service.extract_document", return_value=_make_chunks("EVTEA.pdf")):
            svc.run_assessment("P001", [dummy_pdf])


def test_raises_when_no_files_and_no_prior_index(db_path):
    svc = AssessmentService()
    with pytest.raises(RuntimeError, match="No document_paths"):
        svc.run_assessment("P001", [])


# ── first run ─────────────────────────────────────────────────────────────────

def test_first_run_indexes_chunks_and_stores_fingerprint(db_path, dummy_pdf):
    svc = AssessmentService()
    chunks = _make_chunks("EVTEA.pdf")
    with patch("assessment.service.extract_document", return_value=chunks):
        svc.run_assessment("P001", [dummy_pdf])

    assert _chunk_count(db_path, "P001") == len(chunks)
    assert _fingerprint_count(db_path, "P001") == 1


def test_first_run_persists_evaluation_results(db_path, dummy_pdf):
    svc = AssessmentService()
    with patch("assessment.service.extract_document", return_value=_make_chunks("EVTEA.pdf")):
        results, _ = svc.run_assessment("P001", [dummy_pdf])

    assert len(results) >= 1
    assert _eval_result_count(db_path, "P001") == len(results)


def test_first_run_returns_evaluation_result_objects(db_path, dummy_pdf):
    from evaluation import EvaluationResult
    svc = AssessmentService()
    with patch("assessment.service.extract_document", return_value=_make_chunks("EVTEA.pdf")):
        results, _ = svc.run_assessment("P001", [dummy_pdf])

    assert all(isinstance(r, EvaluationResult) for r in results)
    assert all(r.process_number == "P001" for r in results)


def test_raw_json_stored_in_evaluation_results(db_path, dummy_pdf):
    import json
    svc = AssessmentService()
    with patch("assessment.service.extract_document", return_value=_make_chunks("EVTEA.pdf")):
        results, _ = svc.run_assessment("P001", [dummy_pdf])

    con = sqlite3.connect(str(db_path))
    rows = con.execute(
        "SELECT raw_json FROM evaluation_results WHERE process_number = ?", ("P001",)
    ).fetchall()
    con.close()

    assert len(rows) == len(results)
    for (raw,) in rows:
        parsed = json.loads(raw)
        assert "acao_id" in parsed
        assert "process_number" in parsed


# ── fingerprint reuse ─────────────────────────────────────────────────────────

def test_same_file_skips_extraction_on_rerun(db_path, dummy_pdf):
    svc = AssessmentService()
    chunks = _make_chunks("EVTEA.pdf")
    extract_mock = patch("assessment.service.extract_document", return_value=chunks)

    with extract_mock as m:
        svc.run_assessment("P001", [dummy_pdf])
        first_call_count = m.call_count

    with extract_mock as m:
        svc.run_assessment("P001", [dummy_pdf])
        second_call_count = m.call_count

    assert first_call_count == 1
    assert second_call_count == 0  # fingerprint matched — extraction skipped


def test_same_file_chunk_count_unchanged_on_rerun(db_path, dummy_pdf):
    svc = AssessmentService()
    chunks = _make_chunks("EVTEA.pdf")
    with patch("assessment.service.extract_document", return_value=chunks):
        svc.run_assessment("P001", [dummy_pdf])
        count_after_first = _chunk_count(db_path, "P001")
        svc.run_assessment("P001", [dummy_pdf])
        count_after_second = _chunk_count(db_path, "P001")

    assert count_after_first == count_after_second


def test_no_files_with_prior_index_succeeds(db_path, dummy_pdf):
    svc = AssessmentService()
    with patch("assessment.service.extract_document", return_value=_make_chunks("EVTEA.pdf")):
        svc.run_assessment("P001", [dummy_pdf])

    # second call with no files — uses existing chunks
    with patch("assessment.service.extract_document") as m:
        results, _ = svc.run_assessment("P001", [])
        assert m.call_count == 0  # no extraction called
    assert len(results) >= 1


# ── fingerprint replacement ───────────────────────────────────────────────────

def test_changed_file_triggers_chunk_replacement(db_path, tmp_path):
    svc = AssessmentService()
    pdf = tmp_path / "EVTEA.pdf"

    # First run — v1 content
    pdf.write_bytes(b"fake pdf content v1")
    chunks_v1 = _make_chunks("EVTEA.pdf", n=3)
    with patch("assessment.service.extract_document", return_value=chunks_v1):
        svc.run_assessment("P001", [pdf])
    count_v1 = _chunk_count(db_path, "P001")

    # Second run — different content at same filename → fingerprint mismatch
    pdf.write_bytes(b"fake pdf content v2 - completely different")
    chunks_v2 = _make_chunks("EVTEA.pdf", n=1)
    with patch("assessment.service.extract_document", return_value=chunks_v2):
        svc.run_assessment("P001", [pdf])
    count_v2 = _chunk_count(db_path, "P001")

    assert count_v1 == 3
    assert count_v2 == 1  # stale chunks deleted; only v2 chunks remain


def test_changed_file_updates_fingerprint(db_path, dummy_pdf, tmp_path):
    svc = AssessmentService()

    with patch("assessment.service.extract_document", return_value=_make_chunks("EVTEA.pdf")):
        svc.run_assessment("P001", [dummy_pdf])

    con = sqlite3.connect(str(db_path))
    sha_v1 = con.execute(
        "SELECT sha256 FROM document_fingerprints WHERE process_number='P001' AND filename='EVTEA.pdf'"
    ).fetchone()[0]
    con.close()

    # overwrite file with new content
    dummy_pdf.write_bytes(b"entirely different content for v2")

    with patch("assessment.service.extract_document", return_value=_make_chunks("EVTEA.pdf")):
        svc.run_assessment("P001", [dummy_pdf])

    con = sqlite3.connect(str(db_path))
    sha_v2 = con.execute(
        "SELECT sha256 FROM document_fingerprints WHERE process_number='P001' AND filename='EVTEA.pdf'"
    ).fetchone()[0]
    con.close()

    assert sha_v1 != sha_v2


def test_per_file_replacement_preserves_other_files(db_path, tmp_path):
    """Replacing one file must not disturb chunks from other files in the same Case."""
    svc = AssessmentService()
    file_a = tmp_path / "DocA.pdf"
    file_a.write_bytes(b"file a content")
    file_b = tmp_path / "DocB.pdf"
    file_b.write_bytes(b"file b content")

    chunks_a = _make_chunks("DocA.pdf", n=2)
    chunks_b = _make_chunks("DocB.pdf", n=3)

    def side_effect(path: Path):
        return _make_chunks(path.name, n=2 if path.name == "DocA.pdf" else 3)

    with patch("assessment.service.extract_document", side_effect=side_effect):
        svc.run_assessment("P001", [file_a, file_b])

    count_after_first = _chunk_count(db_path, "P001")
    assert count_after_first == 5  # 2 + 3

    # replace file_a with new content
    file_a.write_bytes(b"file a new content v2")
    chunks_a_v2 = _make_chunks("DocA.pdf", n=1)

    def side_effect_v2(path: Path):
        return chunks_a_v2 if path.name == "DocA.pdf" else chunks_b

    with patch("assessment.service.extract_document", side_effect=side_effect_v2):
        svc.run_assessment("P001", [file_a, file_b])

    # DocB fingerprint still matches — not re-extracted; DocA replaced with 1 chunk
    # Total: 1 (DocA new) + 3 (DocB unchanged) = 4
    count_after_second = _chunk_count(db_path, "P001")
    assert count_after_second == 4
