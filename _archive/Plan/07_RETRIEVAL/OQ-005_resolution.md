# OQ-005 Resolution — LLM Backend Policy (revised 2026-05-06)

**Original Decision Date:** April 28, 2026
**Revised:** May 6, 2026 — data-class split introduced
**Stakeholder:** Solo Development (approval: internal bosses + Master's adviser)

---

## Revision summary

The original resolution treated all external LLM calls as Phase 2+. This was overly
restrictive. The correct boundary is **document publication status**, not data class or phase:

| Document status | External LLM | Rationale |
|---|---|---|
| **Reference / normative documents** (M5D, Rio Manual, TCDF IN) | ✅ Always allowed | Public documents. No residency obligation. |
| **Phase 1 case documents** (already published / publicly shared procurement cases) | ✅ Allowed — not sensitive | Published records carry no residency restriction. |
| **Future case documents for unpublished / in-progress projects** | ❌ Local-first. Explicit opt-in required. | NFR-008 compliance. These may contain sensitive, pre-decisional municipal procurement data. |

NFR-008 says: *"No external transmission of **document content** without explicit authorization."*
In practice this applies only to documents that have not yet been publicly released.
Phase 1 works entirely with published documents — no NFR-008 restriction applies.

---

## 1. LLM policy by document status

### 1.1 Published documents — external LLM allowed (Phase 1)

All Phase 1 work uses documents that are already publicly available. No transmission
restriction applies. This covers:

- Reference / normative documents (M5D, Rio Manual, TCDF IN)
- Case documents for Phase 1 evaluation (published procurement cases)

**All of the following can be sent to external LLM in Phase 1:**
- M5D sub-task text, expected output, complement text
- Rio Manual and TCDF IN artifact descriptions
- Crosswalk `intencao` text
- Case document chunks from published procurement cases
- Retrieval results from both reference and case indexes

### 1.2 Unpublished / in-progress project documents (future phases)

When the system is used to evaluate procurement processes that have **not yet been
made public** (in-progress, pre-decisional documents), NFR-008 applies:

- Case document text stays local by default
- External inference requires explicit opt-in: `ENABLE_EXTERNAL_CASE_EVAL=true`
- Audit log entry mandatory per call
- Legal/security sign-off required before production deployment with in-progress cases

**Trigger:** when an auditor uploads documents for a project that has not yet been
publicly announced or published in the official gazette (Diário Oficial).

---

## 2. Recommended LLM configuration (Phase 1)

```
Reference reasoning      →  External API (Claude, Groq, or similar)
Case evaluation          →  External API (published docs — no restriction)
Assurance pass (FR-021)  →  External API or Local Ollama (temperature=0, deterministic)
Embeddings               →  Local sentence-transformers (always local)
```

For unpublished/in-progress case documents (future phases):
```
Case evaluation          →  Local Ollama (Mistral) — NFR-008
Assurance pass (FR-021)  →  Local Ollama (temperature=0) — NFR-008
```

### 2.1 Config file structure

**File:** `config/llm_backends.json` (git-ignored; template at `config/llm_backends.template.json`)

```json
{
  "reference_reasoning": {
    "backend": "external",
    "provider": "groq",
    "model": "mixtral-8x7b-32768",
    "api_key_env": "GROQ_API_KEY",
    "temperature": 0.3,
    "max_tokens": 2000,
    "timeout_seconds": 30,
    "note": "Public normative docs only. No case document text."
  },
  "case_evaluation": {
    "backend": "local",
    "provider": "ollama",
    "endpoint": "http://localhost:11434",
    "model": "mistral:latest",
    "temperature": 0.3,
    "max_tokens": 2000,
    "timeout_seconds": 60,
    "note": "Case text stays local per NFR-008."
  },
  "assurance_pass": {
    "backend": "local",
    "provider": "ollama",
    "endpoint": "http://localhost:11434",
    "model": "mistral:latest",
    "temperature": 0,
    "max_tokens": 1000,
    "timeout_seconds": 60,
    "note": "FR-021 deterministic pass. Always local."
  },
  "external_case_eval_opt_in": {
    "enabled": false,
    "requires_audit_log": true,
    "audit_log_path": "logs/external_api_calls.jsonl",
    "note": "Off by default. Requires explicit flag + legal sign-off."
  }
}
```

---

## 3. Audit trail (unchanged from original)

All external API calls are logged to `logs/external_api_calls.jsonl`. For reference
reasoning calls, the log entry includes:

```json
{
  "timestamp": "ISO8601",
  "call_type": "reference_reasoning",
  "action_id": "action_1",
  "subtask_id": "subtask_1_1",
  "backend": "groq",
  "model": "mixtral-8x7b-32768",
  "input_tokens": 420,
  "output_tokens": 85,
  "latency_ms": 980,
  "status": "success",
  "data_class": "reference",
  "contains_case_data": false
}
```

The `contains_case_data: false` field is the key guard — it must be programmatically
verified before any call reaches the external backend.

---

## 4. Architecture diagram (Phase 1 revised)

```
Reference Documents (M5D, Rio Manual, TCDF IN)
    ↓  [normalize_pdf_headings + chunking]
SQLite + LanceDB (local vector index)
    ↓  [semantic search with heading filter]
Reference chunks (normative context)
    ↓
[External LLM — reference reasoning]  ← public data, OK
    ↓
Normative evaluation context
    ↓
Case Document Chunks (from uploaded PDFs)   ← sensitive, stays local
    +
[Local Ollama — case evaluation (FR-009/FR-010)]
    ↓
[Local Ollama — assurance pass (FR-021, temp=0)]
    ↓
[SQLite persistence — evaluation records + audit log]
    ↓
Auditor review
```

---

## 5. Resolution summary

| Question | Answer |
|---|---|
| External LLM — Phase 1 (published docs)? | ✅ Yes — reference docs and published case docs, no restriction |
| External LLM — unpublished/in-progress case docs? | ❌ Local-first. Opt-in + audit log + legal sign-off. |
| Embedding model? | Always local (sentence-transformers) |
| Assurance pass (FR-021)? | External OK for published docs; local-only for unpublished case docs |
| Audit log required? | Yes — all external calls |
| NFR-008 applies when? | Only when evaluating documents not yet publicly released |

---

## Document history

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-04-28 | Initial: Phase 1 local-only, Phase 2+ Groq opt-in |
| 2.0 | 2026-05-06 | Data-class split: reference docs → external OK Phase 1; case docs → local-first |
