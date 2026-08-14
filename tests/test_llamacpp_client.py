"""Tests for evaluation.llm.llamacpp.LlamaCppClient (ADR-0054)."""

from __future__ import annotations

import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest

from evaluation.llm.llamacpp import (
    LlamaCppBusy,
    LlamaCppClient,
    LlamaCppTimeout,
    LlamaCppUnavailable,
)


def _ok_response(request: httpx.Request, content: str = "hello", model: str = "test-model") -> httpx.Response:
    return httpx.Response(200, json={"model": model, "choices": [{"message": {"content": content}}]})


def _client(handler, **kwargs) -> LlamaCppClient:
    transport = httpx.MockTransport(handler)
    defaults = dict(base_url="http://test-server:8080", model="test-model", transport=transport)
    return LlamaCppClient(**{**defaults, **kwargs})


# --- Successful completion ---

def test_successful_completion_returns_content():
    client = _client(lambda req: _ok_response(req, content="hello"))
    result = client.complete("sys", "usr")
    assert result == "hello"
    assert client.last_model_used == "test-model"


def test_schema_included_as_response_format():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return _ok_response(request, content="{}")

    schema = {"type": "object", "properties": {}}
    _client(handler).complete("sys", "usr", schema=schema)
    assert captured["body"]["response_format"] == {
        "type": "json_schema",
        "json_schema": {"name": "response", "schema": schema, "strict": True},
    }


def test_no_schema_omits_response_format():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return _ok_response(request)

    _client(handler).complete("sys", "usr")
    assert "response_format" not in captured["body"]


# --- max_tokens guardrail (2026-08-14 — see LlamaCppClient docstring) ---

def test_max_tokens_included_when_set():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return _ok_response(request)

    _client(handler, max_tokens=768).complete("sys", "usr")
    assert captured["body"]["max_tokens"] == 768


def test_max_tokens_omitted_by_default():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return _ok_response(request)

    _client(handler).complete("sys", "usr")
    assert "max_tokens" not in captured["body"]


def test_messages_carry_system_and_user():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return _ok_response(request)

    _client(handler).complete("system text", "user text")
    assert captured["body"]["messages"] == [
        {"role": "system", "content": "system text"},
        {"role": "user", "content": "user text"},
    ]
    assert captured["body"]["temperature"] == 0


# --- Connection refused / DNS — no retry ---

def test_connect_error_raises_unavailable_without_retry():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        raise httpx.ConnectError("refused", request=request)

    with pytest.raises(LlamaCppUnavailable):
        _client(handler, max_timeout_retries=5).complete("sys", "usr")
    assert calls["n"] == 1


# --- Timeout — retried up to max_timeout_retries ---

def test_timeout_retries_then_raises(monkeypatch):
    calls = {"n": 0}
    sleeps: list[float] = []
    monkeypatch.setattr("evaluation.llm.llamacpp.time.sleep", lambda s: sleeps.append(s))

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        raise httpx.ReadTimeout("slow", request=request)

    with pytest.raises(LlamaCppTimeout):
        _client(handler, max_timeout_retries=3, retry_interval=2.0).complete("sys", "usr")

    assert calls["n"] == 3
    assert sleeps == [2.0, 2.0]  # slept between attempts, not after the final failure


def test_timeout_succeeds_on_retry(monkeypatch):
    calls = {"n": 0}
    monkeypatch.setattr("evaluation.llm.llamacpp.time.sleep", lambda s: None)

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 2:
            raise httpx.ConnectTimeout("slow connect", request=request)
        return _ok_response(request, content="recovered")

    result = _client(handler, max_timeout_retries=5).complete("sys", "usr")
    assert result == "recovered"
    assert calls["n"] == 2


# --- Busy (429/503) — no retry ---

@pytest.mark.parametrize("status", [429, 503])
def test_busy_status_raises_without_retry(status):
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(status, json={})

    with pytest.raises(LlamaCppBusy):
        _client(handler, max_timeout_retries=5).complete("sys", "usr")
    assert calls["n"] == 1


# --- Genuine application errors are not swallowed ---

def test_other_http_error_propagates_as_http_status_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error": "bad request"})

    with pytest.raises(httpx.HTTPStatusError):
        _client(handler).complete("sys", "usr")


# --- Concurrency cap (2026-08-14 — see module constant comment for history) ---

def test_default_allows_configured_parallelism():
    """Default max_concurrent_requests (4, matching the gate's own
    ThreadPoolExecutor) must let that many calls run genuinely concurrently —
    serializing them was tried and empirically didn't fix the underlying
    timeouts, so the default should not silently throw away the gate's
    proven concurrent speedup."""
    in_flight = {"count": 0, "max_seen": 0}
    lock = threading.Lock()

    def handler(request: httpx.Request) -> httpx.Response:
        with lock:
            in_flight["count"] += 1
            in_flight["max_seen"] = max(in_flight["max_seen"], in_flight["count"])
        time.sleep(0.05)
        with lock:
            in_flight["count"] -= 1
        return _ok_response(request)

    client = _client(handler)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: client.complete("sys", "usr"), range(4)))

    assert results == ["hello"] * 4
    assert in_flight["max_seen"] == 4


def test_max_concurrent_requests_caps_parallelism():
    in_flight = {"count": 0, "max_seen": 0}
    lock = threading.Lock()

    def handler(request: httpx.Request) -> httpx.Response:
        with lock:
            in_flight["count"] += 1
            in_flight["max_seen"] = max(in_flight["max_seen"], in_flight["count"])
        time.sleep(0.05)
        with lock:
            in_flight["count"] -= 1
        return _ok_response(request)

    client = _client(handler, max_concurrent_requests=2)
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(lambda _: client.complete("sys", "usr"), range(4)))

    assert in_flight["max_seen"] == 2
