# MDAP — EPIC-003: Text Extraction + Segmentation Foundation for Retrieval and Traceability

**Processing date:** 2026-05-18  
**Phase:** MDAP — Module Design and Action Planning  
**Source EPIC:** EPIC-003 (derived from FR-006, FR-007, NFR-005)  
**Pipeline position:** EPIC → **MDAP** → Architecture → Folder Structure

---

## GATE CHECK

| Item | Status |
|---|---|
| EPIC-003 document available | ✅ |
| 5A Phase Transition Note present | ✅ |
| Prior MDAP outputs | EPIC-001 (3 modules), EPIC-002 (4 modules) available |
| Blocking unresolved assumptions | None |
| Hard blocking dependency | EPIC-002 (documents uploaded and validated before extraction) |

---

## MODULES

---

### MODULE-003-01: PDFExtractor

| Field | Value |
|---|---|
| **Responsibility** | Converts a validated PDF into a flat list of typed, positioned text elements using the `unstructured` library with layout detection and OCR enabled; every page is OCR-processed regardless of text layer presence; returns structured elements tagged by type with source page numbers and OCR confidence scores. |
| **User Stories** | US-006 |
| **Module Type** | Infrastructure |
| **Public Interface — IN** | `extract(file_path: Path, doc_id: str) → ExtractionResult` |
| **Public Interface — OUT** | `ExtractionResult(doc_id: str, elements: list[DocumentElement], page_count: int, ocr_pages: int, duration_ms: int, warnings: list[str])` |
| | `DocumentElement(element_id: str, element_type: ElementType, text: str, page_start: int, page_end: int, ocr_confidence: float \| None, bbox: tuple \| None)` |
| | `ElementType: Enum["Title", "NarrativeText", "Table", "ListItem", "Header", "Footer", "Image", "FigureCaption", "PageBreak"]` |
| **Error Contract** | `ExtractionError(doc_id, reason)` — raised only for unrecoverable failures (corrupt PDF, zero pages) |
| | Partial failures (single-page OCR failure) → added to `warnings`, element skipped |
| **Dependencies** | `unstructured` library (`partition_pdf` with `strategy="hi_res"`, `infer_table_structure=True`, `languages=["por"]`), Tesseract OCR / PaddleOCR backend |
| **Consumed By** | MODULE-003-02 (CaseDocumentChunker), `/cases/{case_id}/documents/{doc_id}/extract` endpoint |
| **Isolation Level** | Fully independent — file path only input |
| **Parallel?** | Yes — multiple documents can be extracted concurrently |
| **Risk Level** | High — arbitrary Brazilian procurement PDF layouts; OCR quality varies; `unstructured` dependency is heavy |
| **Flag for Review** | Yes — must be validated on sample procurement documents before Phase 1 sign-off |
| **Cross-Epic Dep?** | None |

**Implementation notes:**
- `unstructured` installation: `pip install "unstructured[pdf]"` — includes Tesseract, pdfminer, detectron2 layout model
- `strategy="hi_res"` enables layout detection (column ordering, table structure); slower but correct for arbitrary layouts
- `languages=["por"]` tunes OCR tokenizer for Portuguese
- `Footer` and `Header` elements are extracted but flagged for exclusion in chunking (MODULE-003-02 filters them)
- Elements with `text.strip() == ""` are discarded before returning

---

### MODULE-003-02: CaseDocumentChunker

| Field | Value |
|---|---|
| **Responsibility** | Converts a list of `DocumentElement` objects into stable, retrievable case chunks with persistent identifiers: `Table` elements become standalone chunks; `Title` elements act as section boundaries resetting the current chunk context; `NarrativeText` and `ListItem` elements are grouped until the character cap (800 chars) with sentence-boundary adjustment; persists chunks to SQLite `case_chunks` and embeds them in LanceDB `case_chunks` table. |
| **User Stories** | US-006 |
| **Module Type** | Domain Logic |
| **Public Interface — IN** | `chunk(doc_id: str, extraction_result: ExtractionResult, max_chars: int = 800, overlap_chars: int = 150) → ChunkResult` |
| **Public Interface — OUT** | `ChunkResult(doc_id: str, chunks_created: int, lancedb_rows: int, table_chunks: int, text_chunks: int)` |
| | `CaseChunk(chunk_id: str, doc_id: str, ordinal: int, element_type: str, text: str, page_start: int, page_end: int, section_title: str \| None, text_hash: str)` |
| **Dependencies** | MODULE-003-01 output (`ExtractionResult`), SQLite `case_chunks` table, LanceDB `case_chunks` table, sentence-transformers model cache |
| **Consumed By** | MODULE-004-03 (SparseRetriever), MODULE-004-04 (DenseRetriever), `/cases/{case_id}/documents/{doc_id}/chunks` endpoint |
| **Isolation Level** | Requires MODULE-003-01 output |
| **Parallel?** | Yes — after MODULE-003-01 |
| **Risk Level** | Medium — OCR noise may cause sentence-boundary detection to fail; accepted as known Phase 1 limitation |
| **Flag for Review** | No |
| **Cross-Epic Dep?** | None |

