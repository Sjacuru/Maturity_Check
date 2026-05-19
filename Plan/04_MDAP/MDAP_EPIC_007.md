# MDAP — EPIC-007: Superior Review Access (Optional Scope)

**Processing date:** 2026-05-18  
**Phase:** MDAP — Module Design and Action Planning  
**Source EPIC:** EPIC-007 (derived from FR-020)  
**Pipeline position:** EPIC → **MDAP** → Architecture → Folder Structure

---

## GATE CHECK

| Item | Status |
|---|---|
| EPIC-007 document available | ✅ |
| 5A Phase Transition Note present | ✅ |
| Prior MDAP outputs | EPICs 001–006 (26 modules) available |
| Blocking unresolved assumptions | ⚠️ [ASSUMPTION] PERSONA-002 interaction model not fully specified |
| Hard blocking dependency | EPIC-006 reports and annotations must exist before review is meaningful |
| Phase 1 note | EPIC-007 is Phase 2 scope — modules are designed here for completeness; implementation deferred |

---

## MODULES

---

### MODULE-007-01: ReviewAccessController

| Field | Value |
|---|---|
| **Responsibility** | Controls access to reports and evaluation records for PERSONA-002 (Audit Superior); in Phase 1 — pass-through (no auth, local deployment, single user); in Phase 2 — validates access token, checks persona, enforces read-only access (no evaluation modification); exposes a middleware-compatible check that wraps EPIC-006 report endpoints. |
| **User Stories** | US-018 |
| **Module Type** | Infrastructure |
| **Public Interface — IN** | `authorize(request: Request, required_persona: str = "PERSONA-002") → AuthResult` |
| **Public Interface — OUT** | `AuthResult(authorized: bool, persona: str, reason: str)` |
| **Phase 1 behavior** | `Config(AUTH_ENABLED=False)` → always returns `AuthResult(authorized=True, persona="PERSONA-002", reason="auth disabled — local Phase 1")` |
| **Phase 2 behavior** | Token validation + persona claim verification; read-only scope enforced at route level |
| **Dependencies** | Config (`AUTH_ENABLED`), Phase 2: token validation library (TBD at Phase 2 design) |
| **Consumed By** | `/review/{case_id}/runs/{run_id}/report` endpoint, MODULE-007-02 |
| **Isolation Level** | Fully independent |
| **Parallel?** | Yes |
| **Risk Level** | Low (Phase 1) / Medium (Phase 2 — access model requires stakeholder sign-off) |
| **Flag for Review** | Yes — Phase 2 access model requires stakeholder decision per OQ-003 resolution |
| **Cross-Epic Dep?** | Wraps MODULE-006-03 (ReportGenerator) endpoints |

---

### MODULE-007-02: SuperiorAnnotationService

| Field | Value |
|---|---|
| **Responsibility** | Allows PERSONA-002 to add review annotations to reports without modifying core evaluation outputs; enforces that the caller is authorized as PERSONA-002 before delegating to MODULE-006-04 (AnnotationService) with `persona="PERSONA-002"`; the separation exists to enforce access policy and produce a distinct audit trail entry for superior annotations. |
| **User Stories** | US-018 |
| **Module Type** | Domain Logic |
| **Public Interface — IN** | `annotate(report_id: str, text: str, auth: AuthResult) → Annotation` |
| **Public Interface — OUT** | `Annotation` (from MODULE-006-04) |
| **Error Contract** | `AccessDeniedError(persona, required)` when `auth.persona != "PERSONA-002"` |
| **Dependencies** | MODULE-007-01 (ReviewAccessController — AuthResult), MODULE-006-04 (AnnotationService — annotation persistence) |
| **Consumed By** | `/review/{case_id}/runs/{run_id}/annotate` endpoint |
| **Isolation Level** | Requires MODULE-007-01 and MODULE-006-04 |
| **Parallel?** | Yes |
| **Risk Level** | Low |
| **Flag for Review** | No |
| **Cross-Epic Dep?** | Depends on MODULE-006-04 (EPIC-006), MODULE-007-01 (intra-EPIC) |

---

## DEPENDENCY MAP (EPIC-007)

```
MODULE-007-01 ──▶ MODULE-007-02 (authorization must pass before annotation)

Cross-Epic inputs:
  MODULE-006-03 ──▶ MODULE-007-01 (reports being accessed)
  MODULE-006-04 ──▶ MODULE-007-02 (annotation persistence)

No circular dependencies.
Critical path: MODULE-007-01 → MODULE-007-02
```

---

## COVERAGE MATRIX (EPIC-007)

| User Story | Module IDs | Covered? |
|---|---|---|
| US-018 (superior reads and annotates reports) | MODULE-007-01, MODULE-007-02 | ✅ ⚠️ [ASSUMPTION] interaction model not fully specified |

---

## IMPLEMENTATION STATUS

| Module | Status | Notes |
|---|---|---|
| MODULE-007-01 | 0% (deferred) | Phase 2 — stub exists in architecture as pass-through |
| MODULE-007-02 | 0% (deferred) | Phase 2 |

---

## OUTPUT VERIFICATION

- [x] Every module traces to EPIC-007 user stories
- [x] Every user story has module coverage
- [x] No circular dependencies
- [x] Phase 2 deferral documented
- [x] Phase 1 stub behavior defined (pass-through)
- [x] Cross-Epic dependencies documented
- [x] Minimum viable modules (2)
- [x] Public interfaces defined

