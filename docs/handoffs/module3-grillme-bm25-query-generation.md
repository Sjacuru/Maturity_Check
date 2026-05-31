# Handoff: Module 3 Grill-Me — BM25 Query Generation

**Date opened:** 2026-05-29 | **Date closed:** 2026-05-30
**Status:** FULLY CLOSED — all grill-me questions resolved; proceed to `to-PRD`
**Next agent task:** Run `to-PRD` for Module 3 (`docs/prompts/02_To-PRD.md`); write pending ADRs first (see How to Continue)

---

## What This Handoff Is

This document records the blocked and then resolved DAN-0002 architecture question that paused the
Module 3 (BM25 retrieval) grill-me session. The blocking question is now settled. The grill-me
must continue through the remaining open questions before the session can feed into `to-PRD`.

---

## Suggested Skills

Before starting, invoke these project process files:

- **grill-me** — `docs/prompts/01_grill-me.md` — read this first; it governs how to conduct the session
- **to-PRD** — `docs/prompts/02_To-PRD.md` — the downstream step after grill-me completes

If the session reaches a point where implementation is ready to begin:

- `/run` — to verify the environment is functional before writing new module code
- `/verify` — to confirm behaviour after implementing a feature

---

## Project Snapshot (minimum context)

**Repo:** https://github.com/Sjacuru/Maturity_Check
**Working dir:** `c:\Users\sanseri\Documents\Projetos\Maturity_Check`
**Conda env:** `rel_voto` (Python 3.11)
**Language:** Bilingual PT + EN

**Completed modules:**
- Module 1: `src/ingestion/` — COMPLETE
- Module 2: `src/extraction/` — COMPLETE (60/60 tests)

**Module 3:** `src/retrieval/` — grill-me in progress, not yet designed

---

## Module 3 Structure (settled)

```
src/retrieval/
    indexing/      ← write-path: index(process_number, chunks) → SQLite
    query/         ← read-path: BM25 search, ranking, cascade execution
    schema/        ← SQLite + FTS5 schema ownership
    interfaces/
        contracts.py   ← RetrievedChunk (sole public output type; RetrievalResult wrapper not adopted)
        protocols.py   ← ChunkRetriever Protocol stub (not enforced at runtime)
```

**Public interface shape:**
- Write path: `index(process_number: str, chunks: list[Chunk]) -> None`
- Read path: cascade execution → `list[RetrievedChunk]`
- `Chunk` imported from `src/extraction/`; `IndexedChunk` is internal only

---

## Decisions Settled in This Session

All of these are binding. Do not reopen unless new evidence explicitly contradicts them.

| Decision | Source |
|---|---|
| Single `src/retrieval/` module (no separate indexing module) | grill-me Q1 |
| `interfaces/contracts.py` = DTOs; `interfaces/protocols.py` = Protocol stubs, not enforced | grill-me Q2 |
| `IndexedChunk` is an internal storage detail — not a public contract type | grill-me Q3 |
| `RetrievedChunk` is the sole public output type; contains text, provenance, process_number, ranking metadata | grill-me Q3 |
| FTS5 virtual table indexes `text` only — not `filename` | grill-me Q4 |
| Exact document-name match uses SQL `WHERE`, not FTS5 | grill-me Q4, ADR-0006 |
| One BM25 query per letter-suffixed Expected Product (1a, 1b, 1c…), results merged and deduplicated | grill-me Q5 |
| Runtime query generation must not involve a live LLM call | grill-me Q6 flag |
| Dense/hybrid retrieval is deferred — retrieval interfaces designed to be backend-agnostic | grill-me Q1–2 |
| **Phase 1 query generation: deterministic preprocessing of IPMP and Rio Manual content only** | DAN-0002 resolution |
| **Offline AI-assisted query artifacts: deferred to Phase 2, requires evidence-based justification** | DAN-0002 resolution |
| **`k` (chunk budget) is a named constant `MAX_CHUNKS_PER_ACAO` owned by retrieval module — not caller-supplied** | grill-me Q6 (cascade stop condition) |
| **Read-path signature: `retrieve_for_acao(acao_id: int, process_number: str) -> list[RetrievedChunk]`** | grill-me Q5B + Q6 |

**Previously settled (ADRs):**
- BM25 via SQLite FTS5, `unicode61 remove_diacritics 2` (ADR-0003)
- Three-step cascade: exact name → BM25 augmented → dense vector fallback (ADR-0006) — **refined below**
- Law/contract numbers use regex, never BM25 query terms (ADR-0007)
- One LLM call per Ação for evaluation; all chunks bundled into one prompt (ADR-0009)

---

## DAN-0002 Resolution

**Decision:** Phase 1 retrieval is deterministic runtime-only.

Query generation uses deterministic preprocessing of IPMP and Rio Manual content. Offline
AI-assisted query artifacts are deferred to Phase 2 and should only be introduced if real-case
retrieval evaluation demonstrates that the deterministic approach is insufficient.

**Rationale:** Introducing offline AI-assisted retrieval profiles now would create a new artifact
lifecycle requiring generation, versioning, provenance tracking, validation, and maintenance —
before any evidence that the simpler approach fails. The project principle of progressive
sophistication applies: start deterministic, evaluate on real cases, escalate only if warranted.

**Phase 2 boundary:** Any future offline AI-assisted retrieval-profile generation is a separate
architecture decision. It must explicitly address provenance, reproducibility, versioning,
validation, maintenance, and artifact governance before adoption.

---

## Final Retrieval Cascade (Phase 1 baseline)

This refines ADR-0006 and should be recorded as a new ADR (next number: 0015-) once the
remaining grill-me questions are resolved and the full cascade design is stable.

### Steps

