"""Tests for evaluation.llm.fallback.FallbackLLMClient (ADR-0054)."""

from __future__ import annotations

import pytest

from evaluation.llm.fallback import FallbackLLMClient
from evaluation.llm.llamacpp import LlamaCppBusy, LlamaCppTimeout, LlamaCppUnavailable


class _StubClient:
    def __init__(self, model_label: str = "model"):
        self.calls = 0
        self.model_label = model_label
        self.last_model_used: str | None = None

    def complete(self, system: str, user: str, schema: dict | None = None) -> str:
        self.calls += 1
        self.last_model_used = self.model_label
        return f"response-from-{self.model_label}"


class _FailingStubClient(_StubClient):
    def __init__(self, exc: BaseException, model_label: str = "model"):
        super().__init__(model_label)
        self._exc = exc

    def complete(self, system: str, user: str, schema: dict | None = None) -> str:
        self.calls += 1
        raise self._exc


def _wrap(primary, fallback, cooldown: float = 10.0) -> FallbackLLMClient:
    return FallbackLLMClient(
        primary,
        fallback,
        primary_provider_label="primary",
        fallback_provider_label="fallback",
        cooldown_seconds=cooldown,
    )


def test_primary_success_used_directly():
    primary = _StubClient("primary-model")
    fallback = _StubClient("fallback-model")
    client = _wrap(primary, fallback)

    result = client.complete("sys", "usr")

    assert result == "response-from-primary-model"
    assert primary.calls == 1
    assert fallback.calls == 0
    assert client.last_provider_used == "primary"
    assert client.last_model_used == "primary-model"


@pytest.mark.parametrize(
    "exc",
    [
        LlamaCppUnavailable("refused"),
        LlamaCppTimeout("timed out"),
        LlamaCppBusy("HTTP 429"),
    ],
)
def test_primary_failure_falls_back(exc):
    primary = _FailingStubClient(exc, "primary-model")
    fallback = _StubClient("fallback-model")
    client = _wrap(primary, fallback)

    result = client.complete("sys", "usr")

    assert result == "response-from-fallback-model"
    assert primary.calls == 1
    assert fallback.calls == 1
    assert client.last_provider_used == "fallback"
    assert client.last_model_used == "fallback-model"


def test_unrelated_exception_is_not_caught():
    """A genuine application bug (not an availability signal) must not be
    silently masked as a fallback trigger."""
    primary = _FailingStubClient(ValueError("real bug"), "primary-model")
    fallback = _StubClient("fallback-model")
    client = _wrap(primary, fallback)

    with pytest.raises(ValueError, match="real bug"):
        client.complete("sys", "usr")
    assert fallback.calls == 0


def test_cooldown_skips_primary_on_subsequent_calls(monkeypatch):
    now = {"t": 1000.0}
    monkeypatch.setattr("evaluation.llm.fallback.time.monotonic", lambda: now["t"])

    primary = _FailingStubClient(LlamaCppUnavailable("refused"), "primary-model")
    fallback = _StubClient("fallback-model")
    client = _wrap(primary, fallback, cooldown=10.0)

    client.complete("sys", "usr")  # fails -> falls back, starts a 10s cooldown
    assert primary.calls == 1
    assert fallback.calls == 1

    now["t"] += 5.0  # still inside the cooldown window
    client.complete("sys", "usr")
    assert primary.calls == 1  # not retried — went straight to fallback
    assert fallback.calls == 2


def test_primary_retried_after_cooldown_elapses(monkeypatch):
    now = {"t": 1000.0}
    monkeypatch.setattr("evaluation.llm.fallback.time.monotonic", lambda: now["t"])

    primary = _StubClient("primary-model")
    attempts = {"n": 0}

    def flaky_complete(system, user, schema=None):
        attempts["n"] += 1
        primary.calls += 1
        if attempts["n"] == 1:
            raise LlamaCppUnavailable("refused")
        primary.last_model_used = primary.model_label
        return "recovered"

    primary.complete = flaky_complete
    fallback = _StubClient("fallback-model")
    client = _wrap(primary, fallback, cooldown=10.0)

    client.complete("sys", "usr")  # fails, falls back, starts cooldown
    assert primary.calls == 1
    assert fallback.calls == 1

    now["t"] += 10.1  # cooldown elapsed
    result = client.complete("sys", "usr")

    assert primary.calls == 2  # primary probed again
    assert result == "recovered"
    assert client.last_provider_used == "primary"
    assert client.last_model_used == "primary-model"


def test_describe_route_before_any_call_names_primary_and_fallback():
    primary = _StubClient("primary-model")
    fallback = _StubClient("fallback-model")
    client = _wrap(primary, fallback)

    description = client.describe_route()

    assert "primary/primary-model" in description
    assert "fallback/fallback-model" in description
    assert "principal" in description


def test_describe_route_during_cooldown_names_fallback_with_remaining_time(monkeypatch):
    now = {"t": 1000.0}
    monkeypatch.setattr("evaluation.llm.fallback.time.monotonic", lambda: now["t"])

    primary = _FailingStubClient(LlamaCppTimeout("timed out"), "primary-model")
    fallback = _StubClient("fallback-model")
    client = _wrap(primary, fallback, cooldown=10.0)

    client.complete("sys", "usr")  # fails -> starts cooldown
    now["t"] += 3.0  # still inside the cooldown window

    description = client.describe_route()

    assert "fallback/fallback-model" in description
    assert "primary/primary-model" in description
    assert "7s" in description  # 10s cooldown - 3s elapsed


def test_describe_route_after_cooldown_elapses_reverts_to_primary(monkeypatch):
    now = {"t": 1000.0}
    monkeypatch.setattr("evaluation.llm.fallback.time.monotonic", lambda: now["t"])

    primary = _FailingStubClient(LlamaCppUnavailable("refused"), "primary-model")
    fallback = _StubClient("fallback-model")
    client = _wrap(primary, fallback, cooldown=10.0)

    client.complete("sys", "usr")  # fails -> starts cooldown
    now["t"] += 10.1  # cooldown elapsed

    description = client.describe_route()

    assert "principal" in description
    assert description.startswith("primary/primary-model")


def test_schema_forwarded_to_underlying_client():
    captured = {}

    class _CapturingClient(_StubClient):
        def complete(self, system, user, schema=None):
            captured["schema"] = schema
            return super().complete(system, user, schema)

    primary = _CapturingClient("primary-model")
    fallback = _StubClient("fallback-model")
    client = _wrap(primary, fallback)

    schema = {"type": "object"}
    client.complete("sys", "usr", schema=schema)
    assert captured["schema"] == schema
