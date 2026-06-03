from __future__ import annotations

import json
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse

from assessment._config import get_db_path
from assessment.api.schemas import ReviewSubmission
from assessment.interfaces.contracts import ReviewOutcome
from assessment.service import AssessmentService

router = APIRouter()
_service = AssessmentService()


# ── POST /cases/{process_number}/assess ──────────────────────────────────────

@router.post("/cases/{process_number}/assess", status_code=200)
async def assess(
    process_number: str,
    files: list[UploadFile],
    force: bool = Query(default=False),
):
    db_path = get_db_path()

    if not force:
        _check_no_review_outcomes(db_path, process_number)

    if force:
        _force_delete(db_path, process_number)

    with tempfile.TemporaryDirectory() as tmp_dir:
        document_paths: list[Path] = []
        for upload in files:
            dest = Path(tmp_dir) / (upload.filename or "document.pdf")
            dest.write_bytes(await upload.read())
            document_paths.append(dest)

        results = _service.run_assessment(process_number, document_paths)

    return {
        "process_number": process_number,
        "acao_ids_assessed": [r.acao_id for r in results],
        "count": len(results),
    }


def _check_no_review_outcomes(db_path: Path, process_number: str) -> None:
    con = sqlite3.connect(str(db_path))
    try:
        row = con.execute(
            "SELECT 1 FROM review_outcomes WHERE process_number = ? LIMIT 1",
            (process_number,),
        ).fetchone()
    finally:
        con.close()
    if row:
        raise HTTPException(
            status_code=409,
            detail=(
                f"A validated ReviewOutcome already exists for process '{process_number}'. "
                "Pass force=true to replace all evaluations and review outcomes."
            ),
        )


def _force_delete(db_path: Path, process_number: str) -> None:
    con = sqlite3.connect(str(db_path))
    try:
        con.execute(
            "DELETE FROM review_outcomes WHERE process_number = ?", (process_number,)
        )
        con.execute(
            "DELETE FROM evaluation_results WHERE process_number = ?", (process_number,)
        )
        con.commit()
    finally:
        con.close()


# ── GET /cases/{process_number}/evaluations ──────────────────────────────────

@router.get("/cases/{process_number}/evaluations")
def list_evaluations(process_number: str):
    db_path = get_db_path()
    con = sqlite3.connect(str(db_path))
    try:
        rows = con.execute(
            "SELECT raw_json FROM evaluation_results WHERE process_number = ?",
            (process_number,),
        ).fetchall()
    finally:
        con.close()

    return [json.loads(raw) for (raw,) in rows]


# ── GET /cases/{process_number}/evaluations/{acao_id} ────────────────────────

@router.get("/cases/{process_number}/evaluations/{acao_id}")
def get_evaluation(process_number: str, acao_id: int):
    db_path = get_db_path()
    con = sqlite3.connect(str(db_path))
    try:
        row = con.execute(
            "SELECT raw_json FROM evaluation_results "
            "WHERE process_number = ? AND acao_id = ?",
            (process_number, acao_id),
        ).fetchone()
    finally:
        con.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"No evaluation found for acao_id={acao_id}, process_number='{process_number}'.",
        )
    return json.loads(row[0])


# ── POST /cases/{process_number}/evaluations/{acao_id}/review ────────────────

@router.post("/cases/{process_number}/evaluations/{acao_id}/review", status_code=201)
def submit_review(process_number: str, acao_id: int, body: ReviewSubmission):
    db_path = get_db_path()

    _require_evaluation_exists(db_path, process_number, acao_id)
    _check_no_existing_review(db_path, process_number, acao_id)

    now = datetime.now(timezone.utc)
    outcome = ReviewOutcome(
        acao_id=acao_id,
        process_number=process_number,
        final_score=body.final_score,
        is_override=body.is_override,
        justification=body.justification,
        evidence_references=body.evidence_references,
        created_at=now,
    )
    _persist_review_outcome(db_path, outcome)
    return outcome.model_dump(mode="json")


def _require_evaluation_exists(db_path: Path, process_number: str, acao_id: int) -> None:
    con = sqlite3.connect(str(db_path))
    try:
        row = con.execute(
            "SELECT 1 FROM evaluation_results WHERE process_number = ? AND acao_id = ?",
            (process_number, acao_id),
        ).fetchone()
    finally:
        con.close()
    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"No evaluation found for acao_id={acao_id}, process_number='{process_number}'.",
        )


def _check_no_existing_review(db_path: Path, process_number: str, acao_id: int) -> None:
    con = sqlite3.connect(str(db_path))
    try:
        row = con.execute(
            "SELECT 1 FROM review_outcomes WHERE process_number = ? AND acao_id = ?",
            (process_number, acao_id),
        ).fetchone()
    finally:
        con.close()
    if row:
        raise HTTPException(
            status_code=409,
            detail=(
                f"A ReviewOutcome already exists for acao_id={acao_id}, "
                f"process_number='{process_number}'."
            ),
        )


def _persist_review_outcome(db_path: Path, outcome: ReviewOutcome) -> None:
    refs = json.dumps(outcome.evidence_references) if outcome.evidence_references is not None else None
    con = sqlite3.connect(str(db_path))
    try:
        con.execute(
            "INSERT INTO review_outcomes "
            "(acao_id, process_number, final_score, is_override, justification, "
            "evidence_references, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                outcome.acao_id,
                outcome.process_number,
                outcome.final_score,
                int(outcome.is_override),
                outcome.justification,
                refs,
                outcome.created_at.isoformat(),
            ),
        )
        con.commit()
    finally:
        con.close()


# ── GET /cases/{process_number}/evaluations/{acao_id}/review ─────────────────

@router.get("/cases/{process_number}/evaluations/{acao_id}/review")
def get_review(process_number: str, acao_id: int):
    db_path = get_db_path()
    con = sqlite3.connect(str(db_path))
    try:
        row = con.execute(
            "SELECT acao_id, process_number, final_score, is_override, justification, "
            "evidence_references, created_at "
            "FROM review_outcomes WHERE process_number = ? AND acao_id = ?",
            (process_number, acao_id),
        ).fetchone()
    finally:
        con.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"No review found for acao_id={acao_id}, process_number='{process_number}'.",
        )

    acao_id_db, pn, final_score, is_override, justification, refs_json, created_at = row
    refs = json.loads(refs_json) if refs_json is not None else None
    outcome = ReviewOutcome(
        acao_id=acao_id_db,
        process_number=pn,
        final_score=final_score,
        is_override=bool(is_override),
        justification=justification,
        evidence_references=refs,
        created_at=datetime.fromisoformat(created_at),
    )
    return outcome.model_dump(mode="json")
