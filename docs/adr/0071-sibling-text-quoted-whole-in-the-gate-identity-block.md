# Sibling product texts are quoted whole in the gate's identity block

The relevance gate's identity block (ADR-0064) names the Expected Products of
the same Ação that are NOT under evaluation, each with its IPMP text, so the
gate can tell the target from its siblings. Until 2026-10-09 each sibling text
was cut at 140 characters. It is now quoted whole
(`relevance_builder._SIBLING_TEXT_MAX = None`); the three lexical-match accepts
the whole text created in this case are handled where such things live, in the
retrieval profiles, as negative patterns measured under the whole-text prompt
before they shipped.

**Why the cut was wrong.** The cut hits 52 of the 164 product texts. What
survives is the generic opening clause ("Documento que apresente…"); what is
removed is the enumeration that actually distinguishes one sibling from
another — 18b lost 571 of its 710 chars (the whole list of what the economic
analysis must contain), 1d lost the list of federal planning instruments, 5b was
cut mid-word. The identity block was therefore telling the gate *that* a sibling
exists but not *what* it asks for, which is the one thing the contrast needs.

**Measured (P1a, 2026-10-09, `measure_sibling_text.py`).** 80 products whose
prompt changes, 1 146 chunks, 5 passes, three conditions interleaved per pass,
gate serial at `reasoning_effort=low`, ledger off, 17 190 calls, 0 errors:

| | 140 chars (before) | whole text | whole text + target label |
|---|---|---|---|
| chunks with a constant verdict | 1 130/1 146 (98.6 %) | 1 140 (99.5 %) | 1 136 (99.1 %) |
| product bits constant over 5 passes | 74/80 | **79/80** | 78/80 |
| Ações whose delivered batch is constant | 17/23 | **22/23** | 21/23 |
| accept rate | 5.3 % | 5.0 % | 6.0 % |
| gate reasoning confusing the target with a sibling | 2.0 % | 2.4 % | 0.0 % |
| mean / max system prompt (chars) | 2 739 / 5 155 | 2 824 (+3.1 %) / 5 155 | 2 913 / 5 155 |

The named true positives (22.2 p.774/p.193, 22.2b p.921) are accepted 5/5 in all
three. Of the nine product bits the whole text moved, six moved to the right
side (13c, 14d, 31.1g: attractor-page confounds rejected; 2c, 15f: a stricter
reading of borderline chunks) and three became stable false accepts — 11a
`_2` p.214 (the BIDDER's "Organograma do GRUPO ECONÔMICO" read as the project
team's organogram), 22.2a `_1` p.231 (a subcontracting clause read as the
technical justification of the risk allocation), 31.1h `_1` p.194 (the risk
matrix's "rotina constante de inspeção e manutenção" read as a quality-control
procedure). All three are lexical matches on a word of the criterion
(organograma, responsabilidade, inspeção): the class a per-product negative
pattern exists for, never a builder rule. The target label was not adopted: it
removes the confusion signal but raises the accept volume 14 % and turns two
more stable rejects into stable accepts (12c p.36, 12e p.58) and loses one true
positive (2d p.4); its gains on Ação 1 (1b, 1d) depend on rulings on 1b's
concept list and the polarity rule that were not taken.

