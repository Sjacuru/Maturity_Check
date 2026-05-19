# MDAP — EPIC-002: Case Record + Document Intake with Pre-validation and Residency Boundary

**Processing date:** 2026-05-18  
**Phase:** MDAP — Module Design and Action Planning  
**Source EPIC:** EPIC-002 (derived from FR-003, FR-004, FR-005, NFR-001, NFR-008)  
**Pipeline position:** EPIC → **MDAP** → Architecture → Folder Structure

---

## GATE CHECK

| Item | Status |
|---|---|
| EPIC-002 document available | ✅ |
| 5A Phase Transition Note present | ✅ |
| Prior MDAP outputs | MODULE-001-01, MODULE-001-02, MODULE-001-03 available |
| Blocking unresolved assumptions | ⚠️ NFR-008 compliance regulation not named (legal review pending — behavior captured, not blocked) |
| Hard blocking dependency | EPIC-001 modules must exist before case evaluation flows can reference framework |

---

## MODULES

---

### MODULE-002-01: CaseService

| Field | Value |
|---|---|
| **Responsibility** | Creates, reads, updates, and lists case records; enforces mandatory field presence (process name, institution, contract reference); generates system-unique case identifiers; rejects incomplete submissions with field-level errors. |
| **User Stories** | US-003 |
| **Module Type** | Domain Logic |
| **Public Interface — IN** | `create(process_name: str, institution: str, contract_ref: str) → CaseRecord` |
| | `get(case_id: str) → CaseRecord \| None` |
| | `list(status: str \| None = None) → list[CaseRecord]` |
| | `update_status(case_id: str, status: CaseStatus) → CaseRecord` |
| **Public Interface — OUT** | `CaseRecord(case_id: str, process_name: str, institution: str, contract_ref: str, created_at: datetime, status: CaseStatus)` |
| | `CaseStatus: Enum["created", "documents_attached", "evaluating", "paused", "completed"]` |
| **Error Contract** | `MissingFieldError(field_name: str)` when mandatory field absent |
| | `CaseNotFoundError(case_id: str)` when case_id unknown |
| **Dependencies** | SQLite `cases` table |
| **Consumed By** | MODULE-002-02, MODULE-003-03 (EvaluationIntentRecorder), EPIC-006 lifecycle, `/cases` router |
| **Isolation Level** | Fully independent |
| **Parallel?** | Yes |
| **Risk Level** | Low |
| **Flag for Review** | No |
| **Cross-Epic Dep?** | None |

**Schema — `cases` table:**
```sql
case_id       TEXT PRIMARY KEY,   -- system-generated UUID
process_name  TEXT NOT NULL,
institution   TEXT NOT NULL,
contract_ref  TEXT NOT NULL,
status        TEXT NOT NULL DEFAULT 'created',
created_at    TEXT NOT NULL,       -- ISO-8601
updated_at    TEXT NOT NULL
```

---

### MODULE-002-02: DocumentUploadService

| Field | Value |
|---|---|
| **Responsibility** | Accepts one or more PDF files for an existing case, writes them to disk under a stable path (`data/cases/{case_id}/{doc_id}_{filename}`), records file metadata per document in SQLite, returns per-file success/failure status. |
| **User Stories** | US-004 |
| **Module Type** | Infrastructure |
| **Public Interface — IN** | `upload(case_id: str, files: list[UploadFile]) → list[UploadResult]` |
| **Public Interface — OUT** | `UploadResult(doc_id: str, filename: str, status: "ok" \| "error", file_path: Path \| None, error_message: str \| None)` |
| **Error Contract** | `CaseNotFoundError(case_id)` if case does not exist |
| | Per-file errors returned in `UploadResult.error_message` (never raises; always returns list) |
| **Dependencies** | MODULE-002-01 (validate case exists), SQLite `case_documents` table, filesystem |
| **Consumed By** | MODULE-002-03 (DocumentValidator), MODULE-003-01 (PDFExtractor), `/cases/{case_id}/documents` router |
| **Isolation Level** | Requires MODULE-002-01 (case existence check) |
| **Parallel?** | Yes — after MODULE-002-01 |
| **Risk Level** | Low |
| **Flag for Review** | No |
| **Cross-Epic Dep?** | None |

**Schema — `case_documents` table:**
```sql
doc_id            TEXT PRIMARY KEY,   -- system-generated UUID
case_id           TEXT NOT NULL REFERENCES cases(case_id),
filename          TEXT NOT NULL,
file_path         TEXT NOT NULL,
file_hash         TEXT NOT NULL,      -- SHA-256 for deduplication
file_size_bytes   INTEGER,
uploaded_at       TEXT NOT NULL,
extraction_status TEXT DEFAULT 'pending',
validation_status TEXT DEFAULT 'pending',
language_detected TEXT
```

---

### MODULE-002-03: DocumentValidator

