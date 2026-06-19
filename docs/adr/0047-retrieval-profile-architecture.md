# ADR-0047 — Retrieval Profile Architecture

BM25 query construction from raw `produto.texto` produces governance framing language rather than evidence-bearing vocabulary: IPMP describes what evidence should contain; case documents use different language to provide it. The system now models each Expected Product as a four-layer evidence ontology — Evidence Intent, Retrieval Signal Concept, Query Terms, Evidence Logic Pattern — and stores the resulting Layer C query terms in a new derived artifact category `data/retrieval_profiles/`. This separates normative meaning (IPMP, immutable canonical source) from operational retrieval strategy (retrieval profile, evolving derived artifact).

See DAN-0002 for the historical competing positions this decision supersedes.

---

## Evidence Ontology

Four layers apply to each Expected Product:

| Layer | Question answered | FTS5 input? |
|---|---|---|
| **A — Evidence Intent** | What kind of evidence is the Expected Product verifying? | No — conceptual |
| **B — Retrieval Signal Concept** | What concepts indicate this evidence in real documents? | No — conceptual bridge |
| **C — Query Terms** | How do these concepts actually appear in case documents? | Yes — FTS5 MATCH inputs |
| **D — Evidence Logic Pattern** | What relational structure constitutes strong evidence? | No — evaluation and reranking only |

Layers A and B are conceptual. They are never FTS5 inputs. They exist to make the derivation of Layer C terms traceable and grounded. Layer D patterns — intervention logic chains such as Problema → Necessidade → Intervenção → Resultado — cannot be evaluated by lexical retrieval; they govern how future reranking and LLM evaluation layers assess evidence strength.

## Evidence Type Taxonomy

Each Layer C query term is classified by the nature of the evidence it represents:

| Type | Description | Default FTS5 encoding |
|---|---|---|
| **A** | Named entities — specific plan names, document titles (PNH, PLANSAB, Plano Nacional de Hidrovias) | Phrase |
| **B** | Domain concepts — sectoral terms (saneamento básico, logística portuária, mobilidade urbana) | Case-by-case |
| **C** | Evidence and process patterns — relational language (diagnóstico setorial, análise de alternativas, priorização de investimentos) | NEAR() |
| **D** | Intervention logic chains | Evaluation and reranking only — not a query term |

Types A–D describe *what kind of evidence* a term represents, not its precision or quality. Type C using NEAR() is not a degraded version of Type A using phrase; they model different kinds of evidence.

## Core Architectural Principle

**Evidence is modeled as relationships, not merely vocabulary.**

Type C evidence — planning processes, diagnostic reasoning, strategic alignment — is relationship-oriented rather than phrase-oriented. A municipality can satisfy an Expected Product without ever naming a national plan; it cannot satisfy it without producing diagnostic, analytical, or planning evidence in some form. NEAR() encoding, mandatory real-document grounding, Evidence Logic Patterns, and the retrieval profile artifact all follow from this principle.

## Retrieval Responsibility Boundary

Retrieval is responsible for candidate generation and recall. It is not responsible for evidence sufficiency, reasoning quality, strategic alignment assessment, or final scoring. Those responsibilities belong to Evidence Logic Patterns (Layer D), future reranking agents, and the LLM evaluation stage. A retrieved irrelevant chunk is recoverable downstream; a chunk never retrieved is permanently lost to the scoring pipeline.

## Retrieval Profile Artifact

`data/retrieval_profiles/` is a derived knowledge artifact category, distinct from:

- `data/ipmp/` — canonical normative source; defines what the requirement means
- `data/rio_manual/` — supporting retrieval aid; connects requirements to document manifestations in Rio PPP cases
- `data/acronyms/` — canonical support source; acronym expansion

Retrieval profiles synthesise all three sources plus real-document observation. IPMP, Rio Manual, and Acronyms are immutable; retrieval profiles evolve as corpus knowledge accumulates. Conflating them would obscure the origin of query vocabulary and which artifact type should change when retrieval quality is updated.

## Profile Population Methodology

Each Expected Product's retrieval profile is populated in three stages, in sequence:

**Stage A — IPMP Concept Extraction:** Derive Layer A (Evidence Intent) and Layer B (Retrieval Signal Concepts) from IPMP text. Conceptual only — no query terms generated at this stage.

**Stage B — Real Document Observation (required for a trusted profile):** Read actual PPP case documents. Extract observed expressions and candidate evidence patterns. These become `provenance: "real_world"` Layer C terms. A profile without Stage B is a Seed profile — not trusted for production scoring.

**Stage C — Canonical Cross-Reference:** Cross-reference Rio Manual hints, legal phrases, and acronym expansions. These become `provenance: "canonical"` Layer C terms. Rio Manual is a supporting retrieval aid, not a co-equal normative source — IPMP defines the requirement; Rio Manual helps discover how it manifests in documents.

Each population session is structured: the domain expert reads relevant document sections and brings observations; the ontology framework is applied to classify and refine them.

## Profile Maturity

| Level | Meaning |
|---|---|
| `seed` | Canonical sources only (Stages A and C). Stage B not yet complete. Suitable for development; not trusted for production scoring. |
| `observed` | Stage B complete — validated against at least one real PPP case document. Trusted for production retrieval. |
| `mature` | Validated against multiple cases and sectors. Evidence patterns reflect cross-sectoral generalisation. |

Stored as a top-level `profile_maturity` field in the retrieval profile JSON. A profile cannot advance to `observed` without at least one real-document population session.

## Profile Evolution — Additive Model

Profiles grow over time. When a profile advances from one maturity level to the next, existing query terms are retained unless empirical validation demonstrates they generate only noise. Terms are never removed by assumption — only by evidence from empirical A/B testing.

Rationale: removing terms before empirical testing risks discarding vocabulary that contributes useful recall. If retrieval quality changes after a profile update, the specific additions can be identified as the cause. A complete regeneration at each maturity advance would make degradation untraceable.

## Term Status

Each query term carries a `status` field recording current confidence from accumulated empirical evidence:

| Status | Meaning |
|---|---|
| `active` | Default; in use, not yet empirically tested |
| `experimental` | Added tentatively during a population session; validation pending |
| `validated` | Confirmed by empirical testing to contribute useful recall |
| `deprecated` | Empirically shown to be noise; retained in profile for auditability |

`provenance` explains where a term came from. `status` explains current confidence. Both are required per term.

## Deferred

**Q6 — Chunk Context Expansion:** Deferred pending retrieval validation. Revisit after Recall@20 results show whether chunk boundaries are the binding constraint on evidence recovery.

**Q7 — Reranking and Agent-Based Evidence Selection:** Deferred pending empirical validation results and revalidation of ADR-0009 (single LLM call per Ação). ADR-0009 was designed under retrieval quality assumptions that require empirical confirmation before extending the pipeline with reranking stages.
