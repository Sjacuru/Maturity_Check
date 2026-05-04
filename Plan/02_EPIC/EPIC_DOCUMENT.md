# EPIC document — Maturity Evaluation System based in M5D and other specific regulation: Manual Rio and TCDF IN (Ação 1 first; local-first)

This EPIC document decomposes `Plan/01_PRD/prd.md` into deliverable EPICs, with strict traceability, explicit boundaries, and **small strategic delivery slices** suitable for close tracking and review.

**Scope ceiling (verbatim, PRD Section 1):** This PRD covers the evaluation of procurement documents against the M5D framework for a single case at a time, producing scored and evidence-backed action-level reports subject to auditor review. Any requirement not traceable to a stated user need or business goal in this document is out of scope by default.

**Personas (PRD Section 3):**
- **PERSONA-001**: Public Auditor
- **PERSONA-002**: Audit Superior / Reviewer (read + annotation only)

**Global constraints (must hold across ALL epics/slices):**
- **Local-first for case document text** (NFR-008 + OQ-005): no external transmission by default; any external path is explicit opt-in and production-gated.
- **No invented thresholds** (OQ-004 / NFR-006): record measurements; do not set seconds targets until pilot.
- **Evidence traceability + auditability**: every persisted evidence item must map to segment/chunk identifiers and crosswalk artifact ids (or explicit “no overlay”).
- **No autonomous adjudication**: system produces recommendations; auditor is final authority.
- **Small strategic chunks**: every epic is planned into slices that can be reviewed and verified independently; no “big bang” implementation.

---

# EPIC HEADER

## Epic Title
M5D case evaluation (Ação 1 vertical) with evidence-traceable retrieval, evaluation, scoring, and review

## Epic Goal
Enable an auditor (PERSONA-001) to complete one full M5D Action evaluation for a single case and receive a structured, scored result with traceable evidence, without manual document search, while enabling superior review (PERSONA-002) where in scope.

## Scope Statement

**In Scope (covered by epics below):**  
FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-008A, FR-008B, FR-008C, FR-008D, FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-014A, FR-015, FR-016, FR-017, FR-018, FR-019, FR-020, FR-021, NFR-001, NFR-002, NFR-003, NFR-004, NFR-005, NFR-006, NFR-007, NFR-008.

**Out of Scope (PRD Section 7):**
- Multi-user workflow management
- Automatic ingestion from external government systems
- Real-time monitoring dashboard
- Evaluation of frameworks other than M5D
- Natural language query interface for auditors
- Automatic contract generation or modification
- Mobile application interface
- Automated report submission to regulatory bodies

**[ASSUMPTION] & [THRESHOLD NEEDED] items carried forward (from PRD):**
- **[ASSUMPTION] PERSONA-002 interaction model** not fully specified (read + annotation only is stated; details TBD).
- **[ASSUMPTION] FR-002** custom weight values pending external definition; equal distribution is interim.
- **[ASSUMPTION] NFR-007** versioning mechanism not fully specified.
- **[ASSUMPTION] NFR-008** compliance regulation not named; flagged for legal review.
- **[THRESHOLD NEEDED] OQ-004 / NFR-006** numeric latency SLO (measure first; do not invent).

---

# EPICS & USER STORIES

## EPIC-001: Structured M5D framework store (with version awareness)

**Derived from:** FR-001, NFR-005, NFR-007  

**Strategic Goal:** Ensure the M5D framework is queryable as structured data before any evaluation occurs.

**Epic Definition of Done:**
- [ ] All in-scope user needs in this epic are covered by stories below
- [ ] Stories do not specify technology choices
- [ ] Acceptance criteria are binary and testable
- [ ] Version awareness is captured as a requirement without inventing a mechanism [ASSUMPTION]

## Risk / Assumption Field
- **[ASSUMPTION] NFR-007**: versioning mechanism not fully specified; preserve behavior intent only.

## Delivery Slices / Chunks (Mandatory)
1. **Slice 1 — Framework availability baseline**
   - **Scope**: Framework ingested and queryable by action identifier for read-only use
   - **Traceability**: FR-001
   - **Acceptance criteria (slice)**:
     - [ ] Given the framework has been ingested, querying an action by identifier returns stage, dimension, sub-tasks, expected outputs, and linked complements without error
   - **Evidence**: CLI/demo output showing sample action query results + doc update describing query contract
2. **Slice 2 — Crosswalk-template alignment for Ação 1**
   - **Scope**: Framework data representations align with crosswalk templates for Ação 1 (no changes to PRD IDs)
   - **Traceability**: FR-001, NFR-005
   - **Acceptance criteria (slice)**:
     - [ ] For Ação 1, the system can surface sub-task identifiers and texts needed by downstream retrieval/evaluation without manual transcription
   - **Evidence**: Example output artifact mapping Ação 1 sub-tasks to framework store entries
3. **Slice 3 — Crosswalk artifact data loaded into queryable store**
   - **Scope**: Crosswalk JSON for in-scope actions is loaded into a queryable store providing `tipo`, `grau`, `artifact_id`, `intencao` (by source), `complement_text_pt`, and `expected_output_text_pt` per sub-task
   - **Traceability**: FR-001, FR-008A, FR-009
   - **Acceptance criteria (slice)**:
     - [ ] Given a sub-task identifier, the system returns all crosswalk artifact rows for that sub-task (artifact_id, jurisdiction_layer, tipo, grau)
     - [ ] Given a sub-task identifier, the system returns the `intencao` text per source in `compose_order` (used as retrieval hook query text by EPIC-004)
     - [ ] Given a sub-task identifier, the system returns `complement_text_pt` (null or populated) for use in evaluation context (OQ-002)
   - **Evidence**: CLI/demo output showing crosswalk query for Ação 1 sub-task 1.2 (has complement) and sub-task 1.1 (null complement)
