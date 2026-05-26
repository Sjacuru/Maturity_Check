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
│   ├── adr/                     ← Architecture Decision Records (10 filled, next: 0011)
│   │   ├── 0001-ipmp-as-primary-reference.md
│   │   ├── 0002-drop-tcdf-in.md
│   │   ├── 0003-bm25-primary-retrieval.md
│   │   ├── 0004-llm-temperature-zero-evaluation.md
│   │   ├── 0005-human-in-the-loop-scoring.md
│   │   ├── 0006-retrieval-cascade-strategy.md
│   │   ├── 0007-deterministic-identifiers-exact-match.md
│   │   ├── 0008-action-level-scoring.md
│   │   ├── 0009-single-llm-call-per-action.md
│   │   └── 0010-tolerant-ingestion-loading-strategy.md
│   ├── MODULE_01_STATE.md       ← ingestion layer full architectural state
│   ├── prd_module_01_ingestion.md ← Module 1 PRD (27 user stories, GitHub issues #1–5)
│   ├── publish_issues.ps1       ← gh issue publish script (issues already created, keep for reference)
│   └── prompts/
│       ├── 01_grill-me.md
│       ├── 02_To-PRD.md
│       └── 03_To_issues.md
├── _archive/                    ← old design docs — DO NOT USE
├── src/
│   └── ingestion/               ← Module 1 (COMPLETE)
│       ├── __init__.py          ← sole public surface
│       ├── ipmp.py              ← IPMP models + get_ipmp_store()
│       ├── rio_manual.py        ← Rio Manual models + get_rio_manual_store()
│       └── acronyms.py          ← get_acronym_store()
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

**Current state (2026-05-26):** Module 1 (ingestion layer) is COMPLETE.
All three singletons implemented and verified. GitHub issues #1–5 closed.
Install with: `SETUPTOOLS_USE_DISTUTILS=stdlib pip install -e .`

**Immediate next steps (in order):**
1. **Resolve open gaps before Module 2** (dedicated sessions):
   - Lei Municipal de PPP law number (needed for `regex_variants` in `data/rio_manual/acao_01.json`)
   - PPA management strategy (cyclic document, strategy undefined)
2. **Design Module 2** — PDF extraction + chunking (run grill-me → to-PRD → to-issues)

**Module sequence (deep modules — one complete before the next):**
1. Ingestion (`src/ingestion/`) ← **COMPLETE**
2. PDF extraction + chunking ← next
3. BM25 retrieval (SQLite FTS5)
4. LLM evaluation (Ollama/Groq, temperature=0)
5. Auditor review interface (FastAPI)
6. Vector fallback (LanceDB)
7. Frontend (Vue.js 3, Phase 2)

**Key reference files:**
- `docs/MODULE_01_STATE.md` — ingestion design (decisions, models, boundaries, gaps)
- `docs/prd_module_01_ingestion.md` — Module 1 PRD (27 user stories, GitHub issues #1–5)
- `CONTEXT.md` — canonical domain glossary
- `docs/adr/` — 10 ADRs, next is `0011-`
- `data/ipmp/acao_01.json` — IPMP source-of-truth for Ação 1
- `data/rio_manual/acao_01.json` — Rio Manual retrieval context for Ação 1

---

## Environment

- Conda env: `rel_voto` (Python 3.11)
- `pip-system-certs` required for HuggingFace downloads through corporate proxy
- Run scripts via `python` directly (not `conda run`) — avoids Windows UTF-8 errors
- Set `PYTHONIOENCODING=utf-8` before running scripts
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
