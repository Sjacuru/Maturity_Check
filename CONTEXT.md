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

**Case**: A PPP procurement business process submitted for evaluation, identified by its `process_number`. Composed of one or more Document Artifacts. May have a `contract_number` if a contract was signed.
_Avoid_: project, submission, dossier, folder

**Process Number**: The canonical business identifier of a Case, assigned during the administrative process lifecycle. Always present.
_Avoid_: case ID, process ID, identifier

**Contract Number**: An optional identifier for a signed contract within a Case. Cannot exist without a `process_number`; a Case may exist without one.
_Avoid_: contract ID, deal number

**Document Artifact**: An individual PDF file associated with a Case. Identified by filename within its Case.
_Avoid_: Case Document (retired), input document, target file, source file, PDF

**Chunk**: The atomic unit of extracted text produced by the extraction module. Page boundaries are the primary provenance boundary; a single page may produce multiple Chunks when the page is large. Carries domain-neutral extraction metadata: `filename`, `page_number`, `chunk_index` (intra-page position), `char_offset`, `text`, `text_length`, `page_total`, `ocr_used`, `source_type`. No Case or business-domain identifiers — those are added by the indexing layer.
_Avoid_: passage, segment, excerpt, text unit

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

**Extraction module**: The Python package (`src/extraction/`) responsible for reading a Document Artifact (PDF) and returning a list of Chunks. Pure transformation layer — no knowledge of Cases, SQLite, BM25, or business-domain identifiers. Public interface: `extract_document(path: Path) -> list[Chunk]`.
_Avoid_: PDF parser, chunker, pipeline, ingestion (that term is taken)

**Retrieval module**: The Python package (`src/retrieval/`) responsible for indexing Document Artifact chunks into SQLite and executing the retrieval cascade to produce evidence for a given Ação. Sub-packages: `indexing/`, `query/`, `schema/`, `interfaces/`. Public write-path entry: `index(process_number: str, chunks: list[Chunk])`. Public read-path entry: retrieval cascade execution returning `list[RetrievedChunk]`.
_Avoid_: search module, BM25 module, query layer

**RetrievedChunk**: The domain-level retrieval result returned by the retrieval cascade. Carries: full `Chunk` provenance (`process_number`, `filename`, `page_number`, `chunk_index`, `char_offset`, `page_total`, `ocr_used`, `source_type`), `text`, `cascade_step` (`"filename_match"` | `"variant_match"` | `"bm25"` | `"regex"`), `expected_product_id` (the Expected Product id that drove the query; null on document-focused and regex paths), `bm25_score` (null on document-focused and regex paths), `rank` (null on document-focused and regex paths). Does not expose SQLite row IDs, FTS5 docids, or other storage internals.
_Avoid_: search result, hit, match, ranked chunk

**Retrieval semantics**: Any logic that interprets canonical domain structures for search purposes — BM25 query construction, acronym expansion, cascade execution, chunk ranking, vector similarity.
_Avoid_: search logic, query logic, downstream logic

**Evaluation module**: The Python package (`src/evaluation/`) responsible for assembling the LLM prompt, executing a single LLM call per Ação, parsing the response, and returning an `EvaluationResult`. Pure evaluation layer — no knowledge of retrieval, SQLite, or Auditor rendering. Public interface: `configure_llm(provider, model, base_url)` and `evaluate(acao_id, process_number, chunks) -> EvaluationResult`.
_Avoid_: scoring module, LLM module, inference layer

**EvaluationResult**: The forensic evaluation artifact produced by the evaluation module for one Ação/Case pair. Carries identity (`acao_id`, `process_number`), reproducibility metadata (`provider`, `model`), evidence supplied (`retrieved_chunks`, `evidence_char_count`), prompt audit trail (`system_prompt`, `user_prompt`), LLM output (`raw_llm_response`, `reasoning`, `proposed_score`), and three orthogonal status flags (`uncertainty_flag`, `parse_failed`, `no_evidence_found`). Defined as a Pydantic `BaseModel` in `src/evaluation/interfaces/contracts.py`.
_Avoid_: scoring result, evaluation DTO, response object, score record

**LLMClient**: A minimal Protocol defining the evaluation module's sole interface to any LLM provider. Single method: `complete(system: str, user: str) -> str`. Concrete implementations: `OllamaClient` (local, default) and `GroqClient` (cloud option). Instantiated via `configure_llm()`.
_Avoid_: AI client, model client, LLM wrapper, provider adapter

**Uncertainty flag**: A boolean field in `EvaluationResult` set by the LLM (via `UNCERTAINTY: yes` in the sentinel block) when retrieved evidence is absent, insufficient, or contradictory with respect to the Ação's Expected Products. Distinct from `parse_failed` (format compliance failure set by Module 4) and `no_evidence_found` (upstream retrieval state set by Module 4 before any LLM call).
_Avoid_: confidence flag, model confidence, uncertainty score

**Operational continuity**: The property of the ingestion module that allows the system to start and run even when individual source-of-truth artifacts have non-fatal Pydantic validation failures, provided fatal integrity errors are absent.
_Avoid_: fault tolerance, resilience, degraded mode, graceful degradation

**Retrieval cascade**: The ordered retrieval strategy for a given Ação: (1) exact document name match, (2) BM25 augmented search, (3) dense vector fallback. Belongs entirely to the retrieval module.
_Avoid_: pipeline, search flow, fallback chain