4. **Slice 4 — Version tagging (behavior-only)**
   - **Scope**: Records include a framework version label; do not implement a full versioning mechanism beyond what is required to not break old records
   - **Traceability**: NFR-007 [ASSUMPTION]
   - **Acceptance criteria (slice)**:
     - [ ] Existing evaluation records continue to display the framework version under which they were evaluated after a new version is ingested
   - **Evidence**: Documented behavior + a minimal demonstration dataset showing old record remains accessible

## User Stories

### US-001: Query the framework by action identifier
As a **PERSONA-001**,  
I want to retrieve the structured M5D definition for a chosen action,  
So that I can run evaluation using an authoritative reference without manual lookup.

**Acceptance Criteria**
- [ ] Given the M5D framework has been ingested, querying any action by its identifier returns its stage, dimension, all sub-tasks, all expected outputs, and all linked complement rows without error.  
- [ ] If an invalid action identifier is requested, the system returns a clear error indicating the identifier is unknown.

**References:** FR-001

### US-002: Preserve access to records across framework updates
As a **PERSONA-002**,  
I want evaluation records to show which framework version they used,  
So that I can review decisions in the proper historical context. **[ASSUMPTION]**

**Acceptance Criteria**
- [ ] Given a new M5D version is ingested, existing evaluation records referencing the prior version remain accessible. **[ASSUMPTION]**  
- [ ] Each evaluation record displays the framework version under which it was evaluated. **[ASSUMPTION]**

**References:** NFR-007

---

## EPIC-002: Case record + document intake with pre-validation and residency boundary

**Derived from:** FR-003, FR-004, FR-005, NFR-001, NFR-008  

**Strategic Goal:** Enable auditors to create cases and attach readable, relevant Portuguese documents with explicit residency safeguards.

**Epic Definition of Done:**
- [ ] Case creation and document attachment behaviors are covered by stories and acceptance criteria
- [ ] Pre-validation requirements are enforced without inventing extra checks beyond PRD
- [ ] Residency boundary is explicit (default local; no external transmission)

## Risk / Assumption Field
- **[ASSUMPTION] NFR-008** compliance regulation not named; legal review required for production posture.

## Delivery Slices / Chunks (Mandatory)
1. **Slice 1 — Case creation validity**
   - **Scope**: Create case record with required fields and unique identifier
   - **Traceability**: FR-003
   - **Acceptance criteria (slice)**:
     - [ ] Case record is created only when all mandatory fields are present
     - [ ] Missing mandatory field is rejected with field-level error
   - **Evidence**: Example created case + negative test examples
2. **Slice 2 — Document attachment**
   - **Scope**: Attach one or more documents to an existing case and confirm per-file receipt status
   - **Traceability**: FR-004
   - **Acceptance criteria (slice)**:
     - [ ] Each file is stored and associated with the case
     - [ ] System confirms per-file success/failure status
   - **Evidence**: Receipt artifact listing per-file status
3. **Slice 3 — Pre-validation gate (readable + Portuguese + plausibility)**
   - **Scope**: Pre-validation check before processing
   - **Traceability**: FR-005, NFR-001
   - **Acceptance criteria (slice)**:
     - [ ] Unreadable or non-Portuguese content is rejected before extraction/indexing
   - **Evidence**: Validation results for pass + fail examples
4. **Slice 4 — Residency boundary disclosure**
   - **Scope**: Ensure no default path transmits uploaded content externally; any opt-in is explicit and auditable
   - **Traceability**: NFR-008
   - **Acceptance criteria (slice)**:
     - [ ] Default configuration does not transmit uploaded document content to external services
     - [ ] If any external transmission is enabled, it requires explicit configuration and authorization
   - **Evidence**: Documented configuration behavior and an audit note template

## User Stories

### US-003: Create a case record
As a **PERSONA-001**,  
I want to create a case record with the required identifiers,  
So that I can attach documents and evaluate the case.

**Acceptance Criteria**
- [ ] A case record is created only when all four fields are present: system-generated unique case identifier, process name, institution name, contract reference number.  
- [ ] If any mandatory field is missing, the system rejects submission with a field-level error naming the missing field.  
- [ ] The system-generated case identifier is unique across all existing cases.

**References:** FR-003

### US-004: Upload one or more documents to a case
As a **PERSONA-001**,  
I want to attach one or more text-bearing documents to an existing case,  
So that the system can evaluate the case using those documents.

**Acceptance Criteria**
- [ ] Given a valid case exists, I can attach one or more files and each file is associated with the case.  
- [ ] The system returns a success/failure status per file.

**References:** FR-004

### US-005: Pre-validate documents before processing
As a **PERSONA-001**,  
I want the system to reject unusable documents before evaluation,  
So that I do not waste time running evaluation on invalid inputs.

**Acceptance Criteria**
- [ ] Each uploaded document is checked for readability before further processing.  
- [ ] Documents that are not in Portuguese are rejected before extraction/indexing.  
- [ ] Documents that fail plausibility checks for procurement vocabulary are rejected before extraction/indexing.

**References:** FR-005, NFR-001

---

## EPIC-003: Text extraction + segmentation foundation for retrieval and traceability

**Derived from:** FR-006, FR-007, NFR-005  

**Strategic Goal:** Convert uploaded documents into stable segments suitable for retrieval, fusion, and evidence traceability.

## Risk / Assumption Field
(None identified.)

## Delivery Slices / Chunks (Mandatory)
1. **Slice 1 — Extract text from uploaded documents**
   - **Scope**: Extract text content and associate extracted text with document and case
   - **Traceability**: FR-006
   - **Acceptance criteria (slice)**:
     - [ ] Extraction produces text used in later retrieval and evaluation
   - **Evidence**: Example extraction output for a sample document
