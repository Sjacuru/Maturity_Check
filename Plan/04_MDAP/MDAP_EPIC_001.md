# MDAP — EPIC-001: Structured M5D Framework Store (with version awareness)

**Processing date:** 2026-05-18  
**Phase:** MDAP — Module Design and Action Planning  
**Source EPIC:** EPIC-001 (derived from FR-001, NFR-005, NFR-007)  
**Pipeline position:** EPIC → **MDAP** → Architecture → Folder Structure

---

## GATE CHECK

| Item | Status |
|---|---|
| EPIC-001 document available | ✅ |
| 5A Phase Transition Note present | ✅ |
| Prior MDAP outputs | N/A — first Epic |
| Blocking unresolved assumptions | ⚠️ NFR-007 versioning mechanism (behavior-only — no design impact on modules) |

---

## MODULES

---

### MODULE-001-01: ReferenceDocumentIngester

| Field | Value |
|---|---|
| **Responsibility** | Reads a reference document (M5D, Rio Manual, TCDF IN) from a markdown file, normalizes heading hierarchy, chunks text, persists chunks to SQLite (`reference_chunks` + `reference_documents`), and embeds chunks in LanceDB. |
| **User Stories** | US-001 (framework queryable after ingest) |
| **Module Type** | Infrastructure |
| **Public Interface — IN** | `ingest(doc_id: str, file_path: Path, doc_title: str, max_chars: int = 3500, overlap: int = 350, embed: bool = True) → IngestResult` |
| **Public Interface — OUT** | `IngestResult(doc_id: str, chunks_created: int, lancedb_rows: int, duration_ms: int, warnings: list[str])` |
| **Dependencies** | `db.py` (SQLite schema), `chunking.py` (normalize + chunk), LanceDB client, sentence-transformers model cache |
| **Consumed By** | CLI ingest commands, EPIC-001 `/framework/ingest` router endpoint, MODULE-004-03, MODULE-004-04 (read chunks after ingest) |
| **Isolation Level** | Fully independent — can be tested with a temporary SQLite + LanceDB instance |
| **Parallel?** | Yes — can start without other EPIC-001 modules |
| **Risk Level** | Medium — `normalize_pdf_headings` heuristics differ per document type; Rio Manual and TCDF IN require separate normalizer paths |
| **Flag for Review** | Yes — normalizer extension for Rio Manual and TCDF IN must be validated before production ingest |
| **Cross-Epic Dep?** | None |

**Implementation notes:**
- Current `m5d_ingest.py` implements the M5D path; this module generalises it to accept any `doc_id`
- Add `doc_type` parameter (`"m5d"` | `"rio_manual"` | `"tcdf_in"`) to select the correct normalizer branch
- `IngestResult.warnings` captures heading deduplication and low-coverage actions (e.g., Ação 15)

---

### MODULE-001-02: CrosswalkStore

| Field | Value |
|---|---|
| **Responsibility** | Loads crosswalk artifact JSON files into the `crosswalk_artifacts` SQLite table and provides per-subtask queries returning `artifact_id`, `jurisdiction_layer`, `tipo`, `grau`, `intencao`, `complement_text_pt`, `expected_output_text_pt`, and `compose_order`. |
| **User Stories** | US-001 (Slice 3 — crosswalk artifacts queryable by subtask) |
| **Module Type** | Infrastructure + Domain Logic |
| **Public Interface — IN (ingest)** | `load(crosswalk_dir: Path) → CrosswalkIngestResult(artifacts_loaded: int, subtasks_covered: list[str], warnings: list[str])` |
| **Public Interface — IN (query)** | `get_artifacts(subtask_id: str) → list[CrosswalkArtifact]` |
| **Public Interface — IN (query)** | `get_complement(subtask_id: str, jurisdiction: str) → str \| None` |
| **Public Interface — OUT** | `CrosswalkArtifact(artifact_id, subtask_id, jurisdiction_layer, tipo, grau, intencao, complement_text_pt, expected_output_text_pt, compose_order)` |
| **Dependencies** | `db.py` (SQLite `crosswalk_artifacts` table), `crosswalk_extract.py` (JSON extraction from templates) |
| **Consumed By** | MODULE-004-02 (HookAssembler), MODULE-005-01 (EvidencePacketBuilder) |
| **Isolation Level** | Fully independent |
| **Parallel?** | Yes |
| **Risk Level** | Low — crosswalk data is small and static per phase |
| **Flag for Review** | No |
| **Cross-Epic Dep?** | None |

