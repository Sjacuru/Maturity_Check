# Architecture Definition — M5D Evaluation System

**Date:** 2026-05-18  
**Status:** APPROVED FOR IMPLEMENTATION  
**Source inputs:** PRD, EPIC document (5A), MDAP CONTEXT.md (28 modules, 7 EPICs)

---

## 1. Architecture Overview

### System Style: Modular Monolith

A single Python/FastAPI application with 7 domain-aligned routers. Each router owns one EPIC's domain and delegates to the modules defined in MDAP. No inter-service HTTP calls — module-to-module communication is direct Python function calls within the same process.

**PRD justification:**
- Solo developer (NFR-005 modularity satisfied by internal boundaries, not deployment boundaries)
- Local-first Phase 1 deployment (NFR-008 — no network surface area to secure)
- May 29 Phase 1 deadline — microservices overhead would consume the available time
- Phase 2 central deployment can be achieved by adding auth middleware and a reverse proxy without restructuring the modules

**Considered and rejected:**
- *Microservices*: premature for a single-developer project; deployment, service discovery, and inter-service auth would double implementation time with no current benefit
- *Serverless*: incompatible with local-first requirement and stateful SQLite/LanceDB stores
- *CLI-only*: insufficient for the auditor UX; FastAPI enables the Phase 2 web UI without rebuilding the interface layer

### High-Level Component Diagram

```
┌────────────────────────────────────────────────────────────────────┐
│                    FastAPI Application (localhost:8000)             │
│                                                                    │
│  /framework  /cases  /documents  /retrieval  /evaluate  /reports   │
│      │           │        │           │           │         │      │
│  [001]        [002]     [003]       [004]       [005]     [006]     │
│  Reference    Case      Document    Retrieval   Evaluation Persist  │
│  Store        Mgmt      Processing  Engine      Engine    + Report  │
│                                                                    │
│  ──────────────────── Shared Data Layer ──────────────────────     │
│  SQLite (WAL + FTS5)          LanceDB (vectors)                    │
│  data/framework.sqlite        data/lancedb/reference/              │
│                               data/lancedb/cases/                  │
└────────────────────────────────────────────────────────────────────┘
         │                                    │
  LLM Adapter                        sentence-transformers
  Ollama (local)                     (local, singleton cache)
  Groq (cloud)
  Anthropic (future)
```

---

## 2. Technology Stack

| Layer | Technology | Justification | Alternative Considered | Limitation |
|---|---|---|---|---|
| Language | Python 3.11 | Existing codebase, rich ML/NLP ecosystem | — | GIL limits true parallelism |
| Web framework | FastAPI | Async, auto-generated OpenAPI docs, Pydantic validation | Flask | Requires ASGI server (uvicorn) |
| Relational DB | SQLite (WAL mode, FTS5) | Zero-config, local-first, FTS5 replaces Whoosh (NFR-005) | PostgreSQL (Phase 2) | Not suitable for multi-user concurrent writes |
| Vector DB | LanceDB | Local file-based, no server, columnar storage, fast ANN | Chroma, Qdrant | Less mature ecosystem |
| Sparse search | SQLite FTS5 | Built into SQLite, BM25 native, no dependency | Whoosh | Less tokeniser control than Whoosh |
| Embeddings | sentence-transformers `paraphrase-multilingual-MiniLM-L12-v2` | Local, Portuguese support, 384-dim, already validated | OpenAI embeddings | NFR-008 — case text must never leave machine |
| PDF extraction | `unstructured` (hi_res + OCR) | Layout detection, column ordering, arbitrary PDF structure, no per-document config | PyMuPDF + PaddleOCR only | Heavy dependency; slow on large PDFs |
| LLM — default | Ollama / Mistral (local) | Free, local, NFR-008 compliant for future Phase 2 unpublished docs | — | Lower reasoning quality than Anthropic |
| LLM — cloud option | Groq | Free tier, OpenAI-compatible, fast | Anthropic (cost) | Rate limits on free tier |
| LLM — future | Anthropic Claude | Best reasoning quality, structured output via tool use | — | Cost |
| Fusion | Custom RRF (pure Python) | Deterministic, no dependency, FR-008D requirement | Learned fusion | Requires pilot calibration for weights |
| Package manager | Anaconda / pip | Existing setup, corporate proxy compatibility | Poetry | `pip-system-certs` required for proxy |
| Frontend (Phase 2) | Vue.js 3 | PRD specification | React | — |