2. **Slice 2 — Segment/chunk with stable identifiers**
   - **Scope**: Create segments with stable segment identifiers for retrieval and evidence linkage
   - **Traceability**: FR-006 (clarified acceptance), FR-014 intent
   - **Acceptance criteria (slice)**:
     - [ ] Each segment has a stable identifier referenced by retrieval/evaluation artifacts
   - **Evidence**: Segment listing showing identifiers + backreference to source document
3. **Slice 3 — Auditor selects action for evaluation**
   - **Scope**: Action selection step exists and is recorded as evaluation intent
   - **Traceability**: FR-007
   - **Acceptance criteria (slice)**:
     - [ ] Auditor can select a specific M5D action for a given case
   - **Evidence**: Recorded selection artifact (case_id + action_id)

## User Stories

### US-006: Extract and segment uploaded documents
As a **PERSONA-001**,  
I want the system to extract and segment my uploaded documents into retrievable segments,  
So that evidence can be found and cited without manual searching.

**Acceptance Criteria**
- [ ] Given a validated uploaded document, the system extracts its text for processing.  
- [ ] The extracted text is segmented into retrievable units with stable identifiers.  
- [ ] Segmentation results can be reused so hybrid retrieval can execute without duplicate chunking for the same uploaded content.

**References:** FR-006

### US-007: Select an action to evaluate for a case
As a **PERSONA-001**,  
I want to select a specific M5D action to evaluate for the case,  
So that the system evaluates the correct requirements set.

**Acceptance Criteria**
- [ ] Given a case with extracted segments, I can select an action identifier for evaluation.  
- [ ] The system records the selected action identifier with the evaluation run context.

**References:** FR-007

---

## EPIC-004: Retrieval policy + hybrid retrieval with deterministic fusion and audit logs

**Derived from:** FR-008, FR-008A, FR-008B, FR-008C, FR-008D, FR-014A, NFR-005, NFR-006, NFR-008  

**Strategic Goal:** Find the best evidence segments for each sub-task using pooled hooks + hybrid retrieval + explicit expansion rules, with auditability and no invented thresholds.

## Risk / Assumption Field
- **[THRESHOLD NEEDED] OQ-004 / NFR-006**: numeric latency budget deferred until pilot; record measured times.
- **Pilot calibration**: `retrieval_floor_stage2`, hit/weak/none cutoffs are to be tuned after first runnable pipeline; do not invent.
- **OQ-005 production gate**: external inference paths that use case text are opt-in and production-gated.

## Delivery Slices / Chunks (Mandatory)
1. **Slice 1 — Artifact identification (FR-008 steps)**
   - **Scope**: Identify which uploaded documents map to required artifacts using filename/title/semantic methods
   - **Traceability**: FR-008
   - **Acceptance criteria (slice)**:
     - [ ] Classification records the method used (filename/title/semantic) per artifact mapping decision
   - **Evidence**: Example artifact mapping record showing method
2. **Slice 2 — Crosswalk pooled hooks for Ação 1**
   - **Scope**: Use crosswalk overlay to produce a pooled hook list per sub-task, with Rio as the authority anchor and TCDF as vocabulary/semantic breadth — not a sequential queue
   - **Traceability**: FR-008A
   - **Acceptance criteria (slice)**:
     - [ ] Retrieval inputs include pooled hooks aligned to crosswalk for the sub-task
   - **Evidence**: Logged hook list for a sample sub-task
3. **Slice 3 — Hybrid retrieval mechanics**
   - **Scope**: Hybrid sparse+dense retrieval over segments with deterministic fusion formula documented
   - **Traceability**: FR-008D
   - **Acceptance criteria (slice)**:
     - [ ] For a query, system returns ranked candidate segments with both sparse and dense inputs and a fused ordering
   - **Evidence**: Retrieval run artifact with ranked list + fused scores
4. **Slice 4 — Expansion + satisficing**
   - **Scope**: Implement early exit rules and tier expansion protocol; satisficing threshold is a resolved PRD constant
   - **Traceability**: FR-008B (MUST), FR-008C (SHOULD)
   - **Acceptance criteria (slice)**:
     - [ ] Satisficing fires when tipo = Direta AND grau = Alto AND confidence ≥ 0.90 (FR-008B + OQ-006, resolved constant); expansion ceases and the trigger is logged
     - [ ] When not met, tier expansion proceeds in documented order (Direta → Indireta → Contextual; Alto → Médio → Baixo within each tipo) and within defined budget
   - **Evidence**: Retrieval decision log showing stop/continue reasons
5. **Slice 5 — Retrieval audit log + dispositions**
   - **Scope**: Persist replayable retrieval decision logs and per-artifact dispositions (hit/weak/none) where overlay exists
   - **Traceability**: FR-014A + PRD constraints C2
   - **Acceptance criteria (slice)**:
     - [ ] Every retrieval decision is logged in a structured, replayable artifact (hook list, ranked candidates, fusion inputs/outputs, overlay weights)
   - **Evidence**: Stored audit payload for one sub-task run

## User Stories

### US-008: Identify required artifacts in uploaded documents
As a **PERSONA-001**,  
I want the system to identify which uploaded documents correspond to required artifacts,  
So that retrieval and evaluation use the correct evidence sources.

**Acceptance Criteria**
- [ ] The system can associate uploaded documents to required artifacts using filename signals where present.  
- [ ] If filename is insufficient, the system uses extracted titles/headers.  
- [ ] If titles are insufficient, the system uses semantic matching on content.  
- [ ] The system records which method(s) were used for each artifact identification decision.

**References:** FR-008

### US-009: Retrieve evidence segments using pooled hooks and hybrid fusion
As a **PERSONA-001**,  
I want the system to retrieve candidate evidence segments for each sub-task using crosswalk-driven hooks,  
So that evaluation is based on the best available evidence without manual searching.

