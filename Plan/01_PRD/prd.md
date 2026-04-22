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
A document with status REJECTED is not processed.

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
context (sub-task + output + complement always included).
Depends on: FR-008

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

FR-011 [MUST]: The system shall evaluate whether each expected
output item of the selected action is present in the retrieved
document content.

Acceptance criteria: For each expected output item in the
selected action, the system returns a binary presence result,
a confidence score, a reasoning statement, and a quoted
evidence excerpt. Assessment follows the same evidence
retrieval path used in FR-009.

Source: Phase 1 evaluation model — expected output presence check.
Depends on: FR-008

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
results, the formula always produces the same score.

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
stored persistently and retrievable by case and action.

Source: Phase 1 — confirmed LLM output format specification.
Depends on: FR-009, FR-010

FR-015 [MUST]: The system shall flag evaluation results that
meet one of four defined conditions: MISSING DOCUMENT (expected
document not uploaded), MISSING INFORMATION (document present
but required content absent), CONFLICTING INFORMATION
(contradictory evidence found across documents), or UNCERTAINTY
(confidence score below acceptable threshold [THRESHOLD NEEDED]).

Acceptance criteria: When any flag condition is met, the system
attaches the flag to the relevant evaluation record with a
description of the condition detected. Flags are visible in
the evaluation result before the auditor reviews it.

Source: Phase 1 error and uncertainty handling model.
Depends on: FR-008, FR-009, FR-011

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
structured result within [THRESHOLD NEEDED — no source
provided] seconds under normal operating conditions.

Acceptance criteria: [THRESHOLD NEEDED — to be defined
before EPIC phase. See OQ-004]

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
PriorityRequirement IDsMUSTFR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-015, FR-018, NFR-001, NFR-002, NFR-003, NFR-004, NFR-005, NFR-008SHOULDFR-016, FR-017, FR-019, NFR-006, NFR-007COULDFR-020WONT— (see Section 7)

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
Status: Pending input from Rodrigo — equal distribution
confirmed as interim default and must be asked and properly provided by the developer before continue building the software in the parts that affect this disscussion

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
Status: Unresolved — flagged from Phase 1.

OQ-003
Question: What is the authorization model for PERSONA-002
(audit superior) access to case reports?
Impact: FR-020
Options: (A) Superior has access to all cases within their
institution. (B) Superior is explicitly assigned to specific
cases by the auditor.
Required by: EPIC phase (if FR-020 is included in scope)
Status: [ASSUMPTION] — not specified in input.

OQ-004
Question: What is the acceptable response time for a
single sub-task evaluation?
Impact: NFR-006
Options: No options — a numeric threshold must be defined
by the product owner before this NFR can be written as
a testable requirement.
Required by: PRD sign-off
Status: [THRESHOLD NEEDED — no source provided]

OQ-005
Question: Does NFR-008 (data residency) prohibit sending
document content to external LLM APIs? If so, FR-009
through FR-012 (which depend on LLM evaluation) conflict
with NFR-008 unless a locally hosted model is used.
Impact: FR-009, FR-010, FR-011, FR-012, NFR-008
Options: (A) Use external LLM API — requires explicit
compliance exception. (B) Use locally hosted model —
no data leaves the deployment environment.
Required by: PRD sign-off — this is a hard blocker
if NFR-008 is enforced strictly.
Status: Flagged as compliance conflict. Requires
legal/security review before EPIC phase.

OQ-006
Question: What constitutes an UNCERTAINTY flag trigger —
what is the confidence threshold below which a result
is flagged as uncertain?
Impact: FR-015, NFR-002
Options: No options — a numeric threshold must be defined.
Required by: Module 4 Spec (Evaluation Engine)
Status: [THRESHOLD NEEDED — no source provided]

OQ-007
Question: Should the system support evaluation of
procurement processes that predate the M5D framework,
and if so, does the evaluation methodology change?
Impact: FR-009, FR-011 — adequacy check interpretation
Options: (A) Same evaluation methodology regardless of
document date. (B) Different scoring interpretation for
pre-M5D documents flagged by auditor.
Required by: EPIC phase
Status: Phase 1 confirmed the system must handle pre-M5D
documents using expected output as primary evidence — but
the scoring formula does not differentiate. [ASSUMPTION]

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
PRD IDRequirement SummaryModuleStatusFR-001Store M5D as structured dataModule 1✓ CoveredFR-002Sub-task weights with default equalModule 1✓ CoveredFR-003Case creation with metadataModule 2A✓ CoveredFR-004Document upload per caseModule 2A✓ CoveredFR-005Document pre-validationModule 2B✓ CoveredFR-006Text extraction and segmentationModule 2A✓ CoveredFR-007Select action for evaluationModule 3✓ CoveredFR-008Three-step document classificationModule 3✓ CoveredFR-009Sub-task presence evaluationModule 4✓ CoveredFR-010Sub-task quality evaluationModule 4✓ CoveredFR-011Expected output presence evaluationModule 4✓ CoveredFR-012Expected output quality evaluationModule 4✓ CoveredFR-013Action score calculationModule 5✓ CoveredFR-014Structured evaluation record per sub-taskModule 4✓ CoveredFR-015Flag conditionsModule 4✓ CoveredFR-016Auditor annotationModule 7⚠ PartialFR-017Re-evaluation triggerModule 7⚠ PartialFR-018Action-level reportModule 6✓ CoveredFR-019Pause and resumeModule 2A⚠ PartialFR-020Superior read accessModule 7✗ UncoveredNFR-001Portuguese languageAll modules✓ CoveredNFR-002Confidence score in every recordModule 4✓ CoveredNFR-003Persistent record storageAll modules✓ CoveredNFR-004System vs auditor content separationModule 6, 7✓ CoveredNFR-005Modular testabilityAll modules✓ CoveredNFR-006Evaluation latency thresholdModule 4✗ Threshold neededNFR-007Framework versioningModule 1⚠ PartialNFR-008Data residencyAll modules⚠ Compliance conflict — OQ-005

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
- FR-009: Sub-task presence evaluation with context
- FR-010: Sub-task quality evaluation
- FR-011: Expected output presence evaluation
- FR-012: Expected output quality evaluation
- FR-013: Action score via weighted formula
- FR-014: Structured evaluation record per sub-task
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
- OQ-001: Sub-task weight values pending — equal default interim
- OQ-002: Complement linkage for sub-tasks without table row and must be asked and properly provided by the developer before continue building the software.
- OQ-003: Authorization model for PERSONA-002
- OQ-007: Scoring differentiation for pre-M5D documents

UNRESOLVED_THRESHOLDS:
- OQ-004: NFR-006 — sub-task evaluation response time
- OQ-006: FR-015 — confidence threshold for UNCERTAINTY flag

HARD_BLOCKER:
- OQ-005: NFR-008 data residency vs external LLM API conflict
  requires legal/security review before EPIC phase can begin.

[/PRD_HANDOFF_BLOCK]

Advancement Gate — Human Action Required
⚠️ RULE 1 — NO AUTOMATIC CHAINING

This PRD is complete as a draft. Before any EPIC is written:

1. You must review every FR and NFR
2. You must verify OQ-005 (data residency vs LLM conflict)
   with appropriate authority — this is a HARD BLOCKER
3. You must resolve OQ-004 and OQ-006 (numeric thresholds)
4. You must complete the ADVANCEMENT GATE SIGN-OFF using
   the template in UNIVERSAL_PHASE_GATES.md (Rules 2A–2J)

I will not begin EPIC phase until you confirm sign-off.