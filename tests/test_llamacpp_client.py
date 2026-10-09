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
    LlamaCppTruncated,
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

# --- finish_reason=length (token-cap truncation) ---

def _length_response(content: str = "", completion_tokens: int = 768) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "model": "test-model",
            "choices": [{"message": {"content": content}, "finish_reason": "length"}],
            "usage": {"completion_tokens": completion_tokens},
        },
    )


def test_finish_reason_length_raises_truncated():
    """A response cut off at the token cap must not be returned as content.

    gpt-oss emits the schema-constrained JSON on a final channel AFTER an
    unconstrained reasoning channel, so a cap firing mid-reasoning yields empty
    or partial content. Returning it let json.loads() fail downstream, which the
    relevance gate then recorded as relevant=False — a silent rejection.
    """
    client = _client(lambda req: _length_response(), max_tokens=768)
    with pytest.raises(LlamaCppTruncated):
        client.complete("sys", "usr")


def test_finish_reason_length_raises_even_with_partial_content():
    client = _client(lambda req: _length_response(content='{"relev'), max_tokens=768)
    with pytest.raises(LlamaCppTruncated):
        client.complete("sys", "usr")


def test_truncated_message_carries_the_cap_and_token_count():
    client = _client(lambda req: _length_response(completion_tokens=768), max_tokens=768)
    with pytest.raises(LlamaCppTruncated) as excinfo:
        client.complete("sys", "usr")
    assert "768" in str(excinfo.value)


def test_finish_reason_stop_returns_content_normally():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "model": "test-model",
                "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
            },
        )

    assert _client(handler).complete("sys", "usr") == "ok"


def test_absent_finish_reason_returns_content_normally():
    """Older/leaner server builds may omit finish_reason entirely."""
    assert _client(lambda req: _ok_response(req, content="ok")).complete("sys", "usr") == "ok"


def test_truncated_is_not_a_primary_failure_for_the_fallback_client():
    """LlamaCppTruncated must not trigger a provider swap: changing provider
    cannot fix a token cap, and swapping models silently is exactly the
    behaviour the GPU-only wiring removed."""
    from evaluation.llm.fallback import _PRIMARY_FAILURES

    assert LlamaCppTruncated not in _PRIMARY_FAILURES


# --- health_check (fail-fast preflight) ---

def test_health_check_passes_when_server_is_ready():
    client = _client(lambda req: httpx.Response(200, json={"status": "ok"}))
    client.health_check()  # must not raise


def test_health_check_raises_unavailable_on_connect_error():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    with pytest.raises(LlamaCppUnavailable):
        _client(handler).health_check()


def test_health_check_raises_timeout_on_connect_timeout():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("timed out", request=request)

    with pytest.raises(LlamaCppTimeout):
        _client(handler).health_check()


@pytest.mark.parametrize("status", [429, 503])
def test_health_check_raises_busy_on_overload(status):
    with pytest.raises(LlamaCppBusy):
        _client(lambda req: httpx.Response(status)).health_check()


def test_health_check_probes_the_health_endpoint():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["method"] = request.method
        return httpx.Response(200, json={"status": "ok"})

    _client(handler).health_check()
    assert seen["url"].endswith("/health")
    assert seen["method"] == "GET"


def test_provider_label_is_set():
    assert _client(lambda req: _ok_response(req)).provider_label == "llamacpp"


# --- reasoning_effort (ADR-0065) ---

def test_reasoning_effort_is_sent_through_chat_template_kwargs():
    """A MODEL setting for gpt-oss, carried in the OpenAI-compatible request as
    chat_template_kwargs — the gate runs at "low" since ADR-0065."""
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(json.loads(request.content))
        return _ok_response(request)

    client = _client(handler, reasoning_effort="low")
    client.complete("sys", "usr")
    assert captured["chat_template_kwargs"] == {"reasoning_effort": "low"}
    assert client.reasoning_effort == "low"


def test_reasoning_effort_absent_by_default_leaves_the_server_default():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(json.loads(request.content))
        return _ok_response(request)

    client = _client(handler)
    client.complete("sys", "usr")
    assert "chat_template_kwargs" not in captured
    assert client.reasoning_effort is None


# --- cache_prompt (server internal, opt-in only) ---

def test_cache_prompt_absent_by_default_so_production_payload_is_unchanged():
    """The frozen configuration sends no cache_prompt key. This test is the
    guard: adding the parameter must not alter a single production request
    byte, or every measurement taken before it is invalidated."""
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(json.loads(request.content))
        return _ok_response(request)

    client = _client(handler)
    client.complete("sys", "usr")
    assert "cache_prompt" not in captured
    assert client.cache_prompt is None


def test_cache_prompt_false_is_sent_when_a_clean_run_is_asked_for():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(json.loads(request.content))
        return _ok_response(request)

    client = _client(handler, cache_prompt=False)
    client.complete("sys", "usr")
    assert captured["cache_prompt"] is False


def test_max_concurrent_requests_is_readable_for_wiring_checks():
    client = _client(lambda req: _ok_response(req), max_concurrent_requests=1)
    assert client.max_concurrent_requests == 1


# --- complete_detailed: reasoning channel + usage (2026-10-03) ---

def _detailed_response(request: httpx.Request, content="{\"relevant\": false}", reasoning="o trecho trata de outra coisa") -> httpx.Response:
    return httpx.Response(200, json={
        "model": "test-model",
        "choices": [{"finish_reason": "stop", "message": {"content": content, "reasoning_content": reasoning}}],
        "usage": {"completion_tokens": 57},
    })


def test_complete_detailed_returns_reasoning_content_and_usage():
    client = _client(lambda req: _detailed_response(req))
    result = client.complete_detailed("sys", "usr")
    assert result.content == '{"relevant": false}'
    assert result.reasoning == "o trecho trata de outra coisa"
    assert result.finish_reason == "stop"
    assert result.completion_tokens == 57
    assert result.model == "test-model"


def test_complete_still_returns_only_the_content():
    client = _client(lambda req: _detailed_response(req))
    assert client.complete("sys", "usr") == '{"relevant": false}'


def test_complete_detailed_without_reasoning_field_gives_none():
    """A model/server without a reasoning channel: content as before, reasoning None."""
    client = _client(lambda req: _ok_response(req, content="hello"))
    result = client.complete_detailed("sys", "usr")
    assert result.content == "hello"
    assert result.reasoning is None
    assert result.completion_tokens is None


def test_complete_detailed_accepts_the_older_reasoning_field_name():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "model": "m", "choices": [{"message": {"content": "x", "reasoning": "antigo"}}],
        })
    assert _client(handler).complete_detailed("sys", "usr").reasoning == "antigo"