**Step A — Rio Manual filename match**
Match the Document Artifact filename against Rio Manual `document_names` for the Ação.
→ Produces zero or more candidate documents.

**Step B — Exact normalized document-name variant match**
Match normalized Document Artifact content (title, headers) against Rio Manual
`document_names` and their `regex_variants` for the Ação.
→ Produces zero or more candidate documents.

**Step C — Token-overlap matching**
Soft lexical hint only. Does not establish document identity. Does not restrict retrieval scope.
→ Records candidates as hints for diagnostics/observability; does not route retrieval.

### Retrieval behavior

**If Step A or Step B identifies candidate document(s):**
- Switch to document-focused retrieval.
- Collect the full candidate document(s) as the evidence package.
- Preserve complete provenance (all chunks from that document, all pages).
- Skip corpus-wide BM25 discovery.

**If neither Step A nor Step B identifies candidate document(s):**
- Record Step C candidates as retrieval hints (for Auditor observability only).
- Continue with normal corpus-wide BM25 retrieval.
- Step C candidates must not restrict or redirect retrieval scope.

### Design notes

- The document-focused path (A or B match) means the evidence package is document-scoped, not
  chunk-ranked. This sidesteps the cascade stop-condition problem for the identified-document case.
- Corpus-wide BM25 path still requires a stop condition (`k`) — this is an open question below.
- Document-level context expansion (adjacent-page, multi-page reconstruction) is a deferred concern
  for both paths; see the deferred items section below.

---

## Remaining Grill-Me Questions

Work through these in order — they have dependencies. Cascade structure is now settled enough to
answer them.

1. ~~**Cascade stop condition (`k`)**~~ — CLOSED. `MAX_CHUNKS_PER_ACAO` named constant, owned by
   retrieval module. Not caller-supplied. Token-budget awareness stays in evaluation, not retrieval.
   Consequence: read-path signature is `retrieve_for_acao(acao_id: int, process_number: str)`.

2. ~~**Acronym expansion placement**~~ — CLOSED. Query-side only, applied during query construction
   inside `query/`. Indexed chunk content remains verbatim document text. `acronyms.json` changes
   never require reindexing.

3. ~~**`RetrievedChunk` fields**~~ — CLOSED. Settled shape (amended after Q4):
   ```python
   class RetrievedChunk(BaseModel):
       process_number: str
       filename: str
       page_number: int
       chunk_index: int
       char_offset: int
       page_total: int
       ocr_used: StrictBool
       source_type: str
       text: str
       cascade_step: Literal["filename_match", "variant_match", "bm25", "regex"]
       expected_product_id: str | None  # null on document-focused and regex paths
       bm25_score: float | None         # null on document-focused and regex paths
       rank: int | None                 # null on document-focused and regex paths
   ```
   Note: `"regex"` applies only to corpus-wide regex hits (chunks found by regex that were not
   in the BM25 top-k). On the document-focused path, regex runs within the already-identified
   document's chunks — those chunks carry `"filename_match"` or `"variant_match"`, not `"regex"`.

4. ~~**Regex search integration (ADR-0007)**~~ — CLOSED. Option C: path-aware augmentation.
   Document-focused path: regex scans only the candidate document's chunks (already in the evidence
   set — no new chunks added, just ensures law-number evidence is present).
   Corpus-wide BM25 path: regex runs independently across the full corpus in parallel with BM25;
   regex hits not in the BM25 top-k enter the result set with `cascade_step = "regex"`.
   `expected_product_id` is null for regex hits.

5. ~~**Module 3 public interface**~~ — CLOSED. Part A: implementation detail. Part B: closed as
   consequence of Q1 — no `k` parameter; signature is
   `retrieve_for_acao(acao_id: int, process_number: str) -> list[RetrievedChunk]`.
   Part C: `list[RetrievedChunk]`, no wrapper.

---

## Deferred Architecture Items (Do Not Implement in Phase 1)

**Document-level context expansion** — open design topic for a future retrieval session:
- Adjacent-page expansion
- Multi-page document reconstruction
- Evidence-package shaping
- Document-level context assembly
- Context reduction strategies for large documents

Revisit when retrieval effectiveness and document-size characteristics are better understood
from real-case evaluation.

**Offline AI-assisted retrieval-profile generation** — see DAN-0002 resolution above.
Introduce only if Phase 1 deterministic retrieval is shown insufficient by evidence.

---

## Key Files

```
docs/dan/0002-bm25-query-generation-strategy.md   ← CLOSED; resolution recorded here
docs/adr/0003-bm25-primary-retrieval.md
docs/adr/0006-retrieval-cascade-strategy.md        ← refined by cascade above; new ADR 0015- needed
docs/adr/0007-deterministic-identifiers-exact-match.md
docs/adr/0009-single-llm-call-per-action.md
CONTEXT.md                                          ← canonical vocabulary
data/ipmp/acao_01.json                              ← inspect produto.text fields directly
data/rio_manual/acao_01.json                        ← inspect document_names and regex_variants
```

---

## How to Continue

All grill-me questions are resolved. The next steps are:

1. **Write pending ADRs** — the following decisions meet all three ADR criteria (hard to reverse,
   surprising without context, genuine trade-off):
   - ADR-0015: Refined retrieval cascade (filename_match → variant_match → document-focused OR
     corpus-wide BM25 + regex). Refines ADR-0006.
   - ADR-0016: FTS5 indexes chunk `text` only, not `filename`.
   - ADR-0017: Acronym expansion is query-side only; indexed content remains verbatim.
   - Consider ADR-0018: `RetrievedChunk` without a `RetrievalResult` wrapper (public contract
     decision, hard to change once Module 4 is built).

2. **Run `to-PRD`** — use `docs/prompts/02_To-PRD.md` to produce the Module 3 PRD from the
   settled design decisions above.
