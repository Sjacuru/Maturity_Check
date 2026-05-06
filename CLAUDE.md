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

## Current Status (as of 2026-05-06)

- PRD: complete, awaiting formal human sign-off
- EPIC document: drafted (`Plan/02_EPIC/EPIC_DOCUMENT.md`)
- Phase 1 plan: complete (`Plan/08_TASK_REGISTRY/PHASE_1_DETAILED_PLAN.md`)
- **We are in Week 1 of Phase 1** (started 2026-04-28)
- Week 1 goal: environment setup (VS Code, Python 3.11, Ollama, SQLite, LanceDB)
- `scripts/check_lancedb_chunks.py` — improved and functional; used for M5D chunk validation (see below)

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
| `Plan/08_TASK_REGISTRY/00_START_HERE.md` | Deliverables summary from 2026-04-28 session |
| `Plan/06_Models/M5D.md` | M5D framework model |

---

## Ingestion — Current State & Next Steps

### Storage split (confirmed)
- **SQLite** (`data/framework.sqlite`): source of truth — full chunk text, heading paths, character offsets, hashes. Tables: `reference_documents`, `reference_chunks`.
- **LanceDB** (`data/lancedb/reference/`): search index — same text + `float32` vectors (dim 384, `paraphrase-multilingual-MiniLM-L12-v2`). Table: `reference_m5d_chunks`. No offsets here.

### M5D ingestion: done
- `doc_id = "m5d_md_v1"`, `max_chars=3500`, `overlap_chars=350`
- `start_char`/`end_char` are offsets in the **normalized** text (post `normalize_pdf_headings`) — validation must apply the same normalization step.

### Next: ingest Rio Manual and TCDF IN
Before ingesting, check these three things per new document:
1. **Heading patterns** — `normalize_pdf_headings` was written for M5D's PDF-conversion style. Verify whether Rio Manual / TCDF IN produce the same running-header patterns, or add new regex rules.
2. **Unique `doc_id`** — use stable IDs like `"rio_manual_v1"` and `"tcdf_in_v1"`. The `doc_id` is hardcoded in `m5d_ingest.py`; each new doc needs its own ingest function or a parameterized version.
3. **Validate after ingestion** — use `start_char`/`end_char` against the normalized source to confirm chunks round-trip correctly before embedding.

### M5D LanceDB chunk validation — in progress (2026-05-06)
`scripts/check_lancedb_chunks.py` is the spot-check tool. Key findings so far:

1. **TOC artifact chunks exist** — ~12 depth-0 heading_paths like `"Ação 7: Defina o escopo..."` (no chapter prefix, text is page numbers). These are table-of-contents lines ingested as real chunks. They will pollute retrieval results and must be filtered out at ingestion time for future documents.
2. **Ação 15 appears missing** — not present in either content or TOC sections of the summary. Needs verification against `Plan/06_Models/M5D.md`.
3. **Heading filter rule** — use segment-startswith match (`"Ação 1"` must match `"Ação 1: ..."` but not `"Ação 10: ..."`). Implemented in the script via regex `^{term}(?:[:\s]|$)` per segment after splitting on `" > "`.
4. **Ordinal ≠ logical order** — TOC entries get low ordinals (appear first in PDF), so sorting by ordinal puts TOC before chapter content. Summary now sorts by numbers extracted from heading segments.

**Next action:** compare `check_lancedb_chunks.py` output against `Plan/06_Models/M5D.md` to identify all missing or malformed Ações before ingesting new documents.

---

## Preferences & Working Style

- Responses in **English** (docs bilingual PT+EN)
- Keep responses short and direct
- No unnecessary comments in code
- All plan documents are bilingual (PT + EN)
- Weekly deliverables include: code + screenshots + documentation (for both tech and non-tech audiences)
