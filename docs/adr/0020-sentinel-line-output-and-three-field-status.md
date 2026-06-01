# Sentinel-line LLM output format and three-field evaluation status

Module 4 instructs the LLM to end every response with a two-line sentinel block:

```
SCORE: <0, 1, ou 3>
UNCERTAINTY: <yes ou no>
```

Module 4 parses this block with regex. Three orthogonal boolean fields in `EvaluationResult` represent distinct conditions that require different Auditor responses:

| Field | Set by | Meaning |
|---|---|---|
| `no_evidence_found` | Module 4, before LLM call | `chunks` list was empty — LLM was not called |
| `uncertainty_flag` | LLM via `UNCERTAINTY: yes` | Evidence absent, insufficient, or contradictory |
| `parse_failed` | Module 4, after LLM response | Sentinel block missing or score not in `{0, 1, 3}` |

`proposed_score` and `reasoning` are `None` when `no_evidence_found=True` or `parse_failed=True`. When `uncertainty_flag=True`, both are still present — the LLM scored and flagged doubt.

The prompt audit trail uses two separate fields (`system_prompt`, `user_prompt`) rather than a single combined string, preserving the architecturally significant system/user boundary for Auditor review.

## Considered options

- **Provider JSON mode** — rejected: JSON mode behavior varies across Ollama and Groq; sentinel parsing works identically on any text-completion endpoint with no provider dependency.
- **Single `uncertainty_flag` covering all failure states** — rejected: conflates evidence gaps (LLM-side, meaningful to domain experts) with format compliance failures (Module 4-side, meaningful to engineers). The Auditor needs to distinguish them.
- **Portuguese label output (`Atendido` / `Parcialmente Atendido` / `Não Atendido`)** — not excluded from reasoning text; rejected only as the machine-readable transport. The integer sentinel is the canonical machine signal; Portuguese labels may appear naturally in the reasoning body.

## Consequences

When `parse_failed=True`, `raw_llm_response` in `EvaluationResult` carries the full LLM output for manual inspection. The WARNING log emitted by Module 4 on parse failure includes the raw response excerpt. Module 5 renders the three status conditions with distinct Auditor-facing explanations.
