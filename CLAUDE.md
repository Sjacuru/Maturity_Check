# CLAUDE.md — M5D Evaluation System

This file provides persistent context for Claude Code sessions across machines.
Update it whenever significant decisions are made or status changes.

---

## Project Overview

**Name:** Project Evaluation System
**Developer:** Solo (Salim / sjacuru@gmail.com)
**Working directory:** `c:\Users\sanseri\Documents\Projetos\Maturity_Check`
**GitHub:** https://github.com/Sjacuru/Maturity_Check
**Language of docs:** Bilingual PT + EN throughout

A document analysis tool that helps Brazilian public auditors evaluate procurement processes against the **Modelo de Cinco Dimensões (M5D)** framework — 46 actions across 3 stages and 5 dimensions. The system retrieves evidence from case documents and produces scored, evidence-backed audit reports for human review.

---

## Stakeholders

- **2 Internal Bosses** — non-technical; receive weekly email status + non-tech deliverable docs
- **Master's Degree Adviser (Professor)** — technical; bi-weekly meetings, receives technical reports

---

## Current Status (as of 2026-05-07)

- PRD: complete, awaiting formal human sign-off
- EPIC document: drafted (`Plan/02_EPIC/EPIC_DOCUMENT.md`)
- Phase 1 plan: complete (`Plan/08_TASK_REGISTRY/PHASE_1_DETAILED_PLAN.md`)
- **We are in Week 1 of Phase 1** (started 2026-04-28)
- Week 1 goal: environment setup (VS Code, Python 3.11, Ollama, SQLite, LanceDB)
- **Ingestion pipeline enhanced (2026-05-06/07)** — TOC fix, stage/dimension metadata, subtask-level chunking (home machine); work machine needs re-ingest (see below)
- **PDF-to-MD tooling extracted (2026-05-07)** — removed from this project; lives in a separate standalone system (see Architecture Decisions)
- To run scripts on Windows (avoids encoding errors): `set PYTHONIOENCODING=utf-8` then call Python directly

### ⏭️ Where to resume next session

1. **Work machine re-ingest** — `Plan/09_TOOLS/` removed; pull git, delete `data/framework.sqlite`, run `python -m maturity_check.cli ingest-m5d`; expected 321 chunks, 45/46 coverage.
2. **Intra-corpus retrieval test** — validate that subtask-level chunks return correct results when queried with subtask descriptions. Run dense vector search on `reference_m5d_chunks` using Ação 1 subtask queries and confirm ranking quality before moving to case document ingestion.
3. **Continue chunk-by-chunk validation** — stopped at Ação 1. Ação 2 structure understood (subtasks i–ix) but not validated. Resume from `python scripts/dump_chunks.py --heading "Ação 2"`.
4. **Retrieval pipeline** (`reference_search.py`) — not yet started; implement after ingestion is confirmed clean on both machines.
5. **Await clean M5D source** — when the Deterministic Semantic Document Reconstruction System delivers `m5d_clean.md`, re-ingest from it, validate 46 Ações + subtask hierarchy, then retire `normalize_pdf_headings` heuristics for M5D.

---

## Timeline

| Phase | Duration | End Date | Goal |
|-------|----------|----------|------|
| Phase 1 | 5 weeks (~200h) | 2026-05-29 | MVP: CLI + hybrid retrieval + LLM eval (Ação 1) |
| Phase 2 | 26 weeks (~1000h) | 2026-11-20 | All 46 M5D actions + Web UI + production deploy |

---

## Key Architecture Decisions

- **LLM policy by document publication status** (OQ-005 rev. 2026-05-06):
  - **Phase 1 — published documents** (reference docs + already-shared procurement cases) → external LLM allowed everywhere; no residency restriction
  - **Future phases — unpublished / in-progress project documents** → local-first per NFR-008; external opt-in requires explicit config + audit log
