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
- **Ingestion pipeline enhanced (2026-05-06) — session ended, continuing from home computer**
  - TOC artifact fix applied (`chunking.py`)
  - `stage`/`dimension` metadata added to SQLite + LanceDB schema
  - `--coverage` flag added to `check_lancedb_chunks.py`
  - `Plan/06_Models/M5D_reference.md` created (all 46 Ações structured reference)
  - Re-ingest completed on work machine: 271 chunks, 45/46 coverage (Ação 15 missing from source)
  - **Home machine: pull git, follow re-ingest reminder below before continuing**
- To run scripts on Windows (avoids encoding errors): `set PYTHONIOENCODING=utf-8` then call Python directly, e.g. `python scripts/check_lancedb_chunks.py --heading "Ação 2"`

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

### M5D ingestion: done (re-ingest required — see reminder below)
- `doc_id = "m5d_md_v1"`, `max_chars=3500`, `overlap_chars=350`
- `start_char`/`end_char` are offsets in the **normalized** text (post `normalize_pdf_headings`) — validation must apply the same normalization step.
- Schema now includes `stage` and `dimension` columns (added 2026-05-06).

### ⚠️ REMINDER: Re-ingest M5D on home computer (pending as of 2026-05-06)
Pipeline changes were made on the **work computer** and committed to git. After pulling on the **home computer**, run:

```bash
# 1. Install package + system certs (corporate proxy fix — do once)
pip install -e .
pip install pip-system-certs

# 2. Re-ingest
maturity-check ingest-m5d

# 3. Validate (run Python directly to avoid conda UTF-8 issues on Windows)
set PYTHONIOENCODING=utf-8
python scripts/check_lancedb_chunks.py --coverage
python scripts/validate_sqlite_chunks.py
```

**Environment notes (work machine, confirmed 2026-05-06):**
- Conda env: `rel_voto` (upgraded to Python 3.11 — was 3.9, incompatible with `>=3.11` requirement)
- `pip-system-certs` required to trust corporate proxy CA for HuggingFace model download
- Run scripts directly via `python` (not `conda run`) to avoid Windows cp1252/UTF-8 encoding errors on Portuguese text
- HuggingFace model now cached at `C:\Users\sanseri\.cache\huggingface\hub\`

Why re-ingest is required:
1. **TOC `continue` fix** (`chunking.py`) — TOC `Ação N:` lines now skipped; previous data has ~12 polluted artifact chunks.
2. **`stage`/`dimension` columns** — new in SQLite + LanceDB schema; existing rows have `NULL` until re-ingest.
3. **`db.py` migration block** — `ALTER TABLE` in `init_framework_schema` handles pre-existing SQLite. Delete those lines (tagged `TODO(migration)`) once re-ingest is confirmed on **both** machines.

### Next: ingest Rio Manual and TCDF IN
Before ingesting, check these three things per new document:
1. **Heading patterns** — `normalize_pdf_headings` was written for M5D's PDF-conversion style. Verify whether Rio Manual / TCDF IN produce the same running-header patterns, or add new regex rules.
2. **Unique `doc_id`** — use stable IDs like `"rio_manual_v1"` and `"tcdf_in_v1"`. The `doc_id` is hardcoded in `m5d_ingest.py`; each new doc needs its own ingest function or a parameterized version.
3. **Validate after ingestion** — use `start_char`/`end_char` against the normalized source to confirm chunks round-trip correctly before embedding.

### M5D LanceDB chunk validation — tooling complete (2026-05-06)
`scripts/check_lancedb_chunks.py` is the spot-check + coverage tool.

- `--coverage` flag: reports which of 46 Ações are present/missing/TOC-only in content chunks.
- `Plan/06_Models/M5D_reference.md`: structured bilingual reference of all 46 Ações with stage and dimension — ground truth for validation and the mapping dict.
- Root causes identified and fixed: TOC artifact leak (`chunking.py`), missing `stage`/`dimension` metadata (`m5d_ingest.py` + `db.py`).

**Re-ingest run on work machine (2026-05-06). Results:**
- 271 chunks ingested, `stage`/`dimension` populated
- Coverage: **45/46** — Ação 15 confirmed missing from source PDF (short section, mostly diagrams)
- TOC artifacts: partially resolved — wrapped multi-line ToC titles still slip through (1-char per artifact, correctly labeled, not retrieval-breaking)
- Ação 46: 80 chunks — Annexes (Anexo 1–10) absorbed into it; not a Phase 1 concern
- SQLite validator: 11 off-by-one offset mismatches (pre-existing, 1-char diff, identical content — investigate separately)

---

## Preferences & Working Style

- Responses in **English** (docs bilingual PT+EN)
- Keep responses short and direct
- No unnecessary comments in code
- All plan documents are bilingual (PT + EN)
- Weekly deliverables include: code + screenshots + documentation (for both tech and non-tech audiences)
