"""The maturity indicator (ADR-0075): the IPMP nota of one case, read from the
stored evaluations and reviews.

Rows are written straight into a scratch database, so every case here is exact;
the IPMP store is the real one (46 Ações, data/ipmp).
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import ingestion.ipmp as _ipmp
from assessment import configure as assessment_configure, init_db as assessment_init_db
from assessment._config import _reset as assessment_reset
from assessment.api.app import create_app
from assessment.maturity import NoEvaluations, band_for, compute_maturity

PROC = "P-MAT"


@pytest.fixture
def db(tmp_path, monkeypatch) -> Path:
    monkeypatch.setattr(_ipmp, "_store", None)  # fresh load of the 46 Ações
    path = tmp_path / "app.db"
    assessment_configure(path)
    assessment_init_db(path)
    yield path
    assessment_reset()


def _evaluation(db: Path, acao_id: int, score: int | None = None, *, no_evidence: bool = False,
                parse_failed: bool = False, margin: dict | None = None) -> None:
    raw = {"acao_id": acao_id, "proposed_score": score}
    if margin is not None:
        raw["score_margin"] = margin
    con = sqlite3.connect(str(db))
    con.execute(
        "INSERT INTO evaluation_results (acao_id, process_number, proposed_score, "
        "uncertainty_flag, parse_failed, no_evidence_found, provider, model, created_at, raw_json) "
        "VALUES (?, ?, ?, 0, ?, ?, 'stub', 'stub', '2026-10-15T00:00:00+00:00', ?)",
        (acao_id, PROC, score, int(parse_failed), int(no_evidence), json.dumps(raw)),
    )
    con.commit()
    con.close()


def _review(db: Path, acao_id: int, final_score: int) -> None:
    con = sqlite3.connect(str(db))
    con.execute(
        "INSERT INTO review_outcomes (acao_id, process_number, final_score, is_override, "
        "justification, evidence_references, created_at) "
        "VALUES (?, ?, ?, 1, 'Teste.', NULL, '2026-10-15T00:00:00+00:00')",
        (acao_id, PROC, final_score),
    )
    con.commit()
    con.close()


def _acao(ind, acao_id):
    return next(a for a in ind.acoes if a.acao_id == acao_id)


def test_full_case_nota_is_points_over_138(db):
    scores = {n: (3 if n % 3 == 0 else 1 if n % 3 == 1 else 0) for n in range(1, 47)}
    for n, s in scores.items():
        _evaluation(db, n, s)
    ind = compute_maturity(PROC, db)
    assert ind.overall.points == sum(scores.values())
    assert ind.overall.max_points == 138
    assert ind.overall.nota == pytest.approx(sum(scores.values()) / 138)
    assert ind.overall.complete
    assert ind.n_reviewed == 0
    assert {a.source for a in ind.acoes} == {"proposed"}


def test_no_evidence_counts_zero_and_unscored_is_left_out(db):
    _evaluation(db, 1, no_evidence=True)
    _evaluation(db, 2, parse_failed=True)
    for n in range(3, 47):
        _evaluation(db, n, 3)
    ind = compute_maturity(PROC, db)
    assert (_acao(ind, 1).points, _acao(ind, 1).source) == (0, "no_evidence")
    assert (_acao(ind, 2).points, _acao(ind, 2).source) == (None, "unscored")
    assert ind.overall.n_counted == 45
    assert ind.overall.max_points == 135
    assert ind.overall.points == 44 * 3
    assert not ind.overall.complete


def test_acoes_without_an_evaluation_are_not_counted(db):
    _evaluation(db, 1, 3)
    _evaluation(db, 7, 1)
    ind = compute_maturity(PROC, db)
    assert ind.overall.n_counted == 2
    assert ind.overall.nota == pytest.approx(4 / 6)
    assert _acao(ind, 2).source == "not_evaluated"
    assert len(ind.acoes) == 46


def test_review_replaces_the_proposed_score(db):
    _evaluation(db, 3, 3, margin={"review_recommended": True, "score_floor": None})
    _evaluation(db, 4, no_evidence=True)
    _review(db, 3, 1)
    _review(db, 4, 3)  # the auditor's own assignment on a sem-evidência Ação (ADR-0023)
    ind = compute_maturity(PROC, db)
    a3, a4 = _acao(ind, 3), _acao(ind, 4)
    assert (a3.points, a3.source, a3.floor_points, a3.review_recommended) == (1, "review", 1, False)
    assert (a4.points, a4.source) == (3, "review")
    assert ind.n_reviewed == 2


def test_floor_follows_the_open_review_signal(db):
    _evaluation(db, 5, 3, margin={"review_recommended": True, "score_floor": 1})
    _evaluation(db, 6, 1, margin={"review_recommended": True, "score_floor": None})
    _evaluation(db, 7, 3, margin={"review_recommended": False, "score_floor": 1})
    _evaluation(db, 8, 1)  # a row persisted before ADR-0068 carries no margin
    ind = compute_maturity(PROC, db)
    assert [(_acao(ind, n).floor_points, _acao(ind, n).review_recommended) for n in (5, 6, 7, 8)] == [
        (1, True),
        (0, True),  # floor None = sem evidência = 0
        (3, False),  # no open review: the floor is the score
        (1, False),
    ]
    assert ind.overall.points == 8
    assert ind.overall.floor_points == 5
    assert ind.overall.nota_floor == pytest.approx(5 / 12)


def test_dimension_phase_and_transition_groups(db):
    for n in range(1, 47):
        _evaluation(db, n, 3)
    ind = compute_maturity(PROC, db)
    assert [(g.label, len(g.acao_ids)) for g in ind.by_dimension] == [
        ("Estratégica", 6),
        ("Econômica", 9),
        ("Comercial", 11),
        ("Financeira", 5),
        ("Gerencial", 15),
    ]
    assert [g.acao_ids for g in ind.by_phase] == [
        list(range(1, 21)),
        list(range(21, 38)),
        list(range(38, 47)),
    ]
    assert ind.transition_points.acao_ids == [16, 37, 38, 45, 46]
    assert all(g.nota == 1.0 for g in ind.by_dimension + ind.by_phase)
    assert ind.band == "satisfactory"


def test_band_follows_the_guides_two_limits():
    assert band_for(None) is None
    assert band_for(0.19) == "alert"
    assert band_for(0.2) == "intermediate"
    assert band_for(0.8) == "intermediate"
    assert band_for(0.81) == "satisfactory"


def test_no_evaluations_raises(db):
    with pytest.raises(NoEvaluations):
        compute_maturity(PROC, db)


def test_maturity_route(db):
    _evaluation(db, 1, 3)
    _evaluation(db, 2, no_evidence=True)
    client = TestClient(create_app())
    resp = client.get(f"/api/cases/{PROC}/maturity")
    assert resp.status_code == 200
    body = resp.json()
    assert body["overall"]["points"] == 3
    assert body["overall"]["n_counted"] == 2
    assert body["band"] == "intermediate"
    assert [g["label"] for g in body["by_dimension"]][0] == "Estratégica"
    assert client.get("/api/cases/OUTRO/maturity").status_code == 404
