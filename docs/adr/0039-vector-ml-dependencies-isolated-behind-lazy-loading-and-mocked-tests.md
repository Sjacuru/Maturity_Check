# ADR-0039 — ML dependencies isolated behind lazy loading and mocked in tests

`sentence_transformers` and `lancedb` are lazily imported inside `vector.py` only when
vector fallback actually executes. Test coverage uses explicit mocking at the `vector.py`
import path; the main suite is unaware of ML infrastructure.

## Decision

- `tests/test_vector_retrieval.py` patches `sentence_transformers.SentenceTransformer`
  and `lancedb.connect` at their import path inside `vector.py`.
- Existing retrieval, assessment, and orchestration tests are never modified to
  accommodate vector infrastructure.
- Lazy-loading guarantees: importing any retrieval module, calling `configure()`, or
  running lexical-only tests never imports or initializes the ML stack.
- No embedder injection parameters, test-only production APIs, or mandatory ML fixtures
  across the suite.
- Phase 1 vector tests validate: fallback activation, vector index lifecycle, provenance
  tagging, orchestration correctness, and LanceDB interaction boundaries — not semantic
  embedding quality.

## Considered Options

- **(b) Real model in `slow` tests** — rejected: CI/CD without cached model breaks;
  test latency is unpredictable; couples test speed to ML infrastructure.
- **(c) Fixture-injected `embedder` parameter** — rejected: adds a parameter to the
  production internal API; complicates the lazy-load design for test convenience.

## Consequences

If future phases require empirical retrieval-quality benchmarking, that becomes a
dedicated evaluation suite separate from deterministic architectural regression tests.
