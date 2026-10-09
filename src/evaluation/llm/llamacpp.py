from __future__ import annotations

import logging
import os
import threading
import time
from dataclasses import dataclass
from pathlib import Path

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
# Name of the variable that carries the server's --api-key, when the owner
# enables one on llama-server. Nothing about generation changes with it: the
# key travels in an Authorization header, the body stays byte-identical.
_API_KEY_ENV = "LLAMACPP_API_KEY"


def _default_api_key() -> str | None:
    """The llama-server --api-key, if one is configured: LLAMACPP_API_KEY in
    the environment, else in the repository's .env. The .env fallback exists
    because the diagnostics scripts build this client directly, without
    main.py's load_dotenv(); they must reach the server with the same key
    production uses. None (no key anywhere) sends no header at all."""
    key = os.environ.get(_API_KEY_ENV)
    if key:
        return key
    try:
        from dotenv import dotenv_values

        env_file = Path(__file__).resolve().parents[3] / ".env"
        if env_file.is_file():
            return dotenv_values(env_file).get(_API_KEY_ENV) or None
    except Exception:  # dotenv missing or unreadable file: behave as "no key"
        return None
    return None


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


@dataclass(frozen=True)
class LlamaCppCompletion:
    """One chat completion with the fields the audit trail keeps besides the
    answer. `reasoning` is gpt-oss's analysis channel as the server returns it
    (`message.reasoning_content`): produced BEFORE the schema-constrained
    answer, so reading it changes nothing about the generation. For the
    relevance gate it is the only justification that exists — the schema has
    one boolean (ADR-0053), and a free-text reason inside the schema is what
    ADR-0053 abandoned. None when the server sends no such field."""

    content: str
    reasoning: str | None = None
    finish_reason: str | None = None
    completion_tokens: int | None = None
    model: str | None = None


