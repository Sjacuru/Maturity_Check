import sqlite3
import tempfile
from pathlib import Path

import pytest

from assessment import configure, init_db
from assessment._config import _reset


@pytest.fixture(autouse=True)
def reset_config():
    yield
    _reset()


@pytest.fixture
def tmp_db(tmp_path):
    db = tmp_path / "test.db"
    configure(db)
    init_db(db)
    return db


# --- configure / get_db_path ---

def test_configure_sets_path(tmp_path):
    db = tmp_path / "app.db"
    configure(db)
    from assessment._config import get_db_path
    assert get_db_path() == db


def test_get_db_path_raises_before_configure():
    from assessment._config import get_db_path
    with pytest.raises(RuntimeError, match="not configured"):
        get_db_path()


# --- init_db creates Module 5 tables ---

def test_init_db_creates_evaluation_results(tmp_db):
    con = sqlite3.connect(str(tmp_db))
    row = con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='evaluation_results'"
    ).fetchone()
    con.close()
    assert row is not None


def test_init_db_creates_review_outcomes(tmp_db):
    con = sqlite3.connect(str(tmp_db))
    row = con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='review_outcomes'"
    ).fetchone()
    con.close()
    assert row is not None


def test_init_db_creates_document_fingerprints(tmp_db):
    con = sqlite3.connect(str(tmp_db))
    row = con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='document_fingerprints'"
    ).fetchone()
    con.close()
    assert row is not None


def test_init_db_is_idempotent(tmp_path):
    db = tmp_path / "app.db"
    configure(db)
    init_db(db)
    init_db(db)  # second call must not raise
    con = sqlite3.connect(str(db))
    tables = {r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    con.close()
    assert {"evaluation_results", "review_outcomes", "document_fingerprints"}.issubset(tables)


def test_init_db_does_not_create_retrieval_tables(tmp_db):
    con = sqlite3.connect(str(tmp_db))
    chunks = con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='chunks'"
    ).fetchone()
    fts = con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='chunks_fts'"
    ).fetchone()
    con.close()
    assert chunks is None
    assert fts is None


def test_evaluation_results_unique_constraint(tmp_db):
    con = sqlite3.connect(str(tmp_db))
    con.execute(
        "INSERT INTO evaluation_results "
        "(acao_id, process_number, proposed_score, uncertainty_flag, parse_failed, "
        "no_evidence_found, provider, model, created_at, raw_json) "
        "VALUES (1, 'P001', 3, 0, 0, 0, 'ollama', 'mistral', '2026-06-02', '{}')"
    )
    con.commit()
    with pytest.raises(sqlite3.IntegrityError):
        con.execute(
            "INSERT INTO evaluation_results "
            "(acao_id, process_number, proposed_score, uncertainty_flag, parse_failed, "
            "no_evidence_found, provider, model, created_at, raw_json) "
            "VALUES (1, 'P001', 1, 0, 0, 0, 'ollama', 'mistral', '2026-06-02', '{}')"
        )
    con.close()


def test_review_outcomes_unique_constraint(tmp_db):
    con = sqlite3.connect(str(tmp_db))
    con.execute(
        "INSERT INTO review_outcomes "
        "(acao_id, process_number, final_score, is_override, justification, "
        "evidence_references, created_at) "
        "VALUES (1, 'P001', 3, 0, NULL, NULL, '2026-06-02')"
    )
    con.commit()
    with pytest.raises(sqlite3.IntegrityError):
        con.execute(
            "INSERT INTO review_outcomes "
            "(acao_id, process_number, final_score, is_override, justification, "
            "evidence_references, created_at) "
            "VALUES (1, 'P001', 1, 0, NULL, NULL, '2026-06-02')"
        )
    con.close()


# --- não aplicável (ADR-0076) ---

_LEGACY_REVIEW_OUTCOMES = """
CREATE TABLE review_outcomes (
    id                  INTEGER PRIMARY KEY,
    acao_id             INTEGER NOT NULL,
    process_number      TEXT    NOT NULL,
    final_score         INTEGER NOT NULL,
    is_override         INTEGER NOT NULL,
    justification       TEXT,
    evidence_references TEXT,
    created_at          TEXT    NOT NULL,
    UNIQUE (acao_id, process_number)
);
"""


def test_init_db_migrates_a_review_outcomes_table_from_before_adr_0076(tmp_path):
    db = tmp_path / "old.db"
    con = sqlite3.connect(str(db))
    con.execute(_LEGACY_REVIEW_OUTCOMES)
    con.execute(
        "INSERT INTO review_outcomes (acao_id, process_number, final_score, is_override, "
        "justification, evidence_references, created_at) "
        "VALUES (3, 'P001', 1, 1, 'Nota.', '[2]', '2026-10-15T00:00:00+00:00')"
    )
    con.commit()
    con.close()

    configure(db)
    init_db(db)
    init_db(db)  # nothing left to migrate the second time

    con = sqlite3.connect(str(db))
    rows = con.execute(
        "SELECT acao_id, process_number, final_score, is_override, justification, "
        "evidence_references, created_at, not_applicable FROM review_outcomes"
    ).fetchall()
    con.execute(
        "INSERT INTO review_outcomes (acao_id, process_number, final_score, is_override, "
        "justification, evidence_references, created_at, not_applicable) "
        "VALUES (45, 'P001', NULL, 0, 'Motivo.', NULL, '2026-10-16T00:00:00+00:00', 1)"
    )
    con.commit()
    tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    con.close()
    assert rows == [(3, "P001", 1, 1, "Nota.", "[2]", "2026-10-15T00:00:00+00:00", 0)]
    assert "review_outcomes_new" not in tables


def test_review_outcomes_check_ties_the_score_to_not_applicable(tmp_db):
    """A score of 0, 1 or 3 exactly when the review is not "não aplicável".
    The NULL case needs the explicit IS NOT NULL: SQLite passes a CHECK that
    evaluates to NULL."""
    con = sqlite3.connect(str(tmp_db))
    insert = (
        "INSERT INTO review_outcomes (acao_id, process_number, final_score, is_override, "
        "justification, evidence_references, created_at, not_applicable) "
        "VALUES (?, 'P001', ?, 0, 'Motivo.', NULL, '2026-10-16', ?)"
    )
    for acao_id, score, na in ((45, None, 0), (46, 3, 1), (2, 2, 0)):
        with pytest.raises(sqlite3.IntegrityError):
            con.execute(insert, (acao_id, score, na))
    con.execute(insert, (45, None, 1))
    con.execute(insert, (1, 3, 0))
    con.commit()
    con.close()
