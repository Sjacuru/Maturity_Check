# Phase 1 PDF extraction: provenance-first, page-constrained chunking

PPP procurement PDFs are heterogeneous — mixed text, scanned images, tables, and inconsistent layout — making reliable semantic reconstruction infeasible without a dedicated document-understanding subsystem. Phase 1 extraction uses page-constrained chunking: page boundaries are the primary provenance boundary, and every Chunk carries mandatory metadata (`document_artifact` filename + `page_number`). The pipeline prioritises robust text recovery over formatting fidelity or semantic layout reconstruction; those concerns are deferred to future phases.

## Considered Options

- **Element-based chunking** (`unstructured` elements grouped to a token limit): semantically cleaner but depends on heading inference and layout analysis that is unreliable across heterogeneous PPP PDFs.
- **Fixed-token window with overlap**: simple to implement; destroys sentence coherence and provides no stable page-level provenance.
- **Page-constrained chunking** ← chosen: guarantees stable provenance, tolerates heterogeneous input quality, simplifies debugging, and provides a sufficient BM25 retrieval surface for Phase 1, Probably the correct Phase 1 decision, considering the folowing refinement Pure “one page = one chunk”
can create: giant chunks, noisy retrieval, diluted BM25 signals. Especially: contracts, annexes, spreadsheets, scanned reports. So we would evolve it slightly with Hybrid Page-Constrained Chunking: Page remains the provenance boundary, BUT within a page:

split if page becomes too large.

Example:

Page 17
 ├── Chunk 17.1
 ├── Chunk 17.2
 └── Chunk 17.3

This preserves auditability, provenance, page reference, retrieval explainability.

While avoiding enormous lexical surfaces.

## Consequences

Every Chunk carries `(filename, page_number)` — the Auditor interface can always trace evidence to a specific page of a specific Document Artifact. Retrieval quality may be lower than element-based chunking on well-structured PDFs; this is an accepted Phase 1 trade-off documented in DAN-0001. Future phases may refine chunking granularity inside the extraction module boundary without changing its public interface.
