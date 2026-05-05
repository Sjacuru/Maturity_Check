# CLAUDE.md — M5D Evaluation System

This file provides persistent context for Claude Code sessions across machines.
Update it whenever significant decisions are made or status changes.

---

## Project Overview

**Name:** M5D Evaluation System
**Developer:** Solo (Salim / sjacuru@gmail.com)
**Working directory:** `c:\Users\sanseri\Documents\Projetos\Maturity_Check`
**GitHub:** https://github.com/Sjacuru/Maturity_Check
**Language of docs:** Bilingual PT + EN throughout

A document analysis tool that helps Brazilian public auditors evaluate procurement processes against the **Modelo de Cinco Dimensões (M5D)** framework — 46 actions across 3 stages and 5 dimensions. The system retrieves evidence from case documents and produces scored, evidence-backed audit reports for human review.

---

## Stakeholders

- **2 Internal Bosses** — non-technical; receive weekly email status + non-tech deliverable docs
- **Master's Degree Adviser (Professor)** — technical; bi-weekly meetings, receives technical reports
- Salim is the sole developer

---

## Current Status (as of 2026-05-04)

- PRD: complete, awaiting formal human sign-off
- EPIC document: drafted (`Plan/02_EPIC/EPIC_DOCUMENT.md`)
- Phase 1 plan: complete (`Plan/08_TASK_REGISTRY/PHASE_1_DETAILED_PLAN.md`)
- **We are in Week 1 of Phase 1** (started 2026-04-28)
- Week 1 goal: environment setup (VS Code, Python 3.11, Ollama, SQLite, LanceDB)

---

## Timeline

| Phase | Duration | End Date | Goal |
|-------|----------|----------|------|
| Phase 1 | 5 weeks (~200h) | 2026-05-29 | MVP: CLI + hybrid retrieval + LLM eval (Ação 1) |
| Phase 2 | 26 weeks (~1000h) | 2026-11-20 | All 46 M5D actions + Web UI + production deploy |

---

## Key Architecture Decisions

- **Local-first** (NFR-008 + OQ-005): no external transmission of case document text by default
- **LLM Phase 1:** Ollama local (Mistral) — no API calls
- **LLM Phase 2+:** Groq API optional opt-in fallback
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
| LLM Phase 1 | Ollama (Mistral, localhost:11434) |
| LLM Phase 2+ | Groq API (optional) |
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

## Preferences & Working Style

- Responses in **English** (docs bilingual PT+EN)
- Keep responses short and direct
- No unnecessary comments in code
- All plan documents are bilingual (PT + EN)
- Weekly deliverables include: code + screenshots + documentation (for both tech and non-tech audiences)
