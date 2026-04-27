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

## Deferred until pilot metrics (don’t invent numbers)

- **OQ-004 / NFR-006 numeric SLO**: EPIC/MDAP should log measured wall-clock baselines first; set seconds targets only after pilot.
- **Pilot calibration**: `retrieval_floor_stage2`, hit/weak/none cutoffs, embedding model id adjustments for Portuguese legal corpora.

