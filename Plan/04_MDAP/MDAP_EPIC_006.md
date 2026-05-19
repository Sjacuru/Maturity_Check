# MDAP — EPIC-006: Persisted Evaluation Record, Scoring, Reporting, Review, and Lifecycle Controls

**Processing date:** 2026-05-18  
**Phase:** MDAP — Module Design and Action Planning  
**Source EPIC:** EPIC-006 (derived from FR-002, FR-013, FR-014, FR-016–019, NFR-001, NFR-003–005)  
**Pipeline position:** EPIC → **MDAP** → Architecture → Folder Structure

---

## GATE CHECK

| Item | Status |
|---|---|
| EPIC-006 document available | ✅ |
| 5A Phase Transition Note present | ✅ |
| Prior MDAP outputs | EPICs 001–005 (21 modules) available |
| Blocking unresolved assumptions | ⚠️ [ASSUMPTION] FR-002 custom weights pending — equal distribution default |
| Hard blocking dependency | EPIC-005 assurance-reviewed outputs must exist before persistence |

---

## MODULES

---

### MODULE-006-01: EvaluationPersister

| Field | Value |
|---|---|
| **Responsibility** | Persists assurance-reviewed `EvaluationResult` records to SQLite with full traceability links (segment chunk_ids, crosswalk artifact_ids, retrieval_log_id, assurance_outcome_id); enforces the persistence gate — storage occurs only after `AssuranceOutcome.passed == True` or an explicit auditor override is recorded; returns a stable `result_id`. |
| **User Stories** | US-014 |
| **Module Type** | Infrastructure |
| **Public Interface — IN** | `persist(run_id: str, result: EvaluationResult, assurance: AssuranceOutcome, override: AuditorOverride \| None = None) → str` (returns `result_id`) |
| **Public Interface — IN types** | `AuditorOverride(auditor_id: str, reason: str, timestamp: datetime)` |
| **Public Interface — OUT** | `result_id: str` |
| **Error Contract** | `PersistenceGateError(subtask_id, flags)` when `assurance.passed == False` and no override provided |
| **Dependencies** | MODULE-005-04 (AssuranceOutcome gate), SQLite `subtask_results` table |
| **Consumed By** | MODULE-006-02 (ScoringEngine), MODULE-006-03 (ReportGenerator), MODULE-006-04 (AnnotationService) |
| **Isolation Level** | Requires AssuranceOutcome — cannot persist without it |
| **Parallel?** | No — sequential after MODULE-005-04 |
| **Risk Level** | Low |
| **Flag for Review** | No |
| **Cross-Epic Dep?** | Depends on MODULE-005-04 (EPIC-005) |

**Schema — `subtask_results` table:**
```sql
result_id         TEXT PRIMARY KEY,
run_id            TEXT NOT NULL REFERENCES evaluation_runs(run_id),
subtask_id        TEXT NOT NULL,
presence          TEXT NOT NULL,        -- "present" | "partial" | "absent"
confidence        REAL NOT NULL,
quality           TEXT,                 -- "adequate" | "inadequate" | NULL
reasoning         TEXT NOT NULL,
source_docs_json  TEXT NOT NULL,        -- JSON list of SourceDocument
evidence_json     TEXT NOT NULL,        -- JSON list of EvidenceRef
flags_json        TEXT NOT NULL,        -- JSON list of Flag
retrieval_log_id  TEXT NOT NULL,
assurance_passed  INTEGER NOT NULL,     -- 0 | 1
override_json     TEXT,                 -- NULL or AuditorOverride JSON
created_at        TEXT NOT NULL
```

---

### MODULE-006-02: ScoringEngine

| Field | Value |
|---|---|
| **Responsibility** | Computes the action score from persisted, assurance-reviewed subtask results using the FR-013 formula verbatim: sub-task presence (40 pts × weights) + sub-task quality (20 pts) + expected output presence (20 pts) + expected output quality (20 pts) = 100 pts total; applies 1/N default weights when custom weights absent; persists the score to `action_scores` table. |
| **User Stories** | US-015 |
| **Module Type** | Domain Logic |
| **Public Interface — IN** | `compute(run_id: str, action_id: int, custom_weights: dict[str, float] \| None = None) → ActionScore` |
| **Public Interface — OUT** | `ActionScore(score_id: str, run_id: str, action_id: int, total: float, presence_component: float, quality_component: float, eo_presence_component: float, eo_quality_component: float, weights_used: dict[str, float], computed_at: datetime)` |
| **Error Contract** | `IncompleteEvaluationError(run_id, missing_subtasks)` when not all subtasks have persisted results |
| | `WeightSumError(weights)` when provided custom_weights do not sum to 1.0 |
| **Dependencies** | SQLite `subtask_results` (reads persisted, assurance-reviewed records), MODULE-001-03 (FrameworkQueryService — N subtasks per action) |
| **Consumed By** | MODULE-006-03 (ReportGenerator) |
| **Isolation Level** | Requires all subtask_results for the run to be persisted |
| **Parallel?** | No — runs after all subtask results are persisted |
| **Risk Level** | Low |
| **Flag for Review** | No |
| **Cross-Epic Dep?** | Depends on MODULE-001-03 (EPIC-001 — subtask count) |

