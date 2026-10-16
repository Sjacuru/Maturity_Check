# "Não aplicável" for Ações 45 and 46

**Status:** accepted (2026-10-16)

The Guide admits "não aplicável" as an absolute exception and names its typical case: Ações 45 and 46, the selection of the winning bidder and the signing of the contract, in a project that has not reached that stage (4.1, p. 50). On 2026-10-16 the user asked for it (message Z: "execute N/A para 45/46"). The auditor may now mark Ação 45 or 46 "não aplicável", with a mandatory motivation, and the Ação leaves the nota's count. Missing evidence is never this: it stays "não atendida" and counts 0.

## What the Guide says (4.1, p. 50)

- "eventual atribuição de “não aplicável” na ação deve ser encarada como exceção absoluta, reservada a circunstâncias rigorosamente justificadas."
- It lists three cases: (a) "a ação diz respeito a uma etapa futura que o empreendimento comprovadamente ainda não alcançou – caso típico das Ações 45 e 46"; (b) an object of very low impact or a one-off scope, with an explicit technical justification; (c) a strategic or confidential project, such as works tied to national security in border areas.
- "o avaliador deve registrar, de forma explícita, a motivação técnica e documental que sustenta a dispensa, prevenindo confusão com situações de inexistência de evidências, as quais permanecem classificadas como “não atendida”."
- The Guide does not spell out the arithmetic. Counting a dispensed Ação as 0 would make it the same as "não atendida", the confusion the Guide warns against, so it leaves the count.

## Decision

- **Who decides.** The auditor, in the review (ADR-0023). The system never proposes it: the pipeline cannot tell a stage not reached from evidence not found, and the Guide asks for a documented motivation.
- **Which Ações.** 45 and 46 only (`NOT_APPLICABLE_ACOES` in `src/assessment/interfaces/contracts.py`). The review route answers 422 for any other Ação.
- **The record.** A `ReviewOutcome` with `not_applicable` true has no `final_score`, is not an override, and carries the motivation in `justification`, which is required and not blank.
- **The table.** `review_outcomes` gets a `not_applicable` column, and `final_score` becomes nullable. A CHECK ties the two; it spells out `final_score IS NOT NULL`, because SQLite lets a CHECK that evaluates to NULL pass. `init_db` rebuilds a table created before this record in one transaction and keeps its rows.
- **The nota (ADR-0075).** The Ação gets the source `not_applicable` and no points, so it leaves the count, the maximum and the floor. A group whose other Ações are all counted stays complete, and every group reports `n_not_applicable`. A not-applicable review counts as reviewed.
- **The page.** The review form of Ações 45 and 46 offers N/A beside 0, 1 and 3, asks for the motivation, and says that missing evidence is not this. The Ação's panel shows "Não aplicável" with the motivation. The indicator names the Ações left out and shows "N/A" on the transition chips.

## Considered options

- **A score sentinel, for example -1:** rejected. It would put a non-score in the score column, and every reader of `final_score` would have to know it.
- **Any Ação:** rejected for now. Cases (b) and (c) need a judgement about the project's nature, and the Guide refuses the label in at least one place: an Ação on public consultation whose hearing was waived must carry a justification and cannot be classed "não aplicável" (5.2.3, p. 202). The user scoped it to 45 and 46.
- **Proposed by the system when 45 or 46 find no evidence:** rejected. It would turn "não atendida" into "não aplicável" by default.

## Consequences

- **The nota rises when 45 and 46 leave and they scored 0.** In the real case both are `sem evidência` (0 points) in the confirmation cycle; with both marked, the maximum goes from 138 to 132 and the points stay.
- **A forced re-run deletes these reviews too** (ADR-0026), like any other review.
- **ADR-0075's consequence on "não aplicável" is superseded** by this record; ADR-0023 gains one outcome without a Final Score.
