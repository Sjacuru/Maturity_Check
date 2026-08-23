# PPP Maturity Check System — Domain Context

A system that evaluates Brazilian public procurement (PPP) case documents against the IPMP framework, producing a 0/1/3 maturity score for each of 46 actions across 5 dimensions, validated by a human auditor.

---

## Language

### Evaluation Domain

**Ação**: One of 46 numbered evaluation units in the IPMP framework, each representing a planning quality criterion to be assessed against case documents.
_Avoid_: step, item, criterion, check, action (use the Portuguese term)

**Dimensão**: One of 5 analytical groupings of Ações in the M5D (Modelo de Cinco Dimensões) framework IPMP adapts from the British Five Case Model: Estratégica, Econômica, Comercial, Financeira, Gerencial. Source: IPMP Guide §2.2. Orthogonal to **Fase** — every Ação belongs to exactly one Dimensão and exactly one Fase.
_Avoid_: category, dimension, area, group; the incorrect list (Técnica, Ambiental e Social, Jurídica e Regulatória) that appeared here before 2026-08-21 — never verified against the source PDF

**Fase**: One of 3 sequential stages of the investment-structuring lifecycle that IPMP's 46 Ações are organized into: Fase Inicial (Ações 1-20, estudo das alternativas), Fase Intermediária (Ações 21-37, aprimoramento da alternativa escolhida), Fase Final (Ações 38-46, consulta pública, revisões e atualizações). Source: IPMP Guide §4, Figuras 3-5.
_Avoid_: stage, step, phase (use the Portuguese term), sprint

**Ponto de Transição**: A structural marker the IPMP Guide's own flowcharts (Figuras 3-5) place on 5 specific Ações (16, 37, 38, 45, 46) that sit at the boundary between two Fases — not a sixth Dimensão. Marks an approval/gating checkpoint, not a content theme.
_Avoid_: transition dimension, sixth dimension, gate (unqualified)

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

**Retrieval Profile**: A derived knowledge artifact (`data/retrieval_profiles/acao_NN.json`) containing the evidence ontology for one Ação — Evidence Intent, Retrieval Signal Concepts, Query Terms, Evidence Logic Patterns, and profile maturity level. Synthesised from IPMP, Rio Manual, acronym tables, and real-document observation; distinct from all three because it evolves and is not a canonical normative source.
_Avoid_: query artifact, query file, search config, retrieval config

**Profile Maturity**: The confidence level of a Retrieval Profile, reflecting how extensively it has been grounded in real PPP case documents. Three levels: `seed` (canonical sources only, not yet trusted for production), `observed` (validated against at least one real case document), `mature` (validated across multiple cases and sectors). Stored as `profile_maturity` in the profile JSON.
_Avoid_: profile version, profile quality, profile completeness

**Term Status**: The current confidence level of an individual Query Term within a Retrieval Profile, based on accumulated empirical evidence from retrieval testing. Four values: `active` (in use, untested), `experimental` (tentatively added, pending validation), `validated` (confirmed to contribute useful recall), `deprecated` (empirically shown to be noise; retained for auditability). Distinct from **Provenance**, which explains origin rather than confidence.
_Avoid_: term quality, term confidence, term flag

**Provenance**: The origin classification of an individual Query Term, distinct from **Term Status** (confidence, not origin). Three values: `canonical` (derived directly from IPMP or Rio Manual source text), `real_world` (observed in an actual PPP case document during a Stage B population session), `synthetic` (derived from general domain knowledge of Brazilian PPP contracting practice, applied offline during profile generation, grounded in neither a specific case document nor the IPMP text itself).
_Avoid_: source, origin, source type

### Module Concepts

**Ingestion module**: The Python package (`src/ingestion/`) responsible for loading, validating, and exposing canonical domain structures from source-of-truth artifacts. Owns no retrieval semantics.
_Avoid_: parser, loader, ETL layer, data access layer

**Extraction module**: The Python package (`src/extraction/`) responsible for reading a Document Artifact (PDF) and returning a list of Chunks. Pure transformation layer — no knowledge of Cases, SQLite, BM25, or business-domain identifiers. Public interface: `extract_document(path: Path) -> list[Chunk]`.
_Avoid_: PDF parser, chunker, pipeline, ingestion (that term is taken)

**Retrieval module**: The Python package (`src/retrieval/`) responsible for indexing Document Artifact chunks into SQLite and executing the retrieval cascade to produce evidence for a given Ação. Sub-packages: `indexing/`, `query/`, `schema/`, `interfaces/`. Public write-path entry: `index(process_number: str, chunks: list[Chunk])`. Public read-path entry: retrieval cascade execution returning `list[RetrievedChunk]`.
_Avoid_: search module, BM25 module, query layer

**RetrievedChunk**: The domain-level retrieval result returned by the retrieval cascade. Carries: full `Chunk` provenance (`process_number`, `filename`, `page_number`, `chunk_index`, `char_offset`, `page_total`, `ocr_used`, `source_type`), `text`, `cascade_step` (`"filename_match"` | `"variant_match"` | `"bm25"` | `"regex"` | `"vector"` — `"regex"` is a preserved-but-unused value since ADR-0052), `expected_product_ids` (list — the Expected Product ids this chunk was retrieved for; empty on document-focused, regex, and vector paths; merged across products by cross-product dedup), `bm25_score` (null on document-focused, regex, and vector paths), `rank` (null on document-focused, regex, and vector paths), `retrieval_mode` (`"lexical"` | `"vector_fallback"`, default `"lexical"` — the field and its values predate ADR-0049 and are not fully accurate to it: vector is no longer only used "as a fallback," it's fused with BM25 unconditionally, but the field itself was not renamed), `matched_concepts` (list — Retrieval Signal Concept keys whose Query Terms matched this chunk's text, populated deterministically post-gate; empty on ungated paths). Does not expose SQLite row IDs, FTS5 docids, or other storage internals.
_Avoid_: search result, hit, match, ranked chunk

