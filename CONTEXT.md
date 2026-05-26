# PPP Maturity Check System — Domain Context

A system that evaluates Brazilian public procurement (PPP) case documents against the IPMP framework, producing a 0/1/3 maturity score for each of 46 actions across 5 dimensions, validated by a human auditor.

---

## Language

### Evaluation Domain

**Ação**: One of 46 numbered evaluation units in the IPMP framework, each representing a planning quality criterion to be assessed against case documents.
_Avoid_: step, item, criterion, check, action (use the Portuguese term)

**Dimensão**: One of 5 thematic groupings of Ações in the IPMP (Estratégica, Técnica, Financeira, Ambiental e Social, Jurídica e Regulatória).
_Avoid_: category, dimension, area, group

**Maturity Score**: The 0/1/3 integer assigned to an Ação after LLM evaluation against the IPMP rubric and scored examples, validated by the Auditor.
_Avoid_: grade, rating, result, mark

**Auditor**: The human reviewer who validates the system's proposed Maturity Score and retrieved evidence for each Ação before the score is accepted.
_Avoid_: user, reviewer, operator, evaluator

**Case Document**: A Brazilian PPP procurement document submitted for evaluation; the search target of the retrieval module.
_Avoid_: project document, input document, target file, source file

**Expected Product** (Produto Esperado): One entry in the `produtos_esperados` list of an Ação, identified by a canonical id (e.g., `1`, `1a`, `1b`). Parent items (numeric-only id) provide display context; letter-suffixed items are the primary evidence boundaries.
_Avoid_: sub-item, checklist item, requirement, sub-criterion

**IPMP**: The primary scoring reference — defines expected products, scoring rubric (0/1/3), scored examples, and narrative criteria per Ação. All scoring decisions are grounded in IPMP.
_Avoid_: framework, standard, criteria document, TCU document

**Rio Manual**: The secondary retrieval reference — provides Rio de Janeiro-specific document names, legal vocabulary, and planning instrument terms that appear in Rio PPP case documents but are absent from IPMP text.
_Avoid_: manual, secondary source, local reference, Rio document

### Data Layer

**Source-of-truth artifact**: A JSON file in `data/ipmp/` or `data/rio_manual/` that is the authoritative, canonical representation of one Ação's evaluation or retrieval data. Multiple downstream modules consume the same artifact for different purposes.
_Avoid_: config file, data file, input file, reference file

**Canonical domain structure**: The validated Python object produced by loading a source-of-truth artifact; preserves the original hierarchy, identifiers, and field organization of the source JSON exactly.
_Avoid_: parsed data, model instance, record, normalized object

**Structural normalization**: The only transformations the ingestion module may apply to a loaded artifact — schema enforcement, type coercion, whitespace cleanup — that do not alter content, meaning, or hierarchy.
_Avoid_: data cleaning, ETL, processing, enrichment

**Intentional incompleteness**: A valid state of a source-of-truth artifact where certain fields are empty or contain placeholder values because the corresponding business data has not yet been researched or confirmed (e.g., unknown law number, empty `regex_variants`).
_Avoid_: missing data, error, invalid state, gap (when the incompleteness is deliberate)

**Progressive enrichment**: The expected lifecycle of source-of-truth artifacts — fields are populated incrementally as domain research advances, without invalidating previously valid structure.
_Avoid_: data migration, update cycle, versioning, backfill

**Artifact integrity**: The structural soundness of a source-of-truth artifact — parseable JSON, structurally valid schema, internally consistent identifiers (e.g., filename suffix matches `acao_id`).
_Avoid_: data quality, completeness, domain validity

### Module Concepts

**Ingestion module**: The Python package (`src/ingestion/`) responsible for loading, validating, and exposing canonical domain structures from source-of-truth artifacts. Owns no retrieval semantics.
_Avoid_: parser, loader, ETL layer, data access layer

**Retrieval semantics**: Any logic that interprets canonical domain structures for search purposes — BM25 query construction, acronym expansion, cascade execution, chunk ranking, vector similarity.
_Avoid_: search logic, query logic, downstream logic

**Operational continuity**: The property of the ingestion module that allows the system to start and run even when individual source-of-truth artifacts have non-fatal Pydantic validation failures, provided fatal integrity errors are absent.
_Avoid_: fault tolerance, resilience, degraded mode, graceful degradation

**Retrieval cascade**: The ordered retrieval strategy for a given Ação: (1) exact document name match, (2) BM25 augmented search, (3) dense vector fallback. Belongs entirely to the retrieval module.
_Avoid_: pipeline, search flow, fallback chain

---

## Relationships

- An **Ação** belongs to exactly one **Dimensão**
- An **Ação** has one or more **Expected Products**, each identified by a canonical id
- One **IPMP** source-of-truth artifact defines one **Ação's** rubric, scored examples, and expected products
- One **Rio Manual** source-of-truth artifact provides retrieval context for the same **Ação**
- The **ingestion module** loads source-of-truth artifacts and exposes **canonical domain structures** via three singletons
- The **retrieval module** consumes canonical domain structures and applies **retrieval semantics** to produce evidence chunks
- The **Auditor** validates the system's proposed **Maturity Score** for each **Ação** before it is accepted
- A **Case Document** is searched by the retrieval module to find evidence for an **Ação's** Expected Products

---

## Example dialogue

> **Dev:** "When I add `acao_17.json` to `data/ipmp/`, will the system pick it up?"
> **Domain expert:** "Yes — the ingestion module auto-discovers all `acao_*.json` files at load time. As long as the JSON is parseable and the structure is valid, it loads. If the Rio Manual artifact for Ação 17 has empty `regex_variants` for a law we haven't identified yet, that's **intentional incompleteness** — the loader logs it and continues. It's not a broken **source-of-truth artifact**."
>
> **Dev:** "Should the ingestion module filter out parent Expected Products (id `'1'`) and only expose the letter-suffixed ones (id `'1a'`, `'1b'`) to avoid retrieval noise?"
> **Domain expert:** "No — those ids are part of the **canonical domain structure**. The ingestion module preserves the full hierarchy exactly as defined in the JSON. Deciding which Expected Products drive BM25 queries is **retrieval semantics** — that decision belongs to the retrieval module, not ingestion. The ingestion module has no knowledge of BM25."
>
> **Dev:** "We're in Phase 1 with only Ação 1 defined. Can the system score a case document for Ação 1 even if `acao_02.json` doesn't exist yet?"
> **Domain expert:** "Yes — that's **progressive enrichment**. The ingestion module loads whatever source-of-truth artifacts exist. Phase 1 naturally loads only Ação 1. Adding Ação 2 later means dropping `acao_02.json` in the right directory — no code change needed."

---

## Flagged ambiguities

- **"validation"** was used to mean both Pydantic schema enforcement and business-domain completeness checking — resolved: ingestion performs structural validation only; domain completeness is tracked via `_meta.known_gaps` in source-of-truth artifacts, not by Pydantic.
- **"normalization"** was considered to include query-oriented transformations (sub-item filtering, acronym expansion) — resolved: normalization in the ingestion module means structural normalization only; all retrieval-oriented transformations are retrieval semantics and belong to the retrieval module.
- **"gap"** was used to mean both structural errors and intentionally incomplete domain data — resolved: structural errors are **artifact integrity** failures (fatal); intentionally incomplete data is captured in `_meta.known_gaps` and is a valid document state (non-fatal).
- **"canonical"** was used loosely to refer to both the JSON file and the loaded Python object — resolved: the JSON file is the **source-of-truth artifact**; the loaded, validated Python object is the **canonical domain structure**.