- **LLM Phase 1:** External API (Claude / Groq) for all reasoning; embeddings always local
- **LLM future (unpublished cases):** Ollama local for case evaluation and assurance pass
- **Embeddings:** Always local (sentence-transformers — case text must never reach embedding API)
- **Retrieval:** Hybrid BM25 sparse + dense semantic (LanceDB) with deterministic fusion (FR-008D)
- **Crosswalk:** policy/retrieval layer — not a UI feature (FR-008A)
- **Output assurance:** single structured judge pass before persistence (FR-021)
- **No autonomous agent loops in v1** — system produces recommendations, auditor is final authority
- **No invented latency thresholds** — measure first (OQ-004 / NFR-006)
- **PDF-to-MD tooling is a separate system (2026-05-07):** The Deterministic Semantic Document Reconstruction System lives in its own repository. This project consumes its output (`m5d_clean.md`, `rio_manual_clean.md`, etc.) but does not own or build the converter. GitHub issue #[see repo] tracks the dependency.

---

## Tech Stack

| Layer | Tool |
|-------|------|
| Language | Python 3.11+ / Anaconda |
| Structured DB | SQLite |
| Vector DB | LanceDB |
| Sparse index | BM25 (whoosh) |
| Embeddings | sentence-transformers (local) |
| LLM — Phase 1 (published docs) | External API (Claude / Groq) — all reasoning |
| LLM — unpublished case docs | Ollama (Mistral, localhost:11434) — local per NFR-008 |
| LLM — assurance pass (unpublished) | Ollama (Mistral, temp=0) — local per NFR-008 |
| Web framework | FastAPI |
| Frontend | Vue.js 3 |
| CLI | Python argparse |

---

## Key Files

| File | Purpose |
|------|---------|
| `Plan/01_PRD/prd.md` | Full product requirements |
| `Plan/02_EPIC/EPIC_DOCUMENT.md` | EPIC breakdown and user stories |
| `Plan/08_TASK_REGISTRY/PHASE_1_DETAILED_PLAN.md` | Week-by-week Phase 1 tasks |
| `Plan/08_TASK_REGISTRY/PHASE_2_DETAILED_PLAN.md` | Block-by-block Phase 2 tasks |
| `Plan/08_TASK_REGISTRY/EXECUTIVE_SUMMARY_AND_TIMELINE.md` | Summary for stakeholders |
| `Plan/07_RETRIEVAL/OQ-005_resolution.md` | LLM architecture decision (local vs Groq) |
| `Plan/07_RETRIEVAL/OQ-007_hybrid_retrieval_strategy.md` | BM25 vs dense vs hybrid decision — read before building `reference_search.py` |
| `Plan/08_TASK_REGISTRY/00_START_HERE.md` | Deliverables summary from 2026-04-28 session |
| `Plan/06_Models/M5D.md` | M5D framework model (raw PDF conversion — will be replaced by clean version from separate system) |
| `Plan/06_Models/M5D_reference.md` | Ground truth: all 46 Ações with stage/dimension mapping |
| `scripts/check_lancedb_chunks.py` | LanceDB spot-check + coverage tool |
| `scripts/dump_chunks.py` | Full-text chunk dump for side-by-side comparison with source |

---

## Ingestion — Current State & Next Steps

### Storage split (confirmed)
- **SQLite** (`data/framework.sqlite`): source of truth — full chunk text, heading paths, character offsets, hashes. Tables: `reference_documents`, `reference_chunks`.
- **LanceDB** (`data/lancedb/reference/`): search index — same text + `float32` vectors (dim 384, `paraphrase-multilingual-MiniLM-L12-v2`). Table: `reference_m5d_chunks`. No offsets here.

### M5D ingestion: subtask-level chunking active (home machine, 2026-05-07)
- `doc_id = "m5d_md_v1"`, `max_chars=3500`, `overlap_chars=350`
- **321 chunks**, 45/46 coverage — Ação 15 missing from source (graphics-heavy section, not a code issue)
- `stage`/`dimension` columns populated for all 45 covered Ações
- Annexes (Anexo 1–10) each have correct heading paths; no longer absorbed into Ação 46
- Subtask items (`i.`, `ii.`, `iii.`...) promoted to `####` level — each has its own chunk
- 6 `(no heading)` chunks: cover pages, legal/ISBN, preface, TOC — kept in DB, filtered at query time

