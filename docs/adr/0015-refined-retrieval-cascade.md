# Refined retrieval cascade: document-identity first, corpus-wide BM25 + regex as fallback

ADR-0006 established a three-step cascade (exact name → BM25 → vector). Operational experience with
Rio PPP case documents shows that document identity and content relevance are fundamentally different
retrieval problems requiring separate treatment. We refine the cascade into two paths: (A) filename
match against Rio Manual `document_names`, (B) exact normalised content match against Rio Manual
`document_names` and their `regex_variants` — if either succeeds, the full candidate document
becomes the evidence package and corpus-wide BM25 is skipped. (C) token-overlap matching is a soft
hint only and does not establish document identity or restrict retrieval scope. If neither A nor B
identifies a document, retrieval falls back to corpus-wide BM25 (one query per letter-suffixed
Expected Product) with parallel corpus-wide regex (ADR-0007 identifiers) running independently.
Corpus-wide regex hits that fall outside the BM25 top-k are included in the result set with
`cascade_step = "regex"`.

**Considered options:** BM25-only (no document-identity step), document-identity as a pre-filter
on BM25 results. Both rejected: BM25 alone drops exact-name evidence when document naming is
inconsistent; pre-filtering BM25 results risks missing law-number evidence not ranked in top-k.

**Consequences:** Two distinct retrieval paths with different evidence-package shapes — document-
focused (all chunks from identified document) vs. BM25-ranked (top-k chunks by term relevance).
`RetrievedChunk.cascade_step` distinguishes `"filename_match"`, `"variant_match"`, `"bm25"`, and
`"regex"`. Dense vector fallback (ADR-0006 step 3) remains in scope for Phase 2.