**Acceptance Criteria**
- [ ] For each sub-task, retrieval uses pooled hooks derived from the applicable jurisdiction overlay (crosswalk); hook query text is assembled from the `intencao` field per source, in `compose_order`.  
- [ ] All hooks (Rio + TCDF) are used as a pooled set — not a sequential queue; no hook set is exhausted before the other is consulted (FR-008A).  
- [ ] Retrieval uses hybrid sparse + dense methods and produces a deterministic fused ranking of candidate segments.  
- [ ] The fusion method and constants are documented and do not change implicitly between runs.

**References:** FR-008A, FR-008D

### US-010: Apply satisficing and tiered expansion rules
As a **PERSONA-001**,  
I want retrieval to stop early when evidence is sufficiently strong, and expand systematically when it is not,  
So that evaluation is efficient while still thorough when needed.

**Acceptance Criteria**
- [ ] If early-exit conditions are met for a sub-task, retrieval expansion stops and the reason is recorded.  
- [ ] If early-exit conditions are not met, retrieval expands in the defined tier order and within defined budgets.  
- [ ] Satisficing fires at confidence ≥ 0.90 (PRD FR-008B + OQ-006, resolved constant — not pilot-calibrated).  
- [ ] The pilot-calibrated values are `retrieval_floor_stage2` (initial band 0.35–0.50) and hit/weak/none disposition cutoffs only; these are deferred measurement tasks until first runnable pipeline.

**References:** FR-008B, FR-008C, NFR-006

---

## EPIC-005: Evaluation engine (presence + quality) with output assurance and uncertainty flags

**Derived from:** FR-009, FR-010, FR-011, FR-012, FR-015, FR-021, NFR-001, NFR-002, NFR-005, NFR-006, NFR-008  

**Strategic Goal:** Produce structured sub-task and expected-output evaluations grounded in an approved evidence packet, then validate outputs deterministically before persistence.

## Risk / Assumption Field
- **OQ-005 / NFR-008**: evaluation that consumes case text is local-first; external paths are opt-in and production-gated.
- **OQ-004 / NFR-006 [THRESHOLD NEEDED]**: do not invent latency targets; record measured baselines.

## Delivery Slices / Chunks (Mandatory)
1. **Slice 1 — Evidence packet contract**
   - **Scope**: Define what constitutes an “approved evidence packet” for evaluation inputs (segments + traceability links + complement text when applicable)
   - **Traceability**: FR-008D, FR-009, FR-014, FR-021
   - **Acceptance criteria (slice)**:
     - [ ] Evaluation inputs reference segment identifiers and (when applicable) crosswalk artifact ids
     - [ ] When the crosswalk record for a sub-task carries a non-null `complement_text_pt`, the complement text is included in the evaluation context (OQ-002)
     - [ ] When `complement_text_pt` is null, only sub-task text + expected output are used as context (OQ-002 Option A)
   - **Evidence**: Example evidence packet artifact showing both null and non-null complement cases (e.g., sub-task 1.1 = null; sub-task 1.2 = Quadro 11)
2. **Slice 2 — Sub-task presence evaluation**
   - **Scope**: Evaluate whether each sub-task is satisfied based on evidence packet
   - **Traceability**: FR-009
   - **Acceptance criteria (slice)**:
     - [ ] Output includes satisfaction judgment and confidence on NFR-002 scale
   - **Evidence**: Example structured evaluation output
3. **Slice 3 — Sub-task quality evaluation**
   - **Scope**: Evaluate quality of each satisfied sub-task
   - **Traceability**: FR-010
   - **Acceptance criteria (slice)**:
     - [ ] Output includes quality assessment fields and confidence
   - **Evidence**: Example structured quality output
4. **Slice 4 — Expected outputs (presence + quality)**
   - **Scope**: Evaluate expected output items using same retrieval evidence path
   - **Traceability**: FR-011, FR-012
   - **Acceptance criteria (slice)**:
     - [ ] Expected output items are evaluated using the retrieval path used for sub-tasks
   - **Evidence**: Example expected-output evaluation record
5. **Slice 5 — Assurance pass (judge) + FR-015 flag conditions**
   - **Scope**: Deterministic validation step after evaluator output and before persistence; raises all four FR-015 flag conditions where applicable
   - **Traceability**: FR-021, FR-015
   - **Acceptance criteria (slice)**:
     - [ ] Persistence occurs only after assurance completes or an explicit, auditor-triggered override is recorded
     - [ ] **MISSING DOCUMENT**: raised when FR-008 three-step classification (exact name → approximate name → semantic) finds no acceptable document for a required artifact after exhausting all methods; the sought artifact_id and last attempted method are recorded
     - [ ] **MISSING INFORMATION**: raised when document(s) are found and classified but the sub-task substance is absent or below threshold; artifact_id is recorded
     - [ ] **CONFLICTING INFORMATION**: raised by the LLM reasoning/assurance pass when contradictory evidence is detected across retrieved segments; no pre-enumeration of file names required — contradiction is identified at the reasoning step
     - [ ] **UNCERTAINTY**: raised when assurance pass confidence < 0.70 (OQ-006, resolved constant)
   - **Evidence**: Assurance result artifact with at least one example of each flag type

## User Stories

### US-011: Evaluate whether each sub-task is satisfied
As a **PERSONA-001**,  
I want the system to evaluate whether each sub-task is satisfied based on retrieved evidence,  
So that I can complete the action evaluation without manual reading of all documents.

**Acceptance Criteria**
- [ ] For each sub-task, the system produces a structured presence/satisfaction output grounded in the approved evidence packet.  
- [ ] When the crosswalk record carries a non-null `complement_text_pt`, evaluation context includes sub-task text + expected output + complement text (OQ-002).  
- [ ] When `complement_text_pt` is null, evaluation context uses sub-task text + expected output only (OQ-002 Option A).  
- [ ] The output includes a confidence value on a 0.0–1.0 scale aligned with NFR-002.  
- [ ] The output includes evidence references traceable to segment identifiers.  
- [ ] All output text fields (reasoning, evidence excerpts, flag messages) are in Portuguese (NFR-001).

