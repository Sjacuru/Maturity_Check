# Regex retrieval (Step D) removed from the cascade

**Status:** accepted — supersedes Step D of ADR-0015

Corpus-wide regex retrieval, introduced in ADR-0015 as Step D (additive, ungated,
`cascade_step="regex"`), is removed from `retrieve_for_acao()` and from `_retrieve_and_select()`
in the assessment service.

## Why

Six empirical cold-start runs on Ação 1 / process 040_101607_2024 revealed four converging problems:

**1. Evidence cap displacement.** Regex hits are unattributed to any expected product and admitted
without passing the relevance gate. Added after the gated evidence set, they push the combined
character count above the `_MAX_EVIDENCE_CHARS` ceiling, causing `_cap_evidence()` to drop the
last gated chunk in sort order. In every observed run this silently dropped pg=211 (1c strategic
goals, 1,711 chars — a gate-approved vector chunk containing the contract's "4.3 Metas" section)
to accommodate two boilerplate glossary pages that matched `Lei 8.987/95` in a definitions table.

**2. Boilerplate dominance.** A content audit of the 27 unique regex hits (after 0.92-threshold
dedup) for Ação 1 classified 63% as boilerplate/neutral (financial definitions, governing-law
glossaries, preamble clauses) and only 33% as containing IPMP-adjacent vocabulary. Of the two hits
that reached the scorer in every run (page-order admission), both were pure glossary pages with zero
IPMP evidence value. The one substantive page the audit identified (pg=639, "12 FLUXO DE CAIXA LIVRE
R$ Mil") was consistently cut by the page-order admission cap before reaching the scorer.

**3. Structural attribution impossibility.** Regex fires on law-citation patterns regardless of
which expected product is being evaluated. There is no principled mechanism to attribute a regex
hit to a specific 1a/1b/1c/1d product. Without product attribution the scorer cannot interpret
regex evidence against the per-product IPMP rubric — it is structurally noise regardless of content.

**4. Destructive scaling across 46 Ações.** The foundational PPP laws (Lei 8.987/95, Lei 11.079/04,
LC 105/2009) appear on hundreds of pages of procurement documents for structural legal reasons
(preambles, definitions, compliance clauses, financial covenants). Every Ação whose `law_references`
includes these laws would generate the same ~38-hit pool per assessment. With 46 Ações, regex would
produce ~1,750 ungated unattributed hits per full-suite run, all structurally equivalent to noise.
The argument "any page eventually fits some Ação" was empirically validated — it means regex is
not selective retrieval but full-document exposure.

## What replaces it

The legitimate retrieval gaps regex was meant to cover are handled by the profiled BM25+vector path:

- **Law-specific phrase terms** in `query_terms` can target specific law numbers where they
  genuinely signal IPMP evidence (e.g., "Lei Orgânica do Município" for 1d alignment). These go
  through the relevance gate and receive product attribution.
- **Vector retrieval** with `evidence_intent` + `retrieval_signal_concepts` semantically reaches
  law-citation-adjacent pages when the surrounding reasoning context makes them relevant.
- **Retrieval profile development** (Stage B observation) is the correct mechanism for recovering
  pages the current profile misses — not an ungated bypass.

The `rio_manual` `law_references` data is retained for concept attribution (checking whether an
accepted chunk cites the expected legal grounding) and for informing future `query_terms` entries.
`src/retrieval/query/regex_search.py` is preserved as a utility module.

## Consequences

- `retrieve_for_acao()` steps: A/B (document-focused) → C (hybrid BM25+vector). No Step D.
- `_retrieve_and_select()` in service.py: returns `selection.accepted` directly; no regex assembly.
- pg=211 (1c strategic goals, `cascade_step="vector"`) is now consistently included in every
  evidence set, no longer displaced by the character cap.
- Evidence set: 18,494 chars (10 gated chunks) — well within `_MAX_EVIDENCE_CHARS=21,000`.
  `_cap_evidence()` no longer fires on normal runs.
- `uncertainty_flag` from Groq no longer fluctuates due to boilerplate regex content reaching the
  scorer — its non-determinism is now confined to genuinely borderline evidence assessments.
- 3 cascade integration tests in `test_regex_retrieval.py` replaced by one test asserting
  `cascade_step="regex"` never appears in `retrieve_for_acao()` results.
- `test_regex_hits_are_capped_at_max_regex_hits` in `test_assessment_service.py` removed.
- `_MAX_REGEX_HITS` constant removed from service.py.
