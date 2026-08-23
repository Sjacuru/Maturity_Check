# PRD — Module 2: PDF Extraction + Chunking

**Status:** Ready for implementation
**Date:** 2026-05-27
**ADRs in scope:** 0011, 0012, 0013, 0014
**Architectural state:** DAN-0001 (`docs/dan/0001-pdf-extraction-chunking.md`)

---

## Problem Statement

Before retrieval or LLM evaluation can occur, the PPP Maturity Check System needs to convert Document Artifacts (PDF files) into structured, typed text units that carry stable provenance. PPP procurement documents are heterogeneous: some are fully scanned, some are mixed digital and image, and many have inconsistent layout or formatting. The system must extract text from all of these reliably, without failing on individual pages or documents, and without attempting semantic reconstruction that would introduce noise or instability. Every extracted unit must carry enough metadata for the Auditor to trace evidence back to a specific page of a specific Document Artifact.

---

## Solution

Build the extraction module (`src/extraction/`) as a Python package with three files: `chunk.py` (the Chunk Pydantic model), `pdf.py` (the two-stage extraction function), and `__init__.py` (sole public surface). The module exposes one function — `extract_document(path: Path) -> list[Chunk]` — which is a pure, stateless transformation. It processes each page independently: native text first, OCR as the primary fallback for insufficient pages. Page boundaries are the primary provenance boundary; large pages are split into sub-page Chunks. The module has no knowledge of Cases, process numbers, SQLite, or BM25.

---

## User Stories

### Chunk model

1. As a developer, I want to call `extract_document(path)` and receive a `list[Chunk]`, so that downstream modules have a single typed contract for extracted text without needing to know how PDFs are processed.

2. As a developer, I want `Chunk` to be a `pydantic.BaseModel` with construction-time validation, so that type mismatches from `unstructured` output are caught at extraction time rather than propagating silently across module boundaries.

3. As a developer, I want `Chunk` to carry the fields `filename`, `page_number`, `chunk_index`, `char_offset`, `text`, `text_length`, `page_total`, `ocr_used`, and `source_type`, so that every Chunk is fully self-describing with provenance and extraction metadata.

4. As a developer, I want `Chunk` to carry no business-domain identifiers (`process_number`, `contract_number`), so that the extraction module remains domain-neutral and the indexing layer is solely responsible for attaching business context when persisting to SQLite.

5. As a developer, I want `Chunk.model_dump()` to produce a flat dict that can be persisted directly to SQLite, so that the indexing layer does not need a custom serialisation step to store extracted chunks.

6. As a developer, I want `text_length` to be the character count of `text`, so that near-empty chunk filtering and size debugging can be performed without re-computing string length downstream.

7. As a developer, I want `source_type` to be a string describing the PDF region composition (`"text"`, `"image"`, `"image+text"`), so that the Auditor and downstream modules have operational provenance describing what kind of content the chunk came from.

### Two-stage extraction

8. As a developer, I want each page to attempt native text extraction first, so that digital PDF pages produce high-fidelity text without OCR overhead.

9. As a developer, I want OCR to trigger automatically when native text extraction on a page produces insufficient readable text, so that scanned pages and image-only pages yield valid Chunks rather than empty ones.

10. As a developer, I want both native-text extraction and OCR to be treated as normal operation — not as an exception handler — so that a Document Artifact composed entirely of scanned pages is processed completely rather than producing empty output.

11. As a developer, I want `ocr_used: bool` on every Chunk to accurately record whether OCR was applied to that chunk's source region, so that I can diagnose extraction quality and identify which pages in a Document Artifact relied on OCR.

### Chunking strategy

12. As a developer, I want page boundaries to be the primary provenance boundary for chunking, so that every Chunk carries a stable, auditable `(filename, page_number)` reference regardless of page content or size.

13. As a developer, I want large pages to be split into multiple sub-page Chunks (hybrid page-constrained chunking), so that oversized Chunks do not dilute BM25 signals or produce retrieval noise on dense pages such as contracts, annexes, or scanned tables.

14. As a developer, I want each sub-page Chunk to carry `chunk_index` (intra-page position, zero-based) and `char_offset` (character offset in the page text), so that the original reading order and text position within a page can always be reconstructed.

15. As a developer, I want `page_total` to be included in every Chunk, so that the relative position of any Chunk within its Document Artifact is always computable without re-reading the PDF.

### Error handling

16. As a developer, I want page-level failures (both native text and OCR stages fail for a page) to be non-fatal, so that one bad page does not abort extraction of the entire Document Artifact.

17. As a developer, I want every page-level failure to produce a structured log entry containing at minimum `filename`, `page_number`, and the error detail, so that I can identify and diagnose extraction failures without re-running the full pipeline.

18. As a developer, I want fatal errors — file not found, unreadable file, invalid PDF, unrecoverable parser failure — to terminate `extract_document()` immediately with an explicit exception, so that infrastructure problems are never silently swallowed.

