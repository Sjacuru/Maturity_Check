PRODUCT REQUIREMENTS DOCUMENT
M5D Evaluation System
Status: Awaiting human sign-off before EPIC phase
Constraints active: GC-1, GC-2, GC-4, GC-5, GC-8, GC-9

Section 1 — Executive Summary
The M5D Evaluation System is a document analysis tool that supports public auditors in assessing whether procurement processes contain the substantive elements required by the Modelo de Cinco Dimensões (M5D or "The Five Case Model") framework. The system receives documents from a completed or in-progress procurement case, evaluates their content against structured M5D directives, and produces a scored, evidence-backed audit report for human review.
The primary user is a public auditor who currently performs this evaluation manually — a process that is time-consuming, inconsistent across auditors, and produces outputs with limited traceability. The system reduces evaluation time and enforces structural consistency while preserving the auditor as the final authority on every result.
The single most important measurable outcome that defines success is: an auditor completes a full evaluation of one M5D Action against a case's documents and receives a structured, scored result with traceable evidence, without performing any manual document search.
Scope Ceiling: This PRD covers the evaluation of procurement documents against the M5D framework for a single case at a time, producing scored and evidence-backed action-level reports subject to auditor review. Any requirement not traceable to a stated user need or business goal in this document is out of scope by default.

Section 2 — Problem Statement
Public auditors are responsible for evaluating whether procurement processes that led to government contracts with private partners demonstrate adequate maturity and adherence to established planning standards. The M5D framework defines approximately 46 actions across 3 stages and 5 dimensions, each with multiple sub-tasks and expected outputs that a well-structured procurement process should address.
The current evaluation process is entirely manual. An auditor reads procurement documents — which may number between 5 and 10 per case, are unstructured, and follow no naming convention — and individually assesses whether each M5D directive is satisfied. This produces three compounding problems:
Inconsistency: Different auditors apply different interpretations of the same directive, producing non-comparable results across cases.
Time cost: Manually searching for evidence of each sub-task across multiple documents is the dominant cost of the evaluation. A single action may require searching across all documents to confirm absence of a required element.
Traceability gap: Current outputs do not systematically link evaluation conclusions to specific document excerpts. This weakens the audit record and makes review by superiors difficult.
No existing tool addresses all three problems simultaneously for the M5D framework in the Brazilian public procurement context. Spreadsheet-based checklists address consistency partially but do not reduce search time or provide evidence traceability. General document search tools do not understand M5D semantics.
The consequence of not solving this problem is continued reliance on a process that scales poorly, produces inconsistent outputs, and cannot be systematically reviewed or improved.

Section 3 — User Personas
PERSONA-001
Role: Public Auditor
Primary goal: Complete a structured, evidence-backed evaluation of a procurement case against M5D directives in less time than manual evaluation requires, while retaining authority to review and correct the system's conclusions.
Primary pain point: Locating relevant content across multiple unstructured documents for each directive is the most time-consuming part of the current process, and the resulting notes lack systematic evidence linkage.
PERSONA-002
Role: Audit Superior / Reviewer
Primary goal: Review evaluation outputs produced by auditors — including system-generated scores and auditor annotations — to validate conclusions before they are recorded.
Primary pain point: Current evaluation outputs vary in structure and depth between auditors, making cross-case comparison and quality review difficult.
Note: PERSONA-002 interacts with the system only in read and annotation mode. They do not configure the system or upload documents. [ASSUMPTION — interaction model for superiors not fully specified in input]

Section 4 — Functional Requirements

Architecture binding — retrieval, validation, and audit (v1)
This subsection records an **engineering product decision** for v1: the crosswalk remains the **retrieval policy layer** (FR-008A); case-corpus retrieval is implemented as **hybrid sparse + dense retrieval with deterministic fusion** (new FR-008D); **deterministic gates** validate evidence packets before LLM evaluation; a **single structured output-assurance pass** (“judge”, new FR-021) validates evaluator outputs before persistence. **Unconstrained tool-using agent loops** and **multi-agent debate** are **out of scope for v1** (defer to later engineering) — see Plan/07_RETRIEVAL/retrieval_satisficing_rules.md.

Hard constraints (governance + PRD alignment)
C1 — Evidence traceability: every persisted evidence item SHALL map to a **source segment/chunk identifier** and to a **crosswalk artifact_id** (or an explicitly logged “no-overlay” path when no crosswalk exists for that sub-task). Satisfies FR-014 evidence linkage intent and NFR-003 persistence expectations.
C2 — Retrieval audit log: every retrieval decision SHALL be logged in a structured, replayable artifact (hook list, ranked candidates, fusion inputs/outputs, overlay weights). Supports FR-014A and internal audit needs.
C3 — Explainability: auditor-facing outputs SHALL separate **facts** (citations, scores, flags) from **model narrative**; “black box only” outputs are not acceptable. Aligns with FR-018 reporting and PERSONA-001 review behavior.
C4 — Bounded cost/latency: per-sub-task budgets for retrieval expansion (FR-008C/FR-008B) and model calls (FR-009/FR-010 plus FR-021 when enabled) SHALL be documented; NFR-006 threshold (OQ-004) MUST include the additional assurance pass.
C5 — No autonomous adjudication: the system produces **recommendations**; the auditor remains final authority (PERSONA-001). Aligns with FR-016/FR-017 and FR-015 semantics.

