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
│   ├── adr/                     ← Architecture Decision Records (18 filled, next: 0019)
│   │   ├── 0001-ipmp-as-primary-reference.md
│   │   ├── 0002-drop-tcdf-in.md
│   │   ├── 0003-bm25-primary-retrieval.md
│   │   ├── 0004-llm-temperature-zero-evaluation.md
│   │   ├── 0005-human-in-the-loop-scoring.md
│   │   ├── 0006-retrieval-cascade-strategy.md
│   │   ├── 0007-deterministic-identifiers-exact-match.md
│   │   ├── 0008-action-level-scoring.md
│   │   ├── 0009-single-llm-call-per-action.md
│   │   ├── 0010-tolerant-ingestion-loading-strategy.md
│   │   ├── 0011-phase1-extraction-strategy.md
│   │   ├── 0012-two-stage-page-extraction.md
│   │   ├── 0013-chunk-pydantic-basemodel.md
│   │   ├── 0014-document-artifact-storage-layout.md
│   │   ├── 0015-refined-retrieval-cascade.md
│   │   ├── 0016-fts5-indexes-text-only.md
│   │   ├── 0017-query-side-acronym-expansion.md
│   │   └── 0018-retrieved-chunk-no-wrapper.md
│   ├── dan/                     ← Deferred Architecture Notes (2 filled, next: 0003)
│   │   ├── 0001-pdf-extraction-chunking.md
│   │   └── 0002-bm25-query-generation-strategy.md  ← unresolved: direct text vs offline LLM-assisted query artifacts
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
│   └── test_regex_retrieval.py  ← regex search + cascade integration tests (13 tests)
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
│   └── retrieval/               ← Module 3 (IN PROGRESS — issues #11–15)
│       ├── __init__.py          ← public surface: configure, index, retrieve_for_acao, RetrievedChunk
│       ├── _config.py           ← module-level DB path: configure() / get_db_path()
│       ├── interfaces/
│       │   └── contracts.py     ← RetrievedChunk Pydantic model (13 fields)
│       ├── schema/
│       │   └── ddl.py           ← init_db(): chunks table + chunks_fts FTS5 virtual table
│       ├── indexing/
│       │   └── writer.py        ← index(process_number, chunks) — idempotent INSERT OR IGNORE
│       └── query/
│           ├── query_builder.py ← build_bm25_query(): product text → FTS5 OR query string
│           ├── bm25.py          ← search_bm25() + MAX_CHUNKS_PER_ACAO=20
│           ├── document.py      ← retrieve_document_focused(): filename_match + variant_match
│           ├── regex_search.py  ← search_regex(): SQLite user-defined function, OR-combined patterns
│           └── cascade.py       ← retrieve_for_acao(): full cascade A→B→C+D
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

**Current state (2026-05-30):** Module 1 (ingestion) COMPLETE. Module 2 (extraction) COMPLETE. Module 3 (retrieval) COMPLETE — all issues #11–15 implemented, 147/147 fast tests passing.
Install with: `SETUPTOOLS_USE_DISTUTILS=stdlib pip install -e .`
Run tests: `pytest -m "not slow"` (fast) or `pytest` (includes OCR; requires `TESSERACT_CMD` env var).

**Module 3 progress (issues #11–15):**
- #11 ✅ `RetrievedChunk` contract + `ChunkRetriever` protocol
- #12 ✅ SQLite schema (`init_db`) + `index()` writer
- #13 ✅ BM25 corpus-wide retrieval: `query_builder`, `bm25`, `cascade`, `retrieve_for_acao` wired
- #14 ✅ Document-focused cascade path: `document.py` (filename_match + variant_match), full cascade
- #15 ✅ Regex retrieval integration: `regex_search.py`, additive to BM25, SQLite user-defined function

**Module sequence (deep modules — one complete before the next):**
1. Ingestion (`src/ingestion/`) ← **COMPLETE**
2. PDF extraction + chunking (`src/extraction/`) ← **COMPLETE**
3. BM25 retrieval (`src/retrieval/`) ← **COMPLETE** (issues #11–15)
4. LLM evaluation (Ollama/Groq, temperature=0)
5. Auditor review interface (FastAPI)
6. Vector fallback (LanceDB)
7. Frontend (Vue.js 3, Phase 2)

**Key reference files:**
- `docs/MODULE_01_STATE.md` — ingestion design (decisions, models, boundaries, gaps)
- `docs/prd_module_01_ingestion.md` — Module 1 PRD (27 user stories, GitHub issues #1–5)
- `docs/prd_module_02_extraction.md` — Module 2 PRD (27 user stories, GitHub issues #6–10)
- `docs/prd_module_03_retrieval.md` — Module 3 PRD (36 user stories, GitHub issues #11–15)
- `CONTEXT.md` — canonical domain glossary
- `docs/adr/` — 18 ADRs, next is `0019-`
- `docs/dan/` — Deferred Architecture Notes (DAN-0002 CLOSED), next is `0003-`
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
