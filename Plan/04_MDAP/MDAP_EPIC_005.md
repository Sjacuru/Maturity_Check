# MDAP — EPIC-005: Evaluation Engine (Presence + Quality) with Output Assurance and Uncertainty Flags

**Processing date:** 2026-05-18  
**Phase:** MDAP — Module Design and Action Planning  
**Source EPIC:** EPIC-005 (derived from FR-009–012, FR-015, FR-021, NFR-001, NFR-002, NFR-005, NFR-006, NFR-008)  
**Pipeline position:** EPIC → **MDAP** → Architecture → Folder Structure

---

## GATE CHECK

| Item | Status |
|---|---|
| EPIC-005 document available | ✅ |
| 5A Phase Transition Note present | ✅ |
| Prior MDAP outputs | EPICs 001–004 (17 modules) available |
| Blocking unresolved assumptions | ⚠️ OQ-005/NFR-008: Phase 1 published docs only — external LLM unrestricted; Phase 2 gates documented |
| Hard blocking dependency | EPIC-004 retrieval output (evidence packet inputs) must exist |

---

## MODULES

---

### MODULE-005-01: EvidencePacketBuilder

| Field | Value |
|---|---|
| **Responsibility** | Assembles the complete, contract-defined evidence packet for one subtask from retrieval results and crosswalk context: resolves `complement_text_pt` (null or populated per OQ-002), attaches `expected_output_text_pt`, includes the full list of fused chunks, links `retrieval_log_id` for audit traceability; this is the single defined contract between retrieval and evaluation — neither the retriever nor the evaluator may bypass it. |
| **User Stories** | US-011, US-012, US-013 |
| **Module Type** | Domain Logic |
| **Public Interface — IN** | `build(subtask_id: str, fused_chunks: list[FusedChunk], retrieval_log_id: str, artifact_mappings: list[ArtifactMapping]) → EvidencePacket` |
| **Public Interface — OUT** | `EvidencePacket(subtask_id: str, subtask_text: str, complement_text_pt: str \| None, expected_output_text_pt: str, chunks: list[FusedChunk], source_documents: list[SourceDocument], retrieval_log_id: str)` |
| | `SourceDocument(doc_id: str, filename: str, artifact_id: str \| None, classification_method: str)` |
| **Dependencies** | MODULE-001-02 (CrosswalkStore — complement + expected output), MODULE-001-03 (FrameworkQueryService — subtask text), MODULE-004-07 (retrieval_log_id), MODULE-004-01 (ArtifactMapping — source documents) |
| **Consumed By** | MODULE-005-03 (SubtaskEvaluator) |
| **Isolation Level** | Requires EPIC-001 and EPIC-004 module outputs |
| **Parallel?** | Yes — one packet per subtask; all subtasks can be built concurrently |
| **Risk Level** | Low |
| **Flag for Review** | No |
| **Cross-Epic Dep?** | Depends on MODULE-001-02, MODULE-001-03 (EPIC-001), MODULE-004-01, MODULE-004-07 (EPIC-004) |

**OQ-002 resolution embedded in this module:**
- If `CrosswalkStore.get_complement(subtask_id)` returns non-null → include in packet as `complement_text_pt`
- If null → `complement_text_pt = None`; evaluator uses only subtask_text + expected_output_text_pt

---

### MODULE-005-02: LLMAdapter

| Field | Value |
|---|---|
| **Responsibility** | Abstracts LLM provider selection behind a single evaluation interface; supports three backends: Ollama/Mistral (local default), Groq (cloud, free tier), Anthropic Claude (future); handles provider-specific API calls, structured JSON output enforcement, retry logic (max 3 attempts with exponential backoff), and ResidencyGuard check before any call; always returns a typed `EvaluationResponse` regardless of backend. |
| **User Stories** | US-011, US-012, US-013 |
| **Module Type** | Infrastructure |
| **Public Interface — IN** | `evaluate(prompt: EvaluationPrompt) → EvaluationResponse` |
| **Public Interface — IN types** | `EvaluationPrompt(system_instruction: str, subtask_text: str, expected_output: str, complement_text: str \| None, evidence_chunks: list[str], language: str = "pt-BR")` |
| **Public Interface — OUT** | `EvaluationResponse(presence: str, confidence: float, quality: str \| None, reasoning: str, evidence_refs: list[str], raw_response: str)` |
| | `presence: "present" \| "partial" \| "absent"` |
| | `quality: "adequate" \| "inadequate" \| None` (null when presence == "absent") |
| **Error Contract** | `LLMUnavailableError(provider, reason)` after max retries |
| | `MalformedResponseError(provider, raw_response)` when structured output parsing fails |
| **Dependencies** | MODULE-002-04 (ResidencyGuard), Config (`LLM_PROVIDER`, `OLLAMA_BASE_URL`, `GROQ_API_KEY`, `ANTHROPIC_API_KEY`) |
| **Consumed By** | MODULE-005-03 (SubtaskEvaluator) |
| **Isolation Level** | Requires ResidencyGuard; otherwise independent |
| **Parallel?** | Yes — concurrent LLM calls per subtask (rate-limit aware) |
| **Risk Level** | High — structured output reliability varies by provider; Ollama/Mistral JSON mode is less reliable than Groq/Anthropic |
| **Flag for Review** | Yes — prompt template and JSON schema must be validated across all three providers |
| **Cross-Epic Dep?** | Depends on MODULE-002-04 (EPIC-002) |

