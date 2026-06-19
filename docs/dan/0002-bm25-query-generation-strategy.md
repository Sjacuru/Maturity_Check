# DAN-0002 — Retrieval: BM25 Query Generation Strategy

**Status:** Closed — decisions recorded in ADR-0047 (Retrieval Profile Architecture) and ADR-0048 (Query Construction and Encoding)
**Related ADR:** ADR-0003 (BM25 primary retrieval), ADR-0006 (retrieval cascade), ADR-0047, ADR-0048
**Closed:** 2026-05-30 | **Last updated:** 2026-06-18

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

---

## Evolution of Query Generation Strategy

This DAN's original question — "direct IPMP text vs. offline query artifacts?" — was resolved in an architectural interview session (2026-06-17/18). The resolution supersedes both Position A and Position B as originally framed.

**What the original positions shared:** both treated query generation as a vocabulary extraction problem. Position A extracted vocabulary from IPMP text directly. Position B extracted vocabulary via an LLM reading the same IPMP text offline. Both started from the same source and would have reproduced the same governance framing language, either directly or at one remove.

**What was replaced:** direct IPMP text tokenisation (`build_bm25_query()` applied to `produto.texto`) was replaced by structured retrieval profiles. The specific failure was diagnosed: `produto.texto` is governance criterion language written for human auditors, not evidence-bearing vocabulary from case documents. Tokenising it into single-word OR-clauses matches IPMP's own framing terms against unrelated chunks rather than finding the evidence IPMP describes.

**What was not adopted:** fully automated LLM-assisted query generation without real-document grounding. An LLM reading only IPMP text would reproduce the same governance framing language at a different level of indirection — the same vocabulary problem in a different form.

**What was adopted:** structured curation via retrieval profiles. Each Expected Product's query terms are derived through a three-stage process — (A) IPMP concept extraction, (B) mandatory real-document observation, (C) Rio Manual and canonical cross-reference. The process is structured and repeatable; real PPP case documents are a required input, not optional enrichment. The resulting artifact is `data/retrieval_profiles/acao_NN.json`.

**Why this supersedes the original framing:** the retrieval profile encodes not just vocabulary but evidence types (A/B/C/D), encoding strategies (phrase vs. NEAR()), provenance, confidence level, and conceptual traceability. The core architectural principle adopted is: *evidence is modeled as relationships, not merely vocabulary*. Neither Position A nor Position B anticipated this.

**Scalability concern resolved:** unsustainable manual maintenance of phrase-variant sets across 46 Ações was explicitly rejected. NEAR() proximity encoding for Type C (process and relational evidence) avoids enumerating paraphrase variants. The structured population methodology (domain expert + ontology framework + real documents) makes the process repeatable across Ações without open-ended manual enumeration.

**ADR-0003 determinism preserved:** retrieval profiles are persisted JSON artifacts. Once generated, runtime retrieval loads them deterministically — same profile → same queries → same BM25 results. The non-deterministic step (human judgment + document reading during a population session) is entirely offline.

**Architecture decisions:** ADR-0047 (Retrieval Profile Architecture), ADR-0048 (Query Construction and Encoding).
