# IPMP schema extended with `fase`, `ponto_transicao`; `dimensao` corrected and tightened

**Status:** accepted

Scaling past Ação 1 surfaced that `dimensao` (free `str` since Module 1) held an incorrect value
set in CONTEXT.md, never verified against the source PDF. Cross-referencing IPMP Guide §2.2 and
the M5D flowcharts (Figuras 3-5) found the actual 5 dimensions — Estratégica, Econômica,
Comercial, Financeira, Gerencial, not the previously documented Estratégica/Técnica/Financeira/
Ambiental e Social/Jurídica e Regulatória — plus a second, orthogonal axis the source material
structures every Ação by: 3 Fases (Inicial/Intermediária/Final), with a small set of Ações (16,
37, 38, 45, 46) marked "PONTOS DE TRANSIÇÃO" at each Fase boundary.

## Decision

`AcaoIPMP` (`src/ingestion/ipmp.py`) gains `dimensao: Literal[...]` (was `str`),
`fase: Literal["Inicial", "Intermediária", "Final"]`, and `ponto_transicao: bool`.
`data/ipmp/acao_01.json` and `acao_02.json` backfilled (`fase: "Inicial"`,
`ponto_transicao: false` for both — Ações 1-4 sit before the first transition point).

## Why now, and why this doesn't reopen ADR-0030's deferral

ADR-0030 defers *aggregation/reporting* on Dimensão — that scope decision stands unchanged. This
is different: it's data capture, not reporting logic, and the source PDF pages were open in front
of us during this session specifically to resolve the dimension question. Deferring the field
addition would mean re-opening the same pages later for the same information — cheap now,
needlessly repeated later. `fase`/`dimensao` also feed a concrete near-term use in ADR-0056: they
inform vocabulary register when a synthesis session drafts Query Terms for a new Ação
(Estratégica-flavored language differs from Gerencial-flavored language).

## Consequences

- `dimensao` becoming a strict `Literal` means a future manually-transcribed `acao_NN.json` with a
  typo'd or unrecognized dimension value now fails Pydantic validation — non-fatal, logged and
  skipped per ADR-0010's tolerant loading — instead of silently loading as an unchecked string.
- No consumer of `fase`/`ponto_transicao` exists yet beyond CONTEXT.md documentation and
  `04_retrieval-profile-synthesis.md`'s register guidance. ADR-0030's deferral of dimensional
  rollups/reporting is unaffected — this ADR captures data, not aggregation logic.
- CONTEXT.md gained: Fase, Ponto de Transição; Dimensão's value list corrected, with the prior
  incorrect list called out in `_Avoid_` so it isn't silently reintroduced later.

## Amendment (2026-10-15): two phase schemes, and the transition points marked

- **The five transition points were not marked.** `ponto_transicao` was false in every file, including 16, 37, 38, 45 and 46. The schema validated and nothing read the field, so nothing failed. The five were checked against the rendered flowchart pages (Figuras 3-5) and set to true (commit 30bd386). `tests/test_ipmp_structure.py` now pins them.
- **The Guide has two phase schemes, and this ADR's opening paragraph conflated them.**
  - The flowcharts draw Inicial (Ações 1-16), Intermediária (17-38) and Final (39-46). Each phase ends with "Obtenha aprovações necessárias para a proposta Inicial/Intermediária/completa de Investimento" and its transition points.
  - Chapter 4 groups the Ações as estudo das alternativas (1-20), aprimoramento da alternativa escolhida (21-37) and consulta pública, revisões e atualizações (38-46).
  - The `fase` field follows chapter 4's boundaries but labels the first block "Inicial". "Intermediária" and "Final" stay in the Literal, used by no file.
- **The label is not renamed here.** `fase` enters every gate prompt ("Dimensão X, fase Y."). Renaming "Inicial" changes the 20 gate prompts of Ações 1-20 and would need a measurement. That is the user's decision.
- **The fields now have a consumer.** The maturity indicator (ADR-0075) groups the Ações by `fase` and over the transition points.

## Amendment (2026-10-16): the first block renamed

- **The user's decision** (message Z): the stored label of Ações 1-20 is now "Estudo das alternativas", the Guide's own name for that block (4.2, "Fase de estudo das alternativas (Ações 1 a 20)"). It matches the other two labels, which already drop the "Fase de" prefix.
- **The Literal holds the three chapter-4 names only.** "Inicial", "Intermediária" and "Final" are the flowchart phases (Figuras 3-5), with other boundaries, and no file uses them. A file carrying one now fails validation, which `tests/test_ipmp_structure.py` catches (all 46 must load).
- **What it changes.** The identity line of the gate prompt ("Dimensão X, fase Y.") of the 74 scored products of Ações 1-20; nothing else in those prompts. The gate digest goes from `6919edcc672b8027` to `0f7c14bd2bdada1d`, and the gate-ledger keys of those prompts change with it. The scorer prompt does not carry `fase`. The maturity indicator shows the new label.
- **Not measured.** Its effect on constancy has not been measured. A borderline chunk can flip on any byte of its prompt, so a cycle of full processes is the check, as for any prompt-wide change.
