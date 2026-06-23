# Pass all retrieved chunks to the LLM prompt without filtering

Module 4 (evaluation) receives `list[RetrievedChunk]` from Module 3 and embeds all chunks in the LLM prompt without filtering, budget enforcement, or truncation. The chunk list is already bounded by Module 3's `MAX_CHUNKS_PER_ACAO` ceiling; further reduction in Module 4 would be premature optimization driven by a hypothetical — not a measured — context window problem.

## Deterministic ordering

Chunks are sorted before embedding, producing a reproducible prompt for the same input:

1. **Cascade step** (ascending position): `filename_match` → `variant_match` → `bm25` → `regex`
2. **Within `bm25`**: `bm25_score` descending, then `rank` ascending, then `chunk_index` ascending
3. **Within all other steps** (`bm25_score` and `rank` are null): `filename` ascending, then `page_number` ascending, then `chunk_index` ascending

## Observability

Evidence section character count is logged at INFO on every evaluation. A WARNING is emitted when the count exceeds a configurable threshold (default: 15,000 chars). This telemetry is the trigger mechanism for future architectural decisions — not a safety valve.

## Considered options

- **Character budget with priority ordering** — dropped: adds Module 4 complexity to solve an unmeasured problem; also presupposes that evidence selection is an evaluation concern rather than a retrieval concern.
- **Count ceiling** — dropped: treats a 2,000-char chunk and a 200-char chunk as equivalent weight; character count is the quantity that actually matters for context windows.
- **Pass-all with deterministic ordering** (chosen): simple, reproducible, and honest about what we don't yet know.

## Consequences

If real evaluation runs expose a context overflow or score-quality degradation, the fix must be located before implementing it: a tighter `MAX_CHUNKS_PER_ACAO` in Module 3 (retrieval concern) or an evidence-selection stage in Module 4 (evaluation concern). The WARNING logs and INFO metrics provide the evidence base for that decision. Either path requires its own ADR.

## Amendment (2026-06-23): corrected evidence cap and num_ctx bugfix

The predicted context-overflow scenario occurred: a real evaluation run retrieved 57,000 chars of evidence (27 chunks via BM25 + additive regex), which exhausted the Ollama/Mistral context window before the model could emit the `SCORE:` sentinel. The fix applied at the time introduced `_MAX_EVIDENCE_CHARS = 20_000` and `EVIDENCE_CHAR_WARN_THRESHOLD = 15_000` in `evaluator.py`, with cascade-priority truncation (`_cap_evidence()`).

That fix was partly miscalibrated. `ollama.py` hardcoded `num_ctx=8192` — a quarter of Mistral 7B's real native context window of 32,768 tokens — which is fixed as part of this amendment regardless of the cap value, since it silently undermines whatever evidence-cap math assumes Mistral's real context. But Mistral's context window turned out not to be the binding constraint at all.

**First attempt (superseded below):** recalculating against Mistral's 32,768-token window alone suggested headroom for ~77,000 chars of evidence, and `_MAX_EVIDENCE_CHARS` was provisionally raised to 50,000. Re-running the live assessment against this value immediately failed:

```
groq.APIStatusError: 413 - Request too large for model `llama-3.3-70b-versatile`
in organization ... service tier `on_demand` on tokens per minute (TPM):
Limit 12000, Requested 19717
```

Groq's on-demand account tier caps requests at **12,000 tokens/minute** — far tighter than the model's nominal 128K context window, and tighter than Mistral's 32K window too. This is an account/billing limit, not a model capability limit, but it is the actual binding constraint for the provider this project runs against in practice (`main.py` hardcodes `configure_llm(provider="groq", ...)`). The failed request also gave a real, measured data point: 6,541 chars of system prompt + up to 50,000 chars of evidence (≈56,500 chars total) was counted by Groq as 19,717 tokens — **≈2.87 chars/token** for this Portuguese system-prompt-plus-chunk-text mix, tighter than the 3.0 chars/token estimate used in the first attempt.

**Corrected calculation**, against the real binding constraint (Groq's 12,000 TPM, using the measured 2.87 chars/token ≈ rounded to 3.0 for a conservative token estimate):
- System prompt for Ação 1, measured: 6,541 chars (~2,180 tokens at 3.0 chars/token)
- Reserved for completion (reasoning + sentinel block): ~1,500 tokens
- Safety margin (~10%): ~1,200 tokens
- Remaining for evidence: ~7,100 tokens ≈ ~21,000 chars

**Final values:**
- `_MAX_EVIDENCE_CHARS`: 20,000 → **21,000** (effectively unchanged — the original value was already close to correct, just not derived from this reasoning)
- `EVIDENCE_CHAR_WARN_THRESHOLD`: kept at **15,000**
- `ollama.py` `num_ctx`: 8192 → **32768** (legitimate independent bugfix — only matters when the Ollama path is actually used, since it has no rate limit of its own)

**Conclusion:** the evidence-cap character budget was never the real lever for fixing uneven per-product representation (1c/1d/rio_hints being starved while 1a/1b dominate) — Groq's account-level rate limit means the ceiling cannot be raised meaningfully for this provider. The actual fix has to come from making better use of the existing ~20K-char budget: selecting the *right* chunks before they consume it. That is what ADR-0049 (hybrid BM25+vector retrieval via per-product RRF) and the planned relevance-gate ADR address — this amendment only fixes a genuine miscalibration bug (`num_ctx`) and confirms the existing cap value was approximately correct all along. The core architecture this ADR establishes — pass all chunks bounded by a single global cap, deterministic chunk ordering, no per-evaluation filtering — is unchanged and remains in force.