FR mapping (where each layer lands)
- Crosswalk policy + pooled hooks: **FR-008A** (and FR-001 for structured framework store feeding prompts/context).
- Three-step discovery + semantic connection: **FR-008** (steps 1–3 remain; hybrid retrieval implements the retrieval mechanics behind step 3 and supports step 2 where applicable).
- Tiered expansion + satisficing: **FR-008C** (SHOULD), **FR-008B** (MUST early exit rules).
- Hybrid BM25+dense+fusion on segments: **FR-008D** (new MUST).
- Segment store supports sparse+dense indices: **FR-006** (clarified acceptance).
- Evaluator inputs/outputs: **FR-009**, **FR-010** (and **FR-011**, **FR-012** on the same retrieval path).
- Structured record + traceability: **FR-014** (extended to reference linked audit payloads), **FR-014A** (SHOULD dispositions).
- Output assurance / judge: **FR-021** (new MUST) — post-generation validation placement.
- Flags: **FR-015** (UNCERTAINTY / MISSING INFORMATION / etc., including assurance-triggered UNCERTAINTY alignment with OQ-006).
- Scoring: **FR-013** uses the persisted, assurance-reviewed record fields as inputs.
- Confidence scale + records: **NFR-002**.
- Modularity/tests: **NFR-005** (retrieval, evaluation, assurance separable).
- Data residency / external models: **NFR-008**, **OQ-005** (still a hard gate for any external document-text processing).

EPIC readiness (explicit): merging this binding **does not replace** human PRD sign-off. **EPIC drafting** for FR-008D/FR-021 MAY proceed on **local-first** assumptions while OQ-005 remains open, provided EPIC branches explicitly on OQ-005 outcomes and does not assume external transmission of procurement text by default. **Committed EPIC execution** (scheduled implementation) that depends on an external inference posture for document text remains blocked until OQ-005 is cleared. OQ-004 SHALL set NFR-006 numeric budgets including the assurance pass. Tool interfaces for a future bounded agent (v2+) SHOULD be implemented as plain callable modules per NFR-005, without enabling an agent loop in v1.

FR-001 [MUST]: The system shall store the complete M5D framework
as structured data, including all stages, dimensions, actions,
sub-tasks, expected outputs, and summary table complements,
prior to any evaluation being performed.

Acceptance criteria: Given the M5D framework has been ingested,
a query for any action by its identifier returns its stage,
dimension, all sub-tasks, all expected output items, and all
linked complement rows without error.

Source: Phase 1 conceptual alignment — M5D as static reference layer.
Reason: Without a structured M5D store, no evaluation can be
performed. This is the foundational dependency for all other FRs.

FR-002 [MUST]: The system shall assign a weight to each sub-task
within an action, defaulting to equal distribution across all
sub-tasks in that action when no custom weight is provided.

Acceptance criteria: Given an action with N sub-tasks and no
custom weights set, the system assigns weight (1/N) to each
sub-task. Given custom weights are provided for all sub-tasks
of an action, the system uses those weights instead of defaults.
The sum of all sub-task weights within a single action equals 1.

Source: Phase 1 scoring model definition. [ASSUMPTION — custom
weight values per sub-task are pending external definition;
default equal distribution confirmed as interim behavior]

FR-003 [MUST]: The system shall accept the creation of a case
record containing at minimum: a unique case identifier generated
by the system, a process name provided by the auditor, an
institution name provided by the auditor, and a contract
reference number provided by the auditor.

Acceptance criteria: A case record is created only when all
four fields are present. Submission of a case record missing
any mandatory field is rejected with a field-level error message
identifying the missing field. The system-generated case
identifier is unique across all existing cases.

Source: Phase 1 case structure definition. Contract reference
mandatory for v1 scope.

FR-004 [MUST]: The system shall allow an auditor to upload one
or more documents to an existing case, where a document is a
file containing text content related to a procurement process.

Acceptance criteria: Given a valid case exists, an auditor can
attach one or more files to it. Each file is stored and
associated with the case. The system confirms receipt of each
file with a success or failure status per file.

Source: Phase 1 document ingestion definition — PERSONA-001
primary workflow.
Depends on: FR-003

FR-005 [MUST]: The system shall perform a pre-validation check
on each uploaded document before it is processed for evaluation,
verifying that the document is readable, is in Portuguese, and
contains vocabulary plausibly associated with a procurement
process.

Acceptance criteria: A document that passes all three checks
receives status ACCEPTED. A document that fails the language
check or domain relevance check receives status WARNED with a
description of the failed check. A document that cannot be read
receives status REJECTED with a reason. The auditor is notified
of the status of each uploaded document. Evaluation cannot begin
on a document with status REJECTED.

Source: Phase 1 — pre-validation step identified as necessary
to prevent wrong-document upload errors.
Depends on: FR-004

FR-006 [MUST]: The system shall extract the text content of
each ACCEPTED document, divide it into segments, and store
those segments in a form that supports content-based retrieval
at evaluation time.

Acceptance criteria: Given a document with status ACCEPTED,
its text content is stored as retrievable segments before any
evaluation action is triggered. A document with status WARNED
may be processed for retrieval only after auditor confirmation.
A document with status REJECTED is not processed. The stored
segment representation SHALL support both **lexical retrieval**
(for example inverted-index / BM25-style search) and **dense
vector retrieval** over identical segment identifiers, so hybrid
retrieval (FR-008D) can be executed without duplicate chunking
pipelines.

Source: Phase 1 document ingestion — embed at upload for reuse
across multiple action evaluations.
Depends on: FR-005

FR-007 [MUST]: The system shall allow an auditor to select a
specific M5D action for evaluation against a case's uploaded
documents.

Acceptance criteria: Given a case with at least one ACCEPTED
document, the auditor can select any M5D action by its
identifier. The system initiates the evaluation pipeline for
that action against the case's documents. The auditor cannot
select an action for evaluation if no ACCEPTED document is
associated with the case.

Source: Phase 1 — evaluation is action-by-action, auditor-initiated.
Depends on: FR-003, FR-006

