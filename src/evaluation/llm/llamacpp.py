from __future__ import annotations

import logging
import threading
import time

from evaluation.progress import report

logger = logging.getLogger(__name__)

_DEFAULT_CONNECT_TIMEOUT = 5.0
_DEFAULT_READ_TIMEOUT = 45.0
_MAX_TIMEOUT_RETRIES = 3
_RETRY_INTERVAL_SECONDS = 3.0
# The server is GPU-backed (~140 tok/s) — generating even a full scorer
# response should take single-digit seconds, so the multi-second-to-90s+
# stalls observed empirically 2026-08-14 are not generation time. Isolated
# testing that day also ruled out this client's own thread concurrency as
# the cause (the stalls recurred even when no other gate call from this
# process was in flight). The remaining candidates are network-path
# variance to the external server (a corporate firewall silently dropping
# packets rather than refusing the connection would look identical
# client-side — see LlamaCppTimeout) or request queuing on the server
# itself; neither is confirmed. 45s/3 retries (worst case ~141s/call) was
# chosen empirically as a middle ground: short enough to fail well before
# the old 90s/5-retry ~7.7min worst case, generous enough that a 120s/
# single-attempt diagnostic run saw zero timeouts on the same case.
_DEFAULT_MAX_CONCURRENT_REQUESTS = 4


class LlamaCppUnavailable(Exception):
    """Connection refused / DNS failure — server not listening at all.

    Fast, definitive signal. Not retried inside complete(): a dead server
    won't come back within the same call, so the caller (FallbackLLMClient)
    decides whether/when to retry the primary again later.
    """


class LlamaCppTimeout(Exception):
    """Connect or read timeout, after exhausting retry attempts.

    Ambiguous signal — either cause below produces the same client-side
    symptom (a hang until our own timeout fires, no active response):
    - A corporate firewall silently dropping packets (no TCP RST) rather
      than actively refusing the connection.
    - The server being genuinely slow/overloaded (observed once: a 174.5s
      runaway generation with a much larger read timeout).
    Both are potentially transient, hence the retry loop before giving up.
    """


class LlamaCppBusy(Exception):
    """HTTP 429/503 — server explicitly reports it cannot serve the request
    right now (e.g. all inference slots occupied). Not retried inside
    complete(): the server told us definitively, no point immediately
    repeating the same request."""


class LlamaCppClient:
    """LLM client for a self-hosted llama.cpp server (OpenAI-compatible
    /v1/chat/completions), with grammar-constrained JSON output support
    (ADR-0053) and a bounded timeout-retry loop (ADR-0054). Connection
    failures and busy responses are not retried here — see
    evaluation.llm.fallback.FallbackLLMClient for the circuit-breaker that
    decides when to retry the primary vs. fall back.
    """

    def __init__(
        self,
        base_url: str,
        model: str,
        connect_timeout: float = _DEFAULT_CONNECT_TIMEOUT,
        read_timeout: float = _DEFAULT_READ_TIMEOUT,
        max_timeout_retries: int = _MAX_TIMEOUT_RETRIES,
        retry_interval: float = _RETRY_INTERVAL_SECONDS,
        max_concurrent_requests: int = _DEFAULT_MAX_CONCURRENT_REQUESTS,
        max_tokens: int | None = None,
        transport=None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._connect_timeout = connect_timeout
        self._read_timeout = read_timeout
        self._max_timeout_retries = max_timeout_retries
        self._retry_interval = retry_interval
        # Hard cap on generated tokens, INCLUDING any hidden reasoning/
        # analysis-channel tokens the model produces before its final
        # schema-constrained content (confirmed 2026-08-14: one gate call —
        # final answer 19 chars — generated 7685 completion tokens, ~23k
        # chars of hidden reasoning, ~55s of pure generation at this
        # server's ~140 tok/s). None = no cap (the scorer wants its
        # "reasoning" field to be genuinely free-length).
        self._max_tokens = max_tokens
        # Caps how many calls from this client instance are in flight to the
        # server at once — a caller (e.g. the gate's ThreadPoolExecutor) may
        # fire several concurrent requests, but they queue here rather than
        # all hitting the server together and racing the read timeout.
        self._semaphore = threading.Semaphore(max_concurrent_requests)
        # Test-only hook: an httpx.MockTransport lets tests exercise the
        # retry/error-mapping logic below without a real network call. None
        # in production — httpx.Client uses its normal transport.
        self._transport = transport
        self.model_label = model
        self.last_model_used: str | None = None

    def complete(self, system: str, user: str, schema: dict | None = None) -> str:
        with self._semaphore:
            return self._complete_locked(system, user, schema)

    def _complete_locked(self, system: str, user: str, schema: dict | None) -> str:
        import httpx

        payload: dict = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0,
            "stream": False,
        }
        if schema is not None:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "response", "schema": schema, "strict": True},
            }
        if self._max_tokens is not None:
            payload["max_tokens"] = self._max_tokens

        timeout = httpx.Timeout(
            connect=self._connect_timeout,
            read=self._read_timeout,
            write=self._connect_timeout,
            pool=self._connect_timeout,
        )
        url = f"{self._base_url}/v1/chat/completions"

        last_timeout_exc: Exception | None = None
        for attempt in range(1, self._max_timeout_retries + 1):
            try:
                with httpx.Client(timeout=timeout, transport=self._transport) as client:
                    response = client.post(url, json=payload)
            except httpx.ConnectError as exc:
                logger.warning(
                    "llama.cpp primary unreachable (connection refused/DNS): %s", exc
                )
                report(
                    "chamando_llm",
                    "Servidor principal (llamacpp) não respondeu à conexão.",
                    "warning",
                )
                raise LlamaCppUnavailable(str(exc)) from exc
            except (httpx.ConnectTimeout, httpx.ReadTimeout) as exc:
                last_timeout_exc = exc
                kind = "connect" if isinstance(exc, httpx.ConnectTimeout) else "read"
                logger.warning(
                    "llama.cpp primary %s timeout (attempt %d/%d): %s",
                    kind, attempt, self._max_timeout_retries, exc,
                )
                report(
                    "chamando_llm",
                    f"Sem resposta do servidor principal em {self._read_timeout:.0f}s "
                    f"— tentativa {attempt}/{self._max_timeout_retries}...",
                    "waiting",
                )
                if attempt < self._max_timeout_retries:
                    time.sleep(self._retry_interval)
                    continue
                raise LlamaCppTimeout(str(exc)) from exc

            if response.status_code in (429, 503):
                logger.warning(
                    "llama.cpp primary reported busy (HTTP %d) — no free inference slot.",
                    response.status_code,
                )
                report(
                    "chamando_llm",
                    f"Servidor principal ocupado (HTTP {response.status_code}).",
                    "warning",
                )
                raise LlamaCppBusy(f"HTTP {response.status_code}")
            response.raise_for_status()

            body = response.json()
            self.last_model_used = body.get("model") or self._model
            return body["choices"][0]["message"]["content"]

        # Unreachable — the loop above always returns or raises — kept only
        # to satisfy static analysis that complete() always returns/raises.
        raise LlamaCppTimeout(str(last_timeout_exc))
