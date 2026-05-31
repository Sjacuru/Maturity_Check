# DAN-0001 — PDF Extraction and Chunking: Deferred Architecture

**Status:** Active (Phase 1 — conservative extraction strategy in place)
**Related ADR:** ADR-0011 (Phase 1 extraction strategy — page-constrained chunking)
**Last updated:** 2026-05-27

---

## Stable Directives

Do not revisit these unless a Future Trigger fires.

1. Provenance is mandatory — every Chunk carries `(document_artifact_filename, page_number)`
2. Retrieval robustness > perfect formatting reconstruction
3. Page boundaries are the primary provenance boundary in Phase 1
4. Heterogeneous PDFs are expected and normal — the system must tolerate them without failure
5. Acceptable degradation is explicitly tolerated: partial OCR, garbled tables, missing headings
6. Extraction quality should improve progressively; Phase 1 establishes the floor, not the ceiling
7. No aggressive semantic reconstruction (heading inference, section rebuilding) in Phase 1

---

## Resolved: Chunk Metadata Model

The following extraction-level metadata fields are finalized for every Chunk (domain-neutral, no Case or business identifiers):

| Field | Type | Purpose |
|---|---|---|
| `filename` | `str` | Document Artifact identity; Auditor provenance |
| `page_number` | `int` | Page provenance; Auditor traceability |
| `chunk_index` | `int` | Intra-page position; stable ordering within a page |
| `char_offset` | `int` | Character offset in page text; enables future highlighting and reconstruction |
| `text` | `str` | The extracted text content |
| `text_length` | `int` | Character count; used for near-empty chunk filtering and size debugging |
| `page_total` | `int` | Total pages in the Document Artifact; relative position context |
| `ocr_used` | `bool` | Whether OCR was applied to this chunk's source region |
| `source_type` | `str` | e.g. `"text"`, `"image"`, `"image+text"` — describes the PDF region composition |

Business-domain identifiers (`process_number`, `contract_number`) are NOT part of the Chunk. They are added by the indexing layer when Chunks are persisted to SQLite.

---

## Known Constraints

- Input is PPP procurement documents (avoid to say brazilian documents because the LLM gets some pattern data from its training data and try to create things based in this wrong knowledge): may be scanned, mixed-media, multi-volume, or inconsistently structured
- `unstructured[pdf]` is the chosen extraction library (see CLAUDE.md Tools table)
- Phase 1 scope: Ação 1 only — chunking strategy is validated against a single real Case
- Auditor interface requires `(filename, page_number)` per Chunk — provenance is a hard requirement, not a nice-to-have
- Corporate proxy environment: HuggingFace model downloads require `pip-system-certs`

---

## Deferred Complexity Areas

Known hard problems intentionally not solved in Phase 1. Each may warrant its own ADR when the time comes.

| Area | Why deferred |
|---|---|
| Semantic heading inference | Unreliable on heterogeneous PDFs without layout ML; false headings create retrieval noise |
| Layout-aware element chunking | Requires document-understanding subsystem not in Phase 1 scope |
| OCR confidence scoring | OCR is a primary pipeline stage (ADR-0012); confidence *thresholds* and quality feedback loops still need empirical calibration |
| Mixed text-image reading order | Column detection and flow reconstruction are layout-dependent |
| Table semantic reconstruction | Tables in PPP documents vary widely; Markdown reconstruction fidelity is low |
| Vector-oriented semantic chunking | Belongs to Module 6 (vector fallback); optimal chunk size differs from BM25 use case |
| Markdown fidelity reconstruction | Not required for BM25 lexical retrieval or LLM evaluation in Phase 1 |
| Layout-aware retrieval boosting | Depends on vector fallback maturity (Module 6) and structural chunk metadata |
| Extraction-level result caching | Phase 1 extraction is stateless — idempotency is the indexing layer's responsibility. Caching becomes relevant under OCR-heavy workloads, repeated evaluation runs, async pipelines, or distributed processing; not justified before those conditions emerge |

---

## Candidate Tooling Ecosystem

Research directions for future phases — not commitments.

| Tool / Approach | Use case | Earliest phase |
|---|---|---|
| `unstructured[pdf]` element mode | Element-based chunking with heading awareness | Phase 2+ |
| `pdfplumber` | Table extraction, bounding-box analysis | Phase 2+ |
| `pymupdf` (fitz) | Fast digital-text extraction, per-page images | Phase 2+ |
| Layout-ML / YOLO-based layout detection | Column and section boundary detection | Phase 3+ |
| Semantic chunking with overlap | Vector retrieval optimisation (smaller chunks) | Module 6 |

---

## Non-Goals for Phase 1

- Perfect Markdown or HTML reconstruction of document structure
- Table-to-structured-data parsing
- Section/heading-aware navigation
- Cross-page semantic continuity detection
- OCR confidence feedback loops
- Document classification by type (Estudo de Viabilidade, Contrato, Edital, etc.)

---

## Future Triggers

Events that should prompt revisiting this DAN and possibly creating a new ADR.

- Retrieval quality on a real PPP case falls below an acceptable threshold attributable to page-based chunking granularity
- First multi-column PDF where reading order is visibly broken in extracted text
- Module 6 (vector fallback) design begins — may require semantically coherent sub-page chunks
- OCR quality is so poor on a specific document type that a new extraction strategy is warranted for that type
- Heading-aware BM25 boosting is considered — requires structural chunk metadata not produced by Phase 1 extraction
