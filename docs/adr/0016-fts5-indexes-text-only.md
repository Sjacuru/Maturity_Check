# FTS5 virtual table indexes chunk text only, not filename

The BM25 augmented search step constructs queries from IPMP Expected Product text and Rio Manual
document names. FTS5 indexing scope determines which terms participate in BM25 ranking. We index
only the chunk `text` column. Exact document-name matching (cascade steps A and B, ADR-0015) uses
SQL `WHERE` clauses against the base `chunks` table — not FTS5.

Including `filename` in FTS5 would conflate structured document-identity matching with free-text
relevance scoring, making BM25 rank partly dependent on document naming conventions rather than
content relevance. The cascade already handles document identity through deterministic SQL; BM25
handles content relevance. Keeping them orthogonal preserves explainable, predictable ranking
behaviour and cleaner separation between the two retrieval mechanisms.

**Considered options:** index `text` + `filename` (with or without column weights). Rejected:
introduces overlap between metadata identity matching and lexical relevance scoring, blurring
retrieval responsibilities.
