# CLAUDE.md — PPP Maturity Check System

This file provides persistent context for Claude Code sessions.
Update it whenever significant decisions are made or status changes.

---

## Project Overview

**Name:** PPP Maturity Check System
**Developer:** Solo (Salim / sjacuru@gmail.com)
**Working directory:** `c:\Users\sanseri\Documents\Projetos\Maturity_Check`
**GitHub:** https://github.com/Sjacuru/Maturity_Check
**Language:** Bilingual PT + EN

A system that evaluates Brazilian public procurement (PPP) documents against the
IPMP framework (Indicador de Percepção de Maturidade de Projetos), producing a
maturity score for each of 46 actions across 5 IPMP dimensions. The evaluation is
human-validated — the system surfaces evidence, the auditor confirms scores.

---

## Strategic Decisions (as of 2026-05-20)

1. **Primary reference: IPMP** — operationalises each action into concrete expected
   products, scoring rubrics (0/1/3), and scored examples
   (Atendido / Parcialmente / Não Atendido).
2. **Secondary reference: Rio Manual** — provides document names and procedures
   used as retrieval hints when searching case documents.
3. **TCDF IN: dropped.**
4. **Scoring: 0 / 1 / 3 per action** (46 actions, max = 138 total).
5. **Retrieval: BM25 primary (SQLite FTS5), deterministic.**
   Cascade per Ação: (1) exact Rio Manual document name match →
   (2) BM25 augmented search (IPMP sub-items + Rio Manual names) →
   (3) dense vector fallback. All three steps in scope for Ação 1.
6. **LLM: temperature=0, fixed prompt per action.** IPMP criteria + scored
   examples embedded in prompt. Human auditor validates every score.