FR-008 [MUST]: The system shall identify which uploaded
document or documents are most relevant to a selected M5D
action using a three-step classification process: first by
exact document name match against expected document names
for that action, second by approximate name match if exact
match fails, third by semantic content match across all
uploaded documents if name matching fails. Even if the name 
matches on first and second try, the third try needs to run
to make sure the content on the document or the chunk has 
conection with the subject.

Acceptance criteria: For a given action, the system returns
at least one document reference or a flag indicating no
relevant document was found. The classification method used
(exact name / approximate name / semantic content) is recorded
in the evaluation result. If no relevant document is found
after all three steps, the system raises a MISSING DOCUMENT flag.

Source: Phase 1 classification engine — three-step discovery pipeline.
Depends on: FR-006, FR-007

FR-008A [MUST]: When a jurisdiction overlay (crosswalk) links
sub-tasks to expected artifacts from more than one reference
source (e.g. Rio Manual and IN 01/2024 TCDF), the system shall
treat all overlay artifacts for the active sub-task as one
pooled set of labeled retrieval hooks. Retrieval shall rank
and aggregate candidate segments from this pool. TCDF artifacts
expand vocabulary and semantic coverage; they are not a second
case jurisdiction in v1 (evaluated cases are Rio). The engine
shall not treat “Rio hooks first, then TCDF hooks only if Rio
fails” as the only correct behavior unless a staged strategy is
proven equivalent in recall to pooled ranking or unless a second
stage is automatically triggered when the best Rio-biased score
is below **retrieval_floor_stage2** (see below).

**retrieval_floor_stage2 (staged retrieval only):** If the
implementation uses a Rio-biased first retrieval stage, it SHALL
automatically run a second stage (full pooled ranking or explicit
TCDF-expanded queries) when the best segment score from the first
stage is strictly below **retrieval_floor_stage2**. The scalar
SHALL be documented in MDAP together with the similarity metric
(cosine, inner product, or other) and normalization. Initial
calibration target band **0.35–0.50** on the chosen normalized
similarity unless MDAP records a different value justified by a
pilot corpus. The PRD does not fix a single numeric constant
across embedding models.

Acceptance criteria: EPIC/MDAP describes pooled retrieval and
any staged optimization; MDAP names **retrieval_floor_stage2**
and the metric; tests include at least one sub-task where the
strongest segment is associated with a TCDF-labeled hook while
Rio-labeled hooks remain in the ranked set; if staged retrieval
is used, tests include one case where first-stage max score is
below **retrieval_floor_stage2** and second stage executes.

Source: Rio v1 crosswalk design — alignment with FR-008 and
evidence traceability.

FR-008B [MUST]: Satisficing early exit for sub-task evidence
collection. If overlay metadata identifies an artifact with
tipo Direta and grau Alto, and the evaluation record for the
sub-task tied to that evidence reports confidence greater than
or equal to 0.90 (NFR-002 scale 0.0–1.0), the system may cease
further artifact-specific retrieval expansions for that sub-task.
Semantic validation required by FR-008 (connection of content
to subject) shall still be satisfied for the selected document
or chunk before a final presence decision is recorded.

Acceptance criteria: Pipeline logs or structured metadata show
early exit when the rule fires; no additional overlay-driven
queries run after exit; FR-008 step three is not skipped for
the chosen evidence path.

Source: Product decision — audit efficiency vs exhaustive search.

FR-008C [SHOULD]: When FR-008B early exit does not apply, expand
artifact-driven retrieval in tier order: (1) Direta by grau Alto,
then Médio, then Baixo; (2) Indireta with the same grau order;
(3) Contextual with the same grau order. Within each tier,
rank by retrieval score with overlay weighting (tipo, grau) and
enforce a fixed candidate budget per sub-task (EPIC/MDAP).

Acceptance criteria: Documented tier order and budget; retrieval traces show tier progression when early exit does not occur.

Source: Crosswalk retrieval rules — see Plan/07_RETRIEVAL/
retrieval_satisficing_rules.md for full sequential specification.

FR-008D [MUST]: For uploaded case documents, the system shall
retrieve candidate evidence segments using a **hybrid retrieval**
approach that combines (1) **lexical retrieval** (for example BM25 or equivalent sparse scoring) over the segment corpus to
strengthen exact artifact titles and procedural phrases, with
(2) **dense vector similarity** over embeddings of the same
segments, and (3) a **deterministic merge** of ranked lists (for
example Reciprocal Rank Fusion or another documented fusion rule).
The system shall then apply FR-008A overlay metadata (tipo, grau, jurisdiction_layer) as part of ranking / weighting before forming an **approved evidence packet** for evaluation.

Acceptance criteria: EPIC/MDAP SHALL document the sparse method,
embedding model family, fusion formula, and any constants; each
sub-task evaluation SHALL persist a **retrieval decision log**
sufficient for audit replay, including: crosswalk hook
artifact_ids used, top-K sparse candidates with scores, top-K
dense candidates with scores, fused ordering, and the FR-008
classification method recorded per selected path (exact name /
approximate name / semantic content). Tests SHALL include at
least one scenario where sparse ranking differs materially from
dense ranking and the fused output changes ordering.

Source: Engineering decision — jurisdiction synonym coverage
without unconstrained agent loops; complements FR-008A and
Plan/07_RETRIEVAL/vector_storage_options.md.
Depends on: FR-006, FR-008, FR-008A

FR-009 [MUST]: The system shall evaluate whether each sub-task
of the selected action is present in the retrieved document
content, using the sub-task text, its expected output
description, and its linked summary table complement as
evaluation context.

Acceptance criteria: For each sub-task in the selected action,
the system returns a binary presence result (present / not
present), a confidence score, a reasoning statement, and a
quoted evidence excerpt from the document. The evaluation
context used is recorded as one of: sub-task only / sub-task
and output / sub-task, output, and complement.