19. As a developer, I want `extract_document()` to return an empty list when all pages in a Document Artifact fail non-fatally, so that the caller handles the zero-chunk case explicitly rather than receiving a partial or broken result.

### Statelessness and idempotency

20. As a developer, I want `extract_document()` to be a pure transformation — no SQLite writes, no caching, no side effects — so that the extraction module is independently testable and composable without hidden state.

21. As a developer, I want `extract_document()` to have no knowledge of `process_number`, `contract_number`, or any other business-domain identifier, so that the extraction module boundary is architecturally enforced and cannot be bypassed by passing context through the extraction layer.

22. As the indexing layer developer, I want `extract_document()` to always re-extract from the PDF file on each call, so that the indexing layer controls all deduplication decisions using `(filename, process_number)` as the idempotency key, without any conflicting state in the extraction layer.

### Storage layout

23. As an operator, I want to drop PDF files into `data/cases/{process_number}/` with arbitrary filenames, so that I can deliver documents without renaming them or knowing their semantic classification in advance.

24. As a developer, I want the extraction module to receive only a `Path` to a PDF file and remain unaware of the `data/cases/` directory convention, so that the extraction module is a pure transformation layer with no knowledge of Case identity or storage layout.

25. As the indexing layer developer, I want to decide which `Path` to pass to `extract_document()` based on the Case's `process_number` and the Document Artifact's filename, so that storage conventions are the indexing layer's responsibility and are not hardcoded into extraction.

### Downstream consumption

26. As the retrieval module developer, I want every Chunk to carry `filename` and `page_number`, so that search results can always reference the specific Document Artifact page that produced the retrieved text.

27. As the Auditor, I want every piece of evidence surfaced by the system to carry `(filename, page_number)` provenance, so that I can always locate the original page in the Document Artifact during score validation.

---

## Implementation Decisions

### Module layout

The extraction package is flat — three files, no sub-packages. OCR is a conditional stage inside the page extraction loop, not an independent subsystem. Splitting into separate files before the complexity justifies it would be speculative modularity.

Files:
- `chunk.py` — `Chunk` Pydantic model only
- `pdf.py` — `extract_document()` implementation, two-stage extraction loop
- `__init__.py` — sole public surface; re-exports `Chunk` and `extract_document`

No other files. Future phases may introduce additional files if extraction complexity genuinely fractures into independent subsystems.

### Public interface

```python
from extraction import Chunk, extract_document

extract_document(path: Path) -> list[Chunk]
```

`extract_document` is the only callable in the public interface. `Chunk` is the only type exported. No other symbols are re-exported. Downstream packages must never import from `extraction.chunk` or `extraction.pdf` directly.

### Chunk model

Nine domain-neutral fields. No business identifiers. Type shape encodes the decisions precisely:

```python
class Chunk(BaseModel):
    filename: str         # Document Artifact filename; provenance identity
    page_number: int      # Source page; primary provenance boundary
    chunk_index: int      # Intra-page position (0-based); stable ordering within a page
    char_offset: int      # Character offset in page text; enables future highlighting
    text: str             # Extracted text content
    text_length: int      # len(text); used for near-empty filtering and size debugging
    page_total: int       # Total pages in the Document Artifact
    ocr_used: bool        # Whether OCR was applied to this chunk's source region
    source_type: str      # "text" | "image" | "image+text"
```

### Chunking strategy

Hybrid page-constrained: page = provenance boundary; sub-page splits when a page exceeds a size threshold. All sub-page Chunks from a page share the same `page_number`; they differ in `chunk_index` and `char_offset`. The exact split threshold is an implementation detail — the PRD does not specify a character limit. The implementer selects a threshold appropriate for BM25 retrieval on PPP procurement documents and documents it in code.

### Two-stage extraction per page

Stage 1: native text extraction via `unstructured[pdf]`. Stage 2: OCR (Tesseract or equivalent, via `unstructured`) if Stage 1 produces insufficient readable text (threshold: implementation detail). Both paths are normal operation. `ocr_used` and `source_type` reflect which path was taken. A page that fails both stages is a non-fatal failure — structured log entry, skip page, continue.

### Error handling

**Fatal — terminate immediately with explicit exception:**
- File not found
- File unreadable (permissions, I/O error)
- Invalid or corrupt PDF (unrecoverable parser failure)

**Non-fatal — structured log entry, skip page, continue:**
- Both extraction stages fail for a page

Page-level non-fatal failures do not accumulate into a module-level failure. The caller receives whatever Chunks were successfully extracted (possibly an empty list).

### Statelessness

`extract_document()` is a pure transformation function. It has no module-level state, no cache, no singleton, and no side effects. Every call reads from the file system and returns a new `list[Chunk]`. The indexing layer handles idempotency via `(filename, process_number)` as the deduplication key. Extraction-level caching is explicitly deferred — see DAN-0001.

### Storage layout