**Retrieval semantics**: Any logic that interprets canonical domain structures for search purposes — BM25 query construction, acronym expansion, cascade execution, chunk ranking, vector similarity.
_Avoid_: search logic, query logic, downstream logic

**Evidence Ontology**: The four-layer framework used to model what an Expected Product is asking for and how to retrieve it. Layer A (Evidence Intent) — what the requirement verifies; Layer B (Retrieval Signal Concept) — what concepts indicate the evidence; Layer C (Query Terms) — how those concepts appear in real documents; Layer D (Evidence Logic Pattern) — what relational structure constitutes strong evidence. Layers A, B, and D are never FTS5 inputs; only Layer C terms enter the retrieval pipeline.
_Avoid_: evidence model, retrieval model, evidence framework

**Evidence Intent**: A Layer A artifact in the Evidence Ontology — a one-sentence description of what an Expected Product is verifying, expressed as an evaluation objective. Never a query term. Example: "Justificativa do projeto — motivos pelos quais o projeto é necessário."
_Avoid_: evidence description, evaluation goal, retrieval objective

**Retrieval Signal Concept**: A Layer B artifact in the Evidence Ontology — a conceptual bridge between an Evidence Intent and the observable language in real documents. Names a concept that, if present in a document, indicates the evidence is likely there. Never a query term. Example: "diagnóstico do estado atual do problema."
_Avoid_: retrieval concept, search concept, evidence indicator

**Query Term**: A Layer C artifact in the Evidence Ontology — the actual FTS5 input derived from a Retrieval Signal Concept. Carries: `encoding` (phrase or near), query text or tokens, `type` (A/B/C), **Provenance**, **Term Status**, optional `concept_ref`, and optional `sector_hint` (set only on `synthetic` Provenance terms, drawn from the **Sector Taxonomy**). All query-facing string values are in Portuguese. One Retrieval Signal Concept may generate multiple Query Terms.
_Avoid_: anchor, search term, BM25 term, retrieval term

**Sector Taxonomy**: The canonical reference list (`data/sector_taxonomy.json`) of Brazilian PPP/concession sector labels that the synthetic-generation skill draws from to set `sector_hint` on `synthetic` Provenance Query Terms. Extended only by a deliberate edit to the file — never invented ad hoc during a generation run.
_Avoid_: sector list, sector enum, sector vocabulary

**Evidence Logic Pattern**: A Layer D artifact in the Evidence Ontology — a description of the relational or causal structure that constitutes strong evidence for an Expected Product (e.g., Problema → Necessidade → Intervenção → Resultado). Never a query term; used only by future reranking agents and the LLM evaluation layer to assess evidence strength.
_Avoid_: evidence pattern, scoring logic, evaluation rule

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

**Retrieval cascade**: The ordered retrieval strategy for a given Ação. Steps A–B are document-focused and deterministic: (A) exact document name match, (B) variant name match. Step C is hybrid: BM25 and dense vector search run unconditionally, once per letter-suffixed Expected Product, and are fused via per-product Reciprocal Rank Fusion (RRF, k=60) — vector is co-equal with BM25, not a fallback (ADR-0049, superseding the earlier "vector only on zero lexical results" model). `rio_hints` stays a separate BM25-only lane, structurally lower-priority than a product-attributed RRF match. Regex additive search (the former Step D) was removed from the cascade entirely (ADR-0052); `search_regex()` is preserved as a utility, unused in the live cascade. All steps belong entirely to the retrieval module.
_Avoid_: pipeline, search flow, fallback chain, vector fallback (superseded terminology — see ADR-0049)

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

- An **Ação** belongs to exactly one **Dimensão** and exactly one **Fase**
- A small subset of Ações also carry the **Ponto de Transição** marker, at the boundary between two **Fases**
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
- A **Retrieval Profile** synthesises data from one **IPMP** artifact, one **Rio Manual** artifact, the acronym table, and real-document observation for the same **Ação**
- A **Retrieval Profile** contains one **Evidence Ontology** entry per letter-suffixed **Expected Product**
- Each **Evidence Ontology** entry contains one **Evidence Intent** (Layer A), one or more **Retrieval Signal Concepts** (Layer B), one or more **Query Terms** (Layer C), and zero or more **Evidence Logic Patterns** (Layer D)
- The ingestion module exposes **Retrieval Profiles** via `get_retrieval_profile_store()` alongside `get_ipmp_store()` and `get_rio_manual_store()`
- **Profile Maturity** advances from `seed` to `observed` only after at least one real PPP case document has been used in a population session (Stage B)
- A Query Term with `synthetic` **Provenance** always starts at `experimental` **Term Status** — it is a hypothesis until promoted, never assembled into the active BM25 query by default

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
- **"anchor"** was used to mean vocabulary source, phrase encoding mechanism, and FTS5 query term simultaneously — retired: the term is now disambiguated into **Evidence Intent** (Layer A — what to look for), **Retrieval Signal Concept** (Layer B — what concept indicates the evidence), and **Query Term** (Layer C — the actual FTS5 input). "Anchor" should not be used in this system.