Source: Phase 1 evaluation model — presence check with full
context (sub-task + expected output; complement included only
when a linked complement row exists per OQ-002).
Depends on: FR-008, FR-008A, FR-008D

FR-010 [MUST]: The system shall evaluate the quality of each
sub-task found present in the document content, producing a
numeric quality score.

Acceptance criteria: For each sub-task assessed as present,
the system returns a quality score between 0 and 10 inclusive,
a reasoning statement explaining the score, and a quoted
evidence excerpt. For sub-tasks assessed as not present,
no quality score is produced.

Source: Phase 1 scoring model — quality layer for sub-tasks.
Depends on: FR-009

FR-021 [MUST]: After draft sub-task evaluation outputs are
produced per FR-009 and FR-010 from an **approved evidence packet**
(only segments/chunks that are linked to a crosswalk
artifact_id, plus stable segment identifiers), the system shall
execute exactly **one** structured **output assurance** pass per
sub-task that validates, without introducing new facts or new
evidence: (1) citations reference only chunk IDs present in the
packet; (2) unsupported claims are flagged relative to the
packet; (3) confidence is consistent with evidence strength. When
assurance adjudicates confidence below **0.70**, the evaluation
record SHALL carry **UNCERTAINTY** per OQ-006 / FR-015. The
assurance pass SHALL use **deterministic decoding defaults**
(for example temperature 0) unless MDAP documents an approved
exception for reproducibility.

Acceptance criteria: Assurance inputs and outputs are persisted
and visible to the auditor with the sub-task record; assurance
SHALL NOT add new document text not present in the packet; logs
SHALL include a reference to the packet version (hash/checksum
or equivalent) used. FR-014 persistence for the sub-task SHALL
occur only after FR-021 completes or after an explicit,
auditor-visible bypass path documented in EPIC (default: no
bypass in v1).

Source: Engineering decision — mitigates plausible-but-wrong
chunk failure mode while preserving auditability.
Depends on: FR-009, FR-010, NFR-002
Out of scope v1: unconstrained tool-using agent loops and
multi-agent debate (see Plan/07_RETRIEVAL/retrieval_satisficing_rules.md).

Scope note (expected outputs): FR-021 is **mandatory for
sub-task** evaluation records in v1. EPIC/MDAP SHALL decide
whether the **same** assurance pass is applied per **expected
output** item (FR-011/FR-012) or only to sub-tasks; if omitted,
expected-output evaluations SHALL document the rationale and any
additional deterministic checks used instead.

FR-011 [MUST]: The system shall evaluate whether each expected
output item of the selected action is present in the retrieved
document content.

Acceptance criteria: For each expected output item in the
selected action, the system returns a binary presence result,
a confidence score, a reasoning statement, and a quoted
evidence excerpt. Assessment follows the same evidence
retrieval path used in FR-009.

Source: Phase 1 evaluation model — expected output presence check.
Depends on: FR-008, FR-008A, FR-008D

FR-012 [MUST]: The system shall evaluate the quality of each
expected output item found present in the document content,
producing a numeric quality score.

Acceptance criteria: For each expected output item assessed
as present, the system returns a quality score between 0 and
10 inclusive and a reasoning statement. For output items
assessed as not present, no quality score is produced.

Source: Phase 1 scoring model — quality layer for expected outputs.
Depends on: FR-011

FR-013 [MUST]: The system shall calculate a total action score
between 0 and 100 for the selected action, applying the
following fixed formula:
- Sub-task presence: 40 points total, distributed by sub-task weight
- Sub-task quality: 20 points total, distributed by sub-task weight
- Expected output presence: 20 points total, distributed equally
- Expected output quality: 20 points total, distributed equally

Acceptance criteria: Given completed evaluations for all
sub-tasks and expected output items of an action, the system
produces a single numeric score between 0 and 100 inclusive.
The score is reproducible: given the same sub-task and output
results, the formula always produces the same score. For
sub-tasks that complete FR-021, the sub-task presence and
quality inputs to this formula SHALL be the **post-assurance**
adjudicated values recorded on the persisted FR-014 record.

Source: Phase 1 scoring model — confirmed formula structure.
Depends on: FR-009, FR-010, FR-011, FR-012

FR-014 [MUST]: The system shall produce a structured evaluation
record per sub-task containing: sub-task identifier, presence
result, quality score (if present), reasoning, evidence excerpt,
confidence score, evaluation context used, framework origin,
and dimension name.

Acceptance criteria: Given a completed sub-task evaluation,
the record contains all nine fields. Any field that cannot
be populated due to absence of content contains a null value
and a flag explaining the reason for absence. Records are
stored persistently and retrievable by case and action. The
persisted sub-task record (or an auditable linked payload)
SHALL also include references to: (a) the FR-008D retrieval
decision log for that sub-task run, and (b) the FR-021 output
assurance result when LLM evaluation is used.

Source: Phase 1 — confirmed LLM output format specification.
Depends on: FR-009, FR-010, FR-021

FR-014A [SHOULD]: When a jurisdiction overlay lists multiple
artifacts for a sub-task, the system should store per-artifact retrieval disposition for audit traceability: hit (strong match), weak (marginal match), or none (no match), each with retrieval score or similarity and the FR-008 method (file name / approximate name / semantic content) where applicable.

Acceptance criteria: For an evaluated sub-task with an overlay, the report or API exposes per-artifact disposition fields or an embedded structure; absent overlay, this structure may be omitted or null.

Source: Crosswalk operational visibility — complements FR-014.

FR-015 [MUST]: The system shall flag evaluation results that
meet one of four defined conditions: MISSING DOCUMENT (expected
document not uploaded), MISSING INFORMATION (document present
but required content absent), CONFLICTING INFORMATION
(contradictory evidence found across documents), or UNCERTAINTY
(confidence score below 0.70 on the evaluation record per OQ-006).