**Removed from stack:** Whoosh — replaced by SQLite FTS5. No functionality lost.

---

## 3. Module-to-Component Mapping

| Component | Modules | Responsibility | Phase |
|---|---|---|---|
| **Reference Service** | MODULE-001-01, 001-02, 001-03 | Ingest and query M5D, Rio Manual, TCDF IN + crosswalk | Phase 1 |
| **Case Service** | MODULE-002-01, 002-02, 002-03, 002-04 | Case CRUD, document upload, validation, residency policy | Phase 1 |
| **Document Processing Service** | MODULE-003-01, 003-02, 003-03 | PDF extraction, chunking, evaluation intent recording | Phase 1 |
| **Retrieval Engine** | MODULE-004-01 through 004-07 | Artifact classification, hook assembly, BM25+dense+RRF, expansion, audit log | Phase 1 |
| **Evaluation Engine** | MODULE-005-01, 005-02, 005-03, 005-04 | Evidence packet, LLM adapter, subtask evaluation, assurance pass | Phase 1 |
| **Persistence + Reporting Service** | MODULE-006-01 through 006-05 | Persist results, score, generate report, annotations, lifecycle | Phase 1 |
| **Review Service** | MODULE-007-01, 007-02 | PERSONA-002 read access, superior annotations | Phase 2 |

---

## 4. Module Consolidation Strategy

```
CONSOLIDATION LOGIC:

By Domain (FastAPI Router / Deployment Layer):
├─ /framework        → Reference Service      (MODULE-001-*)
├─ /cases            → Case Service           (MODULE-002-*)
├─ /documents        → Document Processing    (MODULE-003-*)
├─ /retrieval        → Retrieval Engine       (MODULE-004-*)
├─ /evaluate         → Evaluation Engine      (MODULE-005-*)
├─ /reports          → Persistence+Reporting  (MODULE-006-*)
└─ /review           → Review Service         (MODULE-007-*) — Phase 2

Rationale: MDAP decomposes by Epic responsibility (logical boundaries).
Architecture maps these 1:1 to FastAPI routers (deployment boundaries).
Both views preserved in CONTEXT.md for traceability.
The modular monolith keeps modules as Python packages that are directly
callable — no serialisation overhead for intra-component calls.
```

---

## 5. System Components (Detail)

### 5.1 Reference Service (`/framework`)

- **Modules:** MODULE-001-01, 001-02, 001-03
- **Interfaces exposed:** `POST /framework/ingest`, `POST /framework/crosswalk/load`, `GET /framework/actions/{action_id}`, `GET /framework/actions/{action_id}/subtasks`, `GET /framework/coverage`
- **Dependencies:** SQLite `reference_documents`, `reference_chunks`, `crosswalk_artifacts`; LanceDB `reference_m5d_chunks`, `reference_rio_manual_chunks`, `reference_tcdf_in_chunks`
- **Failure mode:** Ingest failure → partial chunks written; idempotent re-ingest supported via `content_hash` deduplication. Query failure → 404 with clear message.
- **PRD satisfied:** FR-001, NFR-005, NFR-007

### 5.2 Case Service (`/cases`)

- **Modules:** MODULE-002-01, 002-02, 002-03, 002-04
- **Interfaces exposed:** `POST /cases`, `GET /cases/{case_id}`, `GET /cases`, `POST /cases/{case_id}/documents`, `POST /cases/{case_id}/documents/{doc_id}/validate`
- **Dependencies:** SQLite `cases`, `case_documents`; filesystem `data/cases/`
- **Failure mode:** Upload failure → per-file error in response, other files unaffected. Validation failure → document marked invalid, not deleted (auditor can review).
- **PRD satisfied:** FR-003, FR-004, FR-005, NFR-008

### 5.3 Document Processing Service (`/documents`)

