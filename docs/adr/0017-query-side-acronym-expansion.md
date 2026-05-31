# Acronym expansion is applied at query construction time only; indexed chunk text remains verbatim

Domain acronyms (e.g., "PPP" → "Parceria Público-Privada") create vocabulary mismatch between IPMP
query terms and case document text. We resolve this by expanding acronyms during BM25 query
construction inside `query/`, using `acronyms.json` as a text transformation on the query string.
Chunk text written to the FTS5 index remains verbatim as extracted from the document.

Index-side expansion would silently modify stored chunk text, breaking the provenance invariant:
retrieved chunks must faithfully represent source document content for Auditor review. Query-side
expansion preserves this invariant, keeps expansion logic entirely within retrieval semantics (not
indexing), and means changes to `acronyms.json` never require reindexing existing data. Acronym
handling can therefore evolve independently of storage and indexing structures.

**Considered option:** expand acronyms at index time (write expanded forms into the FTS5 table).
Rejected: couples retrieval behaviour to stored content, introduces reindexing requirements, and
compromises chunk provenance for Auditor display.
