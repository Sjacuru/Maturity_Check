# CONTEXT.md — MDAP Module Registry (Traveling State)

**Last updated:** 2026-05-18  
**Stage:** All 7 EPICs processed — ready for Architecture phase

---

## Pipeline Stage

Current stage: MDAP — Module Design and Action Planning ✅ COMPLETE  
Next stage: Architecture Definition

---

## MDAP Module Registry

### EPIC-001 Modules (Reference Store):
- MODULE-001-01: ReferenceDocumentIngester | Type: Infrastructure       | Domain: Reference Store
- MODULE-001-02: CrosswalkStore            | Type: Infra + Domain Logic | Domain: Reference Store
- MODULE-001-03: FrameworkQueryService     | Type: Domain Logic         | Domain: Reference Store

### EPIC-002 Modules (Case Management):
- MODULE-002-01: CaseService              | Type: Domain Logic   | Domain: Case Management
- MODULE-002-02: DocumentUploadService    | Type: Infrastructure | Domain: Case Management
- MODULE-002-03: DocumentValidator        | Type: Domain Logic   | Domain: Case Management
- MODULE-002-04: ResidencyGuard           | Type: Infrastructure | Domain: Policy Enforcement

### EPIC-003 Modules (Document Processing):
- MODULE-003-01: PDFExtractor             | Type: Infrastructure | Domain: Document Processing
- MODULE-003-02: CaseDocumentChunker      | Type: Domain Logic   | Domain: Document Processing
- MODULE-003-03: EvaluationIntentRecorder | Type: Domain Logic   | Domain: Evaluation Orchestration

### EPIC-004 Modules (Retrieval Engine):
- MODULE-004-01: ArtifactClassifier       | Type: Domain Logic   | Domain: Retrieval Engine
- MODULE-004-02: HookAssembler            | Type: Domain Logic   | Domain: Retrieval Engine
- MODULE-004-03: SparseRetriever          | Type: Infrastructure | Domain: Retrieval Engine
- MODULE-004-04: DenseRetriever           | Type: Infrastructure | Domain: Retrieval Engine
- MODULE-004-05: RRFFusion               | Type: Domain Logic   | Domain: Retrieval Engine
- MODULE-004-06: ExpansionController      | Type: Domain Logic   | Domain: Retrieval Engine
- MODULE-004-07: RetrievalAuditLogger     | Type: Infrastructure | Domain: Retrieval Engine

### EPIC-005 Modules (Evaluation Engine):
- MODULE-005-01: EvidencePacketBuilder    | Type: Domain Logic   | Domain: Evaluation Engine
- MODULE-005-02: LLMAdapter               | Type: Infrastructure | Domain: Evaluation Engine
- MODULE-005-03: SubtaskEvaluator         | Type: Domain Logic   | Domain: Evaluation Engine
- MODULE-005-04: AssurancePass            | Type: Domain Logic   | Domain: Evaluation Engine

### EPIC-006 Modules (Persistence + Reporting):
- MODULE-006-01: EvaluationPersister      | Type: Infrastructure | Domain: Persistence + Reporting
- MODULE-006-02: ScoringEngine            | Type: Domain Logic   | Domain: Persistence + Reporting
- MODULE-006-03: ReportGenerator          | Type: Domain Logic   | Domain: Persistence + Reporting
- MODULE-006-04: AnnotationService        | Type: Domain Logic   | Domain: Persistence + Reporting
- MODULE-006-05: LifecycleController      | Type: Domain Logic   | Domain: Persistence + Reporting

### EPIC-007 Modules (Review Access — Phase 2):
- MODULE-007-01: ReviewAccessController   | Type: Infrastructure | Domain: Review Access
- MODULE-007-02: SuperiorAnnotationService| Type: Domain Logic   | Domain: Review Access

**Total Modules: 28**

---

## Cross-Epic Dependency Graph