**Chunking logic:**
```
For each element in ExtractionResult.elements:
  - If element_type == "Header" or "Footer": skip
  - If element_type == "Title": flush current buffer → new chunk; record section_title
  - If element_type == "Table": flush buffer → emit Table as standalone chunk
  - If element_type in ["NarrativeText", "ListItem"]:
      append to buffer; if buffer >= max_chars: snap to nearest sentence end, emit chunk, start new buffer with overlap
  - Other types: skip
```

**Schema — `case_chunks` table:**
```sql
chunk_id      TEXT PRIMARY KEY,
doc_id        TEXT NOT NULL REFERENCES case_documents(doc_id),
ordinal       INTEGER NOT NULL,
element_type  TEXT NOT NULL,
text          TEXT NOT NULL,
page_start    INTEGER,
page_end      INTEGER,
section_title TEXT,
text_hash     TEXT NOT NULL
```

---

### MODULE-003-03: EvaluationIntentRecorder

| Field | Value |
|---|---|
| **Responsibility** | Records the auditor's selection of an M5D action for evaluation against a case; validates that the case exists, the action is covered in the framework, and the case has at least one extracted document; creates an `evaluation_run` record in `pending` state; this is the gate that triggers the evaluation pipeline. |
| **User Stories** | US-007 |
| **Module Type** | Domain Logic |
| **Public Interface — IN** | `record(case_id: str, action_id: int) → EvaluationRun` |
| **Public Interface — OUT** | `EvaluationRun(run_id: str, case_id: str, action_id: int, status: "pending", created_at: datetime, llm_provider: str)` |
| **Error Contract** | `CaseNotFoundError(case_id)` |
| | `ActionNotFoundError(action_id)` — action not in framework coverage |
| | `NoExtractedDocumentsError(case_id)` — no chunked documents exist for this case |
| **Dependencies** | MODULE-002-01 (CaseService — case exists), MODULE-001-03 (FrameworkQueryService — action covered), SQLite `evaluation_runs` table, Config (`LLM_PROVIDER`) |
| **Consumed By** | EPIC-004 pipeline orchestrator, `/cases/{case_id}/evaluate` endpoint |
| **Isolation Level** | Requires EPIC-001 and EPIC-002 modules |
| **Parallel?** | No — must follow case creation and document extraction |
| **Risk Level** | Low |
| **Flag for Review** | No |
| **Cross-Epic Dep?** | Depends on MODULE-001-03 (EPIC-001) and MODULE-002-01 (EPIC-002) |

**Schema — `evaluation_runs` table:**
```sql
run_id        TEXT PRIMARY KEY,
case_id       TEXT NOT NULL REFERENCES cases(case_id),
action_id     INTEGER NOT NULL,
status        TEXT NOT NULL DEFAULT 'pending',
llm_provider  TEXT NOT NULL,
created_at    TEXT NOT NULL,
updated_at    TEXT NOT NULL,
completed_at  TEXT
```

---

## DEPENDENCY MAP (EPIC-003)

```
MODULE-003-01  ──▶  MODULE-003-02 (elements must exist before chunking)
MODULE-003-03  ──── independent within EPIC-003; depends on EPIC-001 + EPIC-002

Cross-Epic inputs:
  MODULE-001-03 ──▶ MODULE-003-03 (action coverage check)
  MODULE-002-01 ──▶ MODULE-003-03 (case existence check)

No circular dependencies.
Critical path: MODULE-003-01 → MODULE-003-02 → MODULE-003-03
```

---

## COVERAGE MATRIX (EPIC-003)

| User Story | Module IDs | Covered? |
|---|---|---|
| US-006 (extract + segment uploaded documents) | MODULE-003-01, MODULE-003-02 | ✅ |
| US-007 (select action for evaluation) | MODULE-003-03 | ✅ |

---

## IMPLEMENTATION STATUS

| Module | Status | Notes |
|---|---|---|
| MODULE-003-01 | 0% | Not started — `unstructured` not yet installed |
| MODULE-003-02 | ~40% | `chunking.py` has core logic (heading-based for reference docs); case document variant not yet built |
| MODULE-003-03 | 0% | Not started |

---

## OUTPUT VERIFICATION

- [x] Every module traces to EPIC-003 user stories
- [x] Every user story has module coverage
- [x] No circular dependencies
- [x] High-risk modules flagged (MODULE-003-01 — unstructured + OCR validation)
- [x] Cross-Epic dependencies documented
- [x] Minimum viable modules (3)
- [x] Public interfaces defined with error contracts
- [x] Parallel workstreams identified

---

## [CONTEXT.MD_UPDATE]

```
### EPIC-003 Modules:
- MODULE-003-01: PDFExtractor               | Type: Infrastructure | Domain: Document Processing
- MODULE-003-02: CaseDocumentChunker        | Type: Domain Logic   | Domain: Document Processing
- MODULE-003-03: EvaluationIntentRecorder   | Type: Domain Logic   | Domain: Evaluation Orchestration

### Cross-Epic Dependencies (NEW):
- MODULE-003-03 depends on MODULE-001-03 (EPIC-001 — action coverage check)
- MODULE-003-03 depends on MODULE-002-01 (EPIC-002 — case existence check)

### High-Risk Modules Flagged:
- MODULE-003-01: unstructured + OCR — must be validated on real procurement PDFs before Phase 1 sign-off

### Unresolved Assumptions Affecting EPIC-003:
- None
```
