"""Tests for evaluation.progress (ADR-0055)."""

from __future__ import annotations

import pytest

from evaluation import progress


@pytest.fixture(autouse=True)
def _reset_reporter():
    progress.set_reporter(None)
    yield
    progress.set_reporter(None)


def test_report_is_noop_without_reporter():
    # Must not raise even though no reporter is registered.
    progress.report("stage", "message")


def test_report_calls_registered_reporter():
    calls = []
    progress.set_reporter(lambda stage, message, level: calls.append((stage, message, level)))

    progress.report("chamando_llm", "Chamando...", "waiting")

    assert calls == [("chamando_llm", "Chamando...", "waiting")]


def test_report_defaults_level_to_info():
    calls = []
    progress.set_reporter(lambda stage, message, level: calls.append(level))

    progress.report("stage", "message")

    assert calls == ["info"]


def test_report_swallows_reporter_exceptions():
    def _boom(stage, message, level):
        raise RuntimeError("reporter is broken")

    progress.set_reporter(_boom)

    # Must not propagate — a broken progress reporter must never interrupt
    # the actual assessment.
    progress.report("stage", "message")


def test_set_reporter_none_disables_reporting():
    calls = []
    progress.set_reporter(lambda stage, message, level: calls.append(1))
    progress.set_reporter(None)

    progress.report("stage", "message")

    assert calls == []
