# ADR-0033 — Vector retrieval is a true fallback: runs only on zero lexical results

Vector retrieval (LanceDB + sentence-transformers) executes if and only if the lexical
cascade (BM25 + regex) returns `len(retrieved_chunks) == 0`. It is a recovery mechanism
for sparse lexical failure, not a co-equal retrieval strategy.

## Decision

- Trigger condition: `len(retrieved_chunks) == 0` after full lexical aggregation/dedup.
- No minimum chunk thresholds, score thresholds, hybrid fusion, weighted ranking, or reranking.
- Every `RetrievedChunk` carries explicit provenance: `retrieval_mode="lexical"` or
  `retrieval_mode="vector_fallback"`, enabling exact audit reconstruction.
- BM25/regex remains the architecturally primary retrieval mechanism.

## Considered Options

- **(b) Additive always** — rejected: mixes similarity spaces, undermines determinism,
  harder to explain academically.
- **(c) Threshold-gated (N chunks)** — rejected: introduces a tunable parameter that
  complicates reproducibility with no clear benefit over true fallback.

## Consequences

Future hybrid retrieval (additive, reranked, or score-fused) requires a separate ADR
and evaluation evidence before becoming default behavior. This ADR explicitly forbids
it without that gate.