class LlamaCppTruncated(Exception):
    """The server stopped because it hit the token cap (finish_reason="length").

    Distinct from the availability failures above: the server answered, it just
    could not finish. For gpt-oss the grammar-constrained JSON is emitted on the
    final channel AFTER an unconstrained reasoning channel, so a cap that fires
    mid-reasoning yields empty or partial content — which json.loads() then
    rejects. Before this exception existed, that outcome reached
    parse_relevance_response() and became relevant=False: a truncated call was
    indistinguishable from a genuine "not relevant" verdict, silently, with no
    log and no counter (2026-09-27 diagnosis). Deliberately NOT one of
    _PRIMARY_FAILURES in fallback.py — swapping providers cannot fix a token cap.
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
        reasoning_effort: str | None = None,
        cache_prompt: bool | None = None,
        transport=None,
        api_key: str | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        # gpt-oss reasoning level ("low" / "medium" / "high"), a MODEL setting
        # passed through the chat template, not a server internal. None sends
        # nothing and leaves the server's default (medium). The gate runs at
        # "low" since ADR-0065: at medium, one prompt had up to 8 distinct
        # verdict trajectories in 8 passes under 4 concurrent calls and still
        # 2-3 states with one call in flight; at low with one call in flight
        # the same chunks were 0/80 unstable across Acoes 14, 22 and 3, with
        # every true positive kept and ~2.5x fewer completion tokens.
        self.reasoning_effort = reasoning_effort
        # Server-internal KV-prefix reuse. None (the default, and what
        # production runs) sends no key at all, so the request is byte-identical
        # to the frozen configuration and the server's own default applies.
        # False is for a diagnostic that was explicitly asked to run with no
        # cache of anything; it costs prefill time and was measured on
        # 2026-10-02 NOT to improve stability in this cell (serial + low:
        # 0/40 oscillating either way).
        self.cache_prompt = cache_prompt
        self.max_concurrent_requests = max_concurrent_requests
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
        # Authorization header for a llama-server started with --api-key.
        # None resolves LLAMACPP_API_KEY (environment, then .env); an explicit
        # "" pins "no key". A wrong or missing key is a hard, explicit failure
        # (HTTP 401/403 -> LlamaCppUnavailable), never a silent degradation
        # (ADR-0059).
        self._api_key = api_key if api_key is not None else _default_api_key()
        self._headers = {"Authorization": f"Bearer {self._api_key}"} if self._api_key else {}
        self.model_label = model
        # Provider label for per-call audit trails. A bare client (the GPU-only
        # wiring in main.py) is read via getattr by callers that also accept a
        # FallbackLLMClient's last_provider_used.
        self.provider_label = "llamacpp"
        self.last_model_used: str | None = None

    def health_check(self, timeout: float | None = None) -> None:
        """Probe /health. Raises LlamaCppUnavailable/LlamaCppTimeout if the
        server is not ready.

        Used as a run preflight: with the GPU-only wiring there is no fallback,
        so a full assessment must fail in seconds with a clear message rather
        than paying a connect timeout per Ação on a server that is switched off.
        """
        import httpx

        probe = timeout if timeout is not None else self._connect_timeout
        try:
            with httpx.Client(timeout=probe, transport=self._transport) as client:
                response = client.get(f"{self._base_url}/health", headers=self._headers)
        except httpx.ConnectError as exc:
            raise LlamaCppUnavailable(str(exc)) from exc
        except (httpx.ConnectTimeout, httpx.ReadTimeout) as exc:
            raise LlamaCppTimeout(str(exc)) from exc
        if response.status_code in (429, 503):
            raise LlamaCppBusy(f"HTTP {response.status_code}")
        if response.status_code in (401, 403):
            raise LlamaCppUnavailable(self._auth_failure_message(response.status_code))
        response.raise_for_status()

    def _auth_failure_message(self, status: int) -> str:
        enviada = "enviada" if self._api_key else "NÃO enviada"
        return (
            f"HTTP {status}: o servidor exige chave de API (--api-key) e a chave "
            f"{enviada} foi recusada — defina {_API_KEY_ENV} (no ambiente ou em .env) "
            f"com a chave configurada no servidor GPU."
        )

    def complete(self, system: str, user: str, schema: dict | None = None) -> str:
        return self.complete_detailed(system, user, schema).content

    def complete_detailed(
        self, system: str, user: str, schema: dict | None = None
    ) -> LlamaCppCompletion:
        """Same call as complete(), returning the answer together with the
        model's reasoning channel and the usage fields (see LlamaCppCompletion).
        Callers that only need the answer keep using complete()."""
        with self._semaphore:
            return self._complete_locked(system, user, schema)

    def _complete_locked(
        self, system: str, user: str, schema: dict | None
    ) -> LlamaCppCompletion:
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
        if self.reasoning_effort is not None:
            payload["chat_template_kwargs"] = {"reasoning_effort": self.reasoning_effort}
        if self.cache_prompt is not None:
            payload["cache_prompt"] = self.cache_prompt

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
                    response = client.post(url, json=payload, headers=self._headers)
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
            if response.status_code in (401, 403):
                msg = self._auth_failure_message(response.status_code)
                logger.error("llama.cpp primary rejected the API key: %s", msg)
                report("chamando_llm", msg, "error")
                raise LlamaCppUnavailable(msg)
            response.raise_for_status()

            body = response.json()
            self.last_model_used = body.get("model") or self._model
            choice = body["choices"][0]
            finish_reason = choice.get("finish_reason")
            message = choice["message"]
            content = message["content"]
            # llama.cpp puts gpt-oss's analysis channel in reasoning_content;
            # older builds used "reasoning". Absent for models without one.
            reasoning = message.get("reasoning_content")
            if reasoning is None:
                reasoning = message.get("reasoning")
            usage = body.get("usage") or {}
            if finish_reason == "length":
                logger.warning(
                    "llama.cpp stopped at the token cap (finish_reason=length): "
                    "max_tokens=%s completion_tokens=%s content_chars=%d — the "
                    "response is incomplete and must not be parsed as a verdict.",
                    self._max_tokens,
                    usage.get("completion_tokens"),
                    len(content or ""),
                )
                report(
                    "chamando_llm",
                    f"Resposta truncada no limite de tokens "
                    f"(max_tokens={self._max_tokens}) — descartada.",
                    "warning",
                )
                raise LlamaCppTruncated(
                    f"finish_reason=length (max_tokens={self._max_tokens}, "
                    f"completion_tokens={usage.get('completion_tokens')})"
                )
            return LlamaCppCompletion(
                content=content,
                reasoning=reasoning if isinstance(reasoning, str) else None,
                finish_reason=finish_reason,
                completion_tokens=usage.get("completion_tokens"),
                model=self.last_model_used,
            )

        # Unreachable — the loop above always returns or raises — kept only
        # to satisfy static analysis that complete() always returns/raises.
        raise LlamaCppTimeout(str(last_timeout_exc))