Acceptance criteria: When any flag condition is met, the system
attaches the flag to the relevant evaluation record with a
description of the condition detected. Flags are visible in
the evaluation result before the auditor reviews it.

Source: Phase 1 error and uncertainty handling model.
Depends on: FR-008, FR-009, FR-011, FR-021

FR-016 [SHOULD]: The system shall allow an auditor to add a
manual annotation to any evaluation record produced by the
system, including flagged records.

Acceptance criteria: Given an evaluation record, the auditor
can attach free-text annotation of any length. The annotation
is stored separately from the system-generated content and
is labeled as auditor-provided. The original system-generated
content is not modified by the annotation.

Source: Phase 1 — auditor validates and can annotate output.
PERSONA-001 primary review behavior.
Depends on: FR-014
Reason [SHOULD]: Auditor review is required by design but
annotation storage is deferrable to v1.1 if interface
complexity is a constraint.

FR-017 [SHOULD]: The system shall allow an auditor to trigger
a re-evaluation of a flagged evaluation record, with the
option to provide additional context or a modified retrieval
instruction before re-execution.

Acceptance criteria: Given a flagged evaluation record, the
auditor can initiate a new evaluation run for the same
sub-task or output item. The re-evaluation run is stored as
a separate record linked to the original. The auditor can
provide modified input before re-run. The original record
is preserved unchanged.

Source: Phase 1 — error re-run behavior: manual prompt edit
or agent re-run on flagged items.
Depends on: FR-015, FR-016
Reason [SHOULD]: Important for quality but requires interface
work that may defer to v1.1.

FR-018 [MUST]: The system shall produce an action-level
evaluation report compiling all sub-task records, all expected
output records, all flags, the total action score, and the
auditor annotations for a given case and action.

Acceptance criteria: Given a completed evaluation of all
sub-tasks and expected output items for one action, the system
generates a report document containing all specified elements.
The report is accessible to the auditor and to PERSONA-002
(audit superior). The report clearly distinguishes
system-generated content from auditor annotations.

Source: Phase 1 output expectations — report per action with
evidence, flags, scores, and reasoning.
Depends on: FR-013, FR-014, FR-015, FR-016

FR-019 [SHOULD]: The system shall allow an auditor to pause
evaluation of a case after completing any action and resume
from the same point in a subsequent session.

Acceptance criteria: Given a case with at least one completed
action evaluation, the auditor can end the session. In a
subsequent session, the case is accessible with all previously
completed evaluations intact. The auditor can select the next
action for evaluation without repeating prior steps.

Source: Phase 1 — partial evaluation and resume confirmed
as required behavior.
Depends on: FR-007
Reason [SHOULD]: Architectural dependency on session
persistence — deferrable if not achievable in v1.

FR-020 [COULD]: The system shall allow PERSONA-002 (audit
superior) to read evaluation reports produced for a case
without the ability to modify evaluation records or trigger
re-evaluation.

Acceptance criteria: Given a completed action-level report,
a user with superior role can access and read the report.
That user cannot add annotations, modify records, or trigger
re-evaluation. Access is restricted to cases the superior
is authorized to review. [ASSUMPTION — authorization model
not fully specified]

Source: Phase 1 case structure — auditor and superior
interaction defined.
Depends on: FR-018
Reason [COULD]: Read access for superiors is desirable but
the authorization model is not yet defined.

Section 5 — Non-Functional Requirements

NFR-001 [MUST]: The system shall accept document input in
Portuguese and produce all evaluation outputs, reasoning
statements, flag descriptions, and reports in Portuguese.

Acceptance criteria: Given a document in Portuguese, all
system-generated text fields in the evaluation record are
in Portuguese. Given a document in a language other than
Portuguese, the pre-validation step assigns status WARNED.

Source: Phase 1 — system operates in Portuguese, Brazilian
government context.

NFR-002 [MUST]: Every system-generated evaluation record
shall include a confidence score indicating the system's
assessed reliability of its own output for that record.

Acceptance criteria: Given a completed evaluation record,
the confidence field contains a numeric value between 0.0
and 1.0 inclusive. A record with no confidence value is
treated as incomplete and triggers an UNCERTAINTY flag.

Source: Phase 1 — confidence levels defined as part of
LLM output format.

NFR-003 [MUST]: All evaluation records shall be stored
persistently and remain retrievable by case identifier
and action identifier after the session in which they
were created ends.

Acceptance criteria: Given a completed evaluation record,
it is retrievable in a new session using the case identifier
and action identifier without any re-evaluation step.
Records are not deleted or modified by session termination.

Source: Phase 1 — pause and resume behavior; report
generation depends on persistent records.

NFR-004 [MUST]: The system shall maintain a clear separation
between system-generated content and auditor-provided content
in all stored records and generated reports.

Acceptance criteria: In every evaluation record and every
report, system-generated fields and auditor annotation fields
are stored in distinct fields. No system process overwrites
an auditor annotation. No auditor annotation is presented
as system-generated output.

Source: Phase 1 — auditor validates output; Rule 2G of
UNIVERSAL_PHASE_GATES.md prohibits self-audit.

NFR-005 [MUST]: The system shall be structured as independent
modules, where each module can be tested in isolation without
requiring all other modules to be operational.

Acceptance criteria: A test suite for Module 1 (M5D Ingestion)
can execute and produce pass/fail results without Module 2A,
2B, 3, 4, 5, 6, or 7 being deployed. This property holds
for each module independently.

Source: Phase 1 — modular, testable in small parts,
step-by-step validation required.