**References:** FR-009, NFR-001, NFR-002

### US-012: Evaluate the quality of satisfied sub-tasks and expected outputs
As a **PERSONA-001**,  
I want the system to assess the quality of satisfied items,  
So that the action score reflects not only presence but adequacy.

**Acceptance Criteria**
- [ ] For each satisfied sub-task, the system produces a structured quality output with confidence.  
- [ ] For each expected output item, the system evaluates both presence and quality using the same retrieval path as the sub-task evaluation.  
- [ ] Outputs include evidence references traceable to segment identifiers.

**References:** FR-010, FR-011, FR-012

### US-013: Validate evaluator output with an assurance pass before persistence
As a **PERSONA-001**,  
I want the system to validate evaluator outputs before they are stored,  
So that persisted records are consistent, structured, and safe to review.

**Acceptance Criteria**
- [ ] After FR-009/FR-010 outputs are produced from an approved evidence packet, the system performs a deterministic validation step before persistence.  
- [ ] The assurance pass raises **MISSING DOCUMENT** when FR-008 exhausts all three classification methods (exact name → approximate name → semantic) and finds no acceptable document for a required artifact; artifact_id and last method attempted are recorded.  
- [ ] The assurance pass raises **MISSING INFORMATION** when document(s) are found and classified but the required sub-task substance is absent or below threshold.  
- [ ] The assurance pass raises **CONFLICTING INFORMATION** when the LLM reasoning step identifies contradictory evidence across retrieved segments.  
- [ ] The assurance pass raises **UNCERTAINTY** when confidence < 0.70 (OQ-006, resolved constant).  
- [ ] Persistence occurs only after assurance completes, or after an explicit auditor override is recorded.

**References:** FR-021, FR-015

---

## EPIC-006: Persisted evaluation record, scoring, reporting, review, and lifecycle controls

**Derived from:** FR-002, FR-013, FR-014, FR-016, FR-017, FR-018, FR-019, NFR-001, NFR-003, NFR-004, NFR-005  

**Strategic Goal:** Persist structured records with traceability, compute action scores, produce reviewable reports, support annotation and reruns, and allow pausing/resuming.

## Risk / Assumption Field
- **[ASSUMPTION] FR-002**: custom weight values pending; equal distribution is default until supplied.

## Delivery Slices / Chunks (Mandatory)
1. **Slice 1 — Persistence schema for evaluations**
   - **Scope**: Persist structured evaluation records for sub-tasks and expected outputs with traceability links
   - **Traceability**: FR-014, NFR-003
   - **Acceptance criteria (slice)**:
     - [ ] Persisted evidence items reference segment identifiers and crosswalk artifact ids (or explicit no-overlay)
   - **Evidence**: Example persisted record view
2. **Slice 2 — Scoring**
   - **Scope**: Compute action score from persisted, assurance-reviewed fields and weights using the PRD FR-013 four-part formula
   - **Traceability**: FR-002, FR-013
   - **Acceptance criteria (slice)**:
     - [ ] Default weights are 1/N when custom weights absent; sum equals 1
     - [ ] Score applies the FR-013 formula verbatim: sub-task presence (40 pts, distributed by weight) + sub-task quality (20 pts) + expected output presence (20 pts) + expected output quality (20 pts) = 100 pts total
     - [ ] **[MDAP INHERITANCE NOTE]** MDAP must carry this formula verbatim from PRD FR-013 into module design; do not approximate, reorder, or restructure the four components
   - **Evidence**: Score breakdown artifact for Ação 1 showing all four components
3. **Slice 3 — Report generation with explainability separation**
   - **Scope**: Produce action-level report separating facts from narrative
   - **Traceability**: FR-018, NFR-004, PRD constraint C3
   - **Acceptance criteria (slice)**:
     - [ ] Report separates citations/scores/flags from narrative explanations
   - **Evidence**: Example report artifact
4. **Slice 4 — Annotations**
   - **Scope**: Auditor can add annotations to persisted records
   - **Traceability**: FR-016
   - **Acceptance criteria (slice)**:
     - [ ] Annotation is attached to the correct persisted record and is visible in report review
   - **Evidence**: Example annotated record
5. **Slice 5 — Re-run + pause/resume**
   - **Scope**: Rerun evaluation and pause/resume a case evaluation lifecycle
   - **Traceability**: FR-017, FR-019
   - **Acceptance criteria (slice)**:
     - [ ] Rerun creates a new evaluation run record linked to the case and action
     - [ ] Pause/resume state is preserved and visible
   - **Evidence**: Rerun record + state transition artifact

## User Stories

### US-014: Persist an evaluation record with traceable evidence
As a **PERSONA-001**,  
I want evaluation outputs to be stored as structured records with traceable evidence,  
So that the audit record can be reviewed and replayed.

**Acceptance Criteria**
- [ ] The system produces a structured evaluation record for the action that includes the sub-task and expected-output results.  
- [ ] The record includes references to (a) the retrieval decision log for each sub-task run and (b) the FR-021 assurance output for that run.  
- [ ] Every persisted evidence item maps to a segment/chunk identifier and crosswalk artifact_id (or explicit “no overlay” when none exists).

**References:** FR-014, NFR-003

### US-015: Compute an action score using defined weights
As a **PERSONA-001**,  
I want the system to compute a total action score using sub-task weights,  
So that the score is consistent across cases and auditors.