**Assessment module**: The Python package (`src/assessment/`) responsible for orchestrating the end-to-end assessment workflow for one Case — accepting Document Artifacts via upload, storing them to disk, calling extraction, indexing, retrieval, and evaluation in sequence, and returning an `EvaluationResult`. Owns the application-service layer; FastAPI routes invoke it; a future CLI may invoke it directly. Does not own HTTP concerns, score persistence, or Auditor rendering. Per-document pipeline: Upload → Store → Extract → Index → Retrieve → Evaluate. (The ingestion module loads IPMP/Rio Manual framework data at startup; it is not a per-document step.)
_Avoid_: pipeline runner, orchestration layer, workflow engine, ingestion (that term is taken by Module 1)

**Review Outcome**: The Auditor's validated record for one EvaluationResult. Carries: `acao_id`, `process_number`, `final_score` (in {0, 1, 3}), `is_override` (bool), `justification` (str | None — required when `is_override=True`, must be None otherwise), `evidence_references` (list[int] | None — chunk indices into `retrieved_chunks`; None means the Auditor did not use the field; [] means the Auditor explicitly supplied an empty set), and `created_at`. All original EvaluationResult status flags are preserved unchanged. A Review Outcome where `is_override=True` or where a manual score was assigned on a no_evidence_found/parse_failed result is an Auditor Intervention. `created_at` is set at the application/persistence boundary, not from client input.
_Avoid_: audit record, final evaluation, validated score, auditor response

**Final Score**: The authoritative Maturity Score for an Ação/Case pair after Auditor review — always in {0, 1, 3}. Produced by accepting `proposed_score` or overriding it. The Final Score coexists with `proposed_score` in storage; they may differ.
_Avoid_: confirmed score, definitive score, accepted score

**Auditor Intervention**: A Review Outcome in which the Final Score was produced by the Auditor manually assigning a score rather than accepting the LLM's `proposed_score`. Applies to: any override (is_override=True), and any manual score assignment on a no_evidence_found or parse_failed EvaluationResult.
_Avoid_: manual override, correction, human correction

---

## Relationships

- An **Ação** belongs to exactly one **Dimensão**
- An **Ação** has one or more **Expected Products**, each identified by a canonical id
- One **IPMP** source-of-truth artifact defines one **Ação's** rubric, scored examples, and expected products
- One **Rio Manual** source-of-truth artifact provides retrieval context for the same **Ação**
- The **ingestion module** loads source-of-truth artifacts and exposes **canonical domain structures** via three singletons
- The **retrieval module** consumes canonical domain structures and applies **retrieval semantics** to produce **RetrievedChunk** lists as evidence for an Ação
- The **retrieval module** indexes `list[Chunk]` keyed by `process_number`; the indexing write-path attaches `process_number` internally — callers supply it, extraction never knows it
- The **evaluation module** consumes `list[RetrievedChunk]` from the retrieval module and IPMP data from the ingestion module to produce one **EvaluationResult** per Ação/Case pair
- The **evaluation module** calls one **LLMClient** (either `OllamaClient` or `GroqClient`) per evaluation via `configure_llm()`
- An **EvaluationResult** carries the proposed **Maturity Score**, full audit trail, and three orthogonal status flags for the **Auditor**
- The **Auditor** validates the system's proposed **Maturity Score** for each **Ação** before it is accepted
- The **assessment module** orchestrates extraction, retrieval, and evaluation for one Case and returns an **EvaluationResult** per Ação
- The **Auditor** produces one **Review Outcome** per **EvaluationResult**, carrying the **Final Score**
- A **Review Outcome** either accepts the `proposed_score` (is_override=False) or overrides it (is_override=True) with a mandatory justification
- An **Auditor Intervention** is a **Review Outcome** where the **Final Score** was not derived from the LLM's `proposed_score`
- A **Case** has one `process_number` (required) and zero or one `contract_number` (optional)
- A **Case** contains one or more **Document Artifacts**
- A **Document Artifact** is chunked into one or more **Chunks** during extraction
- A **Chunk** carries provenance: the **Document Artifact** filename and page number it came from
- The retrieval module searches **Chunks** to find evidence for an **Ação's** Expected Products

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

- **"Case Document"** was used as the term for a submitted PDF — retired: the system distinguishes between a **Case** (the business process, identified by `process_number`) and a **Document Artifact** (an individual PDF within that Case). "Case Document" was ambiguous between the two.

- **"validation"** was used to mean both Pydantic schema enforcement and business-domain completeness checking — resolved: ingestion performs structural validation only; domain completeness is tracked via `_meta.known_gaps` in source-of-truth artifacts, not by Pydantic.
- **"normalization"** was considered to include query-oriented transformations (sub-item filtering, acronym expansion) — resolved: normalization in the ingestion module means structural normalization only; all retrieval-oriented transformations are retrieval semantics and belong to the retrieval module.
- **"gap"** was used to mean both structural errors and intentionally incomplete domain data — resolved: structural errors are **artifact integrity** failures (fatal); intentionally incomplete data is captured in `_meta.known_gaps` and is a valid document state (non-fatal).
- **"canonical"** was used loosely to refer to both the JSON file and the loaded Python object — resolved: the JSON file is the **source-of-truth artifact**; the loaded, validated Python object is the **canonical domain structure**.