**FR-013 formula (verbatim — do not approximate):**
```
presence_component  = 40 × Σ(weight_i × presence_score_i)   # presence_score: 1.0=present, 0.5=partial, 0=absent
quality_component   = 20 × Σ(weight_i × quality_score_i)    # quality_score:  1.0=adequate, 0.5=inadequate, 0=absent
eo_presence_component = 20 × eo_presence_score               # expected output aggregate
eo_quality_component  = 20 × eo_quality_score
total = presence_component + quality_component + eo_presence_component + eo_quality_component  # max = 100
```

**Schema — `action_scores` table:**
```sql
score_id              TEXT PRIMARY KEY,
run_id                TEXT NOT NULL REFERENCES evaluation_runs(run_id),
action_id             INTEGER NOT NULL,
total                 REAL NOT NULL,
presence_component    REAL NOT NULL,
quality_component     REAL NOT NULL,
eo_presence_component REAL NOT NULL,
eo_quality_component  REAL NOT NULL,
weights_json          TEXT NOT NULL,
computed_at           TEXT NOT NULL
```

---

### MODULE-006-03: ReportGenerator

| Field | Value |
|---|---|
| **Responsibility** | Produces the action-level evaluation report from persisted records: JSON structure (factual section — scores, flags, citations, evidence refs) plus a pre-rendered Markdown summary string in Portuguese (narrative section — reasoning summaries, flag explanations, annotation context); separates facts from narrative per NFR-004; all output text in Portuguese per NFR-001. |
| **User Stories** | US-016 |
| **Module Type** | Domain Logic |
| **Public Interface — IN** | `generate(run_id: str) → EvaluationReport` |
| **Public Interface — OUT** | `EvaluationReport(run_id: str, action_id: int, json_data: dict, markdown_summary: str, generated_at: datetime)` |
| **json_data structure** | `{run_id, action_id, score: ActionScore, subtasks: list[SubtaskReportRow], flags: list[Flag], annotations: list[Annotation], evidence_map: dict[chunk_id → EvidenceRef]}` |
| **markdown_summary structure** | Header + score table + per-subtask presence/quality/reasoning + flags section + annotations section — all in Portuguese |
| **Dependencies** | MODULE-006-01 (persisted subtask_results), MODULE-006-02 (ActionScore), MODULE-006-04 (Annotations) |
| **Consumed By** | `/cases/{case_id}/runs/{run_id}/report` endpoint (GET), EPIC-007 (ReviewAccessController) |
| **Isolation Level** | Requires all prior persistence modules |
| **Parallel?** | No — runs after scoring |
| **Risk Level** | Low |
| **Flag for Review** | No |
| **Cross-Epic Dep?** | Report consumed by MODULE-007-01 (EPIC-007) |

---

### MODULE-006-04: AnnotationService

| Field | Value |
|---|---|
| **Responsibility** | Attaches auditor annotations to persisted evaluation targets (subtask result, expected output result, or full evaluation run); stores author persona (`PERSONA-001` or `PERSONA-002`), free text, and timestamp; returns `annotation_id`; annotations appear in reports without altering core evaluation outputs. |
| **User Stories** | US-016 (annotations in report), US-018 (superior annotations) |
| **Module Type** | Domain Logic |
| **Public Interface — IN** | `annotate(target_type: str, target_id: str, persona: str, text: str) → Annotation` |
| | `get_annotations(target_type: str, target_id: str) → list[Annotation]` |
| **Public Interface — OUT** | `Annotation(annotation_id: str, target_type: str, target_id: str, persona: str, text: str, created_at: datetime)` |
| | `target_type: "subtask_result" \| "run"` |
| **Dependencies** | SQLite `annotations` table |
| **Consumed By** | MODULE-006-03 (ReportGenerator), MODULE-007-02 (SuperiorAnnotationService — delegates here) |
| **Isolation Level** | Fully independent |
| **Parallel?** | Yes |
| **Risk Level** | Low |
| **Flag for Review** | No |
| **Cross-Epic Dep?** | Consumed by MODULE-007-02 (EPIC-007) |

**Schema — `annotations` table:**
```sql
annotation_id TEXT PRIMARY KEY,
target_type   TEXT NOT NULL,
target_id     TEXT NOT NULL,
persona       TEXT NOT NULL,
text          TEXT NOT NULL,
created_at    TEXT NOT NULL
```

---

### MODULE-006-05: LifecycleController

