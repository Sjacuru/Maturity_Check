# Retrieval module returns list[RetrievedChunk] directly — no RetrievalResult wrapper

The retrieval module's read-path returns `list[RetrievedChunk]` as its public contract. A wrapper
type (`RetrievalResult`) carrying the chunk list plus cascade-level metadata was considered and
rejected. Every piece of cascade provenance that downstream modules need — which step found the
chunk, BM25 score, rank, expected product id — is carried per-chunk on `RetrievedChunk.cascade_step`
and related fields. No cascade-level aggregate information has been identified that cannot be derived
from the chunk list itself.

A wrapper would introduce a new public contract type and additional coupling between the retrieval
module and Module 4 (LLM evaluation) without a demonstrated requirement. Once Module 4 is built
against the public contract, changing it requires breaking changes. Consistent with the project's
principle of avoiding premature abstraction: introduce the wrapper only if a concrete requirement
for cascade-level aggregate metadata emerges that cannot be met per-chunk.