- **Modules:** MODULE-003-01, 003-02, 003-03
- **Interfaces exposed:** `POST /cases/{case_id}/documents/{doc_id}/extract`, `GET /cases/{case_id}/documents/{doc_id}/chunks`, `POST /cases/{case_id}/evaluate` (intent recording)
- **Dependencies:** `unstructured` library, SQLite `case_chunks`, LanceDB `case_chunks`
- **Failure mode:** OCR failure on single page → warning in response, page skipped. Total extraction failure → `ExtractionError` returned, run not created.
- **PRD satisfied:** FR-006, FR-007, NFR-005

### 5.4 Retrieval Engine (`/retrieval`)

- **Modules:** MODULE-004-01 through 004-07
- **Interfaces exposed:** Called internally by Evaluation Engine; also `GET /cases/{case_id}/runs/{run_id}/retrieval-log/{subtask_id}` for audit inspection
- **Dependencies:** SQLite FTS5 `case_chunks_fts`, LanceDB `case_chunks`, MODULE-001-02, MODULE-001-03, sentence-transformers model cache
- **Failure mode:** Sparse retrieval returns 0 results → empty list (not an error; ExpansionController handles tier expansion). Dense retrieval failure → fallback to sparse-only with warning in audit log.
- **PRD satisfied:** FR-008, FR-008A, FR-008B, FR-008C, FR-008D, FR-014A, NFR-005, NFR-006

### 5.5 Evaluation Engine (`/evaluate`)

- **Modules:** MODULE-005-01, 005-02, 005-03, 005-04
- **Interfaces exposed:** Called internally by the run pipeline; `POST /cases/{case_id}/runs/{run_id}/start`
- **Dependencies:** MODULE-004-07 (retrieval log), MODULE-001-02/03 (framework), MODULE-002-04 (residency), LLM provider (Ollama / Groq / Anthropic)
- **Failure mode:** LLMUnavailableError after 3 retries → run transitions to `failed` state; auditor can rerun. MalformedResponseError → subtask result marked with UNCERTAINTY flag; assurance pass still runs.
- **PRD satisfied:** FR-009, FR-010, FR-011, FR-012, FR-015, FR-021, NFR-001, NFR-002, NFR-008

### 5.6 Persistence + Reporting Service (`/reports`)

- **Modules:** MODULE-006-01 through 006-05
- **Interfaces exposed:** `GET /cases/{case_id}/runs/{run_id}/report`, `POST /cases/{case_id}/runs/{run_id}/annotate`, `POST /cases/{case_id}/runs/{run_id}/lifecycle`, `POST /cases/{case_id}/runs/{run_id}/rerun`
- **Dependencies:** SQLite `subtask_results`, `action_scores`, `annotations`, `evaluation_runs`
- **Failure mode:** Persistence gate rejects unassured result → `PersistenceGateError` with flag list; auditor must provide override or rerun. Score computation with incomplete results → `IncompleteEvaluationError`.
- **PRD satisfied:** FR-002, FR-013, FR-014, FR-016, FR-017, FR-018, FR-019, NFR-001, NFR-003, NFR-004

### 5.7 Review Service (`/review`) — Phase 2

- **Modules:** MODULE-007-01, 007-02
- **Interfaces exposed:** `GET /review/{case_id}/runs/{run_id}/report`, `POST /review/{case_id}/runs/{run_id}/annotate`
- **Dependencies:** MODULE-006-03 (report), MODULE-006-04 (annotations), auth token (Phase 2)
- **Phase 1 behavior:** Pass-through stub — endpoints exist but authorization always passes; no token required.
- **PRD satisfied:** FR-020

---

## 6. Data Architecture

### 6.1 Complete SQLite Schema

```
reference_documents    — ingested reference doc metadata (doc_id, title, version, hash)
reference_chunks       — M5D / Rio Manual / TCDF IN chunks with heading_path, stage, dimension, offsets
crosswalk_artifacts    — crosswalk mappings (artifact_id, subtask_id, tipo, grau, intencao, complement)

cases                  — case records (case_id, process_name, institution, contract_ref, status)
case_documents         — uploaded PDF metadata (doc_id, case_id, filename, file_path, hash, status)
case_chunks            — extracted + chunked case document text (chunk_id, doc_id, element_type, text, pages)
case_chunks_fts        — FTS5 virtual table over case_chunks.text (BM25 index)

evaluation_runs        — evaluation run records (run_id, case_id, action_id, status, llm_provider)
subtask_results        — per-subtask evaluation results (result_id, run_id, presence, confidence, flags...)
action_scores          — computed action scores (score_id, run_id, FR-013 four components)
retrieval_logs         — replayable retrieval audit logs (log_id, run_id, subtask_id, hooks, results...)
annotations            — auditor / reviewer annotations (annotation_id, target_type, target_id, persona, text)
```

