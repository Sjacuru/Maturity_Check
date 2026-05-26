# MDAP — EPIC-004: Retrieval Policy + Hybrid Retrieval with Deterministic Fusion and Audit Logs

**Processing date:** 2026-05-18  
**Phase:** MDAP — Module Design and Action Planning  
**Source EPIC:** EPIC-004 (derived from FR-008, FR-008A–D, FR-014A, NFR-005, NFR-006, NFR-008)  
**Pipeline position:** EPIC → **MDAP** → Architecture → Folder Structure

---

## GATE CHECK

| Item | Status |
|---|---|
| EPIC-004 document available | ✅ |
| 5A Phase Transition Note present | ✅ |
| Prior MDAP outputs | EPICs 001–003 (10 modules) available |
| Blocking unresolved assumptions | ⚠️ [THRESHOLD NEEDED] OQ-004 / NFR-006 — latency SLO deferred; record measurements, do not invent targets |
| Hard blocking dependency | EPIC-003 segments must exist before retrieval can run |

---

## MODULES

---

### MODULE-004-01: ArtifactClassifier

| Field | Value |
|---|---|
| **Responsibility** | Identifies which uploaded case documents correspond to each required artifact for the selected M5D action using three escalating methods: (1) exact filename match against known artifact names, (2) approximate title match using heading text, (3) semantic content match using dense vector similarity; records the classification method used per decision; raises MISSING_DOCUMENT signal if no match found after all three methods. |
| **User Stories** | US-008 |
| **Module Type** | Domain Logic |
| **Public Interface — IN** | `classify(run_id: str, action_id: int, case_doc_ids: list[str]) → ClassificationResult` |
| **Public Interface — OUT** | `ClassificationResult(run_id, mappings: list[ArtifactMapping], unmatched_artifacts: list[str])` |
| | `ArtifactMapping(artifact_id: str, doc_id: str \| None, method: "exact_name" \| "approx_title" \| "semantic" \| "not_found", confidence: float)` |
| **Dependencies** | MODULE-001-03 (FrameworkQueryService — required artifact list), MODULE-004-04 (DenseRetriever — semantic match), SQLite `case_documents` |
| **Consumed By** | MODULE-004-02 (HookAssembler — needs confirmed artifact set), MODULE-005-04 (AssurancePass — unmatched artifacts trigger MISSING_DOCUMENT flag) |
| **Isolation Level** | Requires MODULE-001-03 and MODULE-004-04 |
| **Parallel?** | Yes — after EPIC-003 extraction and MODULE-004-04 is available |
| **Risk Level** | Medium — semantic match accuracy depends on embedding quality and document naming conventions |
| **Flag for Review** | Yes — artifact name vocabulary must be validated against real procurement documents |
| **Cross-Epic Dep?** | Depends on MODULE-001-03 (EPIC-001); Depends on MODULE-004-04 (intra-EPIC — circular risk: see note) |

**Note on MODULE-004-04 dependency:** ArtifactClassifier calls DenseRetriever only for semantic classification (method 3). MODULE-004-04 is a pure infrastructure module with no dependency on MODULE-004-01. No circular dependency.

---

### MODULE-004-02: HookAssembler

| Field | Value |
|---|---|
| **Responsibility** | Assembles the pooled retrieval hook list for one subtask from crosswalk `intencao` texts across all jurisdiction layers (Rio Manual + TCDF IN) in `compose_order`, plus the M5D subtask text itself as an additional hook; deduplicates semantically near-identical hooks; returns an ordered, annotated hook list ready for retrieval. |
| **User Stories** | US-009 |
| **Module Type** | Domain Logic |
| **Public Interface — IN** | `assemble(subtask_id: str) → HookList` |
| **Public Interface — OUT** | `HookList(subtask_id: str, hooks: list[RetrievalHook])` |
| | `RetrievalHook(text: str, source: str, tipo: str, grau: str, compose_order: int)` |
| **Dependencies** | MODULE-001-02 (CrosswalkStore — `get_artifacts(subtask_id)`), MODULE-001-03 (FrameworkQueryService — subtask text) |
| **Consumed By** | MODULE-004-03 (SparseRetriever), MODULE-004-04 (DenseRetriever), MODULE-004-07 (RetrievalAuditLogger) |
| **Isolation Level** | Requires MODULE-001-02 and MODULE-001-03 |
| **Parallel?** | Yes — per subtask, all can run concurrently |
| **Risk Level** | Low |
| **Flag for Review** | No |
| **Cross-Epic Dep?** | Depends on MODULE-001-02 and MODULE-001-03 (EPIC-001) |

