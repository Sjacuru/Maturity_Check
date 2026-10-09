# Score computed in code from per-product verdicts, not taken from the model

**Status:** accepted

The IPMP rubric is a count over an Ação's Expected Products (all evidenced → 3,
some → 1, none → 0). Until now the scorer LLM was asked to apply that count
itself and return a single `score`. `SCORER_SCHEMA` now also requires a
`products` array with one `{product_id, evidenced, justificativa}` entry per
scored Expected Product, and `parse_llm_response()` **computes** `proposed_score`
from those verdicts whenever they cover exactly the Ação's scored product ids,
ignoring the model's own `score`. `build_user_prompt()` correspondingly emits an
evidence block for **every** scored product, marking the empty ones
`NENHUMA evidência foi recuperada para este Produto Esperado.`

## Why

Across four consecutive full 46-Ação runs, scores flipped between 0/1/3 for the
same documents. Two mechanisms in this path explain part of it, both removed here:

1. **Empty product blocks were omitted entirely**, and nothing told the scorer
   that a missing block meant "not evidenced". The model therefore applied the
   rubric to a silently reduced subset of the Ação. In the 2026-09-07 run, Ação
   31 scored a full, unhedged 3 having judged 2 of its 9 products ("Both
   products are adequately evidenced, so the score for each is 3"); Ação 2
   scored 0 with 1 of 4 evidenced. Score bands overlapped almost completely
   against real product coverage (score=3 observed as low as 22% coverage,
   score=1 as high as 100%), meaning the number carried little information about
   what was actually found.
2. **The count itself was a free-text-conditioned judgement.** A count over a
   known list is deterministic; asking a model for it at temperature=0 still
   varies with whatever reasoning it happens to produce first. Moving the
   arithmetic into code makes `proposed_score` a pure function of the verdicts.

Listing `products` **first** in the schema is deliberate: grammar-constrained
generation follows property order, so the model commits to each product
individually before naming an overall score — the per-product judgement becomes
the evidence for the score rather than a rationalisation of it.

## Degradation, not failure

Anything less than a verdict set matching the expected ids exactly — field
absent, malformed, duplicated ids, a subset, unknown ids — falls back to the
model's own `score` (`score_source="model"`) and **forces
`uncertainty_flag=True`**. It never becomes `parse_failed`. A model that does
not cooperate with the richer schema must degrade to the pre-2026-09-27 result,
because a parse failure discards a whole Ação's work; the forced uncertainty
flag is what surfaces the degradation to the auditor instead.

`EvaluationResult` gains `product_verdicts` and `score_source`, both defaulted,
so rows persisted before this change still validate. The read path
(`json.loads(raw_json)`, ADR-0031) does not re-validate, so no migration is
needed and older evaluations render unchanged.

## Considered options

- **Keep asking the model for the score, only add the product blocks** —
  rejected: fixes the missing-subset half of the problem but leaves the count
  itself model-dependent, and the count is the one part with an exact answer.
- **Make a mismatched verdict set a parse failure** — rejected: throws away a
  complete, expensive evaluation over a response-shape problem that the model's
  own `score` can still answer, and a hard failure on every Ação would be worse
  than a flagged one.
- **Compute the score from the accepted-evidence counters instead of the
  model's verdicts** (`n_accepted > 0` per product) — rejected: accepted
  evidence means the gate judged a chunk *relevant*, not that it *satisfies* the
  product's criterion. That conflation is exactly what the negative-evidence
  patterns exist to correct, so it would re-introduce the false full-credit
  scores documented across Ações 14/40/45.

## Consequences

- To revert: remove `products` from `SCORER_SCHEMA`'s `properties` and
  `required`. `parse_llm_response()` then degrades to `score_source="model"` with
  no other change.
- `parse_llm_response(raw, expected_product_ids=...)` — the new argument is
  optional and only `evaluate()` supplies it, so direct callers keep the old
  behaviour.
- The auditor UI (`AcaoPanel.vue`) gains a per-product coverage table and states
  which of the two paths produced the score.
