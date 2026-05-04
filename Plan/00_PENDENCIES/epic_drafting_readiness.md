# EPIC drafting readiness (local-first)

This page is the “go/no-go” for starting the **EPIC drafting prompt**. It is intentionally short.

## Ready to draft EPIC now (engineering)

- **Local-first assumption is allowed** for EPIC drafting: evaluation of **case document text** uses **local models** by default (OQ-005 engineering baseline).
- **Crosswalk policy is authored** for **Ação 1** (Rio + TCDF pooled hooks) under `Plan/06_Models/crosswalk/`.
- **Reference corpus spike exists**: M5D chunks in **SQLite**, and semantic reference search via **LanceDB** + `sentence-transformers`.
- **Retrieval policy docs exist**: staged retrieval floor, tiered expansion, and hybrid direction are documented (PRD + `Plan/07_RETRIEVAL/`).

## Must be explicit in EPIC (don’t hand-wave)

EPIC MUST include explicit stories/tasks for:

- **Case corpus ingestion** (PDF/text → segments) and building **both** sparse + dense indices for the same `segment_id` set (FR-006 + FR-008D).
- **Crosswalk → retrieval wiring** (FR-008A/B/C): pooled hook list, tier expansion, satisficing, overlay weighting.
- **Hybrid fusion** method (FR-008D): document the fusion formula (e.g., RRF) and constants.
- **Retrieval audit log** persistence (FR-014 / FR-014A intent): inputs, candidates, scores, fused ordering, selected evidence packet.
- **FR-021 assurance pass**: deterministic validation step after evaluator output, before persistence.

## Not blocking EPIC drafting, but blocks **production** decisions

- **OQ-005 (production gate)**: any path that sends **case document text** outside the environment (external LLM / external document service) requires **legal/security sign-off**. EPIC may still draft both branches, but **default** remains local-first.
  - **Authoritative constraint docs** (EPIC must follow): `Plan/07_RETRIEVAL/nfr_008_deployment_boundary.md` (boundary rules) + `Plan/07_RETRIEVAL/OQ-005_resolution.md` (implementation details: opt-in, config, audit log).

## Deferred until pilot metrics (don’t invent numbers)

- **OQ-004 / NFR-006 numeric SLO**: EPIC/MDAP should log measured wall-clock baselines first; set seconds targets only after pilot.
- **Pilot calibration**: `retrieval_floor_stage2`, hit/weak/none cutoffs, embedding model id adjustments for Portuguese legal corpora.

---

## Appendix: Boundaries + Run Steps

This appendix provides the operational checklist for going from "pre-EPIC done" to EPIC draft(s) without scope drift. Set boundaries before pasting or running the EPIC drafting prompt.

### 0) What is already accomplished (snapshot)

Use this as the "we are here" line before EPIC drafting.

| Area | Status |
|------|--------|
| PRD north star | `Plan/01_PRD/prd.md` — full product scope |
| Pre-EPIC resolved decisions | `Plan/00_PENDENCIES/pre_epic_resolved_decisions.md` |
| Open pre-EPIC items only | `Plan/00_PENDENCIES/pendencias_pre_epic.md` (OQ-004 deferred; pilot tuning open) |
| EPIC go/no-go | `Plan/00_PENDENCIES/epic_drafting_readiness.md` — **GO** for engineering EPIC draft (local-first) |
| Retrieval / NFR-008 / OQ-005 | `Plan/07_RETRIEVAL/` — boundary + satisficing + vector options + `OQ-005_resolution.md` |
| Ação 1 crosswalk | `Plan/06_Models/crosswalk/` — templates + verification |
| Reference ingest spike | `src/maturity_check/` + `maturity-check` CLI; trace in `pre_epic_implementation_trace.md` |
| Dev setup inventory | `Plan/09_SETUP/installation_inventory.md` |
| Ollama | You confirmed install **worked** — ready for later FR-009/010/021 wiring per EPIC |

**Confirmed next step (engineering):** run the **EPIC drafting prompt** with **PRD + readiness + constraint bundle** as inputs, *after* Section 1 boundaries are explicit.  
This does **not** replace human gates in `UNIVERSAL_PHASE_GATES.md` — review EPIC output before MDAP.

### 1) Boundaries — fill **before** the EPIC prompt

Copy the table into your prompt or keep this file open. Anything left blank defaults to "use repo docs as written."

#### 1.0 Delivery rule: small strategic chunks (EPIC + MDAP must respect)

**Non-negotiable:** implementation must be planned and delivered in **small, reviewable chunks** so progress is trackable and intent stays clear.

| Boundary | Your choice (fill in) |
|----------|------------------------|
| **Chunk size target** | e.g. "1-3 days per chunk", "≤ 1 PR per chunk", "≤ ~300 LOC net change", "1 module + tests" |
| **Chunk scope** | Each chunk must compose part of a solution, e.g. the ingestion of M5D, before ingest other documents like manual and TCDF, and only then create the indexes and prompts to retrieve text that will help enhance the data that will interact with the LLM |
| **Chunk definition** | Each chunk must have: scope statement, PRD/EPIC IDs, acceptance criteria, evidence link(s) |
| **Ordering rule** | e.g. "vertical slice first (Ação 1 end-to-end)", "no big refactors before first runnable pipeline" |
| **Review gate** | Each chunk must pass relevant checks; do not advance phases without human gate per `UNIVERSAL_PHASE_GATES.md`, always check if some code is already written before creating to prevent duplicate or go in a different path from what its original |

#### 1.1 Scope ceiling (what this EPIC generation may cover)

