# Citing Ações: the cited Ação's original instrument is not the revision

Twenty-three IPMP Ações cite another Ação and ask for a *revision*,
*finalisation* or *confirmation* of what that Ação produced (ADR-0070 typed
the 54 edges). Their retrieval profiles were synthesised one Ação at a time
(`docs/prompts/04_retrieval-profile-synthesis.md`), looking only at the citing
Ação's text, and the anchors they share with the cited Ação were demoted to
`experimental` to avoid collisions. Measured on the one real case
(cycle-1 ledger + six independent cold processes), the consequence is not an
empty pool but a **false credit**: of the 309 gate verdicts on citing products,
31 (10 %) accept the cited Ação's ORIGINAL instrument as if it were the
revision. Ação 43 scores 1 in 6/6 processes solely because 43b accepts the
contract's risk matrix and its rebalancing clauses (the allocation instrument
of Ação 22); Ação 35 scores 1 in 6/6 because 35.2e accepts insurance clauses
and matrix rows and 35.2f accepts a matrix row whose mitigation text is
"monitoramento rotineiro". The corpus holds no record of a performed revision
(72 artefact × marker hits, all "será atualizado" boilerplate) and exactly one
finalisation act, the dispatch `_3` p.10 that records the final version of the
documents and orders the notice published.