**Acceptance Criteria**
- [ ] Given an action with N sub-tasks and no custom weights, each sub-task weight is (1/N) and the sum equals 1. **[ASSUMPTION]**  
- [ ] Given custom weights are provided for all sub-tasks of an action, the system uses those weights instead of defaults. **[ASSUMPTION]**  
- [ ] The action score uses the FR-013 formula: sub-task presence (40 pts, by weight) + sub-task quality (20 pts) + expected output presence (20 pts) + expected output quality (20 pts) = 100 pts.  
- [ ] The action score calculation uses the persisted, assurance-reviewed evaluation fields as inputs (no hidden adjustments).

**References:** FR-002, FR-013

### US-016: Produce an explainable report for review
As a **PERSONA-001**,  
I want an action-level report that separates facts from narrative,  
So that I can review and correct conclusions efficiently.

**Acceptance Criteria**
- [ ] The report includes scores, flags, and citations as a factual section separate from narrative explanation.  
- [ ] The report includes auditor annotations in the appropriate context.  
- [ ] The report content is derived from persisted records and their evidence links (no uncited claims).  
- [ ] The report is produced in Portuguese (NFR-001).

**References:** FR-018, NFR-001, NFR-004, FR-016

### US-017: Re-run an evaluation and manage evaluation lifecycle state
As a **PERSONA-001**,  
I want to re-run evaluations and pause/resume work,  
So that I can iterate after uploading new documents or making corrections.

**Acceptance Criteria**
- [ ] The system allows rerunning an evaluation for an action on the same case and records the new run separately.  
- [ ] The system allows pausing and resuming evaluation sessions, and the state is visible on the case.  
- [ ] Reruns and pauses do not erase prior records; they remain accessible for audit history.

**References:** FR-017, FR-019

---

## EPIC-007: Superior review access (optional scope)

**Derived from:** FR-020  

**Strategic Goal:** Allow PERSONA-002 to access and annotate reports within allowed access model.

## Risk / Assumption Field
- **[ASSUMPTION] PERSONA-002 interaction model** details not fully specified; do not extend beyond read + annotation.

## Delivery Slices / Chunks (Mandatory)
1. **Slice 1 — Read access to reports**
   - **Scope**: PERSONA-002 can view reports produced for cases within permitted scope
   - **Traceability**: FR-020
   - **Acceptance criteria (slice)**:
     - [ ] PERSONA-002 can access the report output and see citations/scores/annotations
   - **Evidence**: Demonstration artifact showing read-only access behavior
2. **Slice 2 — Annotation by superior**
   - **Scope**: PERSONA-002 can add review annotations without altering core evaluation outputs
   - **Traceability**: FR-020 + persona note [ASSUMPTION]
   - **Acceptance criteria (slice)**:
     - [ ] PERSONA-002 annotations are stored and visible in the report
   - **Evidence**: Example report with superior annotations
3. **Slice 3 — Access model confirmation**
   - **Scope**: Implement the chosen v1 access model without adding workflow management (out of scope)
   - **Traceability**: FR-020 + OQ-003 resolution (institution-wide default) captured in pre-EPIC decisions
   - **Acceptance criteria (slice)**:
     - [ ] Access model is documented and matches stakeholder decision; any ambiguity is flagged for human review
   - **Evidence**: Documented access policy statement + test evidence

## User Stories

### US-018: Review a report as a superior
As a **PERSONA-002**,  
I want to read and annotate action-level reports produced by auditors,  
So that I can validate conclusions before they are recorded.

**Acceptance Criteria**
- [ ] PERSONA-002 can access the report and see scores, flags, and citations.  
- [ ] PERSONA-002 can add annotations in review mode without changing the underlying evaluation outputs. **[ASSUMPTION]**

**References:** FR-020

---

# Dependencies

## Hard Blocking Dependencies (must sequence)
- EPIC-001 → EPIC-002: framework store must exist before structured evaluation flows can be defined (FR-001 dependency).  
- EPIC-002 → EPIC-003: documents must be uploaded/validated before extraction/segmentation.  
- EPIC-003 → EPIC-004: segments must exist before hybrid retrieval and fusion can run.  
- EPIC-004 → EPIC-005: approved evidence packets depend on retrieval outputs.  
- EPIC-005 → EPIC-006: persistence/scoring/reporting rely on assurance-reviewed evaluation outputs.

## Soft Dependencies (can parallel, but better if sequenced)
- EPIC-006 ⟹ EPIC-007: superior review is easier once reports/annotations exist, but can be designed earlier.

## External Dependencies (out of scope)
- None identified from PRD (external system ingestion explicitly out of scope).

---

# Assumptions & Open Questions

## Unresolved [ASSUMPTION] Items (from PRD)
- [ASSUMPTION] PERSONA-002 interaction model not fully specified (impacts: EPIC-007)  
- [ASSUMPTION] FR-002 custom weight values pending external definition (impacts: EPIC-006)  
- [ASSUMPTION] NFR-007 versioning mechanism not fully specified (impacts: EPIC-001)  
- [ASSUMPTION] NFR-008 compliance regulation not named; legal review required (impacts: EPIC-002, EPIC-005)  

## Unresolved [THRESHOLD NEEDED] Items (from PRD)
- [THRESHOLD NEEDED] OQ-004 / NFR-006 numeric latency SLO for full sub-task pipeline (retrieval + fusion + evaluation + assurance) (impacts: EPIC-004, EPIC-005)

## Open Questions / Conflicts / Out-of-Scope Dependencies
- **Pilot calibration:** `retrieval_floor_stage2`, hit/weak/none cutoffs, and embedding model adjustments are metrics-driven (do not invent). (impacts: EPIC-004)  
- **OQ-005 production gate:** external inference that consumes case text requires explicit opt-in + audit + legal/security sign-off before production; local-first remains baseline. (impacts: EPIC-002, EPIC-005)  
- **Out of scope reminder:** multi-user workflow management remains out of scope even if it would “improve” review flows. (impacts: EPIC-007)  