### 6.2 LanceDB Schema

```
reference_m5d_chunks       — M5D reference embeddings (chunk_id, doc_id, heading_path, stage, dimension, text, vector[384])
reference_rio_manual_chunks — Rio Manual reference embeddings (same schema)
reference_tcdf_in_chunks    — TCDF IN reference embeddings (same schema)
case_chunks                 — Case document embeddings (chunk_id, doc_id, case_id, element_type, text, vector[384])
```

### 6.3 Data Ownership

| Component | SQLite tables owned | LanceDB tables owned |
|---|---|---|
| Reference Service | reference_documents, reference_chunks, crosswalk_artifacts | reference_m5d_chunks, reference_rio_manual_chunks, reference_tcdf_in_chunks |
| Case Service | cases, case_documents | — |
| Document Processing | case_chunks, case_chunks_fts | case_chunks |
| Retrieval Engine | retrieval_logs | reads case_chunks |
| Evaluation Engine | — (reads) | — (reads) |
| Persistence + Reporting | evaluation_runs, subtask_results, action_scores, annotations | — |

### 6.4 Data Flow

```
PDF file
  └──▶ PDFExtractor (unstructured) → DocumentElements
  └──▶ CaseDocumentChunker → CaseChunks → SQLite case_chunks + LanceDB case_chunks
  └──▶ SparseRetriever (FTS5) ─────┐
  └──▶ DenseRetriever (LanceDB) ───┼──▶ RRFFusion → FusedChunks
                                    │
  CrosswalkStore ──▶ HookAssembler ─┘
  FrameworkQueryService ─────────────▶ EvidencePacketBuilder → EvidencePacket
                                                                    │
                                                             LLMAdapter (Ollama/Groq)
                                                                    │
                                                             SubtaskEvaluator → EvaluationResult
                                                                    │
                                                             AssurancePass → AssuranceOutcome
                                                                    │
                                                             EvaluationPersister → SQLite
                                                                    │
                                                             ScoringEngine → ActionScore
                                                                    │
                                                             ReportGenerator → JSON + Markdown
```

### 6.5 Data at Rest / In Transit / Retention

- **At rest:** All data in `data/` directory on local machine. SQLite file encrypted at OS level (no application-level encryption in Phase 1). LanceDB files co-located.
- **In transit (Phase 1):** Only LLM API calls leave the machine (Groq if selected). Case document text is sent to Groq if `LLM_PROVIDER=groq` — Phase 1 scope: published documents only (OQ-005).
- **In transit (Phase 2):** ResidencyGuard enforces no transmission of unpublished document text to external services.
- **Retention:** No automatic deletion. Auditor manages case lifecycle.

---

## 7. Security Architecture

### 7.1 Trust Boundaries

```
[Trusted — Phase 1]
  Local machine filesystem  ← all data
  localhost:8000 FastAPI    ← all API calls (no external exposure)
  localhost:11434 Ollama    ← LLM inference (if Ollama selected)

[External — Phase 1, published docs only]
  api.groq.com              ← Groq LLM calls (if GROQ selected)
  api.anthropic.com         ← Anthropic calls (if ANTHROPIC selected)
```

### 7.2 Authentication

- **Phase 1:** None. App binds to `127.0.0.1` only. Single user. No session management.
- **Phase 2:** Token-based auth (design deferred — stakeholder sign-off per OQ-003). MODULE-007-01 stub is the insertion point.

### 7.3 Authorization

- **Phase 1:** No authorization model. All endpoints accessible.
- **Phase 2:** PERSONA-001 (full access) vs PERSONA-002 (read + annotate, no evaluation modification). Enforced by MODULE-007-01.