**Provider structured output strategy:**
| Provider | Method |
|---|---|
| Ollama/Mistral | `format: "json"` in request body + system prompt enforcing JSON schema |
| Groq | `response_format: {"type": "json_object"}` + system prompt |
| Anthropic | Tool use with `input_schema` matching `EvaluationResponse` |

**System prompt template (Portuguese):**
```
Você é um auditor especialista em avaliação de projetos de investimento público.
Avalie se o subtask a seguir está presente no documento com base nas evidências fornecidas.
Responda APENAS em JSON com os campos: presence, confidence, quality, reasoning, evidence_refs.
Todos os campos de texto devem ser em português brasileiro.
```

---

### MODULE-005-03: SubtaskEvaluator

| Field | Value |
|---|---|
| **Responsibility** | Orchestrates the complete evaluation of one subtask: builds the LLM prompt from the EvidencePacket, calls LLMAdapter, receives the raw EvaluationResponse, maps it to the full EvaluationResult including source documents, flags computation, and evidence chunk references traceable to segment identifiers. |
| **User Stories** | US-011, US-012 |
| **Module Type** | Domain Logic |
| **Public Interface — IN** | `evaluate(evidence_packet: EvidencePacket, run_id: str) → EvaluationResult` |
| **Public Interface — OUT** | `EvaluationResult(subtask_id: str, run_id: str, presence: str, confidence: float, quality: str \| None, reasoning: str, source_documents: list[SourceDocument], evidence: list[EvidenceRef], flags: list[str])` |
| | `EvidenceRef(chunk_id: str, doc_id: str, excerpt: str, page_start: int, page_end: int)` |
| | `flags: list — populated by MODULE-005-04; empty at this stage` |
| **Dependencies** | MODULE-005-01 (EvidencePacket), MODULE-005-02 (LLMAdapter) |
| **Consumed By** | MODULE-005-04 (AssurancePass) |
| **Isolation Level** | Requires MODULE-005-01 and MODULE-005-02 |
| **Parallel?** | Yes — one evaluator call per subtask; all subtasks of one action can run concurrently |
| **Risk Level** | Medium — quality of result depends on LLM and evidence quality |
| **Flag for Review** | No |
| **Cross-Epic Dep?** | None within module; indirect via MODULE-005-01 and MODULE-005-02 |

---

### MODULE-005-04: AssurancePass

| Field | Value |
|---|---|
| **Responsibility** | Performs deterministic validation of an `EvaluationResult` before persistence; raises all four flag conditions defined in FR-015: MISSING_DOCUMENT (artifact not found after all classification methods), MISSING_INFORMATION (docs found but substance absent or confidence below threshold), CONFLICTING_INFORMATION (LLM reasoning identifies contradiction across segments), UNCERTAINTY (confidence < 0.70 per OQ-006 resolved constant); blocks persistence unless assurance passes or an explicit auditor override is recorded. |
| **User Stories** | US-013 |
| **Module Type** | Domain Logic |
| **Public Interface — IN** | `validate(result: EvaluationResult, artifact_mappings: list[ArtifactMapping]) → AssuranceOutcome` |
| **Public Interface — OUT** | `AssuranceOutcome(passed: bool, flags: list[Flag], override_required: bool, assurance_log: str)` |
| | `Flag(type: str, artifact_id: str \| None, reason: str)` |
| **Flag trigger rules** | `MISSING_DOCUMENT`: `ArtifactMapping.method == "not_found"` for any required artifact |
| | `MISSING_INFORMATION`: `result.presence == "absent"` and no MISSING_DOCUMENT already raised |
| | `CONFLICTING_INFORMATION`: `"conflito"` or `"contraditório"` detected in `result.reasoning` (heuristic; Phase 1) |
| | `UNCERTAINTY`: `result.confidence < 0.70` |
| **Error Contract** | Never raises — always returns `AssuranceOutcome`; persistence layer enforces the gate |
| **Dependencies** | MODULE-004-01 output (`ArtifactMapping` list), pure logic + config (`UNCERTAINTY_THRESHOLD = 0.70`) |
| **Consumed By** | MODULE-006-01 (EvaluationPersister — persistence gate) |
| **Isolation Level** | Requires EvaluationResult and ArtifactMappings |
| **Parallel?** | No — must follow MODULE-005-03 |
| **Risk Level** | Medium — CONFLICTING_INFORMATION heuristic is imprecise in Phase 1; Phase 2 should use LLM judge |
| **Flag for Review** | Yes — CONFLICTING_INFORMATION detection method requires expert review |
| **Cross-Epic Dep?** | AssuranceOutcome consumed by MODULE-006-01 (EPIC-006); ArtifactMappings from MODULE-004-01 (EPIC-004) |

