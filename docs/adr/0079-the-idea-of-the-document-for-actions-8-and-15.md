# The idea of the document, for Ações 8 and 15

**Status:** accepted (2026-10-20)

Several Ações ask for a named document (an options study, a risk plan, a consolidated report) that a case may never contain under that name. On 2026-10-19 the user asked to search for what the document must say instead ("identificar o que se pede que esteja no documento, a alma do documento"), and to score the presence of that idea 0 or 1 when the document itself is absent. Pilot cycle 15 measured this on seven products. On 2026-10-20 the user decided to adopt it for Ações 8 and 15 only ("adotar só a 15 e 8").

## Decision

- **Three products change: 8a, 15a and 15c.** Each takes, verbatim, its candidate from the C15 pilot (`scripts/diagnostics/candidates_ideia_piloto.py`):
  - an `evidence_intent` rewritten as the idea, meaning the content wherever it is written, never the document's name;
  - new active canonical terms, each with its source in the profile's changelog: the IPMP, Lei 14.133/2021 art. 18 §1, Lei 8.987/1995 art. 5, Lei 11.079/2004 art. 10, or general vocabulary. None was taken from the case (ADR-0073);
  - `genre_filter_before_lane_cut: true`.
- **What the flag does.** `ExpectedProductProfile.genre_filter_before_lane_cut` is a new field, default false. Without it, each lane (BM25, vector) takes its first 20 hits before the genre filter (ADR-0074). With it, each lane in `retrieval/query/hybrid.py` goes down until it has 20 chunks that are not instrument text and are not empty after noise stripping; RRF then fuses those two lists. Everything after that is unchanged: near-duplicates, the cut of 16, the gate, expansion. Without the flag, instrument text fills the 20 places of these products, and the pool keeps 0 to 4 chunks. With it, 13 to 15.
- **Not a general rule.** This is cycle 10's F20 restricted to products that read an idea outside instruments. As a global rule F20 failed (constancy 34/46, points doubled on economic-study confusions). The flag is ignored on genre-exempt products, which read instrument text by design. The standing rule holds: instrument text never returns to the gate as a general rule.
- **The lanes read the genres with narrative sections released** (ADR-0077), as the harness did. `NARRATIVE_SECTIONS_ENABLED` in evaluation does not reach this switch.

## Evidence

- **C15 phase 2** (10 full processes, 2026-10-20, criterion written first, `scratchpad/acc/criterio_ciclo15.txt`):
  - Ação 15 scored 1 in 10/10, on target pages in every process: the ETP `_2` p.156 and p.161, and the procurement justification `_1` p.3. The pilot's baseline was `sem evidência` in 10/10.
  - Ação 8 scored 1 in 8/10 and `sem evidência` in 2/10, on the ETP `_2` p.157/158 (concession against direct provision).
  - No 3 in 40 evaluations.
  - The checklist question `_2` p.163 was accepted for 15c in 10/10 without moving points.
- **The pilot as a whole was not adopted.** Ações 6 and 42 flipped because their point rested on one borderline page. C16 widened their idea and still failed its rule D5 (more than one support in at least 3 of 5 processes): Ação 6 kept resting on `_2` p.157 alone.
- **Production equals what was measured.** Checked without a model on a copy of the database, with a gate that rejects everything: the production pools of 8a, 15a and 15c equal the pools the harness built in C15 and C16, and every other product of Ações 6, 8, 15 and 42 keeps its pool.

## Consequences

- **The gate prompts of 8a, 15a and 15c change**, so the ledger keys for them change too. The scorer prompt is unchanged.
- **Ação 8 sits at 8 of 10 in C15**, below the 9-of-10 line. The user adopted it knowing this, and the ADR-0068 signal fires on each single-accept 1. Constancy for this exact configuration (8 and 15 without the 6 and 42 candidates) has not been measured in full processes; a confirmation cycle would.
- **Adding the flag to another product needs its own measurement** in full processes, with a criterion written first. The first candidates are 14a, 27a/27b and 41a, which the user asked for on 2026-10-20.
