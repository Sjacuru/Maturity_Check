# Retrieval query expression persisted on RetrievedChunk

`RetrievedChunk` gains a `retrieval_query: str | None = None` field. Each cascade step populates it with the exact execution-level retrieval expression used to produce that chunk.

Per cascade step:
- `filename_match` / `variant_match` — the matched document name or variant string
- `bm25` — the FTS5 OR query string produced by `build_bm25_query()`
- `regex` — the compiled regex pattern string
- `vector` — the natural-language query text passed to the embedding model

Because `RetrievedChunk` is serialized inside `EvaluationResult.raw_json`, this field becomes part of the persisted evaluation provenance with no additional storage schema change.

**Why:** Audit reconstruction is a first-class project goal. `cascade_step` and `expected_product_id` provide retrieval provenance at the strategy level (which step ran, which product drove it). They do not provide provenance at the execution level (what exact expression was evaluated). An Auditor reviewing a score must be able to verify not only that BM25 ran, but exactly what BM25 query ran. This gap was surfaced during Module 7 frontend design when the Auditor Review Interface element "Retrieval query used" could not be satisfied from existing stored fields.

**Scope:** This is a Module 3 (retrieval) + Module 6 (vector) provenance enhancement exposed by Module 7 requirements. It is not a frontend feature. Implementation is part of Module 7 backend changes alongside ADR-0044 (assessment lifecycle metadata).

**Field is nullable** to preserve backward compatibility with any stored `EvaluationResult` rows that pre-date this change. Existing rows will display `null` for retrieval query; new assessments will carry the full expression.
