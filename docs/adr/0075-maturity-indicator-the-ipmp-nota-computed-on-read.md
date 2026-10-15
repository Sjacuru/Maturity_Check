# The maturity indicator: the IPMP nota, computed on read

**Status:** accepted (2026-10-15)

ADR-0030 left aggregation open. On 2026-10-15 the user approved the maturity indicator (message W, item 3). The indicator is the IPMP nota of one case: points divided by three times the Ações counted, between 0 and 1. It is the Guide's "percentual de atendimento" on the project's 0/1/3 scale (CLAUDE.md, Strategic Decision 4: maximum 138). It is reported for the whole case, for each of the five dimensions, for each phase and for the five transition points. It is computed on read from the stored evaluations and reviews and is never stored, so it follows every review as it lands. Nothing in the assessment run changes.

## What the Guide asks for

- **The nota.** It runs from 0 to 1: "notas mais próximas de 1 (100%) são melhores" (3.1; Appendix 6, question 6). The overall nota is the mean over all Ações: "a pontuação geral representa uma média do atendimento de todas as ações" (3.4.4).
- **The dimensions.** The Guide asks for "especial atenção para as notas do iPMP em cada uma das cinco dimensões" (6.2), and its own example is a case with 0.7 overall and 0.3 in the Gerencial dimension.
- **No cut-off between the two limits.** There are no objective cut-offs yet (3.4.3). Notas below 0.2 read as compromised and above 0.8 as satisfactory (3.4.3, 6.2, Appendix 6 question 7). The band between the two gets no reading.
- **Missing evidence.** It stays "não atendida" (4.1).

## Points per Ação

1. **Reviewed:** the auditor's `final_score` (ADR-0023) settles the Ação.
2. **Not reviewed, no evidence found:** 0 points. This is the same rule the acceptance criterion already uses (ADR-0068, 2026-10-10 section).
3. **Not reviewed, with a proposed score:** the persisted `proposed_score`. It is already after the dependency cap (ADR-0070).
4. **Parse failure or no stored evaluation:** not counted. The group is marked incomplete and its nota is over the Ações counted. A parse failure has no score until the auditor assigns one, so it is not a 0.

## The floor

Some unreviewed Ações still carry ADR-0068's optional-review signal. For each of them, the indicator also counts the points the Ação would have if every fragile product fell at once: `min(points, score_floor)`, where a floor of None (`sem evidência`) counts 0. The case gets `nota_floor` beside the nota, and the page names the Ações behind the difference.

No upward claim is made, as in ADR-0068. A rejection that flips to accept is not deterministic from one pass.

## Shape

- **Code.** `src/assessment/maturity.py` holds `compute_maturity()`. The contracts are `AcaoPoints`, `MaturityGroup` and `MaturityIndicator` in `src/assessment/interfaces/contracts.py`.
- **Route.** `GET /api/cases/{process_number}/maturity` returns 404 when the case has no evaluation.
- **Page.** `MaturityIndicator.vue` sits at the top of the case page and is refetched after each submitted review.
- **Phases.** Phases are grouped by the stored `fase` label, in Ação order.
- **Transition points.** The transition points are the five Ações with `ponto_transicao` true (16, 37, 38, 45, 46; the approval gates of the M5D flowcharts, Figuras 3-5). This is the field's first consumer (ADR-0057).
- **Bands.** The Guide's reading (`alert`, `intermediate`, `satisfactory`) is given for the overall nota only. The Guide gives no separate limits per dimension.

## Consequences

- **The page shows the stored evaluation, whatever its age.** On 2026-10-15 the stored evaluation of the real case (`040_101607_2024`) dates from 2026-09-07. That run predates the counted score, the margin and the genre filter. It gives 0.246, while the cycle runs of the current pipeline give 0.07–0.12. The indicator does not re-run anything.
- **Reviews move the nota at once, and are not undone by a re-run.** A forced re-run deletes the reviews with the evaluations (ADR-0026).
- **"Não aplicável" is not supported.** The Guide's example is Ações 45 and 46 in a project that has not reached that stage (4.1). ADR-0023 has no such outcome, so today such an Ação counts as evaluated. Supporting it would change the review contract and the denominator, which is the user's decision.
- **Weights.** The Guide calls the overall nota a plain mean (3.4.4) and, elsewhere, a weighted mean of heterogeneous Ações (6.3.1) without giving weights. Every Ação weighs the same here.

## Considered options

- **Store the indicator with the assessment:** rejected. It would go stale on the first review, and ADR-0030 keeps aggregation out of orchestration.
- **Count a parse failure as 0:** rejected. That would report the system's own failure as the project's "não atendida".
- **Draw a radar chart (the Guide's "polígono"):** deferred. Bars carry the same five numbers without a chart library.
