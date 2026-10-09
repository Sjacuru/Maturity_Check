# The gate treats a chunk that attests NON-fulfilment of the criterion as relevant; the fulfilment judgement stays with the scorer

**Status:** accepted — variant P1 measured 2026-10-03 at serial+low (ADR-0065) on Ações 26, 14, 22 and 3; a sharper wording (P2) was measured and rejected
**Date:** 2026-10-03

One sentence was added to the gate's instructions (`_INSTRUCTIONS` in
`relevance_builder.py`): a chunk that directly addresses what the criterion
asks is relevant even when it records that the item was NOT met, was not
produced, or does not apply to this process — judging fulfilment is the next
stage's job, not this classifier's — and this does not make a chunk relevant
for merely mentioning the topic.

## Why

R11's inspection (ADR-0064, "What R11's inspection surfaced") found Ação 26 going
score=1 → sem_evidencia because its only on-topic chunks — the Procuradoria's
parecer stating that the PPA/LDO/LOA adequacy declaration was *not* met (p.136)
and the structurer's reply that no budget adequacy applies to a concession
(p.144) — were rejected 4/4 for 26a and 26d alike. The captured reasoning was
explicit: "it mentions compatibility with PPA/LDO/LOA but says requisito não
atendido — so it references but does not satisfy". The gate read "evidência
DESTE Produto Esperado" as evidence THAT the product is satisfied. Documented
non-fulfilment — the only place the process treats the question — therefore
never reached the scorer or the auditor, and the Ação looked unexamined
instead of examined and failed. The scope rule is about *which product* a
chunk serves; it says nothing about polarity, so the polarity had to be stated.

## What was measured

All at one call in flight, `reasoning_effort=low`, 4 passes, production prompts
of the day (serial+low base measured the same way):

| | base | **P1 (adopted)** | P2 (sharper, rejected) |
|---|---|---|---|
| 26a p.136 / p.144 | `FFFF` / `FFFF` | `FTFT` / `FTTF` | `TTTT` / `FFFF` |
| 26d p.136 | `FFFF` | **`TTTT`** | `TTTF` |
| 26 other chunks | 0 oscillate | 0 | 26c p.324 `FFTF` (new false-positive candidate; the model lost track of which product it was judging) |
| 22 true positives p.193 / p.774 / p.921 | `TTTT` ×3 | `TFTT` / `TTTT` / `TTTT` | `TTTT` / `TTTT` / `FTTT` |
| 14 (40 pairs) | 0 accepts, 0 oscillate | 0 / 0 | 0 / 0 |
| 3 (8 pairs) | 0 accepts, 0 oscillate | 0 / 0 | p.161 `TFFF` |

End to end, through the production path, three runs of Ação 26 under P1:
`score=0 ×3` (R11 and R12 had `sem_evidencia`), p.136 in the evidence set every
run (26a in two runs, 26a+26d in the third, p.144 once). The outcome is stable
and the parecer is now in front of the scorer and the auditor; the scorer then
withholds credit on its own, as it should.

P2 ("relevante" defined explicitly, the parecer case named) stabilised 26a but
lost p.144, loosened 26d, produced a new oscillating false positive on an
unrelated 26c chunk, touched 22's insurance clause and re-woke Ação 3's p.161.
The lesson of ADR-0064 holds: the shorter wording that states the one missing
fact wins over the one that argues.

## What it does not do

P1 does not make the 26a verdicts on p.136/p.144 single-valued (they are now
borderline rather than wrongly settled), and 22's p.193 showed one flip in four
passes — p.193 is the same risk matrix as p.774, which stays `TTTT` and reaches
the scorer in either case. These residues are what the gate verdict ledger
(ADR-0067) freezes.

## Consequences

- `scripts/diagnostics/measure_gate_prompt_variants.py` keeps `P1` as a no-op
  (the base now contains it) and `P2` as an in-memory variant for comparison.
- Every gate prompt changed, so every ledger key changes; ADR-0066 shipped
  before the ledger was switched on.
- A test pins the sentence's presence (`test_relevance_builder.py`).