NFR-006 [SHOULD]: The system evaluation pipeline shall
complete the evaluation of one sub-task and return a
structured result within a documented time budget under
normal operating conditions.

Acceptance criteria: EPIC/MDAP SHALL record baseline
measured wall-clock latency for the full sub-task pipeline
(retrieval + fusion per FR-008D, evaluator per FR-009/FR-010,
and output assurance per FR-021). A numeric seconds target
(SLO) MAY be added after pilot data; until then, absence of
a fixed threshold does not block EPIC drafting. See OQ-004.

Source: Phase 1 — latency noted as a concern when
discussing complement inclusion strategy.

NFR-007 [SHOULD]: The M5D framework data stored in the
system shall be versioned, such that a new version of
the framework can be ingested without deleting prior
evaluation records that reference the previous version.

Acceptance criteria: Given a new M5D version is ingested,
existing evaluation records that reference action identifiers
from the prior version remain accessible and display the
version of the framework under which they were evaluated.

Source: Phase 1 — M5D is write-once with possible future
versioning. [ASSUMPTION — versioning mechanism not
fully specified]

NFR-008 [MUST] [COMPLIANCE]: The system shall not store
document content from uploaded procurement files outside
the boundaries of the deployment environment without
explicit auditor authorization.

Acceptance criteria: No uploaded document content is
transmitted to an external service without a configuration
setting explicitly enabling that transmission. The default
configuration does not transmit document content externally.

Source: Phase 1 — Brazilian government context implies
data residency sensitivity. [ASSUMPTION — specific
compliance regulation not named; flagged for legal review]
Conflicts with: Any FR that implies external LLM API calls
with document content as input — see OQ-005.

Section 6 — MoSCoW Priority Summary
PriorityRequirement IDsMUSTFR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-008A, FR-008B, FR-008D, FR-009, FR-010, FR-021, FR-011, FR-012, FR-013, FR-014, FR-015, FR-018, NFR-001, NFR-002, NFR-003, NFR-004, NFR-005, NFR-008SHOULDFR-008C, FR-014A, FR-016, FR-017, FR-019, NFR-006, NFR-007COULDFR-020WONT— (see Section 7)

Section 7 — Out of Scope
1. Multi-user workflow management
   Reason: Phase 1 confirmed no systematic workflow between
   users in v1. Auditor and superior interact independently.

2. Automatic ingestion from external government systems
   Reason: v1 requires manual upload. Future version only.

3. Real-time monitoring dashboard
   Reason: System produces per-case reports, not continuous
   monitoring output. Not derivable from stated user need.

4. Evaluation of frameworks other than M5D
   Reason: Not stated in v1 scope. Architecture may permit
   future extension but no FR covers it.

5. Natural language query interface for auditors
   Reason: Not derivable from input. Auditor interaction
   model is structured selection, not free-form query.

6. Automatic contract generation or modification
   Reason: System is evaluation-only. No write access to
   procurement systems is implied.

7. Mobile application interface
   Reason: Not derivable from input. Interface type not
   specified — not included as requirement.

8. Automated report submission to regulatory bodies
   Reason: Report is an internal audit artifact. External
   submission not stated as a requirement.

Section 8 — Open Questions
OQ-001
Question: Sub-task weights per action — what are the
custom weight values for each sub-task in each action?
Impact: FR-002, FR-013
Options: (A) Equal distribution until provided externally.
(B) Block evaluation of any action until weights are
formally defined.
Required by: EPIC phase
Status: Resolved — **Option (A)**. Equal distribution per
action until an external weight table is provided. EPIC
implements FR-002 defaults accordingly; custom weights
replace defaults when supplied for all sub-tasks of an
action (FR-002).

OQ-002
Question: For sub-tasks that have no linked summary table
complement row, should the system use the full summary
table as general context or use sub-task text and expected
output only?
Impact: FR-009, FR-014
Options: (A) Sub-task and output only when no complement
row is linked. (B) Full summary table appended as general
context regardless of direct linkage.
Required by: Module 4 Spec (Evaluation Engine)
Status: Resolved — **Option (A)**. When no complement row
is linked, evaluation context is sub-task + expected output
only. When a complement row exists (FR-001 or crosswalk),
include it per FR-009. Ação 1 complement mapping is
documented in Plan/06_Models/crosswalk/OQ-002_action1_complement_rule.md;
other actions follow the same pattern when authored.

OQ-003
Question: What is the authorization model for PERSONA-002
(audit superior) access to case reports?
Impact: FR-020
Options: (A) Superior has access to all cases within their
institution. (B) Superior is explicitly assigned to specific
cases by the auditor.
Required by: EPIC phase (if FR-020 is included in scope)
Status: Resolved — **Option (A)** for v1 product baseline:
superiors read all cases within their institution/tenant.
Option (B) remains available if multi-tenant policy requires
explicit assignment.

OQ-004
Question: What is the acceptable response time for a
single sub-task evaluation?
Impact: NFR-006, FR-008D, FR-009, FR-010, FR-021
Options: (A) Defer numeric SLO until pilot metrics exist;
require baseline measurement logging in EPIC/MDAP. (B) Set
a numeric seconds target before first release candidate.
The eventual threshold SHALL include the **full** sub-task
pipeline time budget (retrieval + fusion per FR-008D,
evaluator per FR-009/FR-010, and the single output-assurance
pass per FR-021) unless MDAP explicitly documents excluded
phases for a given deployment mode.
Required by: NFR-006 completion for release hardening (not
blocking EPIC drafting).
Status: Deferred — **Option (A)** for EPIC: measure and log
baselines first; numeric SLO optional until pilot data exists.