---

# Coverage Matrix (PRD → EPIC traceability)

Status legend: ✓ Covered, ⚠ Partial (requires follow-up / pilot threshold / assumption), ✗ Uncovered

| PRD ID | Requirement (short) | Epic ID | Status |
| --- | --- | --- | --- |
| FR-001 | Store M5D framework as structured data | EPIC-001 | ✓ |
| FR-002 | Sub-task weights default and override | EPIC-006 | ⚠ |
| FR-003 | Create case record | EPIC-002 | ✓ |
| FR-004 | Upload documents to case | EPIC-002 | ✓ |
| FR-005 | Pre-validate docs | EPIC-002 | ✓ |
| FR-006 | Extract + segment text | EPIC-003 | ✓ |
| FR-007 | Select action for evaluation | EPIC-003 | ✓ |
| FR-008 | Identify artifacts | EPIC-004 | ✓ |
| FR-008A | Crosswalk pooled hooks | EPIC-004 | ✓ |
| FR-008B | Satisficing early exit | EPIC-004 | ✓ |
| FR-008C | Tiered expansion | EPIC-004 | ⚠ |
| FR-008D | Hybrid retrieval + fusion | EPIC-004 | ✓ |
| FR-009 | Evaluate sub-task presence | EPIC-005 | ✓ |
| FR-010 | Evaluate sub-task quality | EPIC-005 | ✓ |
| FR-011 | Evaluate expected output presence | EPIC-005 | ✓ |
| FR-012 | Evaluate expected output quality | EPIC-005 | ✓ |
| FR-013 | Calculate action score | EPIC-006 | ✓ |
| FR-014 | Structured evaluation record + links | EPIC-006 | ✓ |
| FR-014A | Per-artifact disposition hit/weak/none | EPIC-004 | ⚠ |
| FR-015 | Flag conditions: MISSING DOCUMENT / MISSING INFORMATION / CONFLICTING INFORMATION / UNCERTAINTY | EPIC-005 | ✓ |
| FR-016 | Auditor annotations | EPIC-006 | ⚠ |
| FR-017 | Auditor triggers re-run | EPIC-006 | ⚠ |
| FR-018 | Action-level report | EPIC-006 | ✓ |
| FR-019 | Pause/resume evaluation | EPIC-006 | ⚠ |
| FR-020 | Superior review access | EPIC-007 | ⚠ |
| FR-021 | Output assurance pass | EPIC-005 | ✓ |
| NFR-001 | Portuguese language — inputs + all system outputs | EPIC-002, EPIC-005, EPIC-006 | ✓ |
| NFR-002 | Confidence scale + records | EPIC-005 | ✓ |
| NFR-003 | Persistence requirements | EPIC-006 | ✓ |
| NFR-004 | Separate facts vs narrative | EPIC-006 | ✓ |
| NFR-005 | Modular structure | EPIC-001 | ✓ |
| NFR-006 | Latency SLO (measure first) | EPIC-004 | ⚠ |
| NFR-007 | Framework versioning | EPIC-001 | ⚠ |
| NFR-008 | Residency boundary | EPIC-002 | ⚠ |

---

# CONTEXT.md — Development Pipeline State

## Pipeline Stage
Current Stage: EPIC — Decomposition  
Next Stage: MDAP — Module Design and Action Planning  
Next Stage: Architecture creation  
Next Stage: Folder structure definition  

## Canonical Scope Summary
Total In-Scope Requirements: **25 FRs** (FR-001..FR-021 incl. FR-008A/B/C/D, FR-014A) and **8 NFRs** (NFR-001..NFR-008)  
Total Epics Generated: **7**  

## Assumption & Threshold Status
[ASSUMPTION] Items Carried Forward: **4** (plus PERSONA-002 interaction note)  
[THRESHOLD NEEDED] Items Carried Forward: **1** (OQ-004 / NFR-006)  
Assumptions Resolved During EPIC Phase: **0**  

## List of Unresolved [ASSUMPTION] Items
- [ASSUMPTION]: PERSONA-002 interaction model not fully specified (from PRD Section 3)  
- [ASSUMPTION]: FR-002 custom weight values pending external definition (from PRD FR-002)  
- [ASSUMPTION]: NFR-007 versioning mechanism not fully specified (from PRD NFR-007)  
- [ASSUMPTION]: NFR-008 compliance regulation not named; flagged for legal review (from PRD NFR-008)  

## List of Unresolved [THRESHOLD NEEDED] Items
- [THRESHOLD-01]: NFR-006 latency SLO; missing: numeric seconds target for full sub-task pipeline (impacts: EPIC-004, EPIC-005)  

## Confirmed Constraints
- Local-first document-text inference baseline (NFR-008 / OQ-005)  
- No invented numeric SLO thresholds (OQ-004)  
- Deterministic fusion and assurance pass are mandatory in v1 (FR-008D, FR-021)  

## Key Dependencies Discovered
**External Blocking Dependencies:** (None identified.)  
**Out-of-Scope Dependencies:** (None; PRD already enumerates out-of-scope items.)  

---

# 5A — Phase Transition Note for MDAP (alias header; canonical handoff)
Downstream prompts MUST treat this **5A section** as the authoritative EPIC→MDAP handoff payload (even if the EPIC document is reorganized elsewhere). Do not infer or recreate dependencies from narrative sections when 5A is present.

## 5A.1 — Epic Summary List

```
EPIC-001: Structured M5D framework store (with version awareness)
EPIC-002: Case record + document intake with pre-validation and residency boundary
EPIC-003: Text extraction + segmentation foundation for retrieval and traceability
EPIC-004: Retrieval policy + hybrid retrieval with deterministic fusion and audit logs
EPIC-005: Evaluation engine (presence + quality) with output assurance and uncertainty flags
EPIC-006: Persisted evaluation record, scoring, reporting, review, and lifecycle controls
EPIC-007: Superior review access (optional scope)
```