| Field | Value |
|---|---|
| **Responsibility** | Validates an uploaded document against three gates: (1) readability — PDF is parseable and yields extractable content; (2) language — dominant language is Portuguese (NFR-001); (3) plausibility — document contains procurement-domain vocabulary. Returns per-check pass/fail with reason. Does not modify documents. |
| **User Stories** | US-005 |
| **Module Type** | Domain Logic |
| **Public Interface — IN** | `validate(doc_id: str, file_path: Path) → ValidationResult` |
| **Public Interface — OUT** | `ValidationResult(doc_id, readable: bool, language_ok: bool, plausibility_ok: bool, language_detected: str \| None, details: list[str], overall_pass: bool)` |
| **Dependencies** | PyMuPDF (readability probe — text extraction attempt), `langdetect` library (language detection), vocabulary list (configurable, default: procurement Portuguese terms) |
| **Consumed By** | MODULE-002-02 post-upload trigger, `/cases/{case_id}/documents/{doc_id}/validate` endpoint |
| **Isolation Level** | Independent — file_path is the only external input |
| **Parallel?** | Yes — multiple documents can be validated concurrently |
| **Risk Level** | Medium — language detection may flag mixed-language legal documents as non-Portuguese |
| **Flag for Review** | Yes — plausibility vocabulary list must be reviewed with domain experts |
| **Cross-Epic Dep?** | None |

**Implementation notes:**
- Readability gate: attempt `PyMuPDF.open(file_path)` and check page count > 0 and total chars > 50
- Language gate: extract first 2000 chars, run `langdetect.detect()`, accept if `"pt"` or `"pt-br"`
- Plausibility gate: check for at least 2 of: `["licitação", "contrato", "edital", "proposta", "investimento", "obra", "serviço", "fornecedor", "adjudicação", "pregão"]`

---

### MODULE-002-04: ResidencyGuard

| Field | Value |
|---|---|
| **Responsibility** | Enforces that no case document content is transmitted to external services unless explicitly configured; called by the LLM Adapter before any LLM call that receives case document text; in Phase 1 (published documents only), this guard always passes; in Phase 2, checks `RESIDENCY_POLICY` config against `doc_id` publication status. |
| **User Stories** | Implicit in US-005; directly satisfies NFR-008 |
| **Module Type** | Infrastructure |
| **Public Interface — IN** | `check(doc_ids: list[str], destination: str) → ResidencyDecision` |
| **Public Interface — OUT** | `ResidencyDecision(allowed: bool, reason: str, requires_audit_log: bool)` |
| **Dependencies** | Config (`LLM_PROVIDER`, `RESIDENCY_POLICY = "published_only" \| "local_only" \| "explicit_opt_in"`), SQLite `case_documents.publication_status` (Phase 2) |
| **Consumed By** | MODULE-005-02 (LLMAdapter — called before every external LLM request) |
| **Isolation Level** | Fully independent |
| **Parallel?** | Yes |
| **Risk Level** | Low (Phase 1) / High (Phase 2 — legal compliance) |
| **Flag for Review** | Yes — Phase 2 behavior requires legal sign-off per NFR-008 |
| **Cross-Epic Dep?** | Consumed by MODULE-005-02 (EPIC-005) |

**Phase 1 behavior:** `RESIDENCY_POLICY=published_only` → `ResidencyDecision(allowed=True, reason="published documents — external transmission permitted", requires_audit_log=False)`

---

## DEPENDENCY MAP (EPIC-002)

```
MODULE-002-01 ──▶ MODULE-002-02 (case must exist before upload)
MODULE-002-02 ──▶ MODULE-002-03 (file must exist before validation)
MODULE-002-04 ──── independent (consumed by EPIC-005, not EPIC-002 modules)

No circular dependencies.
Critical path: MODULE-002-01 → MODULE-002-02 → MODULE-002-03
Parallel workstreams: MODULE-002-04 independent
```

---

## COVERAGE MATRIX (EPIC-002)

| User Story | Module IDs | Covered? |
|---|---|---|
| US-003 (create case record) | MODULE-002-01 | ✅ |
| US-004 (upload documents) | MODULE-002-02 | ✅ |
| US-005 (pre-validate documents) | MODULE-002-03 | ✅ |
| NFR-008 (residency boundary) | MODULE-002-04 | ✅ ⚠️ [ASSUMPTION — Phase 2 legal review] |

---

## IMPLEMENTATION STATUS

| Module | Status | Notes |
|---|---|---|
| MODULE-002-01 | 0% | Not started |
| MODULE-002-02 | 0% | Not started |
| MODULE-002-03 | 0% | Not started |
| MODULE-002-04 | 0% | Not started — Phase 1 implementation is trivial (always allow) |

---

## OUTPUT VERIFICATION

- [x] Every module traces to EPIC-002 user stories
- [x] Every user story has module coverage
- [x] No circular dependencies
- [x] High-risk modules flagged (MODULE-002-03 language detection, MODULE-002-04 Phase 2)
- [x] Cross-Epic dependencies documented
- [x] Minimum viable modules (4)
- [x] Public interfaces defined with error contracts
- [x] Parallel workstreams identified

---

## [CONTEXT.MD_UPDATE]

```
### EPIC-002 Modules:
- MODULE-002-01: CaseService           | Type: Domain Logic    | Domain: Case Management
- MODULE-002-02: DocumentUploadService | Type: Infrastructure  | Domain: Case Management
- MODULE-002-03: DocumentValidator     | Type: Domain Logic    | Domain: Case Management
- MODULE-002-04: ResidencyGuard        | Type: Infrastructure  | Domain: Policy Enforcement

### Cross-Epic Dependencies (NEW):
- MODULE-002-04 consumed by MODULE-005-02 (LLMAdapter — EPIC-005)

### High-Risk Modules Flagged:
- MODULE-002-03: plausibility vocabulary list requires domain expert review
- MODULE-002-04: Phase 2 legal compliance requires sign-off (NFR-008)

### Unresolved Assumptions Affecting EPIC-002:
- [ASSUMPTION] NFR-008: compliance regulation not named — Phase 1 behavior defined; Phase 2 requires legal review
```
