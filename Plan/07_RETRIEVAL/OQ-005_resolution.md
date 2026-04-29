# OQ-005 Resolution — Local LLM + External Groq API Integration

**Decision Date:** April 28, 2026  
**Stakeholder:** Solo Development (approval: internal bosses + Master's adviser)  
**Scope:** M5D Evaluation System (MVP Phase 1 → Production Phase 2)

---

## Executive Summary

**OQ-005** addresses whether case document text may be sent to external LLM services. This resolution establishes:

- **Phase 1 (MVP):** Local-only inference using **Ollama** (default, no external API calls)
- **Phase 2+ (Production):** Optional **Groq API** integration for faster inference (explicitly configured, auditable)
- **Sensitive Data:** All case document content remains under developer control; no automatic transmission
- **Audit Trail:** All external API calls logged with timestamp, case_id, sub-task_id, data size, response latency

---

## 1. Default Engineering Posture (Phase 1)

### 1.1 Local-First Assumption (NFR-008 Compliance)

**All case document processing** in Phase 1 uses **local infrastructure only:**

| Component | Local Tool | External Alternative | Phase 1 | Phase 2 |
|-----------|-----------|----------------------|---------|---------|
| **LLM inference (FR-009, FR-010, FR-021)** | Ollama (bundled) | Groq API | ✅ Default | 🔄 Optional |
| **Vector embeddings (FR-006, FR-008D)** | sentence-transformers (local cache) | External embedding API | ✅ Only | ❌ Forbidden |
| **Vector storage** | LanceDB (local SQLite + disk) | Cloud vector DB | ✅ Only | ❌ Forbidden |
| **Case document text** | Local disk storage | Cloud storage | ✅ Only | ❌ Forbidden |

### 1.2 Why Local-First?

1. **Data Residency:** Rio municipal auditor data does not leave developer's machine
2. **Cost Control:** No per-token charges for Phase 1 MVP testing
3. **Latency:** Local inference avoids network round-trips during development/testing
4. **Compliance Simplicity:** No external authentication, no vendor dependency
5. **Reproducibility:** Deterministic behavior for debugging and testing

### 1.3 Technology Stack (Phase 1)

```
Case Documents (PDF/TXT)
    ↓
[Local PDF Extractor] (pdfplumber or PyPDF2)
    ↓
[Local Chunker] (maturity_check.ingest.chunking)
    ↓
SQLite (local, WAL mode)  +  LanceDB (local disk index)
    ↓
Sparse Index (BM25)  +  Dense Index (sentence-transformers embeddings)
    ↓
[Retrieval Orchestrator] (local code, no API calls)
    ↓
[Ollama Local LLM] (running on localhost:11434)
    ↓
FR-009/FR-010 Evaluator (local inference)
    ↓
FR-021 Assurance Pass (local inference)
    ↓
[SQLite Persistence] (evaluation records + evidence links + audit log)
    ↓
Auditor UI (review + annotate)
```

**No external API calls in Phase 1.** All processing happens on developer's machine.

---

## 2. Optional External LLM Integration (Phase 2+)

### 2.1 When to Enable Groq API

Groq integration is **opt-in** and **off by default**, enabled only when:

- [ ] Phase 1 MVP is fully tested and working locally
- [ ] Performance benchmarks show local Ollama is insufficient (e.g., latency > 30s per sub-task)
- [ ] Scalability testing on Rio municipal server shows need for faster inference
- [ ] Developer explicitly sets config flag `ENABLE_EXTERNAL_LLM=true`
- [ ] Developer provides valid Groq API key in environment variable `GROQ_API_KEY`
- [ ] Audit log is configured and validated before first API call

### 2.2 Groq API Configuration Structure

**Config file:** `config/llm_backends.json` (git-ignored; template provided)

```json
{
  "llm_backends": {
    "local_ollama": {
      "enabled": true,
      "endpoint": "http://localhost:11434",
      "model": "mistral:latest",
      "timeout_seconds": 60,
      "max_tokens": 2000,
      "temperature": 0.3
    },
    "external_groq": {
      "enabled": false,
      "provider": "groq",
      "api_key_env": "GROQ_API_KEY",
      "model": "mixtral-8x7b-32768",
      "timeout_seconds": 30,
      "max_tokens": 2000,
      "temperature": 0.3,
      "audit_log_enabled": true,
      "audit_log_path": "logs/external_api_calls.jsonl"
    }
  },
  "fallback_strategy": {
    "primary": "local_ollama",
    "secondary": "external_groq",
    "secondary_only_if_primary_fails": true,
    "secondary_case_filter": null
  }
}
```

**How to enable Groq:**

```bash
# Set environment variable
export GROQ_API_KEY="gsk_..."

# Update config file: change "enabled" from false to true
# Application will now use Groq for fallback if Ollama fails
```

### 2.3 What Data Can Be Sent to Groq (Restricted)

**Only in Phase 2+ and only if explicitly enabled:**

- ✅ **Allowed:** Case sub-task text (structured question about required elements)
- ✅ **Allowed:** Anonymized chunk excerpts (100–500 chars)
- ✅ **Allowed:** Metadata (artifact_id, grau, tipo)
- ❌ **FORBIDDEN:** Full document context (preserve privacy)
- ❌ **FORBIDDEN:** Auditor names or institution identifiers
- ❌ **FORBIDDEN:** Case metadata linking to specific projects

**Example allowed query to Groq:**

```
Sub-task 1.1: "Identify evidence that the investment proposal includes market analysis."

Evidence chunk: "O mercado de infraestrutura brasileira apresenta demanda crescente..."

Question: Does this chunk contain evidence of market analysis (sim/não/incerto)?
```

**Example forbidden query:**

```
"Rio Case #2024-001 (Auditor: João Silva) - full document text..."
```

---

## 3. Audit Trail & Security (NFR-008 Compliance)

### 3.1 Audit Log Structure

**Every external API call** (Groq) is logged to `logs/external_api_calls.jsonl`:

```json
{
  "timestamp": "2026-05-15T10:23:45.123Z",
  "case_id": "RIO-2024-001",
  "action_id": "action_1",
  "subtask_id": "subtask_1_1",
  "inference_backend": "groq",
  "input_tokens": 312,
  "output_tokens": 47,
  "latency_ms": 1234,
  "status": "success",
  "sanitized_query_hash": "sha256:abc123...",
  "response_confidence": 0.92,
  "api_endpoint": "https://api.groq.com/openai/v1/chat/completions",
  "auditor_id": null,
  "case_owner": "internal_development"
}
```

**Not logged:** Full query text or response text (only hashes + metadata)

### 3.2 Compliance Checklist (Before Production Deployment)

- [ ] All audit logs are persisted to immutable storage
- [ ] Audit log retention: minimum 2 years (municipal compliance standard)
- [ ] Groq API key is **not committed** to git (use .env files)
- [ ] Groq API responses are **not cached** in git history
- [ ] A security audit has reviewed data anonymization rules above
- [ ] A legal advisor has approved external API usage for Rio deployment
- [ ] Developer has documented which cases/sub-tasks require local-only inference (e.g., highly sensitive)

---

## 4. Configuration-First Workflow

### 4.1 Phase 1 (Local Only)

Developer workflow — no configuration needed:

```bash
# Phase 1 default: everything local
maturity-check ingest-m5d                  # M5D to SQLite + LanceDB
maturity-check evaluate-case --case-id=RIO-001 --action=action_1
  # Internally uses Ollama (localhost:11434)
  # No Groq API calls
```

### 4.2 Phase 2+ (Local + Optional External)

**Scenario A: Stick with Local**

```bash
# No config change needed; continues using Ollama
maturity-check evaluate-case --case-id=RIO-001 --action=action_1
```

**Scenario B: Enable Groq as Fallback**

```bash
# 1. Edit config/llm_backends.json: set external_groq.enabled = true
# 2. Set environment variable
export GROQ_API_KEY="gsk_..."

# 3. Run evaluation (now uses Groq if Ollama unavailable)
maturity-check evaluate-case --case-id=RIO-001 --action=action_1 \
  --config=config/llm_backends.json

# Audit log is automatically written to logs/external_api_calls.jsonl
```

**Scenario C: Groq Only (Production Scaling)**

```bash
# Edit config/llm_backends.json
# Set primary: "external_groq", secondary: null (or local fallback)
# Production deployment would use this after Rio municipal legal sign-off
```

---

## 5. Implementation Phases

### Phase 1 (MVP, Apr 28 - May 29)

| Week | Task | Deliverable |
|------|------|-------------|
| 1–2 | Install Ollama locally; verify model runs | Screenshot of `ollama serve` + `ollama pull mistral` |
| 3–8 | Implement FR-009/FR-010/FR-021 evaluators using Ollama | Python code + test results |
| 9–10 | End-to-end Action 1 Sub-task 1.1 evaluation (local only) | Auditor interface showing result |
| 11 (May 29) | MVP demo + document local-only architecture | Word doc + architecture diagram |

**No external API calls.** OQ-005 branching logic is **stubbed** (config exists but Groq not enabled).

### Phase 2 (Jun 1 - Nov 20)

| Milestone | Task | OQ-005 Gate |
|-----------|------|-----------|
| **Jun–Jul** | Actions 2–5 evaluation | Local only, continue |
| **Aug** | Performance testing on Rio server | Measure latency; decide if Groq needed |
| **Sep** | Groq API integration (code) | Legal/security review of audit trail |
| **Oct** | Production config + deployment prep | Formal OQ-005 sign-off required |
| **Nov** | Full 46 Actions + Groq enabled (if approved) | Production ready |

---

## 6. Technology Constraints & Guarantees

### 6.1 Local LLM (Ollama)

**Guarantee:** Model weights never leave developer's machine.

- Downloaded to `~/.ollama/models/` (local cache)
- Running locally on `localhost:11434`
- No internet required after initial model download
- Cost: $0 (compute only)

### 6.2 External LLM (Groq)

**Guarantee:** Only anonymized, structured queries sent.

- Full document text **never** transmitted
- Queries logged with hash (not plaintext)
- Optional; requires explicit opt-in + config
- Cost: Per-token billing (negotiated with Rio municipal IT)

### 6.3 Case Data

**Guarantee:** All case documents stay local.

- Stored in SQLite (developer's machine)
- Backed up to git (excluded from remote by .gitignore)
- Never transmitted to Groq or any cloud service unless developer explicitly codes it
- Developer is responsible for data security

---

## 7. Resolution Summary

| Question | Answer |
|----------|--------|
| **OQ-005 Default (Phase 1)?** | Local Ollama only; no external API |
| **OQ-005 Optional (Phase 2+)?** | Groq API available if enabled + audited |
| **Who decides external API?** | Developer (you) + Rio municipal IT (deployment) |
| **Audit trail required?** | Yes; logged to `logs/external_api_calls.jsonl` |
| **Data privacy guaranteed?** | Yes; anonymized queries + local-first |
| **Compliance checked?** | Yes; checklist in Section 3.2 |
| **Configuration approach?** | JSON config + environment variables (git-ignored) |

---

## 8. Next Steps

1. ✅ **This document** captures OQ-005 resolution
2. ⏳ **Phase 1 tasks** (starting Week 1) include: "Install Ollama + verify local inference"
3. ⏳ **Phase 2 tasks** (after MVP) include: "Groq API integration + audit trail" (conditional)
4. ⏳ **Update [pendencias_pre_epic.md](../00_PENDENCIES/pendencias_pre_epic.md)** — move OQ-005 from OPEN to RESOLVED

---

## Appendix: Configuration Template

**File:** `config/llm_backends.template.json` (committed to git)

```json
{
  "llm_backends": {
    "local_ollama": {
      "enabled": true,
      "endpoint": "http://localhost:11434",
      "model": "mistral:latest",
      "timeout_seconds": 60,
      "max_tokens": 2000,
      "temperature": 0.3,
      "fallback_enabled": true,
      "notes": "Default for Phase 1 MVP. No API calls."
    },
    "external_groq": {
      "enabled": false,
      "provider": "groq",
      "api_key_env": "GROQ_API_KEY",
      "model": "mixtral-8x7b-32768",
      "timeout_seconds": 30,
      "max_tokens": 2000,
      "temperature": 0.3,
      "audit_log_enabled": true,
      "audit_log_path": "logs/external_api_calls.jsonl",
      "notes": "ENABLE ONLY after Phase 1 MVP is complete and legal review approved."
    }
  },
  "fallback_strategy": {
    "primary": "local_ollama",
    "secondary": "external_groq",
    "secondary_only_if_primary_fails": true,
    "secondary_case_filter": "whitelist_cases.txt"
  }
}
```

**Instructions:**
1. Copy to `config/llm_backends.json`
2. Phase 1: Keep `external_groq.enabled = false`
3. Phase 2: Change to `true` only after legal approval + testing

---

## Document History

| Version | Date | Author | Status |
|---------|------|--------|--------|
| 1.0 | 2026-04-28 | Development | Resolved (Phase 1 + 2+) |