```
EPIC-001 ─────────────────────────────────────────────────────────────────────────┐
  MODULE-001-01 (data) ──────────────────────────────────────────▶ MODULE-001-03  │
  MODULE-001-02 ──────────────▶ MODULE-004-02                                      │
  MODULE-001-02 ──────────────▶ MODULE-004-06                                      │
  MODULE-001-02 ──────────────▶ MODULE-005-01                                      │
  MODULE-001-03 ──────────────▶ MODULE-003-03 (action coverage)                   │
  MODULE-001-03 ──────────────▶ MODULE-004-01 (required artifacts)                 │
  MODULE-001-03 ──────────────▶ MODULE-004-02 (subtask text)                       │
  MODULE-001-03 ──────────────▶ MODULE-005-01 (subtask text + expected output)     │
  MODULE-001-03 ──────────────▶ MODULE-006-02 (subtask count for weights)          │

EPIC-002
  MODULE-002-01 ──────────────▶ MODULE-003-03 (case existence)
  MODULE-002-04 ──────────────▶ MODULE-005-02 (residency check before LLM call)

EPIC-003
  MODULE-003-02 case_chunks ──▶ MODULE-004-03 (BM25 search)
  MODULE-003-02 case_chunks ──▶ MODULE-004-04 (vector search)
  MODULE-003-03 run record  ──▶ MODULE-006-05 (lifecycle initial state)

EPIC-004
  MODULE-004-01 ArtifactMappings ──▶ MODULE-005-01 (source documents in packet)
  MODULE-004-01 ArtifactMappings ──▶ MODULE-005-04 (MISSING_DOCUMENT check)
  MODULE-004-07 retrieval_log_id ──▶ MODULE-005-01 (audit trail link)

EPIC-005
  MODULE-005-04 AssuranceOutcome ──▶ MODULE-006-01 (persistence gate)

EPIC-006
  MODULE-006-03 report ──────────▶ MODULE-007-01 (read access wrapper)
  MODULE-006-04 annotations ─────▶ MODULE-007-02 (delegation)
```

---

## High-Risk Modules Flagged (All EPICs)

| Module | Risk | Reason |
|---|---|---|
| MODULE-001-01 | Medium | Normalizer extension required for Rio Manual and TCDF IN |
| MODULE-003-01 | High | `unstructured` + OCR on arbitrary procurement PDFs — must validate on real samples |
| MODULE-004-01 | Medium | Artifact classifier vocabulary must match real document naming conventions |
| MODULE-004-06 | Medium | Expansion budget and tier ordering require pilot calibration |
| MODULE-005-02 | High | LLM structured output reliability varies by provider — must validate on all three |
| MODULE-005-04 | Medium | CONFLICTING_INFORMATION heuristic is imprecise — Phase 2: replace with LLM judge |
| MODULE-007-01 | Medium | Phase 2 access model requires stakeholder sign-off (OQ-003) |

---

## Unresolved Assumptions (Carry Forward to Architecture)

| ID | Item | Impacts |
|---|---|---|
| A1 | [ASSUMPTION] PERSONA-002 interaction model not fully specified | EPIC-007 |
| A2 | [ASSUMPTION] FR-002 custom weight values pending external definition | EPIC-006 |
| A3 | [ASSUMPTION] NFR-007 versioning mechanism behavior-only | EPIC-001 |
| A4 | [ASSUMPTION] NFR-008 compliance regulation not named — Phase 2 legal review | EPIC-002, EPIC-005 |
| T1 | [THRESHOLD NEEDED] NFR-006 latency SLO — measure first, do not invent | EPIC-004, EPIC-005 |

---

## Implementation Status Summary

| Epic | Modules | Avg Status | Notes |
|---|---|---|---|
| EPIC-001 | 3 | ~60% | M5D path done; crosswalk store + query service interface needed |
| EPIC-002 | 4 | 0% | Not started |
| EPIC-003 | 3 | ~15% | Chunking logic exists for reference docs; case doc path not built |
| EPIC-004 | 7 | ~15% | LanceDB vector search exists; FTS5, fusion, expansion, audit log not built |
| EPIC-005 | 4 | 0% | Not started |
| EPIC-006 | 5 | 0% | Not started |
| EPIC-007 | 2 | 0% | Phase 2 — deferred by design |

**Phase 1 critical path modules (must be completed by 2026-05-29):**  
001-01, 001-02, 001-03, 002-01, 002-02, 002-03, 002-04, 003-01, 003-02, 003-03,  
004-01, 004-02, 004-03, 004-04, 004-05, 004-06, 004-07,  
005-01, 005-02, 005-03, 005-04,  
006-01, 006-02, 006-03, 006-05  
*(MODULE-006-04 annotations and MODULE-007-* deferred to Phase 2)*
