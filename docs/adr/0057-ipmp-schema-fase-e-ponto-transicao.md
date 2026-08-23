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