Decided on 2026-10-10 (user: *"Vamos de A + C agora (medíveis), B como
registro canônico junto"*), three things, each in the surface that owns it —
retrieval profiles and nothing in `src/`:

**A. A negative-pattern class — "the original is not the revision".** Four
per-product negative patterns, written in the citing Ação's own criterion
language, each saying what the cited instrument is (allocation between the
parties, a standing contractual duty) and what the citing product asks for
instead (an assessment with a value and a conclusion; the project team's
response strategy; a review routine of the plan; engagement with an impacted
group). Measured by the item-4 rule (`measure_integral_candidates.py
--candidates candidates_citing_originals.py`, production pools, 2 conditions ×
5 passes, serial at `low`, ledger off, overfitting audit clean — no 3–5-word
phrase absent from the Ação's IPMP and present in the corpus):

| product | target class | rounds | result (base → patched, 5 passes) | controls |
|---|---|---|---|---|
| 43b | contract risk matrix rows (`_1` p.193/194/196), rebalancing-request requirements (p.105), allocation-maintenance clause (p.239) | 3 | round 1–2: p.193/194/239 `TTTTT→FFFFF`, p.105/p.196 `TTTTT` kept ("mentions impact… could be considered evaluation"); round 3 adds a checkable marker — *no value, percentage or conclusion on the sufficiency of this project's resources = an event and its contractual consequence, not the assessment* — and all five go `FFFFF` | 5/5 unchanged |
| 35.2e | insurance clauses (`_1` p.251/p.117), matrix rows without the matrix heading (`_2` p.776), the procurement's own justification read as an "avoid" strategy (`_1` p.3) | 4 | round 2 passes p.251/p.117/p.776; round 3 (a sentence on the justification) loses p.776 again — a byte-sensitive borderline; round 4 restates the class with checkable markers (no risk register entry, no choice among the four responses, no team action) → p.776 and p.3 `TTTTT→FFFFF` | 10/10 unchanged |
| 35.2f | the "monitoramento rotineiro" row in three copies (`_1` p.198, `_2` p.20/p.497) and the rows with "acompanhamento periódico" (`_2` p.126/p.493) | 2 | targets `FFFFF`; the two "controls" `_2` p.126/p.493 (same class) `TTTTT→FFFFF` — the stored base reasoning judged them by **35.2e's** criterion ("strategy of response"), the target-product confusion measured on 2026-10-07; the pattern says, as content, that the response strategy is another product | 7/7 unchanged |
| 33b | standing obligations of the contractor (`_1` p.83: damages, labour law, asset conservation, notifying the grantor), accepted 1/6 in production | 1 | `FFFFF→FFFFF` in this sequence — inert, harmless; applied on the 22.2a precedent (defect observed in production) | 12/12 unchanged |

Two citing accepts were read and deliberately left without a pattern: **28.3**
`_2` p.136, the opinion that says "requisito não atendido" — accepted by the
polarity rule of ADR-0066 as designed, and judged not evidenced by the scorer;
and **37** `_1` p.29, an edital page, which is part of the finalised set the
criterion asks for.

**B. Aligned anchor + marker terms, as a canonical record.** 78
`NEAR(<specific anchor of the cited artefact>, <marker of the citing Ação>)`
terms (`canonical`, `active`, type C, `shared_with_acao` + note) on 42 citing
products — e.g. `NEAR(organograma, revisado)` on 29.1, `NEAR(estratégias,
mitigação, aprofundadas)` on 35.2e, `NEAR(objetivos, estratégicos,
atualizados)` on 39, `NEAR(capacidade, custeio, revisão, final)` on 43a,
`NEAR(estrutura, contratual, alternativa, escolhida)` on 22.1 — the anchor
from the cited Ação's text, the marker (atualizado / revisado / finalizado /
aprofundado, alternativa or opção escolhida, consulta pública, fatos
supervenientes) from the citing Ação's. Bare anchors stay `experimental`:
"identical elements" to the cited Ação would pull the original. Verified
retrieval-only before applying: **0 BM25 hits and 0 of the 42 examined pools
change in this corpus** (which records no revision), so the terms change
nothing here and nothing in any gate prompt — they wait for a corpus where a
revision was recorded.

**C. Finalisation terms for 37 and 42a.** `NEAR(versão, final, documentos)`
and `NEAR(publique, aviso, licitação)` on 37, `NEAR(nova, versão, documentos)`
on 42a — `real_world` (the phrases are the dispatch's, not the Ação's text;
42d holds "versão final dos documentos" canonically in the post-consultation
sense), literal presence confirmed. Retrieval-only: the dispatch enters 37's
pool at rank 2 and 42a's at rank 1, displacing `_1` p.350 and `_1` p.49, never
accepted in six processes. On the gate, in three independent processes, the
dispatch is **rejected for 42a 3/3** ("does not describe what changes or
motivations" — a fair reading of a three-line dispatch), **rejected for 42d
3/3** (no highlighted revised sections) and a **coin for 37** (0/3 in the runs,
5/5 in the harness process, T/F/F in isolated calls: "could be evidence of
internal approval" vs "does not show the complete set"). Two wordings of an
`evidence_intent` addition for 37 (the formal act that approves the finalised
documents counts as internal approval) were measured and **rejected**: each
left p.10 at `TTTTT` and turned 37's three stable accepts (`_1` p.40, `_2`
p.144, `_3` p.2) into `FFFFF` — rule (c) of item 4. Block C therefore stays a
retrieval change; the gate's verdict on the dispatch is the cross-process coin
of ADR-0071. **Reverted the same day, before any commit (ADR-0073):** the user
ruled that the analysed document can never be the source of a query term, and
these three phrases were taken from it.

**Consequences.** Four gate prompts change (43b, 35.2e, 35.2f, 33b; digest
`a80b57e83669cd47` → `6cadc9d8fc0b3810`, 164/164 injections, corpus leakage 0);
the expected score effect is Ação 43 `1 → sem evidência/0` and Ação 35 `1 →`
lower, i.e. the false credits leave the report — a correctness change the
user approved as the purpose of block A. Confirmation across three
independent processes is recorded below. The method lessons stand:
a concrete, checkable textual marker ("no value, percentage or conclusion")
moves a verdict that an abstract distinction ("not the assessment") does not
(the 2026-09-08 finding, reconfirmed); a borderline chunk can flip on any byte
of the prompt (35.2e p.776, 37's three accepts), so a pattern is judged on its
targets AND on every stable control, and every candidate wording is measured,
never reasoned into place.

**Confirmation (three independent processes, 2026-10-10 02:41–04:45, A+B+C
state, `reproducibility.py --runs 1` ×3 through the 8083 tunnel,
`scratchpad/acc/abc_conf{1,2,3}.json`, comparison `$W/compara_abc.py` →
`scratchpad/acc/compara_abc.txt`; 2 314 gate calls and 0 errors per process,
81/81/72 accepted chunks).** Read against the two earlier three-process
groups of the same frozen engine (base d1–d3, 2026-10-06; route A
`rota_a_conf1–3`, 2026-10-09 — the state A+B+C was applied on):

| per-Ação identity over 3 processes | base d1–d3 | route A | A+B+C |
|---|---|---|---|
| examined batch identical | 24/46 | 23/46 | 23/46 |
| product bits identical | 32/46 | 30/46 | 27/46 |
| score identical | 38/46 | 38/46 | 36/46 |
| gate verdicts constant (same prompt, 3 processes) | 97.0 % | 96.4 % | 96.5 % (2 207/2 286, 79 unstable) |

Over all nine processes 2 051/2 194 verdicts (93.5 %) are constant; 143 are
not, and 86 % of the chunks ever accepted are among them — the cross-process
coin of ADR-0071, neither improved nor worsened by A+B+C, which are
correctness changes and were never claimed as a constancy lever.

*Block A, chunk by chunk (A+B+C | route A | base).* 43b: `_1` p.193 FFF |
TTT | TTT, p.196 FFF | TTT | TTT, p.194 FFF | TTT | FTT, p.239 FFF | TTT |
TTT, p.105 **TFF** | TTT | TFT. 35.2e: `_1` p.251 FFF | TFF | FTF, `_1` p.117
FFF | TFF | FFF, `_2` p.776 **TTF** | TFT | TTT, `_1` p.3 **FTF** | FFF | FFF
(the justification page, a new coin). 35.2f: `_1` p.198 FFF | TFT | FFF, `_2`
p.20 FFF | FFF | TFF, `_2` p.497 FFF | TFF | FFF, `_2` p.126 **TFT** | FTT |
TFT, `_2` p.493 FFF in all. 33b: `_1` p.83 FFF | FFF | TFF. The stable
false accepts are gone; what remains are the byte-sensitive borderlines the
harness had already shown (p.776 flipped on a single sentence in round 3) —
`FFFFF` inside one process, a coin across processes, exactly the limit the
governing rule states (a 5-pass in-process measurement establishes direction
and harmlessness only). True positives kept: 22.2 `_2` p.193 TTT, 22.2b `_2`
p.921 TTT, 2d `_1` p.4 TTT; 26d `_2` p.136 TTF and 28.3 `_2` p.136 TFT as
before.

*Outcomes.* **Ação 43: 1,1,1,1,1,1 → 0, sem evidência, sem evidência** — the
false credit left the report; the single process with a score 0 is the one
where the coin p.105 landed on accept and the scorer judged it insufficient.
**Ação 35: 1,1,1 → 1,1,1 — not lowered.** Its accept volume fell from 3–4 to
1–3 and the accepts that had been constant inside one harness process (p.251,
p.117, p.198, p.20, p.497) are gone, but
with eight scored products one accepted chunk on any of them is score 1,
and in each process one coin landed: abc1 = `_2` p.126 (35.2f) + `_2` p.776
(35.2e); abc2 = `_1` p.3 + `_2` p.776 (35.2e) + `_2` p.810 (35.2b, a chunk
never targeted); abc3 = `_2` p.126 (35.2f) alone. Lowering 35 would need
either a further wording round on p.776/p.126 (both already `FFFFF` in the
harness process) or the user's acceptance that a single-coin score 1 on a
band margin of 1 is what ADR-0068 flags for optional review. 33 = sem / 1 /
sem (33c `_2` p.43, the known coin — 33b silent); 37 = 3 / 3 / 3; 42 = sem
×3; 23 = 1 / 1 / 1 (base 3 / 3 / 3, route A 1 / 3 / 1); 45 = 3 / 3 / 3.

*Block C on the gate.* The dispatch `_3` p.10 was **FFT for 37** (route A and
base: not in the pool), FFF for 42a and 42d — the coin seen in the three
`--acoes 37,42` processes, no new stable accept and no lost one.

*Score-variable Ações, A+B+C: 14, 20, 27, 28, 31, 33, 36, 40, 43, 46 (base: 8,
24, 27, 31, 33, 37, 42, 45; route A: 23, 24, 27, 28, 31, 33, 37, 42).* 43 is
the intended change (0 vs sem evidência = whether the coin p.105 landed).
14, 20, 40, 46 each come from ONE new accept in one of nine processes on a
product that had none before (14a `_1` p.3, 20d `_1` p.233, 40b `_2` p.646,
46.2 `_1` p.207 — none of their prompts changed; 20a's Block-B term had 0 hits
and left 20d's pool untouched). 36 is a correlated event worth recording:
36a had 2–5 accepts in 8/9 processes (`_1` p.196 in 7 of those 8) and **0 of 11 in
abc3**, byte-identical prompt, identical examined pool — the whole product
fell in one process, the call-sequence effect of ADR-0065 acting on several
borderline chunks at once, not an effect of the blocks (36 is untouched by
A, B and C). 27, 28, 31, 33 are the known coin Ações in every group.

*Verdict.* A applied and confirmed on its purpose (43), partial on 35 (volume
down, score held by coins); B inert by construction in this corpus; C
retrieval-only, gate coin — then reverted (ADR-0073). No constancy gain, no
constancy loss.

## Fifth round on Ação 35 (2026-10-10)

The user: *"medir uma quinta rodada só em p.776/p.12 e depois deixa o sinal de
revisão opcional do ADR-0068 fazer o seu papel"* (p.12 read as `_2` p.126).
Reading of the two chunks: both are rows of the contract's risk matrix, and
the rows the gate accepts include risks allocated to BOTH parties
("COMPARTILHADO") — the applied patterns spoke of a risk "atribuído a uma das
partes". The round closes that gap with a checkable marker — does each risk
come with the party that bears it (contratada, contratante or both)? — in IPMP
vocabulary ("risco compartilhado", "contratante", "contratada" are 15e's; the
separation between contractual responsibilities and operational management is
Ação 35's own exception). Candidates in
`scripts/diagnostics/candidates_acao35_round5.py`; overfitting audit clean
(strict 0; "matriz de riscos" is IPMP vocabulary of ten other Ações).

*In process* (5 passes; direction and harmlessness only): 35.2f `_2` p.126
FTTTT → FFFFF, 12/12 controls unchanged — passes; 35.2e `_2` p.776 FTTTT →
TTTTT — fails, not applied.

*Across processes* (five pairs of independent `--acoes 35` processes,
interleaved current/round 5, ledger off): the examined pool of every product
is identical in all ten; **35.2f `_2` p.126 current TFTTT → round 5 FFFFF**,
no other 35.2f accept in either arm → applied (negative pattern #3 of 35.2f;
of the 164 gate prompts only 35.2f's changed; digest `892930140524f172` →
`2663212a7b9c87f9`).

*Outcomes of Ação 35: current 1,1,1,1,1 → round 5 0,1,0,1,1.* The current
arm's constant 1 was false credit held by coins. The accepted batch was
distinct in four of five processes in BOTH arms (mean size 2.6 → 1.4), so
batch constancy did not change — the score's apparent constancy did. With one
false accept fewer, the scorer's own coin shows: the byte-identical batch
{`_2` p.776 for 35.2e} scored 0 in one process and 1 in another. The
remaining coins: 35.2e `_2` p.776 (7/10 accepted over both arms), 35.2e `_1`
p.3 (current TTTTT, round 5 FTFFF — its prompt and every call before it are
byte-identical between the arms, so the split is server state or chance),
35.2b `_2` p.810 (2/10) and `_1` p.194 (1/10).

*The ADR-0068 signal on this residue.* It fires in two of five processes per
arm, exactly when score 1 rests on a single accept (floor sem evidência or
0). It is silent when two coins hold the same product (not fragile: current
P1/P3/P4, round 5 P2) and on every score 0 (no upward claim, by design — a 0
that another process would have scored 1 is not flagged). Processes that are
either correct (not met) or flagged: current 2/5 → round 5 4/5. No sixth
round: what remains is the signal's and the auditor's, as the user decided.
Widening the signal (two coin accepts on one product; a 0 resting on a single
accept the scorer rejected) would change what ADR-0068 claims, not any score,
and is the user's call.

## 35.2e measured across processes (2026-10-10, at the request of the user)

35.2e had been rejected on the in-process measurement alone. The user asked
for it to be measured across processes as well, and set the rule for adopting
anything that day: *"Adotar apenas o que tornou o sistema mais consistente."*
Five pairs of independent `--acoes 35` processes, interleaved current /
candidate, ledger off, reasoning recorded (`scratchpad/acc/a35e_{cur,cand}{1..5}`);
the current arm is the profile on disk (35.2f applied); the examined pool is
identical in all ten processes.

- **Direction confirmed across processes, the opposite of the in-process
  verdict.** 35.2e `_2` p.776 was accepted in 7 of 10 current processes (these
  five plus the five round-5 processes above, which ran byte-identical
  prompts) and in 1 of 5 under the candidate. In process the same candidate
  had turned it TTTTT.
- **Outcome of Ação 35: current 1, 1, sem evidência, 1, 1 → candidate sem
  evidência, sem evidência, 1, 0, 1.** Changes against the mode 1 of 5 → 3 of
  5; pairs of processes with the same score 60 % → 20 %. Batch constancy did
  not move (four distinct batches in five processes in both arms; 10 % of the
  pairs identical), nor did verdict constancy (98.6 % → 98.8 % per pair). The
  ADR-0068 signal fired in 4 of 5 current processes and 2 of 5 candidate ones.
- **Not adopted**, by the rule of the day.

The mechanism is general. When the positive score of an Ação rests on several
false coins, removing the most frequent one hands the score to the rarer ones
(here 35.2e `_1` p.3, 2 of 10, and 35.2b `_2` p.810, 3 of 10): the target
moves the intended way and the outcome becomes less constant. The score is
constant only at the two ends of that path, with enough coins that one always
lands (false credit) or with none left (a stable "not met"). A rule that
accepts a step only when it is more consistent therefore stops on the
false-credit side. By the same rule 35.2f, applied in the morning under the
rule then in force, would not have qualified: batch constancy unchanged,
score 1 in five of five processes before, and over the ten current processes
now 1 in seven, 0 in two, sem evidência in one. Whether the rule applies to
35.2f retroactively is the decision of the user.

## R1–R4 closed (2026-10-10)

On 2026-10-08 four reading tasks on the citing Ações were proposed and then
suspended until the larger questions were decided. ADR-0070, this ADR and
ADR-0073 decided them. The user accepted the closure below on 2026-10-10.

- **R1** compared the `evidence_intent` of the reconfirmation Ações that
  evidence against those that do not. Block A's reading answered it: the
  reconfirmations that "evidence" do so by accepting the cited Ação's original
  instrument, not through better intents.
- **R2**, a controlled dependency test on Ação 14, is superseded by ADR-0070's
  dependency cap and review signal.
- **R3** asked whether cases 1 and 4 (the citing Ação and the cited one both
  empty) should be reported as un-evidenceable or have their criterion
  rewritten. They are reported as `sem evidência`, with no rewrite. The corpus
  records no performed revision, Block B found 0 hits, and ADR-0073 forbids
  writing a term or a criterion toward the document.
- **R4**, case 3 read per product (8 and 42), is absorbed by the item-4
  measurement: 42c's pattern was applied, 8d's was rejected, and 8b was inert.

## Ação 35, 43b and 42c in full processes (2026-10-11)

The fifth-round and 35.2e series above ran `--acoes 35` processes. The
2026-10-11 section of ADR-0071 shows that such processes replay and full
processes do not, so those series give direction only. Test cycle 2 ran ten full
processes with the current mixed state (35.2f applied, 35.2e not):

- Ação 35 scored 1 in 9 of 10 processes and 0 once, tolerable on the user's
  scale. The 1 rests on false coins: 35.2e `_2` p.776 accepted 8 of 10 times,
  `_1` p.3 4 of 10, 35.2b `_2` p.810 3 of 10.
- 35.2f `_2` p.126 was accepted 0 of 10 times: the round-5 pattern holds in
  full processes.
- Block A's 43b `_1` p.105 was accepted 2 of 10 times: it mostly holds.
- 42c `_1` p.106 was accepted 7 of 10 times. The 42c pattern, applied on
  2026-10-09 after 3/3 rejections in `--acoes 31,42` processes and rejected in
  all three A+B+C processes above, does not hold in full processes; those
  rejections were coin tosses.

The choice for Ação 35 among (i), (ii) and (iii) is still the user's. In full
processes (iii) is nearly constant at 1, built on the 35.2e coin that (ii)
would remove.
