from __future__ import annotations

import logging
import time

from evaluation.llm.llamacpp import LlamaCppBusy, LlamaCppTimeout, LlamaCppUnavailable
from evaluation.llm.protocol import LLMClient
from evaluation.progress import report

logger = logging.getLogger(__name__)

# Short, user-facing reason strings — never the raw exception message, which
# could echo request/response internals. Keys match the exception types
# caught below.
_FAILURE_REASONS = {
    "LlamaCppUnavailable": "conexão recusada",
    "LlamaCppTimeout": "timeout",
    "LlamaCppBusy": "servidor ocupado",
}

# Failure types that trigger a fallback. All three represent the primary
# being unavailable *right now* for reasons unrelated to the request's own
# validity — a genuine application error (e.g. an HTTP 400 from a malformed
# request) is deliberately NOT included here and propagates as a real
# exception instead of being silently swallowed by the fallback path.
_PRIMARY_FAILURES = (LlamaCppUnavailable, LlamaCppTimeout, LlamaCppBusy)


class FallbackLLMClient:
    """Circuit-breaker wrapper around a primary + fallback LLMClient (ADR-0054).

    Tries `primary` first. On a qualifying failure (connection
    refused/DNS, exhausted timeout retries, or an explicit busy response),
    serves the call from `fallback` and puts the primary into a cooldown
    window — subsequent calls skip straight to `fallback` without
    re-attempting a primary that's likely still down, rather than paying
    the full connect/timeout cost on every single call of a run that can
    involve dozens of them. Once the cooldown elapses, the next call probes
    the primary again; a success clears the cooldown.

    `last_provider_used` / `last_model_used` reflect whichever client
    actually served the most recent call, so EvaluationResult's audit trail
    stays accurate even when a fallback occurred (see evaluator.py's
    actual_provider/actual_model pattern).
    """

    def __init__(
        self,
        primary: LLMClient,
        fallback: LLMClient,
        primary_provider_label: str,
        fallback_provider_label: str,
        cooldown_seconds: float = 10.0,
    ) -> None:
        self._primary = primary
        self._fallback = fallback
        self._primary_provider_label = primary_provider_label
        self._fallback_provider_label = fallback_provider_label
        self._cooldown_seconds = cooldown_seconds
        self._primary_down_until: float = 0.0
        self.last_provider_used: str | None = None
        self.last_model_used: str | None = None

    def describe_route(self) -> str:
        """Human-readable summary of which provider is configured/active right
        now, for progress reporting before any call has been made this run
        (ADR-0055 extension — 'who was chosen and why', not just 'who served
        the last call' like last_provider_used)."""
        primary_model = getattr(self._primary, "model_label", None)
        fallback_model = getattr(self._fallback, "model_label", None)
        primary_desc = (
            f"{self._primary_provider_label}/{primary_model}"
            if primary_model
            else self._primary_provider_label
        )
        fallback_desc = (
            f"{self._fallback_provider_label}/{fallback_model}"
            if fallback_model
            else self._fallback_provider_label
        )

        remaining = self._primary_down_until - time.monotonic()
        if remaining > 0:
            return (
                f"usando {fallback_desc} — {primary_desc} em espera por mais "
                f"{remaining:.0f}s após falha recente"
            )
        return f"{primary_desc} (servidor principal) — fallback configurado: {fallback_desc}"

    def complete(self, system: str, user: str, schema: dict | None = None) -> str:
        now = time.monotonic()
        if now < self._primary_down_until:
            logger.info(
                "Primary (%s) in cooldown (%.1fs remaining) — using fallback (%s) directly.",
                self._primary_provider_label,
                self._primary_down_until - now,
                self._fallback_provider_label,
            )
            report(
                "fallback",
                f"Usando LLM local/{self._fallback_provider_label} — "
                f"principal ainda em espera após falha recente.",
                "warning",
            )
            return self._complete_fallback(system, user, schema)

        try:
            result = self._primary.complete(system, user, schema)
        except _PRIMARY_FAILURES as exc:
            reason = _FAILURE_REASONS.get(type(exc).__name__, "indisponível")
            logger.warning(
                "Primary (%s) failed [%s: %s] — falling back to %s, cooldown %.0fs.",
                self._primary_provider_label,
                type(exc).__name__,
                exc,
                self._fallback_provider_label,
                self._cooldown_seconds,
            )
            report(
                "fallback",
                f"Servidor principal indisponível ({reason}) — usando "
                f"{self._fallback_provider_label} pelos próximos {self._cooldown_seconds:.0f}s.",
                "warning",
            )
            self._primary_down_until = time.monotonic() + self._cooldown_seconds
            return self._complete_fallback(system, user, schema)

        self.last_provider_used = self._primary_provider_label
        self.last_model_used = (
            getattr(self._primary, "last_model_used", None)
            or getattr(self._primary, "model_label", None)
        )
        return result

    def _complete_fallback(self, system: str, user: str, schema: dict | None) -> str:
        result = self._fallback.complete(system, user, schema)
        self.last_provider_used = self._fallback_provider_label
        self.last_model_used = (
            getattr(self._fallback, "last_model_used", None)
            or getattr(self._fallback, "model_label", None)
        )
        return result