### ⚠️ Work machine re-ingest required (as of 2026-05-07)
`chunking.py` was updated on home machine (subtask + annex fixes). On work machine, after `git pull`:

```bash
del data\framework.sqlite
set PYTHONIOENCODING=utf-8
python -m maturity_check.cli ingest-m5d
python scripts/check_lancedb_chunks.py --coverage
```

Expected result: **321 chunks, 45/46 coverage**.

**Environment notes (work machine):**
- Conda env: `rel_voto` (Python 3.11 — upgraded from 3.9)
- `pip-system-certs` required for HuggingFace model download through corporate proxy
- Run scripts via `python` directly (not `conda run`) to avoid Windows UTF-8 encoding errors
- HuggingFace model cached at `C:\Users\sanseri\.cache\huggingface\hub\`

### `chunking.py` — normaliser logic (as of 2026-05-07)
`normalize_pdf_headings` handles M5D-style PDF-converted markdown:

| Pattern | Detection | Action |
|---------|-----------|--------|
| Book-title running headers | `_PDF_BOOK_TITLE_RE` | Stripped entirely |
| Chapter running headers (`Capítulo N:`) | `_PDF_CHAPTER_RE` | First occurrence → `##`; rest deduplicated |
| Action body headings (`Ação N:`) | `_PDF_ACTION_RE` | Non-TOC → `###`; TOC (trailing digits/underscores) → dropped |
| Annex headings (`Anexo N`) | `_PDF_ANNEX_RE` | Non-TOC → `##`; deduplicated; wrapped running-headers detected by prefix match |
| Subtask items (`i.`, `ii.`, `iii.`...) | `_PDF_SUBTASK_RE` | Promoted to `####`; description kept as both heading and first body line |

### Next: ingest Rio Manual and TCDF IN
Before ingesting each new document:
1. **Test `normalize_pdf_headings`** against the new file — M5D patterns may not apply; add new regexes if needed
2. **Assign a stable `doc_id`** (e.g., `"rio_manual_v1"`) and create a dedicated ingest function
3. **Validate after ingestion** — use `check_lancedb_chunks.py` and `validate_sqlite_chunks.py` before proceeding

---

## Deterministic Semantic Document Reconstruction System (separate project)

**Decision made: 2026-05-07** — The PDF-to-Markdown converter was extracted out of this project into a standalone system. Rationale: it is a general-purpose tool applicable beyond M5D, and keeping it here bloated the scope of this repo.

**What it does:** Converts PDF-origin documents into clean, structured Markdown with deterministic heading hierarchy — no heuristic normalisation needed downstream.

**Interface to this project:**
- Input: raw PDF (M5D, Rio Manual, TCDF IN, etc.)
- Output: clean `.md` file delivered to `Plan/06_Models/` (e.g., `m5d_clean.md`)
- This project then ingests the clean file directly — `normalize_pdf_headings` heuristics become redundant for M5D once the clean file arrives

**Tracked via:** GitHub issue on this repo (see issue created 2026-05-07) linking to the separate system's repository.

---

## Evaluation Pipeline Design — Decisions Made (2026-05-07)

### Chunking strategy: subtask-level (implemented)
```
## Capítulo N                     (chapter)
### Ação N: ...                   (action)
#### i. [subtask description]     (individual evaluation criterion)
```
Retrieval and scoring at subtask level → aggregation up to Ação → Dimensão → Stage → Final report.

### Evaluation flow (agreed, not yet implemented)
For each Ação → for each subtask: retrieve top-K from case doc (hybrid BM25 + dense) → LLM scores (present/partial/absent + confidence) → aggregate.

### Query formulation (decided)
Use both subtask verbatim text AND a rephrased question form.

### Retrieval strategy (OQ-007, decided)
Always run BM25 + dense, always fuse — no routing. See `Plan/07_RETRIEVAL/OQ-007_hybrid_retrieval_strategy.md`.

---

## Preferences & Working Style

- Responses in **English** (docs bilingual PT+EN)
- Keep responses short and direct
- No unnecessary comments in code
- All plan documents are bilingual (PT + EN)
- Weekly deliverables include: code + screenshots + documentation (for both tech and non-tech audiences)