**Implementation notes:**
- Phase 1 scope: all available crosswalk mappings (Ação 1 templates + any others present in `Plan/06_Models/crosswalk/`)
- `crosswalk_artifacts` schema: `artifact_id TEXT PK, subtask_id TEXT, action_id INT, jurisdiction_layer TEXT, tipo TEXT, grau TEXT, intencao TEXT, complement_text_pt TEXT, expected_output_text_pt TEXT, compose_order INT, version TEXT`
- `version` field satisfies NFR-007 behavior intent without implementing a full versioning mechanism

---

### MODULE-001-03: FrameworkQueryService

| Field | Value |
|---|---|
| **Responsibility** | Exposes read-only queries over the ingested reference framework: get action definition by id, list subtasks for an action, list actions by stage/dimension, check coverage (which actions have chunks), return framework version label. |
| **User Stories** | US-001, US-002 |
| **Module Type** | Domain Logic |
| **Public Interface** | `get_action(action_id: int) → ActionDefinition \| None` |
| | `get_subtasks(action_id: int) → list[SubtaskDefinition]` |
| | `list_actions(stage: str \| None, dimension: str \| None) → list[ActionSummary]` |
| | `get_coverage() → dict[int, bool]` — which action_ids have chunks |
| | `get_version(doc_id: str) → str \| None` |
| **Public Interface — OUT types** | `ActionDefinition(action_id, stage, dimension, title, doc_id)` |
| | `SubtaskDefinition(subtask_id, action_id, label, text, ordinal)` |
| | `ActionSummary(action_id, stage, dimension, title, chunk_count)` |
| **Dependencies** | SQLite `reference_chunks`, `reference_documents` |
| **Consumed By** | MODULE-004-02 (HookAssembler), MODULE-005-01 (EvidencePacketBuilder), MODULE-003-03 (EvaluationIntentRecorder — validates action_id), EPIC-001 `/framework` router |
| **Isolation Level** | Fully independent — read-only over existing data |
| **Parallel?** | Yes |
| **Risk Level** | Low |
| **Flag for Review** | No |
| **Cross-Epic Dep?** | None |

---

## DEPENDENCY MAP (EPIC-001)

```
MODULE-001-01  ──(provides data)──▶  MODULE-001-03
MODULE-001-02  ──(provides data)──▶  (consumed by EPIC-004, EPIC-005)
MODULE-001-03  ──(read-only query)──▶  (consumed by EPIC-003, EPIC-004, EPIC-005)

No circular dependencies.
Critical path: MODULE-001-01 → MODULE-001-03 (data must exist before queries work)
Parallel workstreams: MODULE-001-02 can be loaded independently of MODULE-001-01
```

---

## COVERAGE MATRIX (EPIC-001)

| User Story | Module IDs | Covered? |
|---|---|---|
| US-001 (query framework by action) | MODULE-001-01, MODULE-001-03 | ✅ |
| US-001 Slice 3 (crosswalk queryable) | MODULE-001-02 | ✅ |
| US-002 (framework version on records) | MODULE-001-02 (`version` field), MODULE-001-03 (`get_version`) | ✅ ⚠️ [ASSUMPTION] |

---

## IMPLEMENTATION STATUS

| Module | Status | Notes |
|---|---|---|
| MODULE-001-01 | ~80% implemented | `m5d_ingest.py` covers M5D path; needs generalisation for Rio Manual and TCDF IN |
| MODULE-001-02 | ~20% implemented | `crosswalk_extract.py` extracts JSON; SQLite table and query interface not yet built |
| MODULE-001-03 | ~60% implemented | Queries exist in `reference_search.py`; needs clean service interface wrapping |

---

## OUTPUT VERIFICATION

- [x] Every module traces to EPIC-001 user stories
- [x] Every user story has module coverage
- [x] No circular dependencies
- [x] High-risk modules flagged (MODULE-001-01 — normalizer extension)
- [x] Cross-Epic dependencies documented
- [x] Minimum viable modules (3)
- [x] Public interfaces defined
- [x] Parallel workstreams identified

---

## [CONTEXT.MD_UPDATE]

```
### EPIC-001 Modules:
- MODULE-001-01: ReferenceDocumentIngester | Type: Infrastructure | Domain: Reference Store
- MODULE-001-02: CrosswalkStore            | Type: Infrastructure + Domain Logic | Domain: Reference Store
- MODULE-001-03: FrameworkQueryService     | Type: Domain Logic | Domain: Reference Store

### High-Risk Modules Flagged:
- MODULE-001-01: normalizer must be extended for Rio Manual and TCDF IN (review required)

### Unresolved Assumptions Affecting EPIC-001:
- [ASSUMPTION] NFR-007: versioning mechanism behavior-only — version string in crosswalk_artifacts and reference_documents, no full versioning system
```

---

## 6A (PRELIMINARY): Processing EPIC-001

All modules for Epic 1: **3 modules**  
Pending Epics 2–7: Full module registry in subsequent MDAP calls
