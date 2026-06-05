# ADR-0034 — Vector fallback lives inside src/retrieval/, not a separate module

Vector retrieval (LanceDB + sentence-transformers) is implemented inside `src/retrieval/`
as `src/retrieval/query/vector.py`. Cascade orchestration remains in `cascade.py`.

## Decision

- No separate `configure()`, orchestration, persistence ownership, or public API surface
  for the vector concern.
- ML-heavy imports (`from sentence_transformers import SentenceTransformer`) are lazy:
  they execute only when `vector.py` is actually called (i.e., lexical cascade returned zero).
- The architectural invariant is: "retrieval owns retrieval strategies" — not a BM25
  module + a vector module as co-equal peers.

## Considered Options

- **(b) New `src/vector/` module** — rejected: premature separation of a concern that
  is currently a single subordinate step in the cascade. Would split what is
  conceptually one thing (getting chunks for an Ação) across two modules.

## Consequences

If semantic retrieval later becomes primary, independently configurable, operationally
distinct, lifecycle-heavy, or experimentally managed, a future ADR may split it into
its own subsystem. Module 6 must not preemptively encode that future architecture.