OQ-005
Question: Does NFR-008 (data residency) prohibit sending
document content to external LLM APIs? If so, FR-009
through FR-012 (which depend on LLM evaluation) conflict
with NFR-008 unless a locally hosted model is used.
Impact: FR-009, FR-010, FR-011, FR-012, FR-021, NFR-008
Options: (A) Use external LLM API — requires explicit
compliance exception. (B) Use locally hosted model —
no data leaves the deployment environment.
Required by: PRD sign-off — this is a hard blocker
if NFR-008 is enforced strictly.
Status: Engineering default resolved — **Option (B)** for
all inference that consumes **uploaded case document text**
(local hosting by default). Option (A) remains a **branch**
requiring explicit configuration, audit logging, and
**legal/security sign-off before production**. EPIC drafting
SHALL assume local-first unless a task explicitly implements
an opt-in external path. See Plan/07_RETRIEVAL/nfr_008_deployment_boundary.md.

OQ-006
Question: What constitutes an UNCERTAINTY flag trigger —
what is the confidence threshold below which a result
is flagged as uncertain?
Impact: FR-015, NFR-002
Options: No options — a numeric threshold must be defined.
Required by: Module 4 Spec (Evaluation Engine)
Status: Resolved — threshold 0.70 (70%). Values strictly below
0.70 on the evaluation record confidence field trigger UNCERTAINTY
per FR-015. Early exit for retrieval expansion uses 0.90 per FR-008B
and does not change this flag threshold.

OQ-007
Question: Should the system support evaluation of
procurement processes that predate the M5D framework,
and if so, does the evaluation methodology change?
Impact: FR-009, FR-011 — adequacy check interpretation
Options: (A) Same evaluation methodology regardless of
document date. (B) Different scoring interpretation for
pre-M5D documents flagged by auditor.
Required by: EPIC phase
Status: Resolved — **Option (A)** for methodology: same
M5D-based evaluation regardless of document date. Pre-M5D
processes are evaluated to surface a **maturity gap**; the
FR-013 formula does not change by era. Option (B) narrative
disclaimers may appear in FR-018 reporting text if the auditor
flags vintage, but scores use the same rule set.

OQ-008
Question: For FR-021 output assurance, should the judge use
the same local LLM as FR-009/FR-010 with stricter decoding,
or a separate smaller model (SLM)?
Impact: FR-021, NFR-006, OQ-005
Options: (A) Same model, temperature 0, judge-only prompt.
(B) Separate SLM for cost/latency experiments.
Required by: EPIC / Module 4
Status: Resolved — **Option (A)** as v1 default (same local
model, deterministic decoding, judge restricted to scoring and
flags — no new facts). EPIC may pilot Option (B) under local
NFR-008 posture only.

Section 9 — Success Metrics
SM-001
Metric: Time to complete evaluation of one M5D Action
Measurement: Wall-clock time from auditor selecting an
action to receiving the structured evaluation result,
measured across 10 consecutive evaluation runs.
Baseline: [UNKNOWN — establish at launch]
Target: [THRESHOLD NEEDED — see OQ-004]
Linked to: FR-007 through FR-014, NFR-006

SM-002
Metric: Evidence traceability rate
Measurement: Percentage of evaluation records that contain
at least one quoted evidence excerpt from a source document.
Baseline: 0% (current manual process produces no
structured evidence linkage)
Target: [THRESHOLD NEEDED — no source provided]
Linked to: FR-014, NFR-003

SM-003
Metric: Flag false positive rate
Measurement: Percentage of MISSING INFORMATION flags
raised by the system that the auditor overrides as
"information was present" upon manual review.
Baseline: [UNKNOWN — establish at launch]
Target: [THRESHOLD NEEDED — no source provided]
Linked to: FR-015

SM-004
Metric: Auditor override rate
Measurement: Percentage of system-generated presence
results (present/not present) that the auditor reverses
through annotation or re-evaluation trigger.
Baseline: [UNKNOWN — establish at launch]
Target: [THRESHOLD NEEDED — no source provided]
Linked to: FR-016, FR-017
Note: A high override rate indicates evaluation quality
is below acceptable threshold.

Section 10 — Coverage Matrix
PRD IDRequirement SummaryModuleStatusFR-001Store M5D as structured dataModule 1✓ CoveredFR-002Sub-task weights with default equalModule 1✓ CoveredFR-003Case creation with metadataModule 2A✓ CoveredFR-004Document upload per caseModule 2A✓ CoveredFR-005Document pre-validationModule 2B✓ CoveredFR-006Text extraction and segmentationModule 2A✓ CoveredFR-007Select action for evaluationModule 3✓ CoveredFR-008Three-step document classificationModule 3✓ CoveredFR-008DHybrid sparse+dense retrieval + fusionModule 3✓ CoveredFR-009Sub-task presence evaluationModule 4✓ CoveredFR-010Sub-task quality evaluationModule 4✓ CoveredFR-021Structured output assurance (judge)Module 4✓ CoveredFR-011Expected output presence evaluationModule 4✓ CoveredFR-012Expected output quality evaluationModule 4✓ CoveredFR-013Action score calculationModule 5✓ CoveredFR-014Structured evaluation record per sub-taskModule 4✓ CoveredFR-015Flag conditionsModule 4✓ CoveredFR-016Auditor annotationModule 7⚠ PartialFR-017Re-evaluation triggerModule 7⚠ PartialFR-018Action-level reportModule 6✓ CoveredFR-019Pause and resumeModule 2A⚠ PartialFR-020Superior read accessModule 7✗ UncoveredNFR-001Portuguese languageAll modules✓ CoveredNFR-002Confidence score in every recordModule 4✓ CoveredNFR-003Persistent record storageAll modules✓ CoveredNFR-004System vs auditor content separationModule 6, 7✓ CoveredNFR-005Modular testabilityAll modules✓ CoveredNFR-006Evaluation latency thresholdModule 4⚠ Baseline first (OQ-004 deferred)NFR-007Framework versioningModule 1⚠ PartialNFR-008Data residencyAll modules⚠ Production gate — OQ-005 external path