---

## [CONTEXT.MD_UPDATE]

```
### EPIC-007 Modules:
- MODULE-007-01: ReviewAccessController      | Type: Infrastructure | Domain: Review Access (Phase 2)
- MODULE-007-02: SuperiorAnnotationService   | Type: Domain Logic   | Domain: Review Access (Phase 2)

### Cross-Epic Dependencies (NEW):
- MODULE-007-01 wraps MODULE-006-03 endpoints (EPIC-006)
- MODULE-007-02 depends on MODULE-006-04 (EPIC-006 — annotation delegation)

### High-Risk Modules Flagged:
- MODULE-007-01: Phase 2 access model requires stakeholder decision per OQ-003

### Unresolved Assumptions Affecting EPIC-007:
- [ASSUMPTION] PERSONA-002 interaction model not fully specified — constrained to read + annotation only

### Total Modules: 28
  EPIC-001: 3  |  EPIC-002: 4  |  EPIC-003: 3  |  EPIC-004: 7
  EPIC-005: 4  |  EPIC-006: 5  |  EPIC-007: 2
```

---

## 6A — PHASE TRANSITION NOTE FOR ARCHITECTURE

All 7 EPICs processed. Full module registry complete.

### All 28 Modules by Epic:

| Epic | Module | Name | Type | Domain |
|---|---|---|---|---|
| 001 | MODULE-001-01 | ReferenceDocumentIngester | Infrastructure | Reference Store |
| 001 | MODULE-001-02 | CrosswalkStore | Infra + Domain | Reference Store |
| 001 | MODULE-001-03 | FrameworkQueryService | Domain Logic | Reference Store |
| 002 | MODULE-002-01 | CaseService | Domain Logic | Case Management |
| 002 | MODULE-002-02 | DocumentUploadService | Infrastructure | Case Management |
| 002 | MODULE-002-03 | DocumentValidator | Domain Logic | Case Management |
| 002 | MODULE-002-04 | ResidencyGuard | Infrastructure | Policy Enforcement |
| 003 | MODULE-003-01 | PDFExtractor | Infrastructure | Document Processing |
| 003 | MODULE-003-02 | CaseDocumentChunker | Domain Logic | Document Processing |
| 003 | MODULE-003-03 | EvaluationIntentRecorder | Domain Logic | Evaluation Orchestration |
| 004 | MODULE-004-01 | ArtifactClassifier | Domain Logic | Retrieval Engine |
| 004 | MODULE-004-02 | HookAssembler | Domain Logic | Retrieval Engine |
| 004 | MODULE-004-03 | SparseRetriever | Infrastructure | Retrieval Engine |
| 004 | MODULE-004-04 | DenseRetriever | Infrastructure | Retrieval Engine |
| 004 | MODULE-004-05 | RRFFusion | Domain Logic | Retrieval Engine |
| 004 | MODULE-004-06 | ExpansionController | Domain Logic | Retrieval Engine |
| 004 | MODULE-004-07 | RetrievalAuditLogger | Infrastructure | Retrieval Engine |
| 005 | MODULE-005-01 | EvidencePacketBuilder | Domain Logic | Evaluation Engine |
| 005 | MODULE-005-02 | LLMAdapter | Infrastructure | Evaluation Engine |
| 005 | MODULE-005-03 | SubtaskEvaluator | Domain Logic | Evaluation Engine |
| 005 | MODULE-005-04 | AssurancePass | Domain Logic | Evaluation Engine |
| 006 | MODULE-006-01 | EvaluationPersister | Infrastructure | Persistence + Reporting |
| 006 | MODULE-006-02 | ScoringEngine | Domain Logic | Persistence + Reporting |
| 006 | MODULE-006-03 | ReportGenerator | Domain Logic | Persistence + Reporting |
| 006 | MODULE-006-04 | AnnotationService | Domain Logic | Persistence + Reporting |
| 006 | MODULE-006-05 | LifecycleController | Domain Logic | Persistence + Reporting |
| 007 | MODULE-007-01 | ReviewAccessController | Infrastructure | Review Access |
| 007 | MODULE-007-02 | SuperiorAnnotationService | Domain Logic | Review Access |

### High-Risk Modules (require expert review before implementation):
- MODULE-001-01: normalizer extension for Rio Manual and TCDF IN
- MODULE-003-01: `unstructured` OCR validation on real procurement PDFs
- MODULE-004-01: artifact classifier vocabulary validation
- MODULE-004-06: expansion budget and tier ordering — pilot required
- MODULE-005-02: LLM structured output across all three providers
- MODULE-005-04: CONFLICTING_INFORMATION heuristic — Phase 2 replace with LLM judge
- MODULE-007-01: Phase 2 access model — stakeholder sign-off required

### Unresolved Assumptions (carry forward to Architecture):
- [ASSUMPTION] NFR-007: versioning behavior-only
- [ASSUMPTION] NFR-008: Phase 2 legal review required
- [ASSUMPTION] FR-002: custom weights pending
- [ASSUMPTION] PERSONA-002 interaction model not fully specified
- [THRESHOLD NEEDED] NFR-006: latency SLO — measure first
