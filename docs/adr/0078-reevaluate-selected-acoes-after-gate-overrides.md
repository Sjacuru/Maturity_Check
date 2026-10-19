# Re-evaluate selected Ações after gate overrides, recalculating their dependents

**Status:** accepted (2026-10-19)

The auditor can overturn a gate verdict (ADR-0067), but until now the new verdict reached a score only through a full forced assessment, which re-extracts nothing yet re-runs all 46 Ações and deletes every review of the case, the "não aplicável" of Ações 45 and 46 included (ADR-0026). On 2026-10-19 the user asked how to make the system re-evaluate after marking a passage, and decided: the auditor goes through the Ações, marks what is needed and re-evaluates at the end, or re-evaluates all of them, at the auditor's own risk; the review of a re-evaluated Ação is deleted after a confirmation, because it referred to an evaluation that no longer exists; no justification is required to accept the new score; the Ações that depend on a re-evaluated one are recalculated.

## Decision

- **Route.** `POST /api/cases/{p}/reevaluate` with `{acao_ids, delete_reviews}`. Each listed Ação runs retrieval, the genre filter, the gate and the scorer again from the documents already indexed. The ledger answers every recorded verdict, overrides included; only chunks never judged reach the model. Its evaluation is replaced. 422 for an unknown Ação or an empty list, 404 for an Ação without a stored evaluation.
- **Reviews.** The review of a re-evaluated Ação is deleted. Without `delete_reviews=true`, a request that would delete reviews is refused with 409 and the lists of the reviewed targets and of the reviewed Ações that may be recalculated; the interface turns that into a confirmation and repeats the request. A new score then comes through the existing review: accepting needs no note, changing the score needs a justification (ADR-0023).
- **Dependents.** One ascending walk over the Ações. An Ação that cites with effect (ADR-0070: `pre` caps, `artefato` signals review) an Ação whose score changed has its cap recomputed on the stored result, without the model (`recompute_dependency_cap`): the counted score is recovered from the stored cap, the margin is rebuilt from the stored evidence and verdicts, the new cap is applied. The result is identical to a fresh `evaluate()` with the new prior results (tested). When the dependent's score changes, its review is deleted too and its own dependents follow. The row keeps its date, since the gate did not run for it.
- **Pending overrides.** `GET /api/cases/{p}/reevaluation/pending` lists the auditor overrides recorded after the evaluation of their Ação was produced. The case page shows them in a "Reavaliação" block with two buttons, "Reavaliar Ações com override pendente" and "Reavaliar todas as Ações" (with its own confirmation), and a chip on each pending Ação.
- **Failures.** A server down at the start gives 503 and changes nothing. A server lost midway stops the model calls: the Ações already re-evaluated stay, their dependents are still recalculated, the rest are listed as not reached, and the route answers 503 with that report. Any other error in one Ação keeps its evaluation and its review and the walk goes on.

## What this amends

- **ADR-0067:** an override applies from the next re-evaluation of its Ação, not only from the next assessment of the case.
- **ADR-0070:** "base proposta, no cascade" still holds for reviews: a review never moves another Ação's score. A re-evaluation changes a proposed score, and its dependents are recalculated from it.
- **ADR-0026:** the replacement lifecycle gains a per-Ação replacement. It deletes only the reviews named above and leaves the chunks, the fingerprints and the other evaluations untouched.

## Considered options

- **A forced assessment after each override:** rejected. It costs all 46 Ações and every review for one passage.
- **Refuse to re-evaluate a reviewed Ação:** rejected by the user. The review referred to an evaluation that no longer exists.
- **Mandatory justification to accept a re-evaluated score:** rejected by the user. The override itself already carries one.
- **Warn about dependents instead of recalculating:** rejected by the user. The cap is arithmetic over stored data, so recalculating costs nothing and keeps the case consistent.

## Consequences

- The scorer is not in the ledger: re-evaluating an Ação whose batch did not change can still move its score (the scorer coin, about 9 % of identical batches). The review stays the auditor's last word.
- Re-evaluating all Ações of SMG-040 after ADR-0077 sent 28 chunks to the gate that the 2026-10-16 evaluation never judged: the narrative sections and the cleaner stamp text change prompts. Expect a few such calls whenever the code changed since the last assessment.
- An override recorded within the same second as the evaluation of its Ação is not listed as pending: the ledger stores whole seconds.