### 7.4 Secrets Management

- API keys stored in `.env` file, read via `pydantic-settings`; never committed to git (`.gitignore`).
- Config keys: `LLM_PROVIDER`, `OLLAMA_BASE_URL`, `GROQ_API_KEY`, `ANTHROPIC_API_KEY`, `RESIDENCY_POLICY`.

### 7.5 Known Attack Surfaces (Phase 1)

| Surface | Risk | Mitigation |
|---|---|---|
| PDF upload | Malformed PDF crashing unstructured | try/except around `partition_pdf`; return ExtractionError |
| LLM prompt injection | Case doc content manipulating LLM output | AssurancePass validates structured fields deterministically |
| SQLite injection | Query parameters | Parameterised queries only; no string interpolation in SQL |
| LLM API key exposure | Key in logs or error messages | Pydantic SecretStr; keys never logged |

### SECURITY FLAGS (Human Review Required):
- [ ] Phase 2 authentication flows
- [ ] Phase 2 authorization / permission management
- [ ] External API credential rotation policy
- [ ] NFR-008 legal compliance sign-off for Phase 2 unpublished document paths

---

## 8. Integration Points

| External System | Purpose | Phase | Fallback |
|---|---|---|---|
| Ollama (localhost:11434) | LLM inference — default | Phase 1 | Switch `LLM_PROVIDER=groq` |
| Groq (api.groq.com) | LLM inference — cloud option | Phase 1 | Switch `LLM_PROVIDER=ollama` |
| Anthropic API | LLM inference — best quality | Future | — |
| HuggingFace Hub | sentence-transformers model download (one-time) | Phase 1 | Use cached model at `~/.cache/huggingface/hub/` |
| `unstructured` (local) | PDF layout detection + OCR | Phase 1 | Warn on failure; mark page as low-confidence |

---

## 9. Scalability and Performance

**Phase 1 targets:** Single user, local machine, Ação 1 only (6 subtasks). No SLO invented per OQ-004/NFR-006. Measure and record baselines on first runnable pipeline.

**Bottleneck identification:**
| Step | Expected bottleneck | Mitigation |
|---|---|---|
| PDF extraction | `unstructured` hi_res mode is slow (10–60s per document) | Run once per document; results persisted |
| LLM evaluation | 6 subtask × LLM call latency | Parallel subtask evaluation (async FastAPI + asyncio.gather) |
| Vector embedding | sentence-transformers model load | Singleton cache — loaded once per process |
| BM25 search | FTS5 query | Indexed; fast for local SQLite |
| Dense search | LanceDB ANN | Fast; runs concurrently with BM25 |

**Horizontal scaling (Phase 2):** Replace SQLite with PostgreSQL + pgvector or keep LanceDB with a centralised server. FastAPI workers can scale horizontally once shared state moves to a server database.

---

## 10. Deployment Architecture

### Phase 1 (Local)

```
Developer machine
├── uvicorn src/maturity_check/main.py --host 127.0.0.1 --port 8000
├── data/
│   ├── framework.sqlite          ← all relational data
│   ├── lancedb/reference/        ← reference embeddings
│   └── lancedb/cases/            ← case document embeddings
├── .env                          ← API keys (not committed)
└── Plan/06_Models/output.md      ← M5D source (ingested once)
```

### Phase 2 (Central)

- Single server (cloud VM or on-prem)
- Replace SQLite → PostgreSQL; LanceDB → server-mode or pgvector
- Add reverse proxy (nginx) + auth middleware
- Module code unchanged — only infra layer (db.py, LanceDB client) swaps

### CI/CD

- Phase 1: None (solo developer, local only)
- Phase 2: GitHub Actions — lint, type check (mypy), integration tests against test SQLite

### Rollback

- Phase 1: `git checkout` + delete `data/framework.sqlite` + re-ingest
- Phase 2: Database migration versioning (Alembic or equivalent)

---

## 11. Architectural Risks and Open Decisions