---

### MODULE-004-03: SparseRetriever

| Field | Value |
|---|---|
| **Responsibility** | Executes BM25 keyword search over case document chunks using SQLite FTS5; accepts a list of query strings (hooks) and a `case_id` filter; unions results across all hooks; returns deduplicated ranked list of `ScoredChunk` objects sorted by BM25 score descending. |
| **User Stories** | US-009 |
| **Module Type** | Infrastructure |
| **Public Interface — IN** | `search(queries: list[str], case_id: str, limit: int = 50) → list[ScoredChunk]` |
| **Public Interface — OUT** | `ScoredChunk(chunk_id: str, doc_id: str, text: str, page_start: int, page_end: int, score: float, rank: int)` |
| **Dependencies** | SQLite FTS5 virtual table `case_chunks_fts` (mirrors `case_chunks.text`) |
| **Consumed By** | MODULE-004-05 (RRFFusion) |
| **Isolation Level** | Fully independent — pure SQLite query |
| **Parallel?** | Yes — runs concurrently with MODULE-004-04 |
| **Risk Level** | Low |
| **Flag for Review** | No |
| **Cross-Epic Dep?** | None |

**FTS5 setup:**
```sql
CREATE VIRTUAL TABLE case_chunks_fts USING fts5(
  chunk_id UNINDEXED,
  doc_id UNINDEXED,
  text,
  content='case_chunks',
  content_rowid='rowid',
  tokenize='unicode61 remove_diacritics 2'
);
```
`remove_diacritics 2` normalises accented Portuguese characters (ã, ç, é → a, c, e) for fuzzy matching.

---

### MODULE-004-04: DenseRetriever

| Field | Value |
|---|---|
| **Responsibility** | Executes semantic vector search over case document chunks via LanceDB; encodes query strings with the local sentence-transformer model singleton (`paraphrase-multilingual-MiniLM-L12-v2`); accepts a list of queries and a `case_id` filter; unions results across all query vectors; returns deduplicated ranked list sorted by L2 distance ascending. |
| **User Stories** | US-009 |
| **Module Type** | Infrastructure |
| **Public Interface — IN** | `search(queries: list[str], case_id: str, limit: int = 50) → list[ScoredChunk]` |
| **Public Interface — OUT** | `ScoredChunk(chunk_id: str, doc_id: str, text: str, page_start: int, page_end: int, score: float, rank: int)` |
| **Dependencies** | LanceDB `case_chunks` table, sentence-transformers model cache (`_MODEL_CACHE` singleton in `reference_search.py`) |
| **Consumed By** | MODULE-004-01 (ArtifactClassifier — semantic match), MODULE-004-05 (RRFFusion) |
| **Isolation Level** | Fully independent |
| **Parallel?** | Yes — runs concurrently with MODULE-004-03 |
| **Risk Level** | Low |
| **Flag for Review** | No |
| **Cross-Epic Dep?** | None |

---

### MODULE-004-05: RRFFusion

| Field | Value |
|---|---|
| **Responsibility** | Merges sparse (BM25) and dense (vector) result lists using Reciprocal Rank Fusion with formula `score = Σ 1/(k + rank_i)` where `k=60` by default (configurable); joins on `chunk_id`; preserves both component ranks in output for audit logging; produces a single deterministic fused ranking. The fusion formula and constants are fixed per run and do not change implicitly. |
| **User Stories** | US-009 |
| **Module Type** | Domain Logic |
| **Public Interface — IN** | `fuse(sparse: list[ScoredChunk], dense: list[ScoredChunk], k: int = 60, limit: int = 20) → list[FusedChunk]` |
| **Public Interface — OUT** | `FusedChunk(chunk_id: str, doc_id: str, text: str, page_start: int, page_end: int, fused_score: float, sparse_rank: int \| None, dense_rank: int \| None)` |
| **Dependencies** | None — pure computation |
| **Consumed By** | MODULE-004-06 (ExpansionController), MODULE-004-07 (RetrievalAuditLogger), MODULE-005-01 (EvidencePacketBuilder) |
| **Isolation Level** | Fully independent — no I/O |
| **Parallel?** | No — requires both MODULE-004-03 and MODULE-004-04 output |
| **Risk Level** | Low |
| **Flag for Review** | No |
| **Cross-Epic Dep?** | None |