---

## DEPENDENCY MAP (EPIC-005)

```
MODULE-005-01 ──▶ MODULE-005-03 (evidence packet is input to evaluator)
MODULE-005-02 ──▶ MODULE-005-03 (LLM call via adapter)
MODULE-005-03 ──▶ MODULE-005-04 (result must exist before assurance)

Cross-Epic inputs:
  MODULE-001-02, MODULE-001-03 ──▶ MODULE-005-01
  MODULE-004-01, MODULE-004-07 ──▶ MODULE-005-01
  MODULE-002-04 ──▶ MODULE-005-02
  MODULE-004-01 ──▶ MODULE-005-04

Cross-Epic outputs:
  MODULE-005-04 AssuranceOutcome ──▶ MODULE-006-01 (EPIC-006)

No circular dependencies.
Critical path: 001 → 003 → 004 (sequential per subtask)
Parallel workstreams: All subtasks of one action can run through 001→003→004 concurrently
```

---

## COVERAGE MATRIX (EPIC-005)

| User Story | Module IDs | Covered? |
|---|---|---|
| US-011 (evaluate sub-task presence) | MODULE-005-01, MODULE-005-02, MODULE-005-03 | ✅ |
| US-012 (evaluate quality of satisfied items) | MODULE-005-03 (quality field in response) | ✅ |
| US-013 (assurance pass before persistence) | MODULE-005-04 | ✅ |
| FR-015 MISSING DOCUMENT | MODULE-005-04 | ✅ |
| FR-015 MISSING INFORMATION | MODULE-005-04 | ✅ |
| FR-015 CONFLICTING INFORMATION | MODULE-005-04 | ✅ ⚠️ heuristic — Phase 1 |
| FR-015 UNCERTAINTY | MODULE-005-04 | ✅ |

---

## IMPLEMENTATION STATUS

| Module | Status | Notes |
|---|---|---|
| MODULE-005-01 | 0% | Not started |
| MODULE-005-02 | 0% | Not started — LLM providers not yet integrated |
| MODULE-005-03 | 0% | Not started |
| MODULE-005-04 | 0% | Not started |

---

## OUTPUT VERIFICATION

- [x] Every module traces to EPIC-005 user stories
- [x] Every user story has module coverage
- [x] No circular dependencies
- [x] High-risk modules flagged (MODULE-005-02, MODULE-005-04)
- [x] Cross-Epic dependencies documented
- [x] Minimum viable modules (4)
- [x] Public interfaces defined with full type signatures
- [x] OQ-002 complement resolution embedded in MODULE-005-01

---

## [CONTEXT.MD_UPDATE]

```
### EPIC-005 Modules:
- MODULE-005-01: EvidencePacketBuilder | Type: Domain Logic   | Domain: Evaluation Engine
- MODULE-005-02: LLMAdapter            | Type: Infrastructure | Domain: Evaluation Engine
- MODULE-005-03: SubtaskEvaluator      | Type: Domain Logic   | Domain: Evaluation Engine
- MODULE-005-04: AssurancePass         | Type: Domain Logic   | Domain: Evaluation Engine

### Cross-Epic Dependencies (NEW):
- MODULE-005-01 depends on MODULE-001-02, MODULE-001-03 (EPIC-001)
- MODULE-005-01 depends on MODULE-004-01, MODULE-004-07 (EPIC-004)
- MODULE-005-02 depends on MODULE-002-04 (EPIC-002 — ResidencyGuard)
- MODULE-005-04 depends on MODULE-004-01 (EPIC-004 — ArtifactMappings)
- MODULE-005-04 AssuranceOutcome consumed by MODULE-006-01 (EPIC-006)

### High-Risk Modules Flagged:
- MODULE-005-02: structured output reliability varies by LLM provider — prompt + schema validation required
- MODULE-005-04: CONFLICTING_INFORMATION heuristic is imprecise — Phase 2 replace with LLM judge

### Unresolved Assumptions Affecting EPIC-005:
- OQ-005/NFR-008: Phase 1 published docs only — external LLM unrestricted; Phase 2 requires explicit opt-in + audit
- [THRESHOLD NEEDED] NFR-006: latency SLO — measure; do not invent
```
