# GPU-only execution: the LLM fallback chain is unwired, not removed

**Status:** accepted
**Amends:** ADR-0054 (primary/fallback LLM client with circuit breaker)

`main.py` now wires **only** `LlamaCppClient` (the personal GPU-backed
`gpt-oss-20b` server) for both the gate and the scorer. `FallbackLLMClient`,
`GroqClient` and `OllamaClient` remain in the repository, fully tested, but are
no longer constructed at startup. If the GPU server is unreachable, an
assessment now fails with an explicit error before evaluating anything, rather
than silently continuing on a different model.

## Why unwire a working fallback

ADR-0054's reasoning still holds for availability. What it did not account for is
that a fallback changes *which model produced a score* without changing anything
the auditor sees. Three concrete problems:

1. **No audit trail at the point that matters.** The gate has no per-call
   provider field (ADR-0054 explicitly deferred that). A run that silently
   switched the gate from `gpt-oss-20b` to `qwen2.5:7b` part-way produces an
   evaluation whose accept/reject decisions came from two different models, with
   only log lines to say so. For a system whose entire premise is
   reproducibility (Strategic Decision #7), that is the wrong failure mode.
2. **It undermines gate investigations.** The 2026-08-27 gate-forensics work
   reached its conclusion by calling the llama.cpp primary directly, bypassing
   `FallbackLLMClient` — i.e. it measured a path production did not always use.
   Any conclusion about gate stability is unsound while the provider can change
   under it.
3. **Cost.** A full 46-Ação run on the local Ollama fallback takes many hours.
   As a degraded mode for an interactive test cycle it is not usable, so in
   practice the fallback converts a fast failure into a very slow one.

**Fail fast instead.** `AssessmentService` health-probes the configured clients
once, before extraction, and aborts the whole assessment if the server is down —
so the operator learns immediately rather than after the first Ação. Documents
already extracted and indexed are kept (that work is reusable), and a mid-run
infrastructure failure aborts while preserving the Ações already evaluated.

## Why the modules stay in the tree

They are the record that this was tried, and the design (circuit breaker,
failure taxonomy, `last_provider_used` audit attribute) is sound and worth
keeping should a second GPU-backed provider ever be added — a *comparable*
fallback is a different proposition from a smaller-model one. Deleting them
would also delete `tests/test_fallback_llm_client.py`'s coverage of that
taxonomy. They are unwired at exactly one place (`main.py`), so re-enabling is a
local change, not a reconstruction.

## Consequences

- A GPU outage is now a hard stop. This is the intended behaviour: an
  unreproducible score is worse than no score.
- `LlamaCppClient` gains `health_check()` and a `provider_label`, used by the
  new `AssessmentService._preflight_llm()`.
- Infrastructure failures (`LlamaCppUnavailable`/`Timeout`/`Busy`) are
  re-raised out of the per-Ação loop, while an error in one Ação's own
  evaluation is recorded and the run continues — the two are deliberately not
  treated alike.
- `tests/test_assessment_resilience.py` covers preflight abort, mid-run abort,
  and the single-bad-Ação case.
