# CLAUDE.md — PPP Maturity Check System


This file provides persistent context for Claude Code sessions: the current state and the
standing rules. Update it whenever significant decisions are made or status changes.
The dated record of every session (what was asked, measured, decided and left open) is
`HISTORICO.md` at the root, newest entry first: add one entry there per session and keep
this file short.

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

## Strategic Decisions (as of 2026-05-20; #2 and #4 updated 2026-10-15, #8 on 2026-10-16, #6 on 2026-11-15)

1. **Primary reference: IPMP** — operationalises each action into concrete expected
   products, scoring rubrics (0/1/3), and scored examples
   (Atendido / Parcialmente / Não Atendido).
2. **Secondary reference: Rio Manual** — provides document names and procedures
   used as retrieval hints when searching case documents. Populated for Ações 1
   and 2 only (`data/rio_manual/`): for the other 44, `retrieve_document_focused`
   returns None, so cascade steps A/B (the focal route) never fire and retrieval
   goes straight to step C (recorded 2026-10-15).
3. **TCDF IN: dropped.**
4. **Scoring: 0 / 1 / 3 per action** (46 actions, max = 138 total). The case's IPMP
   nota is the points over three times the Ações counted, computed on read (ADR-0075).
5. **Retrieval: BM25 (SQLite FTS5) + dense vector, deterministic.**
   Cascade per Ação: (A) exact document name match → (B) variant name match →
   (C) BM25 and vector fused via per-product Reciprocal Rank Fusion (RRF,
   k=60) — vector is **co-equal and always-on**, not a fallback, since
   ADR-0049 (superseded ADR-0033's "vector only on zero lexical results").
   `rio_hints` stays a BM25-only lane. Regex additive search (former Step D)
   was removed entirely (ADR-0052).
6. **LLM: temperature=0, fixed prompt per action.** IPMP criteria + scored
   examples embedded in prompt. Human auditor validates every score.
   **Sole provider: the owner's own GPU server** (`189.60.217.20`, reached only through an SSH tunnel on port 443 to server port 8083 via `LLAMACPP_BASE_URL`: the server port 8080 serves another, intermittent service and port 8080 is blocked on the client network, per the user on 2026-10-10; RTX 5070
   Ti, `gpt-oss-20b-F16.gguf` served by `llama-server.exe` = llama.cpp), for both
   the scorer and the pre-scoring relevance gate (ADR-0050, ADR-0059). GPU down
   → the run fails loudly; nothing falls back. The Groq/Ollama circuit-breaker
   chain (ADR-0054) was unwired on 2026-09-27 and deleted on 2026-11-15 (the
   user: they "se mostraram ineficientes em diversos momentos"); ADR-0054
   stays as the record of what was tried.
   **Naming rule (2026-10-02):** "llama.cpp" is the software running ON that
   GPU, not an alternative to it — `LlamaCppClient` IS the GPU client. Every
   measurement since ADR-0059 went to this server; the only Groq-based
   measurement in the project's history is the 2026-08-13 scoring probe, long
   superseded. Say "servidor GPU" for the provider; say "llama.cpp" only when
   its internals (slots, prompt cache, grammar) are the subject. Server-specific
   request parameters (`id_slot`, `cache_prompt`, …) are not to be used in
   production or diagnostics unless the user explicitly asks; the gpt-oss
   `reasoning_effort` level is a MODEL setting, not a server internal.