| Field | Value |
|---|---|
| **Responsibility** | Manages evaluation run state machine transitions (`pending → running → paused → completed \| failed`); handles pause/resume with full state preservation; triggers re-runs by creating new `evaluation_run` records linked to the same case and action while keeping the original run intact; prevents conflicting concurrent runs on the same case + action pair. |
| **User Stories** | US-017 |
| **Module Type** | Domain Logic |
| **Public Interface — IN** | `transition(run_id: str, event: LifecycleEvent) → EvaluationRun` |
| | `rerun(run_id: str) → EvaluationRun` (creates new run, does not modify original) |
| | `get_status(run_id: str) → EvaluationRun` |
| **Public Interface — IN types** | `LifecycleEvent: Enum["start", "pause", "resume", "complete", "fail"]` |
| **Error Contract** | `InvalidTransitionError(run_id, current_state, event)` for illegal state transitions |
| | `ConcurrentRunError(case_id, action_id)` if an active run already exists |
| **Dependencies** | SQLite `evaluation_runs`, MODULE-003-03 (EvaluationIntentRecorder — creates initial run record) |
| **Consumed By** | EPIC-004/005/006 pipeline orchestrator, `/cases/{case_id}/runs/{run_id}/lifecycle` endpoint |
| **Isolation Level** | Requires existing evaluation_run record |
| **Parallel?** | No — state transitions are sequential |
| **Risk Level** | Low |
| **Flag for Review** | No |
| **Cross-Epic Dep?** | Depends on MODULE-003-03 (EPIC-003) |

**State machine:**
```
pending ──start──▶ running ──pause──▶ paused ──resume──▶ running
running ──complete──▶ completed
running ──fail──▶ failed
rerun: completed/failed ──▶ creates new run in pending state; original unchanged
```

---

## DEPENDENCY MAP (EPIC-006)

```
MODULE-006-01 ──▶ MODULE-006-02 (scores computed after persistence)
MODULE-006-02 ──▶ MODULE-006-03 (score included in report)
MODULE-006-04 ──▶ MODULE-006-03 (annotations included in report)
MODULE-006-05 ──── independent within EPIC-006

Cross-Epic inputs:
  MODULE-005-04 (AssuranceOutcome) ──▶ MODULE-006-01
  MODULE-001-03 ──▶ MODULE-006-02 (subtask count for weights)
  MODULE-003-03 ──▶ MODULE-006-05 (initial run record)

Cross-Epic outputs:
  MODULE-006-03 report ──▶ MODULE-007-01 (EPIC-007)
  MODULE-006-04 AnnotationService ──▶ MODULE-007-02 (EPIC-007)

No circular dependencies.
Critical path: 001 → 002 → 003
Parallel: MODULE-006-04 and MODULE-006-05 are independent
```

---

## COVERAGE MATRIX (EPIC-006)

| User Story | Module IDs | Covered? |
|---|---|---|
| US-014 (persist evaluation record with traceable evidence) | MODULE-006-01 | ✅ |
| US-015 (compute action score with weights) | MODULE-006-02 | ✅ ⚠️ [ASSUMPTION] custom weights pending |
| US-016 (produce explainable report) | MODULE-006-03, MODULE-006-04 | ✅ |
| US-017 (re-run + pause/resume lifecycle) | MODULE-006-05 | ✅ |

---

## IMPLEMENTATION STATUS

| Module | Status | Notes |
|---|---|---|
| MODULE-006-01 | 0% | Not started |
| MODULE-006-02 | 0% | Not started |
| MODULE-006-03 | 0% | Not started |
| MODULE-006-04 | 0% | Not started |
| MODULE-006-05 | 0% | Not started |

---

## OUTPUT VERIFICATION

- [x] Every module traces to EPIC-006 user stories
- [x] Every user story has module coverage
- [x] No circular dependencies
- [x] FR-013 formula carried verbatim per MDAP inheritance note
- [x] Cross-Epic dependencies documented
- [x] Minimum viable modules (5)
- [x] Public interfaces defined with schemas
- [x] Parallel workstreams identified

---

## [CONTEXT.MD_UPDATE]

```
### EPIC-006 Modules:
- MODULE-006-01: EvaluationPersister  | Type: Infrastructure | Domain: Persistence + Reporting
- MODULE-006-02: ScoringEngine        | Type: Domain Logic   | Domain: Persistence + Reporting
- MODULE-006-03: ReportGenerator      | Type: Domain Logic   | Domain: Persistence + Reporting
- MODULE-006-04: AnnotationService    | Type: Domain Logic   | Domain: Persistence + Reporting
- MODULE-006-05: LifecycleController  | Type: Domain Logic   | Domain: Persistence + Reporting

### Cross-Epic Dependencies (NEW):
- MODULE-006-01 depends on MODULE-005-04 (EPIC-005 — AssuranceOutcome gate)
- MODULE-006-02 depends on MODULE-001-03 (EPIC-001 — subtask count)
- MODULE-006-05 depends on MODULE-003-03 (EPIC-003 — initial run record)
- MODULE-006-03 report consumed by MODULE-007-01 (EPIC-007)
- MODULE-006-04 consumed by MODULE-007-02 (EPIC-007)

### High-Risk Modules Flagged:
- None in EPIC-006

### Unresolved Assumptions Affecting EPIC-006:
- [ASSUMPTION] FR-002: custom sub-task weights pending external definition — default 1/N
```
