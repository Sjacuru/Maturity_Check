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

That fix was miscalibrated. `ollama.py` hardcoded `num_ctx=8192` — a quarter of Mistral 7B's real native context window of 32,768 tokens. The 20,000-char cap was sized as if the usable window were far smaller than it actually is, which in turn caused legitimate evidence (1c/1d/rio_hints chunks in later Ação 1 retrieval runs) to be truncated by `_cap_evidence()` even though the corpus had room for it.

**Corrected calculation**, measured against Mistral 7B's actual 32,768-token window:
- System prompt for Ação 1, measured: 6,541 chars (~1,869 tokens at ~3.5 chars/token)
- Reserved for completion (reasoning + sentinel block): ~1,500 tokens
- Safety margin (~10%, against tokenizer-estimate error and Ollama's behavior near the `num_ctx` boundary): ~3,277 tokens
- Remaining for evidence: ~25,800 tokens ≈ ~77,000 chars at a conservative 3.0 chars/token for Portuguese (accented text tokenizes less efficiently than English)

**New values** (chosen as a clean, conservative number well under the ~77,000-char computed ceiling, rather than the precise computed value):
- `_MAX_EVIDENCE_CHARS`: 20,000 → **50,000**
- `EVIDENCE_CHAR_WARN_THRESHOLD`: 15,000 → **35,000** (keeps the same ~70% ratio to the cap)
- `ollama.py` `num_ctx`: 8192 → **32768** (same underlying bug, fixed on both sides — raising the char cap without this fix would have recreated the original incident)

This amendment changes only the numeric thresholds and the Ollama client's context-window configuration. The core architecture this ADR establishes — pass all chunks bounded by a single global cap, deterministic chunk ordering, no per-evaluation filtering — is unchanged and remains in force. A model-based relevance gate (selecting which chunks reach the LLM based on actual relevance rather than a character budget alone) is a separate, larger architectural change tracked in its own ADR.