**The patterns, measured first under the whole-text prompt**
(`measure_integral_candidates.py`, 2026-10-09, 2 conditions × 5 passes over the
production pool of each product, 580 calls; rule = item 4's bit-level rule:
target rejected every pass, product bit constant, no control chunk that was
homogeneous at base moves, overfitting audit clean — no 3–5-word phrase of the
pattern absent from the Ação's IPMP text and present in the corpus):

| product | pattern (criterion language, from the Ação's own IPMP text) | target base → patched | controls moved |
|---|---|---|---|
| 31.1h | an inspection/maintenance routine listed as a risk response or a standing operational duty is not a quality-control procedure of the project | `TTTTT → FFFFF` | 0/13 |
| 33b | a transition/takeover plan of the contractor (meetings with the grantor or the previous provider, inspection of assets) is not a stakeholder engagement plan | `TTTTT → FFFFF` | 0/12 |
| 11a | a bidder's qualification document (its own corporate or staff organogram) is not the project team's organogram | `FFFFF → FFFFF` — inert in this sequence | 0/14 |
| 22.2a | a clause that only attributes responsibility to one party is not the technical justification of the allocation | `FFFFF → FFFFF` — inert in this sequence | 0/15 |

31.1h and 33b are applied. 11a and 22.2a came out inert: their targets,
accepted 5/5 under the whole-text prompt in P1a, were rejected 15/15 the same
day in two further call sequences (the route-A order and a reproduction of
P1a's hoje → integral → patched neighbourhood), on byte-identical prompts.
That is the call-sequence effect of ADR-0065 seen across processes rather than
within one — inside each sequence not one of the 116 chunk × condition
trajectories of this measurement was mixed. A pattern whose effect cannot be
observed is not shipped on the strength of its harmlessness: **22.2a was
applied** only after the accept reappeared in production (confirmation pass 2
below, gate accept of p.231 for 22.2a, absorbed by the scorer), and re-confirmed
on Ação 22 alone (3 runs: p.231 rejected 3/3, score 1 ×3, the true positives
p.193/p.921 kept); **11a stays in the harness, unapplied** (p.214 rejected in
all five sequences since P1a).

**Confirmation across processes — the result that qualifies the decision.**
Three independent runs of the whole case (one process each, ledger off,
`reproducibility.py --runs 1` ×3, 2026-10-09 17:40–19:43) against the three
ADR-0069 baseline runs of the 140-char prompt (d1–d3):

| | 140 chars (d1–d3) | whole text + 31.1h/33b (conf1–3) |
|---|---|---|
| Ações with an identical delivered batch in 3 runs | 24/46 | 23/46 |
| Ações with identical product bits | 32/46 | 30/46 |
| Ações with an identical outcome | 38/46 | 38/46 |
| chunk × product verdicts identical in 3 runs | 2 228/2 298 (97.0 %) | 2 201/2 284 (96.4 %) |
| of the chunks accepted at least once, unstable | 70/121 (58 %) | 83/129 (64 %) |
| gate calls / accepts per run | 2 321 / 83–86 | 2 314 / 79–88 |

The within-process gain P1a measured (22/23 against 17/23 Ações with a constant
batch) does not exist across processes: the two regimes are equal within the
noise of three coins. The reason is in the data, not in the prompt. Over the
six independent processes (d1–d3 + conf1–3), 1 125 chunk × product verdicts
belong to products whose prompt is byte-identical in all six; 1 067 (94.8 %)
are constant, and of the 69 ever accepted only **11 are accepted in all six**
— 58 are coins, concentrated on the same pages as every earlier map (`_1`
p.196, `_2` p.136, `_1` p.194, `_2` p.223, `_1` p.29, `_2` p.134). On the same
chunks, P1a's within-process five passes were constant 98.6 %, and 9 chunks
were 5/5 accepted in P1a and 3/3 rejected in d1–d3. A five-pass measurement
inside one process establishes a patch's direction and harmlessness; it does
not estimate the run-to-run constancy the project is measured by. Independent
processes do.

The user kept it on 2026-10-10 ("fidelidade do bloco de identidade, custo zero medido, não é alavanca de constância"). So the whole text stays for what it provably fixes — the identity block now
says what each sibling asks for — at a measured cost of zero on every
run-to-run metric; it is not the constancy lever, and nothing here is claimed
to be. The one-line revert is `_SIBLING_TEXT_MAX = 140`.

**Consequences.** 87 of the 164 gate system prompts change (every product with
a sibling longer than 140 chars), so the ADR-0067 ledger keys change with them
(the first warm assessment re-asks the gate once; the ledger is report
reproducibility, not a stability number). The prompt-size budget of ADR-0069 is
untouched: over the 164 prompts the mean goes from 2 757 to 2 846 chars
(+3.2 %), the median from 2 684 to 2 742, and the largest (3a, 5 204) is
unchanged. The diagnostics reproduce the old
prompt by setting the limit (`measure_sibling_text.py` condition `hoje`). The
31.1h pattern also closes the coin that the 2026-10-09 confirmation of 31.1g
had surfaced under the 140-char prompt (p.194 accepted in 2 of 3 runs, score 0
instead of `sem evidência`).
