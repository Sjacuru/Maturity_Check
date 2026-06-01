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
