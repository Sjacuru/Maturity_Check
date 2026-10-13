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

## The target label measured across processes (2026-10-10)

P1a measured `rotulado` inside one process only. That variant is the whole text
plus two changes: the target is rendered like a sibling
(`- 1b (EM AVALIAÇÃO) — texto`), and it is named in the criterion heading
(`## Critério de relevância do Produto Esperado 1b`).

It was measured again by the method this ADR established: three independent
whole-case processes, run as
`reproducibility.py --runs 1 --gate-variant rotulado --record-reasoning` with
the ledger off. The variant installs `measure_sibling_text.rotula_alvo` in
memory and was dry-checked on 164/164 prompts. The comparison arm is the three
A+B+C processes of ADR-0072, run from the same tree without the variant.

The comparison covers the 41 Ações whose prompts and pools did not change
between the two arms. Ações 11, 35, 37 and 42 changed in between; Ação 9 timed
out once under the label and is excluded. The unit is a pair of independent
processes, averaged over the three pairs of each arm.

| 41 Ações | whole text (A+B+C) | whole text + label |
|---|---|---|
| Ações with an identical delivered batch, per pair (the three pairs) | 23.3 (22, 26, 22) | 20.7 (23, 19, 20) |
| Ações with identical product bits, per pair | 28.0 (28, 31, 25) | 25.7 (27, 23, 27) |
| Ações with an identical outcome, per pair | 33.7 (33, 35, 33) | 30.3 (33, 30, 28) |
| chunk × product verdicts identical, per pair | 97.6 % | 97.4 % |
| Ações whose outcome varies over the 3 processes | 10 | 15 |
| … counting `sem evidência` as 0 | 7 | 12 |
| accepts per process | 73, 72, 63 | 75, 70, 86 (+11 %) |
| target-product confusion in the reasoning | 2.4 % (P1a, in-process) | 0 of 6 665 |

The label does what it was built for: the gate no longer mistakes a sibling for
the target. It buys nothing the project is measured by. Every constancy metric
is equal or lower, and the accept volume rises 11 %. With three processes per
arm, "not better" is established. "Worse" is only suggestive, because the best
labelled pair equals the A+B+C pairs on the outcome.

The harms P1a predicted inside one process did not reproduce as stable accepts.
1d p.144 was rejected 3/3, so Ação 1 stays at 1 in all six processes. The 2d
p.4 true positive was kept 3/3. 12c p.36 and 12e p.58 are one-in-three coins.

What did reproduce is the direction of the change. Thirty-five product × chunk
pairs were read one by one, with the chunk text and the labelled gate's own
reasoning:

- all 16 that the label accepts in two or three processes and the other arm
  never;
- all 8 the other way round;
- the 8 whose frequency moved by at least half;
- 3 that had moved after the first two processes.

**12 moved the right way.**

- Gained:
  - 23.4 `_1` p.355, a rebalancing clause and 23.4's literal target;
  - 2d `_2` p.157, the gap statement (items not covered by the current
    contracts).
- Rejected more often:
  - an interference-relocation clause for 13c;
  - a subcontracting clause for 15e;
  - the `_1` p.195 attractor for 23.1;
  - edital definitions and habilitação requirements for 25c (p.12, p.41, `_2`
    p.961);
  - bidder tax instructions for 32a;
  - standing obligations for 36a;
  - the edital's ineligibility procedure for 25d (p.53);
  - a compliance checklist for 4b (`_2` p.163).

**15 moved the wrong way.**

- Annex lists read as the annexed content:
  - 22.2 `_1` p.64 "Matriz de Risco";
  - 25a `_2` p.232 "Cronograma da Licitação".
- Contract definitions and clauses read as planning products:
  - 10c `_1` p.323 "FINANCIADOR";
  - 10a `_1` p.106, 3/3;
  - 15c `_1` p.332, and `_2` p.681 at 3/3;
  - 5b `_2` p.493;
  - 12b `_2` p.920, a power-of-attorney model;
  - 13b `_1` p.84, the concessionaire's monthly reports, 3/3;
  - 34b `_1` p.284, its mobilisation plan.