---

### MODULE-004-06: ExpansionController

| Field | Value |
|---|---|
| **Responsibility** | Decides whether retrieval should stop (satisficing) or continue to the next tier (expansion) for a given subtask; satisficing fires when `tipo=Direta AND grau=Alto AND confidence >= 0.90` (FR-008B resolved constant); expansion follows tier order `Direta → Indireta → Contextual` and `Alto → Médio → Baixo` within each tipo (FR-008C); records stop/continue reason per decision; operates within a configurable budget (max tiers, max total chunks). |
| **User Stories** | US-010 |
| **Module Type** | Domain Logic |
| **Public Interface — IN** | `evaluate(fused_chunks: list[FusedChunk], crosswalk: list[CrosswalkArtifact], current_tier: TierSpec, budget: ExpansionBudget) → ExpansionDecision` |
| **Public Interface — OUT** | `ExpansionDecision(stop: bool, reason: str, next_tier: TierSpec \| None, satisficing_triggered: bool)` |
| | `TierSpec(tipo: str, grau: str)` |
| | `ExpansionBudget(max_tiers: int = 3, max_total_chunks: int = 100)` |
| **Dependencies** | MODULE-001-02 (CrosswalkStore — artifact tipo/grau), MODULE-004-05 output |
| **Consumed By** | Retrieval orchestrator (pipeline coordinator in EPIC-004 router) |
| **Isolation Level** | Requires crosswalk data and fused results |
| **Parallel?** | No — sequential decision per tier |
| **Risk Level** | Medium — pilot-calibrated values (`retrieval_floor_stage2`, hit/weak/none cutoffs) are deferred; do not invent |
| **Flag for Review** | Yes — expansion budget and tier ordering must be validated in pilot |
| **Cross-Epic Dep?** | Depends on MODULE-001-02 (EPIC-001) |

**Resolved constants (not pilot-calibrated):**
- Satisficing threshold: `confidence >= 0.90` (FR-008B + OQ-006)
- UNCERTAINTY flag: `confidence < 0.70` (OQ-006)

**Deferred (pilot calibration):**
- `retrieval_floor_stage2` initial band `0.35–0.50`
- hit / weak / none disposition cutoffs

---

### MODULE-004-07: RetrievalAuditLogger

| Field | Value |
|---|---|
| **Responsibility** | Persists a complete, replayable retrieval decision log for one subtask run: hook list, sparse results, dense results, fusion inputs and outputs, expansion decisions, and final fused list; assigns a stable `retrieval_log_id` returned to callers for evidence traceability. |
| **User Stories** | US-009 (audit trail), US-010 (expansion log) |
| **Module Type** | Infrastructure |
| **Public Interface — IN** | `log(run_id: str, subtask_id: str, hooks: HookList, sparse: list[ScoredChunk], dense: list[ScoredChunk], fused: list[FusedChunk], expansion_decisions: list[ExpansionDecision]) → str` (returns `retrieval_log_id`) |
| **Public Interface — OUT** | `retrieval_log_id: str` |
| **Dependencies** | SQLite `retrieval_logs` table |
| **Consumed By** | MODULE-005-01 (EvidencePacketBuilder — `retrieval_log_id` goes into evidence packet) |
| **Isolation Level** | Fully independent |
| **Parallel?** | No — logs after retrieval completes |
| **Risk Level** | Low |
| **Flag for Review** | No |
| **Cross-Epic Dep?** | retrieval_log_id consumed by MODULE-005-01 (EPIC-005) |

**Schema — `retrieval_logs` table:**
```sql
log_id              TEXT PRIMARY KEY,
run_id              TEXT NOT NULL REFERENCES evaluation_runs(run_id),
subtask_id          TEXT NOT NULL,
hooks_json          TEXT NOT NULL,   -- JSON serialisation of HookList
sparse_results_json TEXT NOT NULL,
dense_results_json  TEXT NOT NULL,
fused_results_json  TEXT NOT NULL,
expansion_json      TEXT NOT NULL,
created_at          TEXT NOT NULL
```

---

## DEPENDENCY MAP (EPIC-004)