| Risk | Impact | Mitigation |
|---|---|---|
| `unstructured` OCR quality on arbitrary PDFs | Retrieval misses evidence present in images | Validate MODULE-003-01 on 10 real procurement PDFs before Phase 1 sign-off |
| LLM structured output failures (Ollama/Mistral) | EvaluationResult malformed; assurance pass needed | MODULE-005-02 retry + fallback to Groq; log all raw responses |
| Phase 1 deadline (May 29, 11 days) | Pipeline not end-to-end | 26 modules in critical path; daily progress tracking required |
| SQLite write contention (Phase 2 multi-user) | Data loss or corruption | Accepted for Phase 1; resolved by PostgreSQL migration in Phase 2 |
| Expansion controller pilot calibration | Wrong tier ordering degrades retrieval | Log all expansion decisions; calibrate after first 5 case evaluations |

### Deferred Decisions

| Decision | Deferred to | Trigger |
|---|---|---|
| NFR-006 latency SLO (numeric) | After pilot | First full pipeline run on real case |
| FR-002 custom weight values | External stakeholder | Domain expert input |
| NFR-008 Phase 2 compliance | Phase 2 design | Legal review sign-off |
| Phase 2 auth mechanism | Phase 2 design | Stakeholder OQ-003 resolution |
| CONFLICTING_INFORMATION LLM judge | Phase 2 | Replace MODULE-005-04 heuristic |

---

## OUTPUT VERIFICATION

- [x] Every component maps to MDAP modules
- [x] Every technology choice cites PRD/NFR requirement
- [x] Failure modes defined for all major components
- [x] Trust boundaries explicitly identified
- [x] Module consolidation strategy documented
- [x] Security-critical components flagged for human review
- [x] No code or pseudocode included
- [x] Simplest architecture satisfying requirements chosen (modular monolith)
- [x] Unresolved assumptions (5A.3) acknowledged
- [x] Whoosh removed from tech stack (replaced by SQLite FTS5)

---

## [CONTEXT.MD_UPDATE]

```
## Architecture Definition Complete

### System Style: Modular Monolith (single FastAPI application)

### Components:
- Reference Service:            MODULE-001-*  | Ingest + query framework + crosswalk
- Case Service:                 MODULE-002-*  | Case CRUD + document upload + validation + residency
- Document Processing Service:  MODULE-003-*  | PDF extraction + chunking + intent recording
- Retrieval Engine:             MODULE-004-*  | Artifact classify + hooks + BM25 + dense + RRF + expansion + audit
- Evaluation Engine:            MODULE-005-*  | Evidence packet + LLM adapter + subtask eval + assurance
- Persistence + Reporting:      MODULE-006-*  | Persist + score + report + annotate + lifecycle
- Review Service:               MODULE-007-*  | PERSONA-002 access + annotations (Phase 2)

### Technology Stack:
- Backend:     Python 3.11 + FastAPI + uvicorn
- Database:    SQLite (WAL + FTS5) + LanceDB
- Embeddings:  sentence-transformers (local, paraphrase-multilingual-MiniLM-L12-v2)
- PDF:         unstructured (hi_res + OCR)
- LLM:         Ollama/Mistral (default) | Groq | Anthropic (future)
- Frontend:    Vue.js 3 (Phase 2)

### High-Risk Components (Human Review Required):
- MODULE-003-01: unstructured OCR validation on real procurement PDFs
- MODULE-005-02: LLM structured output reliability across providers
- MODULE-007-01: Phase 2 access model (stakeholder sign-off)

### Architectural Risks:
- OCR quality on arbitrary Brazilian procurement PDFs
- LLM structured output failures (Ollama/Mistral less reliable)
- Phase 1 deadline — 26 modules in critical path, 11 days

### Unresolved Assumptions Affecting Architecture:
- NFR-006 latency SLO — measure first
- NFR-008 Phase 2 compliance — legal review required
- FR-002 custom weights — stakeholder input required
- PERSONA-002 interaction model — read + annotate only (constrained)
```

---

## 7A — PHASE TRANSITION NOTE FOR FOLDER/FILE STRUCTURE

