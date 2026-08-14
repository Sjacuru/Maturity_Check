"""Tests for assessment.progress (ADR-0055)."""

from __future__ import annotations

from assessment import progress


def test_emit_then_get_events_returns_in_order():
    progress.start_run("P1")
    progress.emit("P1", "verificando_arquivos", "Verificando...", "info")
    progress.emit("P1", "documentos_disponiveis", "Prontos.", "success")

    events = progress.get_events("P1")

    assert [e["stage"] for e in events] == ["verificando_arquivos", "documentos_disponiveis"]
    assert [e["message"] for e in events] == ["Verificando...", "Prontos."]
    assert [e["level"] for e in events] == ["info", "success"]


def test_emit_default_level_is_info():
    progress.start_run("P1")
    progress.emit("P1", "stage", "message")

    events = progress.get_events("P1")

    assert events[0]["level"] == "info"


def test_get_events_since_filters_older_events():
    progress.start_run("P1")
    progress.emit("P1", "a", "first")
    progress.emit("P1", "b", "second")
    progress.emit("P1", "c", "third")

    events = progress.get_events("P1", since=1)

    assert [e["message"] for e in events] == ["second", "third"]


def test_seq_is_monotonic_and_unique():
    progress.start_run("P1")
    for i in range(5):
        progress.emit("P1", "stage", f"msg{i}")

    events = progress.get_events("P1")

    assert [e["seq"] for e in events] == [0, 1, 2, 3, 4]


def test_start_run_clears_prior_events():
    progress.start_run("P1")
    progress.emit("P1", "stage", "stale from a previous run")

    progress.start_run("P1")

    assert progress.get_events("P1") == []


def test_unknown_process_number_returns_empty_list():
    assert progress.get_events("never-started") == []


def test_events_are_isolated_per_process_number():
    progress.start_run("A")
    progress.start_run("B")
    progress.emit("A", "stage", "for A")
    progress.emit("B", "stage", "for B")

    assert [e["message"] for e in progress.get_events("A")] == ["for A"]
    assert [e["message"] for e in progress.get_events("B")] == ["for B"]


def test_emit_without_start_run_still_works():
    """emit() must not require start_run() first — a caller that only ever
    emits (never explicitly starting a fresh log) still gets a working log."""
    progress.emit("never-started-explicitly", "stage", "message")

    events = progress.get_events("never-started-explicitly")

    assert len(events) == 1


def test_log_is_trimmed_beyond_max_events():
    progress.start_run("P1")
    for i in range(progress._MAX_EVENTS + 20):
        progress.emit("P1", "stage", f"msg{i}")

    events = progress.get_events("P1")

    assert len(events) == progress._MAX_EVENTS
    # Oldest events are dropped, seq numbers stay monotonic (not reused).
    assert events[0]["seq"] == 20
    assert events[-1]["seq"] == progress._MAX_EVENTS + 19


def test_make_reporter_binds_process_number():
    progress.start_run("P1")
    reporter = progress.make_reporter("P1")

    reporter("stage", "message", "warning")

    events = progress.get_events("P1")
    assert len(events) == 1
    assert events[0]["level"] == "warning"