7. **Reproducibility** is the core academic constraint (professor's requirement).
   BM25 (deterministic retrieval) + temperature=0 = same input → same score.
8. **Phase 1 scope: Ação 1 only.**
9. **IPMP ingestion: manual.** PDF structure is mixed text/image; data is static.
   Expected products sub-items (a/b/c/d) per action become BM25 search queries.
10. **Development methodology:** CONTEXT.md → ADR → to-PRD → grill-me per module.
    **Deep modules:** one module fully designed and built before the next begins.
    No stubs, no parallel tracks, no "fill in later."

---

## Auditor Review Interface (7 elements)

For each scored action, the system presents to the human auditor:
1. IPMP criteria for the action
2. Retrieval query used
3. Retrieved chunks (with source document + page number)
4. Exact LLM prompt sent
5. LLM reasoning
6. Uncertainty flag
7. Proposed score (0 / 1 / 3)

---

## Project Structure

```
Maturity_Check/
├── CLAUDE.md                    ← this file
├── CONTEXT.md                   ← domain glossary (filled 2026-05-25)
├── pyproject.toml               ← Python project packaging
├── .gitignore
├── docs/
│   ├── adr/                     ← Architecture Decision Records (48 filled, next: 0049-)
│   │   ├── 0001–0021            ← Modules 1–4 decisions (see adr/ directory)
│   │   ├── 0022-module5-orchestration-service.md
│   │   ├── 0023-review-outcome-contract.md
│   │   ├── 0024-shared-sqlite-schema-ownership.md
│   │   ├── 0025-evaluation-result-persistence-hybrid.md
│   │   ├── 0026-evaluation-lifecycle-replacement-model.md
│   │   ├── 0027-assessment-api-contract.md
│   │   ├── 0028-extracted-artifacts-as-canonical-representation.md
│   │   ├── 0029-document-fingerprint-reuse-semantics.md
│   │   ├── 0030-assessment-scope-from-ipmp-store.md
│   │   ├── 0031-evaluation-result-direct-http-serialization.md
│   │   ├── 0032-module5-configuration-and-startup-sequencing.md
│   │   ├── 0033–0046            ← Modules 6–7 decisions (vector fallback, frontend)
│   │   ├── 0047-retrieval-profile-architecture.md  ← evidence ontology, derived artifact, maturity model
│   │   └── 0048-query-construction-and-encoding.md ← phrase preservation, NEAR(), encoding by type
│   ├── dan/                     ← Deferred Architecture Notes (2 filled, next: 0003)
│   │   ├── 0001-pdf-extraction-chunking.md
│   │   └── 0002-bm25-query-generation-strategy.md  ← CLOSED: resolved by ADR-0047 + ADR-0048; Evolution section added 2026-06-18
│   ├── MODULE_01_STATE.md       ← ingestion layer full architectural state
│   ├── prd_module_01_ingestion.md ← Module 1 PRD (27 user stories, GitHub issues #1–5)
│   ├── prd_module_02_extraction.md ← Module 2 PRD (27 user stories, GitHub issues #6–10)
│   ├── publish_issues.ps1       ← gh issue publish script (issues already created, keep for reference)
│   └── prompts/
│       ├── 01_grill-me.md
│       ├── 02_To-PRD.md
│       └── 03_To_issues.md
├── _archive/                    ← old design docs — DO NOT USE
├── tests/
│   ├── test_chunk.py            ← Chunk model unit tests (13 tests)
│   ├── test_extract_digital.py  ← native text extraction integration tests (14 tests)
│   ├── test_chunking.py         ← sub-page splitting tests (13 unit + 4 integration)
│   ├── test_error_handling.py   ← fatal + non-fatal error handling tests (7 tests)
│   ├── test_retrieved_chunk.py  ← RetrievedChunk model tests (28 tests)
│   ├── test_schema.py           ← init_db tests (5 tests)
│   ├── test_indexing.py         ← index() integration tests (10 tests)
│   ├── test_bm25_retrieval.py   ← BM25 query builder + search tests (24 tests)
│   ├── test_document_retrieval.py ← filename_match + variant_match + cascade tests (19 tests)
│   ├── test_regex_retrieval.py  ← regex search + cascade integration tests (13 tests)
│   ├── test_evaluation_contract.py ← EvaluationResult model + invariant tests (16 tests)
│   ├── test_response_parser.py  ← sentinel parsing + parse_failed tests (16 tests)
│   ├── test_prompt_builder.py   ← system/user prompt assembly + ordering tests (15 tests)
│   └── test_evaluate_orchestration.py ← evaluate() full flow with StubLLMClient (12 tests)
├── src/
│   ├── ingestion/               ← Module 1 (COMPLETE)
│   │   ├── __init__.py          ← sole public surface
│   │   ├── ipmp.py              ← IPMP models + get_ipmp_store()
│   │   ├── rio_manual.py        ← Rio Manual models + get_rio_manual_store()
│   │   └── acronyms.py          ← get_acronym_store()
│   ├── extraction/              ← Module 2 (COMPLETE — issues #6–10)
│   │   ├── __init__.py          ← sole public surface: Chunk, extract_document
│   │   ├── chunk.py             ← Chunk pydantic.BaseModel (9 fields)
│   │   └── pdf.py               ← extract_document() — word-count heuristic + OCR
│   ├── retrieval/               ← Module 3 (COMPLETE — issues #11–15)
│   │   ├── __init__.py          ← public surface: configure, index, retrieve_for_acao, RetrievedChunk
│   │   ├── _config.py           ← module-level DB path: configure() / get_db_path()
│   │   ├── interfaces/
│   │   │   └── contracts.py     ← RetrievedChunk Pydantic model (13 fields)
│   │   ├── schema/
│   │   │   └── ddl.py           ← init_db(): chunks table + chunks_fts FTS5 virtual table
│   │   ├── indexing/
│   │   │   └── writer.py        ← index(process_number, chunks) — idempotent INSERT OR IGNORE
│   │   └── query/
│   │       ├── query_builder.py ← build_bm25_query(): product text → FTS5 OR query string
│   │       ├── bm25.py          ← search_bm25() + MAX_CHUNKS_PER_ACAO=20
│   │       ├── document.py      ← retrieve_document_focused(): filename_match + variant_match
│   │       ├── regex_search.py  ← search_regex(): SQLite user-defined function, OR-combined patterns
│   │       └── cascade.py       ← retrieve_for_acao(): full cascade A→B→C+D
│   ├── evaluation/              ← Module 4 (COMPLETE — issues #16–20)
│   │   ├── __init__.py          ← public surface: configure_llm, evaluate, EvaluationResult
│   │   ├── _config.py           ← module-level LLMClient: configure_llm() / get_llm_client()
│   │   ├── evaluator.py         ← evaluate(): full orchestration + EVIDENCE_CHAR_WARN_THRESHOLD
│   │   ├── interfaces/
│   │   │   └── contracts.py     ← EvaluationResult Pydantic model (14 fields, 3 flag invariants)
│   │   ├── llm/
│   │   │   ├── protocol.py      ← LLMClient Protocol (complete(system, user) -> str)
│   │   │   ├── ollama.py        ← OllamaClient: Ollama HTTP API, temperature=0
│   │   │   └── groq.py          ← GroqClient: Groq SDK, temperature=0
│   │   ├── prompt/
│   │   │   └── builder.py       ← build_system_prompt(acao_id), build_user_prompt(chunks)
│   │   └── parsing/
│   │       └── response.py      ← ParsedResponse dataclass + parse_llm_response(raw)
│   └── assessment/              ← Module 5 (GRILL-ME COMPLETE — PRD next, issues #21–25)
│       ├── __init__.py          ← public surface: configure, init_db, AssessmentService, ReviewOutcome
│       ├── _config.py           ← module-level DB path: configure() / get_db_path()
│       ├── service.py           ← AssessmentService: run_assessment(process_number, document_paths)
│       ├── interfaces/
│       │   └── contracts.py     ← ReviewOutcome Pydantic model (7 fields, validator invariants)
│       ├── schema/
│       │   └── ddl.py           ← init_db(): evaluation_results + review_outcomes + document_fingerprints
│       └── api/
│           ├── app.py           ← create_app() — FastAPI app; imported by main.py only
│           ├── routes.py        ← 5 Phase 1 routes
│           └── schemas.py       ← request body Pydantic models (write-side only)
├── main.py                      ← runtime entry point: configure → init_db → create_app
└── data/
    ├── ipmp/
    │   └── acao_01.json         ← complete (Phase 1 scope)
    ├── rio_manual/
    │   └── acao_01.json         ← complete (schema v1.0, known gaps documented)
    └── acronyms/
        └── acronyms.json        ← complete
```

---

## ⏭️ Where to Resume

**Current state (2026-07-01):** Modules 1–7 COMPLETE. 388 tests (376 fast + 12 slow-marked — `pytest -m "not slow"` runs 376). Retrieval profile architecture (ADR-0047+0048) implemented and populated for Ação 1. Hybrid BM25+vector retrieval (ADR-0049) and the LLM relevance gate (ADR-0050) are both live, validated against the real corpus, and latency-tuned (ADR-0050's 2026-06-29 amendment + ADR-0051).

**Evidence pipeline enhancements (2026-07-01):**
- Pre-gate semantic dedup (`_prefilter_near_duplicates`, threshold=0.92) live in `evidence_selection.py`: drops near-exact candidate duplicates before gate evaluation, saving ~6 gate calls/run (3 for 1b conclusion copies, 3 for 1d boilerplate copies). Does not affect post-gate dedup (threshold=0.70).
- 1b retrieval profile expanded with 5 empirically-derived terms: "fluxo de caixa livre", "receita projetada", "premissas básicas", "CAPEX", "custos operacionais". BM25 ranking shifted (conclusion demoted from rank 1 to rank 5) but RRF vector component still surfaces pg=192 conclusion first — confirmed content gap: document provides financial viability conclusion, not the "panorama" IPMP expects for 1b.
- 1d profile: known false-positive (pg=235 BASE LEGAL boilerplate) not yet addressed — deferred to next retrieval profile review.

**Relevance gate, current configuration:** `qwen2.5:7b` via Ollama (not `bode-alpaca-pt-br` — see ADR-0050 amendment for why). Binary relevant/not-relevant only — no LLM cleaning (dropped; `evaluation/evidence_selection.py::strip_extraction_noise()` is the only cleaning now, deterministic). `_MAX_EXAMINED=8` candidates examined per product; per-product gating runs concurrently via `ThreadPoolExecutor`. Measured: ~20.6 min for a full Ação 1 assessment on the reference CPU-only hardware (6-core/12-thread, no usable GPU) — down from 68 min pre-fix, but still far from "all 46 actions in one interactive sitting" (~15.8 hours extrapolated). **ADR-0051: interactive assessments are scoped to one Ação today, a small batch (3-4) once Phase 1 expands — never a full 46-action run in one sitting.** Smaller local models (`LiquidAI/LFM2.5-350M`) were tested and rejected (blanket-accept failure, not viable at that size for this task).

**Current enhancement queue — ALL COMPLETE:**
1. ✅ Retrieval profiles — 1b updated with 5 real-document terms (marked experimental to avoid BM25 TOC ranking)
2. ✅ Pre-gate semantic dedup (`_prefilter_near_duplicates`, threshold=0.92)
3. ✅ Regex retrieval REMOVED from cascade (ADR-0052) — Step D dropped entirely. Restores pg=211 (1c strategic metas) to every evidence set by eliminating the cap displacement. `search_regex()` preserved as utility.
4. ✅ Deterministic concept attribution (`_attribute_concepts`) — `matched_concepts` on both `RetrievedChunk` and `RejectedChunk`
5. ✅ `build_query_from_terms` filters experimental/deprecated terms — BM25 retrieval only uses active/validated terms

**Key architectural lessons from this work:**
- `build_query_from_terms` now filters by status (active/validated only) — experimental terms excluded from BM25 but included in concept attribution
- Experimental terms in retrieval profiles = "registered for attribution and future validation, not yet trusted for retrieval"
- `_prefilter_near_duplicates` runs in production `select_evidence()` but live_report.py must also call it for accurate representation
- Ollama KV cache can produce identical test output across runs for identical prompts — careful comparison of candidate rankings (not just gate verdicts) is needed to verify retrieval changes

**Latency:** ~17-20 min/Ação (ADR-0051 scope: one Ação at a time). Pre-gate dedup saves ~6 gate calls (3 for 1b conclusion copies, 3 for 1d boilerplate). Further reduction requires non-LLM pre-filter or fine-tuned small model (deferred).

**Tests:** 386 fast + 12 slow = 398 total. Run with `pytest -m "not slow"` for fast path.

Install with: `SETUPTOOLS_USE_DISTUTILS=stdlib pip install -e .`
Run tests: `pytest -m "not slow"` (fast) or `pytest` (includes OCR; requires `TESSERACT_CMD` env var).

**Module 5 design decisions (grill-me 2026-06-02):**
- ADR-0022: `AssessmentService` owns orchestration; FastAPI is presentation layer
- ADR-0023: Review Outcome contract — accept/override; `final_score` always in {0,1,3}; `justification` required on override
- ADR-0024: Shared SQLite DB, schema-level table ownership per module
- ADR-0025: `EvaluationResult` persistence — hybrid (normalised columns + `raw_json` blob)
- ADR-0026: Replacement lifecycle; no versioning; app-layer 409 guard; explicit DELETE+INSERT (no INSERT OR REPLACE)
- ADR-0027: 5 Phase 1 routes; multipart file upload; synchronous execution
- ADR-0028: PDFs are transient; `chunks` table is canonical extracted artifact store; no PDF storage
- ADR-0029: SHA-256 fingerprint-based reuse/replacement; `document_fingerprints` table owned by Module 5
- ADR-0030: Assessment scope from `get_ipmp_store()`, not hardcoded; aggregation deferred
- ADR-0031: `EvaluationResult.model_dump()` as direct HTTP response; no shaped DTOs for reads
- ADR-0032: Independent `configure(db_path)` per module; `main.py` owns startup sequencing

**Module sequence (deep modules — one complete before the next):**
1. Ingestion (`src/ingestion/`) ← **COMPLETE**
2. PDF extraction + chunking (`src/extraction/`) ← **COMPLETE**
3. BM25 retrieval (`src/retrieval/`) ← **COMPLETE** (issues #11–15)
4. LLM evaluation (`src/evaluation/`) ← **COMPLETE** (issues #16–20)
5. Auditor review interface (`src/assessment/` + `main.py`) ← **COMPLETE** (issues #21–25)
6. Vector fallback (LanceDB)
7. Frontend (Vue.js 3, Phase 2)

**Key reference files:**
- `docs/prd_module_04_evaluation.md` — Module 4 PRD (36 user stories, GitHub issues #16–20)
- `docs/prd_module_05_assessment.md` — Module 5 PRD (35 user stories, GitHub issues #21–25)
- `CONTEXT.md` — canonical domain glossary (updated 2026-06-18: Retrieval Profile, Evidence Ontology, Evidence Intent, Retrieval Signal Concept, Query Term, Evidence Logic Pattern, Profile Maturity, Term Status)
- `docs/adr/` — 51 ADRs, next is `0052-`
- `docs/dan/` — Deferred Architecture Notes (both closed), next is `0003-`
- `docs/handoffs/retrieval-profile-design-2026-06-17.md` — full design session handoff (evidence ontology, schema, population methodology)
- `data/ipmp/acao_01.json` — IPMP source-of-truth for Ação 1
- `data/rio_manual/acao_01.json` — Rio Manual retrieval context for Ação 1

---

## Environment

- Conda env: `rel_voto` (Python 3.11)
- `pip-system-certs` required for HuggingFace downloads through corporate proxy
- Run scripts via `python` directly (not `conda run`) — avoids Windows UTF-8 errors
- Set `PYTHONIOENCODING=utf-8` before running scripts
- Set `TESSERACT_CMD=C:\Users\sanseri\AppData\Local\Programs\Tesseract-OCR\tesseract.exe` — conda subprocess does not inherit User-level PATH; set in `.claude/settings.local.json`
- HuggingFace model cached at `C:\Users\sanseri\.cache\huggingface\hub\`

---

## Tools in Use

| Layer | Tool |
|---|---|
| Language | Python 3.11 / Anaconda |
| Web framework | FastAPI + uvicorn |
| Structured DB | SQLite (WAL + FTS5 for BM25) |
| Vector DB | LanceDB (fallback retrieval only) |
| PDF extraction | `unstructured[pdf]` (layout-aware, OCR) |
| Embeddings | sentence-transformers (local, fallback only) |
| LLM evaluation | Ollama/Mistral (default, local) or Groq (cloud option) |
| Frontend | Vue.js 3 (Phase 2) |

---

## Methodology

### ADR (`docs/adr/`)

Sequential numbering: `0001-slug.md`. Create directory lazily — only when the first ADR is needed.

**Template:**
```
# {Short title}
{1-3 sentences: context, decision, why.}
```

**Optional sections** (only when they add genuine value):
- `Status` frontmatter: `proposed | accepted | deprecated | superseded by ADR-NNNN`
- `Considered Options` — when rejected alternatives are worth remembering
- `Consequences` — when non-obvious downstream effects need calling out

**Numbering:** scan `docs/adr/` for the highest number, increment by one.

**When to create — all three must be true:**
1. Hard to reverse
2. Surprising without context — a future reader would wonder "why on earth did they do it this way?"
3. Result of a real trade-off — genuine alternatives existed

**What qualifies:** architectural shape, technology choices with lock-in, boundary/scope decisions (including explicit exclusions), deliberate deviations from the obvious path, constraints not visible in code, rejected alternatives where the rejection is non-obvious.

---

### DAN (`docs/dan/`)

Deferred Architecture Notes capture strategy spaces that are too important to lose but intentionally unresolved. Unlike ADRs (sealed decisions), DANs are living documents that evolve across phases.

**Use a DAN when:**
- A design area has stable directives but open trade-offs not ready to become ADRs
- Known complexity is intentionally deferred (with documented reasons)
- Multiple future triggers may change the approach independently

**Numbering:** sequential `0001-slug.md` in `docs/dan/`.

**Template:**
```
# DAN-{NNNN} — {Subsystem}: Deferred Architecture

**Status:** Active | Closed (decisions moved to ADR-XXXX)
**Related ADR:** (if any)
**Last updated:** {date}

## Stable Directives       ← do not revisit unless a trigger fires
## Known Constraints       ← hard requirements the module must satisfy
## Deferred Complexity Areas  ← table of deferred problems + why
## Candidate Tooling Ecosystem  ← research directions, not commitments (optional)
## Non-Goals for Phase N   ← explicit exclusions
## Future Triggers         ← events that require revisiting this DAN
```

**When to close a DAN:** mark `Status: Closed` and link the ADRs that resolved the deferred areas. Do not delete — closed DANs explain why certain ADRs exist.

---

### CONTEXT.md (root)

Single-context repo — one `CONTEXT.md` at root.

**Template:**
```
# {Context Name}
{One or two sentence description.}

## Language
**Term**: One-sentence definition of what it IS.
_Avoid_: rejected synonyms

## Relationships
- **Term A** produces one or more **Term B**s

## Example dialogue
> Dev/domain-expert conversation showing terms interacting naturally.

## Flagged ambiguities
- Term used ambiguously — resolved: clear resolution.
```

**Rules:**
- Be opinionated: pick one canonical name, list rejected synonyms under _Avoid_.
- One sentence per definition. Define what it IS, not what it does.
- Only project-specific concepts — not general programming terms.
- Show relationships with cardinality where obvious.
- Always write an example dialogue.
- Flag and resolve any term used ambiguously.
- **CONTEXT.md is a glossary only.** No implementation details, specs, or scratch-pad notes.

---

### grill-me

Prompt file: `docs/prompts/grill-me.md`.
to-PRD skill: `docs/prompts/To-PRD.md`.
IPMP reference PDF: `docs/IPMP TCU2026 - Indicador_percepcao_maturidade.pdf`.

Use before designing each new module to stress-test the plan against the domain model and documented decisions. Updates CONTEXT.md and ADRs inline as decisions crystallise — do not batch.

During a grill-me session: challenge terminology against CONTEXT.md, sharpen fuzzy language, stress-test with concrete scenarios, cross-reference with code when relevant.