7. **Reproducibility** is the core academic constraint (professor's requirement).
   BM25 (deterministic retrieval) + temperature=0 = same input → same score.
8. **Scope: all 46 Ações.** Phase 1 began with Ação 1 only. Since 2026-09-07 every
   Ação has its IPMP file and retrieval profile, and every assessment evaluates all
   46 (the scope comes from the IPMP store, ADR-0030). Every measurement so far uses
   one case (SMG-040). On 2026-10-16 the user accepted the stability margin and closed
   the scorer verification, the condition set for a second case document; the
   document is the user's to supply.
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
├── CLAUDE.md                ← this file: current state and standing rules
├── HISTORICO.md             ← dated record of every session, newest first
├── CONTEXT.md               ← domain glossary
├── main.py                  ← runtime entry point: GPU clients → configure → init_db → create_app
├── pyproject.toml, pytest.ini
├── docs/
│   ├── adr/                 ← 79 ADRs, next 0080- (0074 genre filter + document index; 0075 IPMP nota;
│   │                          0076 "não aplicável" for 45/46; 0077 narrative sections; 0078 re-evaluation
│   │                          after gate overrides; 0079 the idea of the document)
│   ├── dan/                 ← 2 Deferred Architecture Notes, both closed; next 0003-
│   ├── prd/                 ← PRDs of Modules 1–7
│   ├── prompts/             ← 01 grill-me, 02 to-PRD, 03 to-issues, 04 profile synthesis (no document),
│   │                          05 profile validation (against a real case document)
│   ├── handoffs/            ← design-session handoffs
│   └── *.pdf                ← IPMP Guide (TCU 2026), Rio Manual volumes, the SMG-040 case documents
├── src/
│   ├── ingestion/           ← Module 1: IPMP store (46 Ações), Rio Manual, acronyms, retrieval profiles,
│   │                          dependency edges (ADR-0070), genre exemptions (ADR-0074)
│   ├── extraction/          ← Module 2: Chunk, extract_document (word-count heuristic + OCR), noise.py
│   ├── retrieval/           ← Module 3: indexing, BM25 + vector fused by RRF (query/hybrid.py), document-
│   │                          focused steps A/B, genre/ (classifier, segmentation, narrative sections, index)
│   ├── evaluation/          ← Module 4: select_evidence (genre filter, gate, ledger, expansion), evaluate,
│   │                          margin (ADR-0068), dependency cap (ADR-0070), prompts, parser,
│   │                          llm/llamacpp.py (LlamaCppClient, the only client)
│   └── assessment/          ← Module 5: AssessmentService, maturity (ADR-0075), re-evaluation (ADR-0078),
│                              FastAPI app with 10 routes
├── frontend/                ← Module 7: Vue 3, built to frontend/dist and served by FastAPI
├── tests/                   ← 45 test files; 751 fast tests (`pytest -m "not slow"`)
├── scripts/
│   ├── diagnostics/         ← reproducibility.py (the battery harness) and the measurement scripts;
│   │                          candidates_*.py are in-memory patches for --candidates/--apply
│   ├── validation/          ← coverage map, evidence tracer, concordance report (LEIAME.md)
│   ├── a3_inspect_retrieval_acao2.py, a4_inspect_evaluation_acao2.py ← per-Ação template (prompt 05)
│   └── create_test_corpus.py
├── data/
│   ├── ipmp/                ← acao_01…46.json (source of truth), dependencias.json (54 edges),
│   │                          isencoes_genero.json (16 genre-exempt products)
│   ├── retrieval_profiles/  ← acao_01…46.json, all `observed`; 8a 15a 15c 14a 27a 27b 41a cut their
│   │                          lanes after the genre filter (ADR-0079)
│   ├── rio_manual/          ← Ações 1 and 2 only (steps A/B never fire elsewhere)
│   ├── acronyms/, sector_taxonomy.json, test_corpus/
│   ├── app.db               ← (gitignored) shared SQLite: chunks + FTS5, document index, evaluations,
│   │                          reviews, fingerprints, gate ledger
│   └── lancedb/             ← (gitignored) one vector table per process, named with a sha256 prefix
├── scratchpad/              ← (gitignored) acc/ cycle outputs and criterio_*.txt; servidor/ GPU-server scripts
└── _archive/                ← out of active development, listed in INDICE.md — DO NOT USE
```

---

## Current State (2026-11-15)

Modules 1–7 are complete. Every assessment evaluates all 46 Ações, and every measurement so far uses one
case: SMG-040, stored in `data/app.db` as `040_101607_2024`; the harness uses `SMG-040_101607_2024`. The
scorer verification closed on 2026-10-16. The next phase is improving PDF extraction; after it, the next strong test is a second case document, which the user
will supply. The full record is in `HISTORICO.md`; the 87th pass (2026-11-15) is its newest entry.

**Production configuration.** Change it only on the user's decision.
- **Retrieval:**
  - Steps A/B: document name match (Rio Manual, Ações 1–2 only).
  - Step C, per scored product: BM25 and vector fused by RRF (k=60), 20 per lane.
  - Genre filter (ADR-0074): instrument text leaves the pool before the gate. Narrative sections of instrument documents are released (ADR-0077). 16 products are genre-exempt.
  - Seven products cut their lanes after the genre filter (ADR-0079): 8a, 15a, 15c, 14a, 27a, 27b, 41a.
- **Gate** (servidor GPU, gpt-oss at `reasoning_effort` low, one call in flight, ADR-0065):
  - prompt: identity block with whole sibling texts (ADR-0064, ADR-0071) and the polarity sentence (ADR-0066);
  - pool handling: dedup at 0.92, 16 candidates examined, neighbour expansion behind the genre filter;
  - verdict ledger on in production (ADR-0067).
- **Scorer:**
  - Runs at the model's default effort.
  - It gives one verdict per product, and the code counts the 0/1/3 score (ADR-0058).
  - A deterministic margin goes with the score, plus an optional review signal (ADR-0068).
  - A dependency cap applies: no 3 when a `pre` dependency was not met (ADR-0070).
- **Maturity:**
  - The nota iPMP is computed on read and shown in the UI as "Percentual de aderência" (ADR-0075).
  - "Não aplicável" exists only for Ações 45 and 46, set by the auditor (ADR-0076).
  - Selected Ações can be re-evaluated after gate overrides (ADR-0078).

**Constancy** is the number of Ações with the same points in at least 9 of 10 full processes, counting
`sem evidência` as 0.
- The baseline is C17 and C18, two cycles of the same configuration: 41 and 39 of 46. The Ações below 9 of 10 are the documented residue: 2, 3, 10, 23 and 37 in both cycles, plus 32 and 35 in C18.
- The user accepted the stability margin on 2026-10-16.
- C18 measured the adopted state of 14a, 27a, 27b and 41a and passed its criterion (amendment to ADR-0079): 14 = 27 = 1 in 10/10, 41 = 1 in 9/10, no 3.
- A ten-process battery takes about 2 h 55 min, about 17 min per process: C17 took 2 h 54 min, C18 2 h 53 min.

**Stored case:**
- 46 evaluations from the forced `/assess` of 2026-11-06, and a populated gate ledger.
- No reviews: the 13 written during UI tests were deleted on 2026-11-15, at the user's request. The nota is 16/138 (11.6 %).
- These evaluations predate the adoption of 14a, 27a, 27b and 41a (Ação 27 is stored as `sem evidência`). A new `/assess` would bring them up to date.

**Repository:** everything up to the 88th pass is committed and pushed to `origin/main` (2026-11-25). The 24 commits from `e5e5fa1` on (now `e5898c4`) were rewritten before the push to drop two network addresses; `HISTORICO.md`, 88th pass, has the old to new hash map.

**Open for the user:**
- **The model does not start on the GPU server (since 2026-11-25).** Smart App Control is in enforcement there and blocks the unsigned `llama-server.exe` (task result 0x800711C7, CodeIntegrity events 3033/3077/3118). Turning it off on the server is the user's decision; Windows cannot turn it back on without a reset. `HISTORICO.md`, 88th pass.
- Revoke the Groq key in the Groq console. Its line was removed from `.env` on 2026-11-15 without reading the value. `GROQ_SSL_VERIFY` stays there, read by nothing.
- The C17 caveats: 41a reads the pre-publication justification; the 27a scorer names cost categories that no passage carries.
- **Next phase: improve PDF extraction (Module 2)**, before the second case document. The user will say when it starts (2026-11-15); do not start it before then.
- A second case document, later.
- Document dates in the document index, the precondition for any tempestividade test (later).
- Deferred: the 25a retrieval gap, 1b/3a canonicity, rotation of the fallback password.

**Key reference files:**
- `data/ipmp/acao_NN.json`: the IPMP source of truth.
- `docs/IPMP TCU2026 - Indicador_percepcao_maturidade.pdf`: the Guide.
- `scripts/diagnostics/reproducibility.py`: the battery harness.
- `scripts/diagnostics/audit_gate_prompts.py`: the gate prompt audit, digest and leakage.
- `scratchpad/servidor/LEIAME.txt`: how to drive the GPU server.
- `docs/prompts/04_*` and `05_*`: profile synthesis and validation.

---

## Standing Rules

**GPU server and access**
- The only LLM is the owner's GPU server. The model runs on server port 8083 and is reached only through an SSH tunnel on port 443: `ssh -N -L 18083:192.168.0.132:8083 -p 443 -i ~/.ssh/maturity_llmserver sshadmin@189.60.217.20`, with `LLAMACPP_BASE_URL=http://127.0.0.1:18083`.
- Never use port 8080. Never start the OCR task 8082 alongside the model, nor anything alongside another llama-server.
- **Before any GPU work:**
  - Run a read-only `gpu_livre.ps1` through `scratchpad/servidor/ssh_ps_file.py`.
  - Others use that GPU, for games too. If it does not read LIVRE, do not run: tell the user and wait for the go-ahead.
  - Long runs carry an alert-only GPU watch.
- Start the model with `sobe_8083.ps1`. Stop it with `para_8083.ps1` after setting `$alvo` to the current llama-server PID. In PowerShell strings write `$($x):`, never `$x:`.
- Remote scripts go only as a `.ps1` file through `ssh_ps_file.py` (scp, then `powershell -File`).
- Never run encoded, compressed or generated PowerShell on this workstation (`-EncodedCommand`, gzip, `[scriptblock]::Create`), not even as a local test: the corporate antivirus kills it. If creating powershell.exe or cmd.exe returns "Acesso negado", stop, tell the user, and never retry.
- Server-internal request parameters (`id_slot`, `cache_prompt`) are used only when the user asks. Say "servidor GPU" for the provider.
- When reading `.secrets/llm_server_access.md`, drop the password lines. Do not read `.env`.

**Measurement**
- Constancy is measured only across independent full 46-Ação processes, with the ledger off (ADR-0071). Single-Ação runs and in-process passes give direction only.
- A battery is one invocation of `reproducibility.py --runs N`. No runner of mine resumes it or fills gaps. Disclose every helper, such as the tunnel and the GPU watch.
- Write the criterion in `scratchpad/acc/criterio_cicloN.txt` before the first model call.
- Adoption needs non-inferiority (constancy, no new confusion) plus a legitimate target, and the user decides it.
- Report the direction on the target and the constancy of the outcome separately: removing one false coin can make the outcome less constant.
- Judge prompt-wide variants by full-process aggregates, never by named pairs in one process.

**Content**
- Query terms, concepts and negative patterns are document-agnostic (ADR-0073). The case only tests them; it never sources them.
- Never return instrument text to the gate as a general rule, and never write negative patterns tailored to this case's pages. Narrative sections are the one exception (ADR-0077).
- An IPMP field left unset or never loaded is a relevant defect: verify it against the Guide, fix the data, and pin it with a test.
- Diagnose the class of defect, not the Ação: the next case will not break in the same items.

**Code and records**
- Preserve the architecture and the behaviour; no broad refactor. Delete only what is shown useless, and only once the user approves.
- Retrieval profiles are hand-formatted JSON:
  - edit them textually and verify by content;
  - keep their line endings;
  - never `sed -i` repo files.
- Commit only when the user asks; push only when asked. Never put the user's personal details in an external request.
- Add one entry per session to `HISTORICO.md`, newest first. This file keeps only the current state and the rules.

---

## Environment

- `python` on PATH is the base Anaconda (3.13); it ran cycles 17 and 18. The conda env `rel_voto` (Python 3.11)
  has the same sentence-transformers (5.4.1) and LanceDB (0.30.2) versions
- Install: `SETUPTOOLS_USE_DISTUTILS=stdlib pip install -e .`; fast tests: `pytest -m "not slow"`; all tests
  (OCR) need `TESSERACT_CMD`
- `pip-system-certs` required for HuggingFace downloads through corporate proxy
- Run scripts via `python` directly (not `conda run`) — avoids Windows UTF-8 errors
- Set `PYTHONIOENCODING=utf-8` before running scripts
- Set `TESSERACT_CMD=C:\Users\sanseri\AppData\Local\Programs\Tesseract-OCR\tesseract.exe` — conda subprocess does not inherit User-level PATH; set in `.claude/settings.local.json`
- HuggingFace model cached at `C:\Users\sanseri\.cache\huggingface\hub\`
- Set `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1` before running anything that calls `retrieval/query/vector.py` (i.e. any real assessment run) — a newer `transformers`/`huggingface_hub` probes for an optional `adapter_config.json` on huggingface.co even for a fully-cached, non-adapter model, and that probe fails with `SSL: CERTIFICATE_VERIFY_FAILED` behind the corporate proxy (confirmed 2026-08-25, `pip-system-certs`'s truststore injection doesn't cover it). The offline flags skip the network probe entirely and use the local cache, which already has the model.

---

## Tools in Use

| Layer | Tool |
|---|---|
| Language | Python 3.11–3.13 / Anaconda |
| Web framework | FastAPI + uvicorn |
| Structured DB | SQLite (WAL + FTS5 for BM25) |
| Vector DB | LanceDB (co-equal with BM25, always-on, fused via per-product RRF — ADR-0049) |
| PDF extraction | `unstructured[pdf]` (layout-aware, OCR) |
| Embeddings | sentence-transformers (local CPU, fixed model, offline flags — co-equal vector lane, not a fallback) |
| LLM evaluation | **Owner's GPU server only** — `189.60.217.20`, server port 8083 reached through an SSH tunnel on 443 (`LLAMACPP_BASE_URL=http://127.0.0.1:18083`; never 8080), RTX 5070 Ti 16 GB, `gpt-oss-20b-F16.gguf` served by `llama-server.exe` (llama.cpp b8198), scorer + gate, temperature 0, grammar-constrained JSON (ADR-0053, ADR-0059). No fallback: the Groq/Ollama clients were deleted on 2026-11-15. Bring-up/stop procedure and credentials: `.secrets/llm_server_access.md` (gitignored). Server-control scripts: `scratchpad/servidor/` (gitignored), run only through `ssh_ps_file.py` (a `.ps1` copied and run with `-File`, never encoded). |
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

Prompt file: `docs/prompts/01_grill-me.md`.
to-PRD skill: `docs/prompts/02_To-PRD.md`.
IPMP reference PDF: `docs/IPMP TCU2026 - Indicador_percepcao_maturidade.pdf`.

Use before designing each new module to stress-test the plan against the domain model and documented decisions. Updates CONTEXT.md and ADRs inline as decisions crystallise — do not batch.

During a grill-me session: challenge terminology against CONTEXT.md, sharpen fuzzy language, stress-test with concrete scenarios, cross-reference with code when relevant.