```
MODULE-004-02 ──▶ MODULE-004-03 (hooks needed for BM25 queries)
MODULE-004-02 ──▶ MODULE-004-04 (hooks needed for vector queries)
MODULE-004-03 ──┐
                ├──▶ MODULE-004-05 (both needed for fusion)
MODULE-004-04 ──┘
MODULE-004-05 ──▶ MODULE-004-06 (fused list needed for expansion decision)
MODULE-004-05 ──▶ MODULE-004-07 (fused list logged)
MODULE-004-01 ──── (runs before hook assembly; independent of 02–07)

Cross-Epic inputs:
  MODULE-001-02 ──▶ MODULE-004-02, MODULE-004-06
  MODULE-001-03 ──▶ MODULE-004-01, MODULE-004-02
  MODULE-003-02 ──▶ MODULE-004-03, MODULE-004-04 (case_chunks must exist)

No circular dependencies.
Critical path: 002 → 003+004 (parallel) → 005 → 006 → 007
Parallel workstreams: MODULE-004-03 and MODULE-004-04 run concurrently
                      MODULE-004-01 runs before 002 (independently)
```

---

## COVERAGE MATRIX (EPIC-004)

| User Story | Module IDs | Covered? |
|---|---|---|
| US-008 (identify artifacts) | MODULE-004-01 | ✅ |
| US-009 (retrieve evidence with pooled hooks + hybrid fusion) | MODULE-004-02, 03, 04, 05, 07 | ✅ |
| US-010 (satisficing + tiered expansion) | MODULE-004-06 | ✅ ⚠️ pilot calibration deferred |
| FR-014A (hit/weak/none disposition) | MODULE-004-06 (expansion decision records disposition) | ⚠️ partial — cutoffs deferred to pilot |

---

## IMPLEMENTATION STATUS

| Module | Status | Notes |
|---|---|---|
| MODULE-004-01 | 0% | Not started |
| MODULE-004-02 | 0% | Not started |
| MODULE-004-03 | 0% | `reference_search.py` has SQLite LIKE search; FTS5 not yet built |
| MODULE-004-04 | ~60% | `search_reference_lancedb()` in `reference_search.py` covers reference; case_chunks variant not yet built |
| MODULE-004-05 | 0% | Not started |
| MODULE-004-06 | 0% | Not started |
| MODULE-004-07 | 0% | Not started |

---

## OUTPUT VERIFICATION

- [x] Every module traces to EPIC-004 user stories
- [x] Every user story has module coverage
- [x] No circular dependencies within EPIC-004
- [x] High-risk modules flagged (MODULE-004-01, MODULE-004-06)
- [x] Cross-Epic dependencies documented
- [x] Minimum viable modules (7 — each has distinct responsibility)
- [x] Public interfaces defined with full type signatures
- [x] Parallel workstreams identified (03 + 04 concurrent)

---

## [CONTEXT.MD_UPDATE]

```
### EPIC-004 Modules:
- MODULE-004-01: ArtifactClassifier   | Type: Domain Logic    | Domain: Retrieval Engine
- MODULE-004-02: HookAssembler        | Type: Domain Logic    | Domain: Retrieval Engine
- MODULE-004-03: SparseRetriever      | Type: Infrastructure  | Domain: Retrieval Engine
- MODULE-004-04: DenseRetriever       | Type: Infrastructure  | Domain: Retrieval Engine
- MODULE-004-05: RRFFusion            | Type: Domain Logic    | Domain: Retrieval Engine
- MODULE-004-06: ExpansionController  | Type: Domain Logic    | Domain: Retrieval Engine
- MODULE-004-07: RetrievalAuditLogger | Type: Infrastructure  | Domain: Retrieval Engine

### Cross-Epic Dependencies (NEW):
- MODULE-004-01 depends on MODULE-001-03 (EPIC-001)
- MODULE-004-02 depends on MODULE-001-02 and MODULE-001-03 (EPIC-001)
- MODULE-004-06 depends on MODULE-001-02 (EPIC-001)
- MODULE-004-03, MODULE-004-04 consume case_chunks from MODULE-003-02 (EPIC-003)
- MODULE-004-07 retrieval_log_id consumed by MODULE-005-01 (EPIC-005)

### High-Risk Modules Flagged:
- MODULE-004-01: artifact name vocabulary must match real procurement document naming
- MODULE-004-06: expansion budget and tier ordering require pilot validation

### Unresolved Assumptions Affecting EPIC-004:
- [THRESHOLD NEEDED] NFR-006: latency SLO — measure and record, do not invent
- Pilot calibration: retrieval_floor_stage2, hit/weak/none cutoffs deferred
```
