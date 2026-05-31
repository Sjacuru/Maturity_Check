# DAN-0002 — Retrieval: BM25 Query Generation Strategy

**Status:** Closed — decision recorded in `docs/handoffs/module3-grillme-bm25-query-generation.md`
**Related ADR:** ADR-0003 (BM25 primary retrieval), ADR-0006 (retrieval cascade)
**Closed:** 2026-05-30 | **Last updated:** 2026-05-29

---

## Context: The Single Unresolved Decision

> **Should BM25 query strings be derived directly from IPMP/Rio Manual source-of-truth artifacts at runtime, or should a separate offline preparation step generate retrieval-optimised query artifacts that runtime retrieval consumes?**

This question was not resolved in the Module 3 grill-me session (2026-05-29) and requires a dedicated architecture-review session before the BM25 query-construction implementation begins.

---

## Minimum Architectural Context

**Retrieval cascade (ADR-0006), step 2 — BM25 augmented search:**
For a given Ação, the system runs one BM25 FTS5 query per letter-suffixed Expected Product (1a, 1b, 1c, 1d). Results are merged, deduplicated, and ranked. This produces the evidence set for LLM evaluation.

**Query inputs available at runtime:**
- `AcaoIPMP.produtos_esperados[n].text` — IPMP description of what evidence to expect
- `AcaoRioManual.document_names` — Rio-specific document names for the Ação
- `acronyms.json` — domain acronym expansion map

**What the query generation step must produce:**
A FTS5-compatible query string per Expected Product, fed directly to SQLite BM25 ranking.

**Key constraint:** ADR-0003 requires that retrieval be deterministic — same input → same query → same ranked results. This constraint governs *runtime* retrieval. Whether it also governs the *preparation* of query artifacts is the unresolved question.

---

## Settled Decisions (Do Not Reopen)

- BM25 via SQLite FTS5 with `unicode61 remove_diacritics 2` is the primary retrieval method. (ADR-0003)
- Retrieval runs one query per letter-suffixed Expected Product, not one combined query per Ação. (grill-me Q5, 2026-05-29)
- FTS5 virtual table indexes chunk `text` only — not `filename`. (grill-me Q4, 2026-05-29)
- Exact document-name match (cascade step 1) uses SQL `WHERE`, not FTS5. (ADR-0006, grill-me Q4)
- Law/contract numbers use regex via ADR-0007 — never BM25 query terms.
- Acronym expansion is permitted as a text transformation in query construction.
- Runtime query generation must not involve a live LLM call.

---

## Why This Is Unresolved

During the grill-me session, the following concern was raised:

> The IPMP and Rio Manual source-of-truth artifacts contain significantly more text than is appropriate for direct BM25 query construction. `produto.text` is a governance description written for human auditors, not a retrieval-optimised search string. Direct use as a BM25 query may produce noisy, over-broad, or semantically diluted queries.

This triggered a competing position from the user:

> Query preparation could be done offline — once, or infrequently — using an LLM to generate retrieval-focused query strings per Expected Product. The output would be persisted as a new source-of-truth artifact. Runtime retrieval would load that artifact and use it deterministically, preserving ADR-0003.

The session did not validate or reject either position. The key clarification that emerged: **this is not about runtime LLM query generation**. It is about whether a separate, one-time or infrequent offline preparation phase should produce retrieval-oriented query artifacts that the runtime BM25 system consumes.

---

## Conceptual Boundaries

| Concept | Definition |
|---|---|
| **Runtime retrieval** | The live query-execution path: query string → FTS5 → ranked chunks. Must be deterministic (ADR-0003). |
| **Query generation** | The process that produces query strings from domain artifacts. May be offline or runtime; this is the unresolved question. |
| **Offline preparation** | A one-time or infrequent process (not in the critical path of retrieval) that generates and persists intermediate artifacts. Can use non-deterministic tools (e.g., LLM at temperature=0) because it runs outside the live scoring pipeline. |
| **Retrieval execution** | Synonymous with runtime retrieval above. |
| **Query artifact** | A persisted, versioned file containing pre-generated BM25 query strings, produced by offline preparation. Does not exist yet; is Position B's proposed output. |

