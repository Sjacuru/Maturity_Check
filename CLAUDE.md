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
- **M5D ingestion validated and clean on home machine (2026-05-07):** 270 chunks, 45/46 coverage
- **⚠️ Work machine needs re-ingest** — pull git, delete `data/framework.sqlite`, run `python -m maturity_check.cli ingest-m5d`
- To run scripts on Windows (avoids encoding errors): `set PYTHONIOENCODING=utf-8` then call Python directly, e.g. `python scripts/check_lancedb_chunks.py --coverage`

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

### M5D ingestion: clean and validated (home machine, 2026-05-07)
- `doc_id = "m5d_md_v1"`, `max_chars=3500`, `overlap_chars=350`
- **270 chunks**, 45/46 coverage — Ação 15 missing from source (graphics-heavy section, not a code issue)
- `stage`/`dimension` columns populated for all 45 covered Ações
- Annexes (Anexo 1–10) each have correct heading paths; no longer absorbed into Ação 46
- `start_char`/`end_char` are offsets in the **normalized** text (post `normalize_pdf_headings`)

### ⚠️ Work machine re-ingest required (as of 2026-05-07)
`chunking.py` was updated on home machine. On work machine, after `git pull`:

```bash
# Delete old database (schema + data incompatible with migration block removed)
del data\framework.sqlite

# Re-ingest
set PYTHONIOENCODING=utf-8
python -m maturity_check.cli ingest-m5d

# Validate
python scripts/check_lancedb_chunks.py --coverage
```

Expected result: **270 chunks, 45/46 coverage**.

**Environment notes (work machine):**
- Conda env: `rel_voto` (Python 3.11)
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

Key fixes applied (2026-05-07):
- `_PDF_ANNEX_RE`: requires `(?:\s|–|$)` after number — avoids matching inline refs like `"Anexo 9."` in body text
- `_PDF_TOC_ANNEX_RE`: stricter TOC check for annexes (requires `_{2,}`) — avoids false-positive on `"Princípios do G20"` (G20 ends in digits)
- `seen_annex_headings`: deduplicates annex running-headers the same way chapters are deduplicated
- Prefix check: wrapped running-headers (2–3 line wraps, with or without trailing space) are detected as prefixes of known full titles and skipped
- Trailing-space join: handles the case where first body occurrence is itself wrapped (e.g., Anexo 3)
- Switched from `for` loop to `while i` (index-based) to enable look-ahead and multi-line joins

### `check_lancedb_chunks.py` — validation tool (as of 2026-05-07)
- `--coverage`: reports 45/46 Ações present; shows missing list
- Default run: shows all heading paths in **logical (numeric) order**, indented by depth
- Content chunks and TOC artifact chunks shown in separate sections
- `--heading "Ação N"`: exact segment match — `"Ação 1"` does NOT match `"Ação 10"`
- `--limit 0` (default): no cap on results; `--show-text`: full chunk text

### Next: ingest Rio Manual and TCDF IN
Before ingesting each new document:
1. **Test `normalize_pdf_headings`** against the new file — M5D patterns may not apply; add new regexes if needed
2. **Check heading wrap patterns** — different PDFs wrap differently; the prefix-dedup logic handles M5D style but verify
3. **Assign a stable `doc_id`** (e.g., `"rio_manual_v1"`) and create a dedicated ingest function
4. **Validate after ingestion** — use `check_lancedb_chunks.py` and `validate_sqlite_chunks.py` before proceeding

---

## Preferences & Working Style

- Responses in **English** (docs bilingual PT+EN)
- Keep responses short and direct
- No unnecessary comments in code
- All plan documents are bilingual (PT + EN)
- Weekly deliverables include: code + screenshots + documentation (for both tech and non-tech audiences)