- Risk-matrix rows:
  - 28.2 `_1` p.193, 3/3;
  - 8d `_1` p.196;
  - 15e `_2` p.494, 3/3.
- ADR-0072's Block A target 43b `_1` p.105 came back.
- The Ação 45 true positive `_2` p.23 was lost once, and Ação 45 was
  `sem evidência` in that process.

**8 are borderline or wait on rulings about the profile:**

- 1b `_1` p.192, now 3/3. It is the economic study that 1b's own concept list
  declares valid.
- 1d `_2` p.136;
- 23.2 `_2` p.138 and p.145;
- 2c `_2` p.478;
- 4a `_1` p.76;
- 23.4 `_1` p.383;
- 15d `_2` p.20.

Read together, the moves look like a more literal match against the target's
own words. A chunk that shares them gets in: the same interference clause,
`_1` p.332, is accepted for 15c ("remoção de interferências") and rejected for
13c. A chunk that does not share them gets out.

So the label removes some false accepts, adds more, and fixes several at 3/3.
It also overrides negative patterns that exclude a class sharing the target's
words: 8d, 15e and 43b here, and 12e p.58 among the P1a chunks.

**Recommendation: do not adopt it.** Nothing was ever applied, because the
variant lives only in the harness. The status quo stays: the whole text, with
no label. The confusion signal it removes is not a constancy lever.

Raw data is in `scratchpad/acc/rot_conf{1,2,3}.json` (gitignored). The third
process was rerun after the client's SSH tunnel dropped mid-run. The failed run
is kept aside as `rot_conf3_tunel_caiu.*` and is not counted.

## Single-Ação processes do not replace full runs either (2026-10-11)

Test cycle 2 ran ten full processes of the whole case (`reproducibility.py
--runs 1`, ledger off, 2026-10-10 23:35 to 2026-10-11 06:28, through the SSH
tunnel to the owner's 8083 instance). ADR-0069 made the examined pool
positional, so every process sent the same 2 310 gate prompts, byte for byte,
in the same order. The verdicts still differed between processes, and they
differed from the start:

- In 42 of the 45 pairs of processes, the first gate difference (per-product
  counters or delivered batch) is at Ação 1, the first Ação gated; in the other
  3 it is at Ação 2. Whenever everything up to an Ação was identical, that Ação
  differed in 45 of 48 cases.
- Ação 1 run alone, as ten separate processes on 2026-10-10 with the same
  profile and the same prompts (`--acoes 1`, the option-B and 1d series of
  ADR-0073), delivered the same batch in 45 of 45 pairs. Inside the ten full
  processes it delivered the same batch in 15 of 45 pairs; its product bits
  were identical in 45/45 and 29/45. The score was 1 in all twenty processes.

So a series of processes that each run one Ação, or a few, does what five
passes inside one process do (the 2026-10-09 finding above): it replays. It
shows the direction of a change and whether the change harms its controls; it
does not estimate the run-to-run constancy of a full assessment. From here on,
constancy is measured only on full 46-Ação processes.

The carrier is outside the client, since the prompts and their order are the
same. Server state (what the previous process left in the cache and the slots)
is the hypothesis. Probing it needs server-internal request parameters, which
the project uses only when the user asks.

Measurements whose direction stands and whose magnitude does not carry to full
runs, all made on `--acoes` subsets: the option-B gain of Ação 1 and the costs
of the 1b and 3a candidates (ADR-0073, corrected there); the fifth round and the
35.2e series on Ação 35 (ADR-0072, note added there); the 11a, 22.2a and 31/42
confirmations; the Block C runs. Where full processes exist they agree on
direction: in cycle 2, 35.2f `_2` p.126 was accepted 0 of 10 times and Block A's
43b `_1` p.105 2 of 10. They also show what a subset hides: the 42c pattern,
applied after 3/3 rejections in `--acoes 31,42` processes, does not hold, and
`_1` p.106 was accepted 7 of 10 times.

Cycle 2's other results are recorded in CLAUDE.md (63rd pass): 26/46 Ações with
identical points in all ten processes, 31/46 at 90 % or more, and 83 % of the
point changes coming from the gate.
