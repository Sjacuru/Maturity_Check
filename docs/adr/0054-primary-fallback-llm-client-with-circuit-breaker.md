# Primary/fallback LLM client with circuit-breaker cooldown

**Status:** accepted

Both LLM interaction points (gate and scorer) now go through a `FallbackLLMClient`
wrapper: a personal, self-hosted llama.cpp server (`gpt-oss-20b`, hosted outside the
corporate network) is the **primary** provider for both roles; each role's previous
sole provider becomes its **fallback** — Groq (`openai/gpt-oss-20b`) for the scorer,
local Ollama (`qwen2.5:7b`) for the gate. A failure of the primary does not simply
fall back for one call and try again next time from scratch — it opens a
**circuit-breaker cooldown**: for 10 seconds after a failure, calls go straight to
the fallback without re-attempting the primary, then the next call after the
cooldown probes the primary again.

## Why a circuit breaker instead of per-call retry-then-fallback

A single assessment run makes dozens of gate calls (up to ~40 per Ação) plus one
scorer call. Retrying the primary on every individual call during an extended
outage wastes the full connect/timeout budget dozens of times over, and — worse —
means an outage silently degrades the *entire* run to the local Ollama fallback's
throughput rather than failing over cleanly. The cooldown bounds that cost: one
failure pays the timeout once, then every call for the next 10 seconds goes
straight to the fallback. If the primary recovers, the next call after the
cooldown finds out and resumes using it.

## Failure taxonomy and trigger conditions

Three distinct client-side symptoms map to three exception types
(`src/evaluation/llm/llamacpp.py`), each handled differently:

| Symptom | Exception | Retried inside `complete()`? | Likely cause |
|---|---|---|---|
| Connection refused / DNS failure | `LlamaCppUnavailable` | No — immediate fallback | Server process not running |
| Connect or read timeout | `LlamaCppTimeout` | Yes — up to 5 attempts, 3s apart | Ambiguous (see below) |
| HTTP 429 / 503 | `LlamaCppBusy` | No — immediate fallback | All 4 inference slots occupied |

**Timeout is deliberately treated as retryable and ambiguous.** A connect timeout
in particular (TCP handshake never completes, no active refusal) is the expected
client-side symptom of a corporate firewall silently dropping outbound packets —
indistinguishable, from the client alone, from the server simply being slow. Both
causes can be transient, so both get the same short retry loop before the call
gives up and falls back. Connect timeout is bounded at 5s per attempt (fail fast
enough that a genuinely blocked path doesn't stall the run); read timeout is
bounded at 90s per attempt (comfortably above the ~5–15s normal range observed
during earlier testing, without waiting out the 174.5s runaway-generation outlier
seen once in that same testing). Every failure is logged with its exception type
and message specifically so a recurring pattern can be read back later and
attributed — a run of `LlamaCppUnavailable` entries points at the server process
itself; a run of connect-phase `LlamaCppTimeout` entries is more consistent with a
network-level block than a slow server.

**Connection-refused/DNS is deliberately NOT retried inside `complete()`.** A
dead server won't come back within a 3-second gap the way a transient timeout
might; retrying it would only add latency to the failing call without materially
improving the odds of success. Availability recovery is delegated entirely to the
circuit breaker's cooldown-then-reprobe cycle instead.

**Non-2xx statuses other than 429/503 are not treated as availability failures.**
An HTTP 400 (a malformed request — a real bug) propagates as a genuine
`httpx.HTTPStatusError`, not silently masked by a fallback. Falling back on a
request-shape bug would not fix it (the same malformed request likely fails
against the fallback too) and would hide the actual problem.

## What "fallback" restores

The fallback pairing is deliberately the *exact* pre-ADR-0054 configuration:
Groq/`openai/gpt-oss-20b` for the scorer (ADR-0053), local Ollama/`qwen2.5:7b` for
the gate (ADR-0050). Groq was never a candidate fallback for the gate — its
account-level rate limit already can't absorb the gate's call volume (ADR-0019
amendment) — so the gate's fallback stays purely local.

## Audit trail

`EvaluationResult.provider`/`.model` must reflect whichever client actually served
a given scorer call, not just the statically configured primary. `evaluator.py`
now reads `getattr(client, "last_provider_used", None) or provider` (mirroring the
existing `last_model_used` pattern) — `FallbackLLMClient` sets both attributes
after every call to the label of whichever underlying client served it. This is a
no-op for the simple single-provider configuration path used in tests
(`StubLLMClient` doesn't set `last_provider_used`, so `actual_provider` falls back
to the statically configured value, unchanged from before this ADR). The gate has
no equivalent per-call schema field for provider/model — its audit trail is
log-only (`logger.warning`/`logger.info` at each trigger and cooldown event), not
a `RejectedChunk`/`RetrievedChunk` contract change; adding that is out of scope
here.

## Considered options

- **Retry the primary on every call, no cooldown** — rejected: pays the full
  timeout cost on every one of the ~40 gate calls in a run during an outage,
  instead of once.
- **Never retry the primary once it fails (permanent fallback for the rest of the
  process)** — rejected: a transient outage (e.g. the user's machine briefly
  losing network) would degrade the rest of the session even after recovery, with
  no way to resume using the faster/preferred primary short of restarting the
  process.
- **Exponential backoff instead of a fixed 10s cooldown** — rejected for now: adds
  complexity (tracking consecutive-failure count, backoff ceiling) not justified
  by a single personal server with no observed flapping pattern; a fixed cooldown
  is simple to reason about and easy to test deterministically. Revisit if the
  primary is observed to flap (fail, recover, fail again) within a single run.
- **Structured per-gate-call provider/model audit trail** (schema change to
  `RejectedChunk`/`RetrievedChunk`) — deferred: log-level visibility is enough to
  answer "was the corporate network blocking this" after the fact; a full schema
  change is a larger, separately-scoped piece of work if per-chunk provider
  attribution is ever needed.

## Consequences

- New `src/evaluation/llm/llamacpp.py` (`LlamaCppClient`,
  `LlamaCppUnavailable`/`LlamaCppTimeout`/`LlamaCppBusy`) and
  `src/evaluation/llm/fallback.py` (`FallbackLLMClient`).
- `OllamaClient` and `GroqClient` gain a `model_label` attribute (set at
  construction) so `FallbackLLMClient` has a reliable label source even before a
  client's first successful call.
- New `evaluation._config.configure_llm_client()` /
  `configure_gate_llm_client()` — raw setters accepting an already-constructed
  `LLMClient` (e.g. a `FallbackLLMClient`), alongside the existing
  `configure_llm()`/`configure_gate_llm()` provider-string dispatch, which is
  unchanged and still used directly by tests.
- `main.py` constructs the primary/fallback pair explicitly per role and wires
  each through the new setters; the previous single-provider
  `configure_llm()`/`configure_gate_llm()` calls are replaced.
- `evaluator.py` records `actual_provider` alongside the existing `actual_model`
  pattern.
- New tests: `tests/test_llamacpp_client.py`, `tests/test_fallback_llm_client.py`.
