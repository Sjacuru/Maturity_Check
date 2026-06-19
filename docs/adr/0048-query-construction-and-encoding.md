# ADR-0048 — Query Construction and Encoding

The query construction layer destroyed multi-word phrases by tokenising all source text into single-word OR-clauses before FTS5 received the query string; multi-word terms in IPMP text and acronym expansions lost their phrase structure in Python before the database was involved. This is corrected by a phrase-preserving construction pattern, extended to support NEAR() proximity queries for Type C evidence terms. Together these changes constitute Layer 1 of the retrieval improvement plan and are a prerequisite for any vocabulary curation work.

---

## Phrase Preservation

Two query construction mechanisms existed in production with opposite phrase behaviour:

**`rio_hints` path (`cascade.py`):** wraps each Rio Manual hint whole in double quotes and joins with OR. FTS5 receives `"multi word term"` and treats it as an exact-sequence phrase query. Phrase structure survives end-to-end. Validated by Phase A: 3 of 4 correctly retrieved pages came via this path.

**`build_bm25_query()` path (`query_builder.py`):** splits all input text on whitespace, filters words by minimum length, dedupes into a set, and OR-joins single lowercased tokens. A phrase like "Plano Nacional de Hidrovias" becomes `"plano" OR "nacional" OR "hidrovias"` — three independent single-token clauses with no sequence constraint. The destruction happens in Python before FTS5 is involved.

Layer 1 corrects this by applying the phrase-preserving join pattern uniformly to the 1a–1d query construction path. The pattern is already proven; it is extended from `rio_hints` to all Expected Product query construction.

## Acronym Expansions as Atomic Phrase Terms

When an acronym (e.g., PNH) appears in `produto.texto`, its expansion is appended before query construction. Under the old mechanism, "Plano Nacional de Hidrovias" was immediately tokenised into three isolated words. Under Layer 1, each expansion is passed intact to FTS5 as `"Plano Nacional de Hidrovias"` — a 4-token phrase query matching only chunks containing that exact sequence.

This provides an immediate, measurable behavioural effect for Expected Product 1d, which contains PNL, PDE, Plansab, PNLP, and PNH in its `produto.texto` — five Type A named-entity terms upgraded from isolated word-clauses to precise phrase queries without any vocabulary curation.

## Encoding Strategy by Evidence Type

| Evidence Type | Default FTS5 encoding | Rationale |
|---|---|---|
| **A** — Named entities | Phrase (`"Plano Nacional de Hidrovias"`) | Low variability; exact token sequence is the identity of the entity |
| **B** — Domain concepts | Case-by-case | Some concepts are phrase-stable; others appear in paraphrase forms |
| **C** — Evidence and process patterns | NEAR() (`NEAR("diagnóstico" "problema", 5)`) | Relationship-oriented; exact sequence is incidental to the evidence |
| **D** — Intervention logic | Not a query term | FTS5 cannot detect cross-paragraph causal chains |

Phrase and NEAR() are not different quality levels — they model different kinds of evidence. Phrase encoding models identity (this exact plan name). NEAR() encoding models relationship (these two concepts co-occur meaningfully).

## NEAR() as Primary Encoding for Type C

NEAR() is adopted as the **primary** encoding for Type C evidence terms, not as a fallback when phrase matching fails. Type C terms model relational evidence — the presence of a connection between two concepts regardless of syntactic form. "diagnóstico aprofundado do problema" and "o problema foi diagnosticado" satisfy the same evidence pattern; strict phrase matching would require a separate variant for each form.

Operational argument: maintaining exhaustive phrase-variant sets for Type C across 46 Ações is unsustainable. NEAR() encodes the relationship faithfully without enumerating every paraphrase, which is the scaling argument for using it from the start rather than adding it later as a patch.

## Query Term Schema

Each query term in `data/retrieval_profiles/acao_NN.json`:

```json
// phrase-encoded term (Type A or stable Type B)
{
  "encoding": "phrase",
  "text": "Plano Nacional de Hidrovias",
  "type": "A",
  "provenance": "canonical",
  "status": "active",
  "concept_ref": "alinhamento_planos_nacionais"
}

// NEAR-encoded term (Type C)
{
  "encoding": "near",
  "tokens": ["diagnóstico", "problema"],
  "distance": 5,
  "type": "C",
  "provenance": "canonical",
  "status": "active",
  "concept_ref": "diagnostico_problema"
}
```

All query-facing string values (`text`, `tokens`) are in Portuguese, matching case document language. Structural field names are in English. `concept_ref` is optional; it keys into the `retrieval_signal_concepts` map in the same profile for traceability.

## Considered Options

**Phrase-only for all terms:** rejected because Type C evidence is relationship-oriented, not phrase-oriented. Phrase matching for "diagnóstico setorial" would miss "realizou um diagnóstico do setor" even though both express the same evidence pattern.

**Single-word OR tokenisation retained alongside curation:** evaluated empirically, not assumed to be complementary. The A/B validation plan (ADR-0047) compares Strategy A (curated terms only) against Strategy B (curated terms plus algorithmic extraction) across four metrics: Recall@20, best rank position, candidate pool composition, and unique evidence pages recovered. The decision to retire algorithmic extraction will be data-driven.