---

## Competing Positions

### Position A — Direct text from source-of-truth artifacts

Expected Product `text` fields from `data/ipmp/acao_*.json` become BM25 query strings directly, with acronym expansion applied as a text transformation.

**Flow:**
```
AcaoIPMP.produto.text
    ↓ acronym expansion
    ↓ (optional) Rio Manual document name appended
FTS5 BM25 query string   ← consumed at runtime
```

**Supporting argument:** The IPMP text already describes what evidence to look for. It is the authoritative expression of what "Expected Product 1a" means. Using it directly preserves the connection between the scoring rubric and the retrieval query. Acronym expansion handles the main vocabulary mismatch problem (e.g., "PPP" → "Parceria Público-Privada").

**Risks:**
- IPMP `produto.text` may be verbose — FTS5 BM25 is sensitive to query length; long queries dilute term weights.
- Governance language may use abstract framing ("demonstrar a viabilidade…") that doesn't match how case documents phrase the same content.
- Rio Manual document names appended naively may introduce noise if the document doesn't exist for this Case.

---

### Position B — Offline LLM-assisted query artifact preparation

A separate offline process reads source-of-truth artifacts (IPMP + Rio Manual) and produces a `data/retrieval_queries/acao_*.json` artifact containing retrieval-optimised query strings per Expected Product. Runtime retrieval loads this artifact deterministically.

**Flow:**
```
AcaoIPMP.produto.text + AcaoRioManual.document_names
    ↓ offline LLM (temperature=0, one-time or infrequent)
data/retrieval_queries/acao_01.json   ← persisted artifact
    ↓ loaded at runtime (deterministic, same as IPMP/Rio artifacts)
FTS5 BM25 query string
```

**Supporting argument:** Governance artifacts are not retrieval-optimised by construction. An offline preparation step can extract retrieval-relevant vocabulary, abbreviate verbose descriptions, and incorporate domain knowledge (Rio-specific terminology, common document phrasings) that the raw IPMP text lacks. Runtime determinism is preserved because the LLM runs offline; the persisted artifact is the stable input.

**Risks:**
- Adds a new artifact type (`data/retrieval_queries/`) and a new offline process that must be documented, versioned, and re-run when IPMP artifacts change.
- Reproducibility depends on the LLM prompt + model version being stable — if either changes, query artifacts change, and retrieval results change even without code changes.
- Requires validation that LLM-generated queries actually improve retrieval over direct text (this has not been measured).
- Increases pre-Phase-1 setup cost: offline preparation must run before any Case can be evaluated.

---

## Unvalidated Assumptions

Both positions rest on assumptions that have not been tested against real Case data:

| Assumption | Held by | Status |
|---|---|---|
| IPMP `produto.text` is too verbose for effective BM25 | Position B | Untested — no retrieval evaluation has been run |
| Acronym expansion alone closes the vocabulary gap | Position A | Untested |
| LLM-generated query strings outperform direct text on Brazilian procurement documents | Position B | Untested |
| Offline query artifacts remain stable across Ações as IPMP artifacts are enriched | Position B | Untested |
| FTS5 BM25 ranking degrades meaningfully with long query strings | Position B | Not benchmarked |

---

## Question for the Next Session

> **Given that:**
> - runtime retrieval must remain deterministic (ADR-0003);
> - IPMP `produto.text` is written for human auditors, not retrieval systems;
> - offline LLM-assisted preparation is permitted in principle (it runs outside the scoring pipeline);
> - no retrieval evaluation against real Case data has been performed yet;
>
> **Should Module 3 implement query generation as:**
>
> **(A)** direct use of `produto.text` with acronym expansion only, deferring any query optimisation until retrieval failures are observed in practice; or
>
> **(B)** an offline preparation step that generates and persists a `data/retrieval_queries/acao_*.json` artifact, making retrieval-query vocabulary a first-class artifact managed alongside IPMP and Rio Manual artifacts?
>
> If (B): what triggers a re-run of the offline preparation? What versioning or hash strategy ensures reproducibility when the LLM or prompt changes?
