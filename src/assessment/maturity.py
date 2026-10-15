"""The maturity indicator of one case: its IPMP nota (ADR-0075).

The IPMP Guide defines the nota as the percentual de atendimento of the 46
Ações, between 0 and 1: the plain mean over every Ação, also read per
dimension. With the project's 0/1/3 points per Ação (CLAUDE.md, Strategic
Decision 4) that is points / (3 x Ações counted).

Computed on read from the stored evaluations and reviews and never stored, so
it always reflects the latest review. Nothing here runs during an assessment:
ADR-0030 kept aggregation out of orchestration, and this module only reads.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import NamedTuple

from ingestion import get_ipmp_store

from assessment._config import get_db_path
from assessment.interfaces.contracts import AcaoPoints, MaturityGroup, MaturityIndicator

# The Guide's two reference limits (Appendix 6, question 7): below 0.2 is a
# technical alert, above 0.8 is satisfactory. The band between them needs a
# representative sample the Guide does not have yet, so it carries no reading.
ALERT_BELOW = 0.2
SATISFACTORY_ABOVE = 0.8

# The order in which the Guide lists the five dimensions of the M5D.
_DIMENSION_ORDER = ("Estratégica", "Econômica", "Comercial", "Financeira", "Gerencial")


class NoEvaluations(LookupError):
    """The case has no stored evaluation, so there is no indicator to compute."""


class _StoredEvaluation(NamedTuple):
    proposed_score: int | None
    parse_failed: bool
    no_evidence_found: bool
    score_margin: dict | None


def band_for(nota: float | None) -> str | None:
    """The Guide's reading of a nota: "alert", "intermediate" or "satisfactory"."""
    if nota is None:
        return None
    if nota < ALERT_BELOW:
        return "alert"
    if nota > SATISFACTORY_ABOVE:
        return "satisfactory"
    return "intermediate"


def compute_maturity(process_number: str, db_path: Path | None = None) -> MaturityIndicator:
    db = Path(db_path) if db_path is not None else get_db_path()
    evaluations, reviews = _read_case(db, process_number)
    if not evaluations:
        raise NoEvaluations(process_number)

    acoes = [
        _acao_points(acao, evaluations.get(acao.acao_id), reviews.get(acao.acao_id))
        for acao in sorted(get_ipmp_store().acoes.values(), key=lambda a: a.acao_id)
    ]

    by_dimension = [
        _group(dim, [a for a in acoes if a.dimensao == dim])
        for dim in _DIMENSION_ORDER
        if any(a.dimensao == dim for a in acoes)
    ]
    # Phases in the order the Ações run; the label is the stored one.
    phases: list[str] = []
    for a in acoes:
        if a.fase not in phases:
            phases.append(a.fase)
    by_phase = [_group(f, [a for a in acoes if a.fase == f]) for f in phases]

    overall = _group("Geral", acoes)
    return MaturityIndicator(
        process_number=process_number,
        overall=overall,
        band=band_for(overall.nota),
        alert_below=ALERT_BELOW,
        satisfactory_above=SATISFACTORY_ABOVE,
        by_dimension=by_dimension,
        by_phase=by_phase,
        transition_points=_group("Pontos de transição", [a for a in acoes if a.ponto_transicao]),
        n_reviewed=sum(a.source == "review" for a in acoes),
        acoes=acoes,
    )


def _read_case(
    db: Path, process_number: str
) -> tuple[dict[int, _StoredEvaluation], dict[int, int]]:
    con = sqlite3.connect(str(db))
    try:
        eval_rows = con.execute(
            "SELECT acao_id, proposed_score, parse_failed, no_evidence_found, raw_json "
            "FROM evaluation_results WHERE process_number = ?",
            (process_number,),
        ).fetchall()
        review_rows = con.execute(
            "SELECT acao_id, final_score FROM review_outcomes WHERE process_number = ?",
            (process_number,),
        ).fetchall()
    finally:
        con.close()

    evaluations = {
        acao_id: _StoredEvaluation(
            proposed_score=score,
            parse_failed=bool(parse_failed),
            no_evidence_found=bool(no_evidence),
            # Rows persisted before 2026-10-05 carry no margin (ADR-0068).
            score_margin=json.loads(raw).get("score_margin"),
        )
        for acao_id, score, parse_failed, no_evidence, raw in eval_rows
    }
    reviews = {acao_id: final_score for acao_id, final_score in review_rows}
    return evaluations, reviews


def _acao_points(acao, stored: _StoredEvaluation | None, review_score: int | None) -> AcaoPoints:
    base = {
        "acao_id": acao.acao_id,
        "titulo": acao.titulo,
        "dimensao": acao.dimensao,
        "fase": acao.fase,
        "ponto_transicao": acao.ponto_transicao,
    }
    # The auditor's final score settles the Ação (ADR-0023).
    if review_score is not None:
        return AcaoPoints(**base, points=review_score, source="review", floor_points=review_score)
    if stored is None:
        return AcaoPoints(**base, points=None, source="not_evaluated", floor_points=None)
    # Missing evidence stays "não atendida" (Guide 4.1): 0 points, not a gap.
    if stored.no_evidence_found:
        return AcaoPoints(**base, points=0, source="no_evidence", floor_points=0)
    # A parse failure has no score until the auditor assigns one.
    if stored.proposed_score is None:
        return AcaoPoints(**base, points=None, source="unscored", floor_points=None)

    points = stored.proposed_score  # already after the dependency cap (ADR-0070)
    margin = stored.score_margin or {}
    recommended = bool(margin.get("review_recommended"))
    floor = points
    if recommended:
        # ADR-0068: the score if every fragile product fell at once; None means
        # nothing accepted would remain, i.e. sem evidência, which counts 0.
        score_floor = margin.get("score_floor")
        floor = 0 if score_floor is None else min(points, int(score_floor))
    return AcaoPoints(
        **base,
        points=points,
        source="proposed",
        review_recommended=recommended,
        floor_points=floor,
    )


def _group(label: str, members: list[AcaoPoints]) -> MaturityGroup:
    counted = [a for a in members if a.points is not None]
    points = sum(a.points for a in counted)
    floor = sum(a.floor_points for a in counted)
    max_points = 3 * len(counted)
    return MaturityGroup(
        label=label,
        acao_ids=[a.acao_id for a in members],
        n_counted=len(counted),
        points=points,
        max_points=max_points,
        nota=points / max_points if max_points else None,
        floor_points=floor,
        nota_floor=floor / max_points if max_points else None,
        complete=len(counted) == len(members),
    )
