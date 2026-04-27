# NFR-008 — Deployment boundary (document text vs models)

**Normative PRD:** [NFR-008](../01_PRD/prd.md) — uploaded procurement document content does not leave the deployment boundary unless an **explicit, auditable opt-in** is enabled.

## Default posture (engineering — v1 / EPIC baseline)

| Data class | Default | Opt-in external? |
|------------|---------|------------------|
| **Uploaded case PDFs / extracted text / chunks** | **Stay local** (disk + local index + local inference) | **No** unless a named integration is enabled **and** the auditor/org policy allows it (separate legal sign-off for production). |
| **M5D / Rio Manual / IN TCDF reference material** | Prefer **local** copies in `Plan/06_Models/` for indexing; same NFR-008 rules if copied into “live” case stores | Optional cloud **reference** search only if it does not send **case** document text. |
| **Embedding model weights** | Download to local cache (e.g. Hugging Face Hub **weights only**) | Allowed as **file download**; **not** a license to send case text to a public inference API. |
| **LLM inference for FR-009 / FR-010 / FR-021** | **Local** runtime (e.g. Ollama / local vLLM / bundled weights) | External LLM API is **off** by default; turning it on is a **product + compliance** decision (OQ-005 branch). |

## What “explicit opt-in” must include (minimum)

1. **Configuration flag** (off by default) naming the external service.
2. **Scope statement:** which object types may be sent (e.g. “chunks only”, max size, redaction rules if any).
3. **Audit log entry** when the path is used (who/when/which case), aligned with FR-008D / FR-014 traceability goals.
4. **UI disclosure** to the auditor that content may leave the boundary for that evaluation run.

## Relationship to OQ-005

- **EPIC drafting** may assume **local-only** inference for document-bearing calls until legal/security selects an allowed external posture.
- **Production** deployment that sends **case** document text to a third-party API requires **OQ-005** closure with written authority.

## Relationship to FR-008D / FR-021

Hybrid retrieval (FR-008D) and output assurance (FR-021) **do not require** external services. Any EPIC task that introduces cloud vector DB or cloud LLM for **case** text must be gated behind NFR-008 opt-in design above.