Document Artifacts live at `data/cases/{process_number}/{filename}`. The extraction module receives only a `Path` — it is unaware of this convention. Semantic metadata (document name, classification, contract flags, user annotations) belongs to SQLite, not the filesystem.

### Extraction module boundaries

**Owns:** Chunk schema, two-stage extraction loop, page-level error handling, `ocr_used` / `source_type` metadata, chunking logic.

**Does not own:** SQLite persistence, BM25 indexing, process_number / contract_number, document classification, deduplication, extraction caching, Case identity.

---

## Testing Decisions

**What makes a good test for this module:** tests must verify external behavior observable through the public interface (`extract_document()` and the `Chunk` fields), not internal implementation stages. A test must not assert whether native text or OCR was used — it asserts what the Chunk contains. Testing that OCR triggers for a scanned page is valid (it's observable via `ocr_used`); testing that a private `_run_ocr()` method was called is not.

**What is tested:**

- **Unit tests — `Chunk` model:** Pydantic validation rules for each field; construction with valid inputs; construction failure on invalid types; `model_dump()` output shape. These tests are fast, isolated, and require no PDF files.

- **Integration tests — `extract_document()`:** Run against real fixture PDFs. Minimum two fixtures: one digital PDF (native text expected), one scanned PDF (OCR expected). Assertions: non-empty list returned; all Chunks carry correct `filename`; `page_number` values are within valid range; `chunk_index` values are contiguous within a page; `ocr_used` is `True` for at least one Chunk in the scanned fixture.

- **Slow marker:** Integration tests that trigger OCR are marked `@pytest.mark.slow`. The default test run (without `--slow`) skips OCR tests to allow fast development cycles.

**Prior art:** Module 1 (`src/ingestion/`) established the Pydantic validation test pattern. Unit tests for `Chunk` follow the same structure.

**Fixture PDF selection:** The implementer selects fixture PDFs from the real PPP case document corpus. Fixtures are committed to the test directory. A fully scanned page (no native text, OCR required) must be present in the scanned fixture to verify the OCR path.

---

## Out of Scope

- SQLite persistence of Chunks — that is the indexing layer's responsibility
- BM25 indexing or FTS5 schema — Module 3
- Process number or contract number assignment to Chunks — indexing layer
- Document name inference or semantic classification of Document Artifacts
- Extraction-level caching or deduplication — explicitly deferred in DAN-0001
- Cross-page semantic continuity detection
- Heading inference or section-aware chunking
- Table semantic reconstruction (Markdown or structured data)
- Column detection or multi-column reading order
- OCR confidence scoring or quality feedback loops
- Document classification by type (Estudo de Viabilidade, Contrato, Edital, etc.)
- Vector-oriented semantic chunking (Module 6 scope)
- Markdown or HTML reconstruction of document structure
- Anything downstream of returning `list[Chunk]`

---

## Further Notes

- **"PPP procurement documents," not "Brazilian documents":** This constraint is critical throughout all code comments, log messages, and documentation. Using "Brazilian" as a descriptor causes LLM training data contamination — the LLM will attempt to apply country-specific assumptions from its training data instead of treating the documents as the heterogeneous corpus they are. This applies equally to prompt text, variable names, and comments.

- **`unstructured[pdf]` is the chosen extraction library** — see CLAUDE.md Tools table. The extraction module must not introduce additional PDF parsing libraries in Phase 1.

- **OCR engine dependency:** `unstructured[pdf]` requires Tesseract (or equivalent). This is an accepted Phase 1 dependency. Corporate proxy environment requires `pip-system-certs` for any HuggingFace model downloads triggered by `unstructured`.

- **Phase 1 scope:** Only Ação 1 is evaluated. The extraction module is Ação-agnostic — it processes any Document Artifact path. Phase 1 validation is against a single real PPP case.

- **DAN-0001 is the living reference** for all deferred extraction complexity: heading inference, layout-aware chunking, OCR confidence scoring, table reconstruction, vector-oriented chunking, and extraction caching. When a future trigger fires, consult DAN-0001 before creating new ADRs.

- **Schema evolution:** The `Chunk` Pydantic model is expected to evolve. Field definitions are the source of truth for schema changes across modules. When fields are added, all downstream consumers (SQLite schema, BM25 indexing, LLM prompt assembly) must be updated accordingly.

- **Assumptions downstream modules must preserve:**
  1. `extract_document()` is the only entry point into the extraction module — no direct imports from `extraction.chunk` or `extraction.pdf`.
  2. `Chunk` carries no business-domain identifiers — `process_number` and `contract_number` are added by the indexing layer.
  3. `list[Chunk]` may be empty if all pages fail non-fatally — downstream must handle this case.
  4. `(filename, page_number, chunk_index)` is the stable identity of a Chunk within a Document Artifact extraction run.
  5. `ocr_used` and `source_type` are authoritative for OCR provenance — downstream must not infer these from text content.