## 5A.2 — Coverage Matrix

| PRD ID | Requirement | Epic ID | Status |
| --- | --- | --- | --- |
| FR-001 | Store M5D framework as structured data | EPIC-001 | ✓ |
| FR-002 | Sub-task weights default and override | EPIC-006 | ⚠ |
| FR-003 | Create case record | EPIC-002 | ✓ |
| FR-004 | Upload documents | EPIC-002 | ✓ |
| FR-005 | Pre-validate docs | EPIC-002 | ✓ |
| FR-006 | Extract + segment | EPIC-003 | ✓ |
| FR-007 | Select action | EPIC-003 | ✓ |
| FR-008 | Identify artifacts | EPIC-004 | ✓ |
| FR-008A | Crosswalk pooled hooks | EPIC-004 | ✓ |
| FR-008B | Satisficing early exit | EPIC-004 | ✓ |
| FR-008C | Tiered expansion | EPIC-004 | ⚠ |
| FR-008D | Hybrid retrieval + fusion | EPIC-004 | ✓ |
| FR-009 | Sub-task presence eval | EPIC-005 | ✓ |
| FR-010 | Sub-task quality eval | EPIC-005 | ✓ |
| FR-011 | Expected output presence | EPIC-005 | ✓ |
| FR-012 | Expected output quality | EPIC-005 | ✓ |
| FR-013 | Action score | EPIC-006 | ✓ |
| FR-014 | Structured record + links | EPIC-006 | ✓ |
| FR-014A | hit/weak/none disposition | EPIC-004 | ⚠ |
| FR-015 | Flag conditions: MISSING DOCUMENT / MISSING INFORMATION / CONFLICTING INFORMATION / UNCERTAINTY | EPIC-005 | ✓ |
| FR-016 | Auditor annotations | EPIC-006 | ⚠ |
| FR-017 | Re-run | EPIC-006 | ⚠ |
| FR-018 | Action report | EPIC-006 | ✓ |
| FR-019 | Pause/resume | EPIC-006 | ⚠ |
| FR-020 | Superior access | EPIC-007 | ⚠ |
| FR-021 | Assurance pass | EPIC-005 | ✓ |
| NFR-001 | Portuguese language — inputs + all system outputs | EPIC-002, EPIC-005, EPIC-006 | ✓ |
| NFR-002 | Confidence scale | EPIC-005 | ✓ |
| NFR-003 | Persistence | EPIC-006 | ✓ |
| NFR-004 | Facts vs narrative separation | EPIC-006 | ✓ |
| NFR-005 | Modularity | EPIC-001 | ✓ |
| NFR-006 | Latency SLO | EPIC-004 | ⚠ |
| NFR-007 | Framework versioning | EPIC-001 | ⚠ |
| NFR-008 | Residency boundary | EPIC-002 | ⚠ |

## 5A.3 — Unresolved [ASSUMPTION] & [THRESHOLD NEEDED] Items

```
Unresolved [ASSUMPTION] Items:
- [ASSUMPTION]: PERSONA-002 interaction model not fully specified (impacts: EPIC-007)
- [ASSUMPTION]: FR-002 custom weight values per sub-task pending external definition (impacts: EPIC-006)
- [ASSUMPTION]: NFR-007 versioning mechanism not fully specified (impacts: EPIC-001)
- [ASSUMPTION]: NFR-008 compliance regulation not named; flagged for legal review (impacts: EPIC-002, EPIC-005)

Unresolved [THRESHOLD NEEDED] Items:
- [THRESHOLD-01]: NFR-006 latency SLO; missing: numeric seconds target for full sub-task pipeline (impacts: EPIC-004, EPIC-005)
```

## 5A.4 — Inter-Epic Dependencies

```
Hard Blocking Dependencies:
EPIC-001 → EPIC-002: Framework store required before evaluation flow can be defined (FR-001 dependency)
EPIC-002 → EPIC-003: Documents must be uploaded/validated before extraction/segmentation
EPIC-003 → EPIC-004: Segments required before hybrid retrieval and fusion
EPIC-004 → EPIC-005: Retrieval required to build approved evidence packets
EPIC-005 → EPIC-006: Persistence/scoring/reporting require assurance-reviewed outputs

Soft Dependencies:
EPIC-006 ⟹ EPIC-007: Superior review easier once reports exist, but can be designed earlier

External Dependencies:
(None identified.)
```

## 5A.5 — Open Questions / Conflicts Discovered

```
Logical Conflicts:
- (None identified beyond already-documented OQ-005/NFR-008 constraints.)

Missing Information:
- [THRESHOLD NEEDED] NFR-006 numeric latency SLO (OQ-004) for full pipeline (impacts: EPIC-004, EPIC-005)
- Pilot calibration values (retrieval_floor_stage2 band 0.35–0.50; hit/weak/none disposition cutoffs) — note: satisficing 0.90 and UNCERTAINTY 0.70 are resolved PRD constants, NOT pilot values (impacts: EPIC-004)

Out-of-Scope Dependencies:
- (None; PRD out-of-scope list is explicit.)

Persona / Scope Anomalies:
- PERSONA-002 detailed interaction model not fully specified; constrain to read + annotation only (impacts: EPIC-007)
```

## 5A.6 — Module Domain Mapping (Optional Hint for MDAP)

- EPIC-001: Framework Store  
- EPIC-002: Case Intake + Document Validation + Residency Boundary  
- EPIC-003: Extraction + Segmentation  
- EPIC-004: Retrieval Orchestrator + Audit Log  
- EPIC-005: Evaluation Engine + Assurance Pass + Flags  
- EPIC-006: Persistence + Scoring + Reporting + Annotations + Lifecycle  
- EPIC-007: Reviewer Access (optional)  