Handoff Block
[PRD_HANDOFF_BLOCK]

FR_IN_SCOPE:
- FR-001: Store complete M5D as structured data
- FR-002: Sub-task weights with equal default
- FR-003: Case creation with mandatory metadata
- FR-004: Document upload attached to case
- FR-005: Pre-validate documents before processing
- FR-006: Extract and segment document text
- FR-007: Auditor selects action for evaluation
- FR-008: Three-step document classification
- FR-008A: Pooled crosswalk retrieval hooks (Rio + TCDF)
- FR-008B: Satisficing early exit (Direta + Alto + confidence >= 0.90)
- FR-008C: Tiered artifact expansion when early exit does not apply
- FR-008D: Hybrid lexical + dense retrieval + deterministic fusion on case segments (auditable)
- FR-009: Sub-task presence evaluation with context
- FR-010: Sub-task quality evaluation
- FR-021: Structured output assurance pass (single judge call per sub-task; no new facts)
- FR-011: Expected output presence evaluation
- FR-012: Expected output quality evaluation
- FR-013: Action score via weighted formula
- FR-014: Structured evaluation record per sub-task
- FR-014A: Per-artifact retrieval disposition (hit/weak/none) when overlay exists [SHOULD]
- FR-015: Four-type flag system on evaluation results
- FR-016: Auditor annotation on evaluation records
- FR-017: Re-evaluation trigger on flagged records
- FR-018: Action-level compiled evaluation report
- FR-019: Pause and resume case evaluation
- FR-020: Superior read-only access to reports

NFR_MUST_SHOULD:
- NFR-001: [MUST] All outputs in Portuguese
- NFR-002: [MUST] Confidence score in every record
- NFR-003: [MUST] Persistent record storage
- NFR-004: [MUST] System vs auditor content separated
- NFR-005: [MUST] Modular independent testability
- NFR-006: [SHOULD] Sub-task evaluation latency threshold
- NFR-007: [SHOULD] M5D framework versioning
- NFR-008: [MUST] Data residency — no external transmission default

SCOPE_CEILING:
"This PRD covers the evaluation of procurement documents
against the M5D framework for a single case at a time,
producing scored and evidence-backed action-level reports
subject to auditor review. Any requirement not traceable
to a stated user need or business goal in this document
is out of scope by default."

PERSONAS:
- PERSONA-001: Public Auditor
- PERSONA-002: Audit Superior / Reviewer

UNRESOLVED_ASSUMPTIONS:
- (none for EPIC drafting — structural OQs closed in Section 8;
  see archive [pre_epic_resolved_decisions.md](../00_PENDENCIES/pre_epic_resolved_decisions.md))

RESOLVED_THRESHOLDS:
- OQ-006: UNCERTAINTY when evaluation confidence < 0.70 (FR-015);
  satisficing early exit for retrieval expansion when confidence >= 0.90
  per FR-008B (Direta + Alto + tied evidence).
- Architecture binding (Section 4 preamble): v1 retrieval uses
  crosswalk policy (FR-008A) + hybrid sparse+dense fusion (FR-008D)
  + deterministic pre-generation gates + single structured output assurance pass (FR-021); unconstrained agent loops deferred.
- OQ-001: Equal sub-task weights until external table (FR-002).
- OQ-002: Complement context Option (A) — sub-task + output only
  when no complement row linked.
- OQ-003: PERSONA-002 read access Option (A) — institution scope.
- OQ-007: Pre-M5D documents — same methodology (maturity gap narrative).
- OQ-008: FR-021 judge — same local model, temperature 0, judge-only prompt (default).

UNRESOLVED_THRESHOLDS:
- OQ-004: NFR-006 numeric seconds SLO — deferred until pilot
  measurements (baseline logging required in EPIC/MDAP).

HARD_BLOCKER (production only):
- OQ-005: Legal/security sign-off still required before **production**
  deployment that sends **case document text** to **external**
  inference services. **Engineering default is local-only (Option B)**;
  see Plan/07_RETRIEVAL/nfr_008_deployment_boundary.md. EPIC/MDAP
  **drafting** proceeds local-first; no silent cloud default.

[/PRD_HANDOFF_BLOCK]

Advancement Gate — Human Action Required
⚠️ RULE 1 — NO AUTOMATIC CHAINING

This PRD is complete as a draft. Before **committed EPIC
execution** (scheduled build work) begins:

0. You must review the **Architecture binding** subsection at
   the start of Section 4 (FR-008D hybrid retrieval + FR-021
   output assurance; agent loops deferred)
1. You must review every FR and NFR
2. You must verify OQ-005 (data residency vs LLM conflict)
   with appropriate authority before **production** external
   inference — engineering default is **local-first** (see
   Plan/07_RETRIEVAL/nfr_008_deployment_boundary.md)
3. You must resolve OQ-004 (numeric latency threshold); OQ-006
   resolved at 0.70 UNCERTAINTY and 0.90 satisficing per FR-008B
4. You must complete the ADVANCEMENT GATE SIGN-OFF using
   the template in UNIVERSAL_PHASE_GATES.md (Rules 2A–2J)

I will not treat EPIC execution as approved until you confirm
sign-off.

Planning clarification: **EPIC drafting** (local-first
architecture for FR-008D + FR-021, modular tool surfaces per
NFR-005) may proceed in parallel with OQ-005 **only** if the EPIC
explicitly treats external LLM/API usage as a gated branch and
does not assume cloud execution of procurement text by default.
**Committed implementation scheduling** for any path that sends
document text out of the deployment boundary remains blocked until OQ-005 is resolved.