```
[7A_PHASE_TRANSITION_NOTE]

### Components Ready for File Structuring:
1. Reference Service:           MODULE-001-01/02/03  | Low risk  | src/maturity_check/reference/
2. Case Service:                MODULE-002-01/02/03/04 | Low risk | src/maturity_check/cases/
3. Document Processing Service: MODULE-003-01/02/03  | HIGH risk | src/maturity_check/documents/
4. Retrieval Engine:            MODULE-004-01..07    | Medium risk | src/maturity_check/retrieval/
5. Evaluation Engine:           MODULE-005-01..04    | HIGH risk | src/maturity_check/evaluation/
6. Persistence + Reporting:     MODULE-006-01..05    | Low risk  | src/maturity_check/reporting/
7. Review Service (Phase 2):    MODULE-007-01/02     | deferred  | src/maturity_check/review/

### Module-to-File Mapping Guidance:
src/maturity_check/
├── main.py                     ← FastAPI app + router registration
├── config.py                   ← pydantic-settings Config class
├── db.py                       ← SQLite schema init (extended with new tables)
├── reference/
│   ├── ingester.py             ← MODULE-001-01: ReferenceDocumentIngester
│   ├── crosswalk.py            ← MODULE-001-02: CrosswalkStore
│   └── query.py                ← MODULE-001-03: FrameworkQueryService
├── cases/
│   ├── service.py              ← MODULE-002-01: CaseService
│   ├── upload.py               ← MODULE-002-02: DocumentUploadService
│   ├── validator.py            ← MODULE-002-03: DocumentValidator
│   └── residency.py            ← MODULE-002-04: ResidencyGuard
├── documents/
│   ├── extractor.py            ← MODULE-003-01: PDFExtractor
│   ├── chunker.py              ← MODULE-003-02: CaseDocumentChunker
│   └── intent.py               ← MODULE-003-03: EvaluationIntentRecorder
├── retrieval/
│   ├── classifier.py           ← MODULE-004-01: ArtifactClassifier
│   ├── hooks.py                ← MODULE-004-02: HookAssembler
│   ├── sparse.py               ← MODULE-004-03: SparseRetriever
│   ├── dense.py                ← MODULE-004-04: DenseRetriever
│   ├── fusion.py               ← MODULE-004-05: RRFFusion
│   ├── expansion.py            ← MODULE-004-06: ExpansionController
│   └── audit_log.py            ← MODULE-004-07: RetrievalAuditLogger
├── evaluation/
│   ├── evidence.py             ← MODULE-005-01: EvidencePacketBuilder
│   ├── llm_adapter.py          ← MODULE-005-02: LLMAdapter
│   ├── evaluator.py            ← MODULE-005-03: SubtaskEvaluator
│   └── assurance.py            ← MODULE-005-04: AssurancePass
├── reporting/
│   ├── persister.py            ← MODULE-006-01: EvaluationPersister
│   ├── scoring.py              ← MODULE-006-02: ScoringEngine
│   ├── report.py               ← MODULE-006-03: ReportGenerator
│   ├── annotations.py          ← MODULE-006-04: AnnotationService
│   └── lifecycle.py            ← MODULE-006-05: LifecycleController
└── review/                     ← Phase 2
    ├── access.py               ← MODULE-007-01: ReviewAccessController
    └── superior.py             ← MODULE-007-02: SuperiorAnnotationService

### Existing files to migrate/refactor (not delete):
- src/maturity_check/ingest/m5d_ingest.py → generalise → reference/ingester.py
- src/maturity_check/ingest/chunking.py   → split: reference normalizer stays; case chunker → documents/chunker.py
- src/maturity_check/reference_search.py  → split: dense.py (MODULE-004-04) + sparse.py (MODULE-004-03)
- src/maturity_check/db.py               → extend schema (new tables); keep filename
- src/maturity_check/cli.py              → retain as thin CLI wrapper; primary interface moves to FastAPI

### High-Risk Components (Implementation Review Before Coding):
- Document Processing: MODULE-003-01 (unstructured) — test on real PDFs first
- Evaluation Engine: MODULE-005-02 (LLM adapter) — validate JSON schema across providers first

### Dependency Graph (component level):
Reference Service  ←── Retrieval Engine ←── Evaluation Engine ←── Persistence Service
Case Service       ←── Document Processing ←── Retrieval Engine
Document Processing ←── Retrieval Engine

[/7A_PHASE_TRANSITION_NOTE]
```
