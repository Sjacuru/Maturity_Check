# Narrative sections of instrument documents reach the gate

**Status:** accepted (2026-10-19)

The genre filter (ADR-0074) removes every chunk of an instrument document (edital, termo de referência, contract and their normative annexes) before the gate, for every product whose criterion is not the instrument itself. Those documents usually open with sections that describe instead of prescribe: the introduction, the context and history of the project, its justification. On 2026-10-19 the user asked to let those through ("capturar dentre esses casos as páginas/chunks de contratos, editais e correlacionados aqueles vinculados à introdução, histórico, breve análise, conclusão, cronograma"). After test cycle 11 the user decided to keep it without CRONOGRAMA: chunks of an instrument document that lie in a section with a narrative title now read as OUTRO for the filter.

This narrows the standing rule of 2026-10-18 ("never give instrument text back to the gate as a general rule"): what returns is not instrument text in the sense of that rule, but the instrument's own account of the project, found by a document-agnostic convention of titles, never by a page map.

## Decision

- **What is released.** A section whose title is one of INTRODUÇÃO, APRESENTAÇÃO, CONTEXTO, CONTEXTUALIZAÇÃO, HISTÓRICO, ANTECEDENTES, JUSTIFICATIVA, MOTIVAÇÃO, DIAGNÓSTICO, SITUAÇÃO ATUAL, BREVE ANÁLISE, ANÁLISE PRELIMINAR, CONSIDERAÇÕES INICIAIS/FINAIS, CONCLUSÃO. These are general drafting conventions; none was taken from a page of a case (ADR-0073).
- **Section boundaries.** The title opens the section; the next title of the same level or higher closes it ("2." closes "1."; "1.4" does not). A number alone on its line gives its level to the title on the next line. An unnumbered section ends at the next unnumbered title standing alone. An instrument document whose own title is narrative (an annex named after one of the titles) is released whole. A chunk is released when half or more of its noise-stripped text lies inside a narrative section. Table-of-contents lines are not titles; the "considerandos" of a minuta are not a section.
- **CRONOGRAMA is out.** A schedule annex says what will happen, not that it happened, the class that misled Ação 45 in cycle 6. In cycle 11 it brought no legitimate accept and the only confusion (below). Removing it was decided after the result, and it is recorded as such.
- **Where it lives.** `src/retrieval/genre/narrative.py` computes the sections; the document index stores each chunk's section title in `chunk_genre.narrative_section`; `get_chunk_genres` reads a released chunk as OUTRO. It applies wherever the filter applies: the pool, neighbour expansion and the focal route. Exempt products are unchanged.
- **Rules version.** `GENRE_RULES_VERSION` = `2026-10-19.1`, so every index is rebuilt on its next read. A `chunk_genre` table of the older shape (no `narrative_section` column) is dropped with its state and rebuilt: it holds derived data only.
- **Switch.** `evidence_selection.NARRATIVE_SECTIONS_ENABLED`; `reproducibility.py --no-narrative-sections` turns it off. The cycle-11 variant stays in the harness as the record (`--narrative-sections`, `scripts/diagnostics/narrative_sections.py`), which on top of production only adds the CRONOGRAMA sections back.

## Test cycle 11 (2026-10-19)

One invocation of `reproducibility.py --runs 10 --narrative-sections` against cycle 8, 10:03 to 12:32, under a criterion written before the first model call (`scratchpad/acc/criterio_ciclo11.txt`). Process 9 lost Ação 23 to three gate timeouts; it was not refilled.

- **Released in SMG-040:** 33 chunks in 12 documents (the introduction of each TR and of both editais, the introduction of the B3 manual, and the bidding-schedule annex). No instrument here has a "conclusão" or "breve análise". 14 of the 33 reached some examined pool; the TR justifications did not, because they nearly repeat the procurement justification `_1` p.3 and the near-duplicate prefilter removes them.
- **A. Constancy:** 40/46 with the same points in 9+ of 10, as in cycle 8 (below 9: 2 3 10 23 35 37). Passed.
- **B. Gain (3 of 6 pre-listed targets in 5+ of 10):** 1 of 6. Failed. The TR's statement of the concession's objectives (`_1` p.140) was accepted for 1c in 10/10. In cycle 8 the 1c bit held in 9 of 10 processes on `_1` p.2 and p.3, which fell together once; it now holds in 10 of 10 with an independent page, without changing points (Ação 1 scored 1 throughout). The four 4a targets became coins (2 of 10 or less): the gate reads them as objectives, not as benefits tied to needs.
- **C. Harm:** no confusion accepted in 5+ of 10 (C1) and no modal change (C2). All 17 confusions listed before the run were rejected in 10/10, the Ação 45 future-act rules among them. Four new coins (C3): the three 4a targets and the schedule annex `_2` p.974, accepted once for 31.1f by a reasoning that judged 31.1c, which gave Ação 31 one point in process 6.
- **Cost:** about 30 more gate calls per process (+6 %) and 0.6 min; varying pairs 66 to 70.
- **Margin (D):** not met, on Estratégica (7/10) as in cycle 8 (8/10); nota median 0.087 (cycle 8: 0.094).
- **Rule E** said discard. **The user decided to keep S** (2026-10-19): for one process, no relevant information was lost and the gain, though small, is correct; with constancy at about 40/46, any further gain will be small.
- **Without CRONOGRAMA, checked without a model** on the production path with a gate that rejects everything: the released set is cycle 11's minus the three schedule-annex chunks (30 chunks); the examined pools equal cycle 11's except that `_2` p.973/974 leave 20d, 31.1f, 35.2b and 45; 473 pool calls per process.

## Decision rule for evidence-recovery changes

Rule B of cycle 11 asked for a gain the case did not hold. From now on, a change whose purpose is to recover evidence passes on non-inferiority: constancy not worse beyond chance (A), no confusion accepted in 5+ of 10 (C1), no modal change resting on a confusion (C2), and at least one pre-listed target gained and read as legitimate. The cost (calls, coins) is reported.

## Considered options

- **Discard S by rule E:** rejected by the user; S did no measured harm.
- **Keep CRONOGRAMA:** rejected. Its only measured effect was a confusion, and in another process the same title may release a contract's physical-financial schedule annex, an obligation.
- **Release by chunk label instead of section:** rejected. Many chunks of an instrument are labelled OUTRO (cycle 3: the TR's descriptive passages), and letting those through would return the per-chunk filter ADR-0074 chose against.

## Consequences

- The section heuristic was tuned on one corpus. On a second case, an unrecognized title only keeps its section out (harmless); a narrative title opening a long normative section would release it. The second case document is the test.
- Readers of `chunk_genre.genre` still see the document's genre; the effective genre the filter reads is `get_chunk_genres`.
