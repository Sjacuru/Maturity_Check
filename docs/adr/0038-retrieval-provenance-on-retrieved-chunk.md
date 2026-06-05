# ADR-0038 — Retrieval provenance is artifact-level metadata on RetrievedChunk

Each `RetrievedChunk` carries `retrieval_mode: Literal["lexical", "vector_fallback"] = "lexical"`
as a direct field. Provenance is co-located with the chunk, not returned as a separate
cascade value.

## Decision

- `RetrievedChunk` in `src/retrieval/interfaces/contracts.py` gains:
  `retrieval_mode: Literal["lexical", "vector_fallback"] = "lexical"`
- Default `"lexical"` is semantically correct for all existing chunks; no existing test
  or constructor breaks.
- Vector fallback explicitly sets `retrieval_mode="vector_fallback"` on returned chunks.
- Provenance serializes naturally into `raw_json` blobs in `evaluation_results`.
- No tuple-return provenance, external registries, or retrieval-context side channels.

## Considered Options

- **(b) Tuple return `(chunks, retrieval_mode)`** — rejected: loses per-chunk provenance;
  a single batch-level mode breaks down if mixed-mode retrieval ever appears.
- **Plain `str`** — rejected in favour of `Literal[...]` for contract explicitness and
  Pydantic validation integrity.

## Consequences

If future hybrid retrieval produces mixed retrieval sources within the same evidence set,
per-chunk provenance is already in place without contract redesign.