| Boundary | Your choice (fill in) |
|----------|------------------------|
| **Primary vertical** | Default: **Ação 1 end-to-end** only for *implementation* stories; PRD remains north star for *deferred* items. |
| **Out of scope for this EPIC pass** | e.g. "No UI polish beyond MVP", "No actions 2-16 implementation stories" |
| **May mention but not implement** | e.g. "46 actions backlog as future epics only" |

#### 1.2 Inference and data residency (must align with docs)

| Boundary | Your choice |
|----------|-------------|
| **Default inference** | **Local** (Ollama) for case-bearing text — per `epic_drafting_readiness.md` + `nfr_008_deployment_boundary.md` |
| **External LLM (Groq, etc.)** | EPIC may draft **opt-in branch + gates**; **no** silent default; production per `OQ-005_resolution.md` |
| **Embeddings / vectors** | Local `sentence-transformers` + LanceDB for reference/case indices unless PRD explicitly allows otherwise |

#### 1.3 Non-negotiables for EPIC output (from readiness page)

EPIC draft **must** include explicit tasks/stories for:

- Case ingestion → segments → **sparse + dense** on same `segment_id` (FR-006 + FR-008D)
- Crosswalk → retrieval wiring (FR-008A/B/C)
- Hybrid **fusion** formula + constants (FR-008D)
- Retrieval **audit log** persistence (FR-014 / FR-014A intent)
- **FR-021** assurance pass before persistence

#### 1.4 Explicit "do not invent"

| Item | Rule |
|------|------|
| **OQ-004 / NFR-006 seconds** | Log **measured** wall-clock only; no numeric SLO targets until pilot |
| **Pilot thresholds** | `retrieval_floor_stage2`, hit/weak/none — bands or TBD + measurement task, not fake numbers |

#### 1.5 Traceability and gates

- Every major EPIC decision must cite **FR/NFR** or **pre_epic_resolved_decisions** / `07_RETRIEVAL` docs.
- After EPIC draft: walk **gates 2A-2J** in `UNIVERSAL_PHASE_GATES.md` before locking baseline.
- EPIC and MDAP must define work as **chunkable increments** (small, strategically ordered) with evidence and review gates.

### 2) Input bundle (attach or paste for the EPIC prompt)

Minimum set:

1. `Plan/01_PRD/prd.md` — requirements source  
2. `Plan/00_PENDENCIES/epic_drafting_readiness.md` — go/no-go + must-haves  
3. `Plan/00_PENDENCIES/pre_epic_resolved_decisions.md` — resolved product/engineering defaults  
4. `Plan/00_PENDENCIES/pendencias_pre_epic.md` — what is still open / deferred  
5. `Plan/07_RETRIEVAL/nfr_008_deployment_boundary.md` + `Plan/07_RETRIEVAL/OQ-005_resolution.md` — residency + opt-in detail  
6. `Plan/07_RETRIEVAL/retrieval_satisficing_rules.md` + `Plan/07_RETRIEVAL/vector_storage_options.md` — retrieval stack behavior  
7. `Plan/06_Models/crosswalk/` — Ação 1 policy (templates + verification)  
8. `EPIC_Prompt.md` — the EPIC generator prompt you will run  
9. **Section 1 of this file** (your filled boundaries)

Optional but useful:
- `Plan/00_PENDENCIES/pre_epic_implementation_trace.md` — map spike code to EPIC stories  
- `UNIVERSAL_PHASE_GATES.md` — remind model: no scope creep; human review between phases  

### 3) EPIC prompt — execution plan (step-by-step)

Do **not** chain automatically; one deliberate run, then human review.

| Step | Action | Owner |
|------|--------|--------|
| 1 | Complete **Section 1** boundaries (above) | You |
| 2 | Assemble **Section 2** files in the tool you use (Cursor chat, Copilot, etc.) | You |
| 3 | Run EPIC drafting prompt with instructions: *"Generate EPIC(s) traceable to PRD; respect readiness + boundary docs; first implementation vertical Ação 1; defer full 46-action build to backlog; no numeric SLO invention; **structure EPICs so implementation can ship in small strategic chunks with explicit gates + evidence**."* | You + model |
| 4 | Save EPIC output to repo (e.g. `Plan/02_EPIC/` or name agreed in repo) | You |
| 5 | Run **scope/traceability** pass using gates **2A-B** in `UNIVERSAL_PHASE_GATES.md` | You |
| 6 | Fix gaps or regenerate targeted sections only | You + model |
| 7 | Only then: **MDAP** / architecture prompts (separate runs) | Per gates doc |

### 4) Suggested one-liner to start the EPIC run (after boundaries)

Paste something like:

> Using the attached PRD and `epic_drafting_readiness.md` as hard constraints, draft an EPIC for **M5D Ação 1** (ingest, crosswalk, hybrid retrieval FR-008A-D, evaluation FR-009/010, FR-021, audit FR-014/014A). Default **local Ollama** for case text; external LLM only as an **explicit opt-in** epic with production gates per `OQ-005_resolution.md`. Do not invent numeric latency SLOs (OQ-004). Map each epic/story to FR/NFR IDs. List open items only as backlog or measurement tasks.

### 5) After EPIC — immediate follow-ups

- [ ] Map `src/maturity_check/` spike to EPIC stories (or mark superseded) via `pre_epic_implementation_trace.md`  
- [ ] Update Planner / task registry if you use `Plan/08_TASK_REGISTRY/` (optional; not blocking EPIC quality)  
- [ ] Proceed to MDAP only after gate approval on EPIC  

*Last aligned with repo state: EPIC readiness GO; Ollama installed; `pendencias_pre_epic.md` lists OQ-004 deferred and pilot calibration open.*

