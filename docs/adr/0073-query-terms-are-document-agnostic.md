# Query terms are document-agnostic: a case document tests a profile, it never sources one

The user ruled on 2026-10-10 that the document under analysis "não pode ser o
parâmetro para a criação dos termos das queries, sob o risco de encontrarmos
documentos/chunks relevantes apenas para o processo em análise. A busca tem que
ser agnóstica em relação ao documento. Precisamos poder avaliar qualquer
documento de qualquer tipo com as queries aqui criadas." From now on a Query
Term's source lies outside the analysed case: the term is `canonical` —
general vocabulary of the Ação's concept, valid for any document of any type
(see the clarification below) — or a sector pattern (`synthetic`,
experimental by default, ADR-0056). A case
document is used to TEST a profile — whether a term pulls boilerplate, whether
a product has anything to find (a content gap), what the gate and the scorer
do. Literal presence of a phrase in a case document is never a reason to add a
term or to promote one to `active`. No new `real_world` term is created.

**Clarification by the user, the same day.** *"os termos de busca não podem
ser customizados para o documento onde as informações são buscadas, mas isso
não significa que termos fora do IPMP não possam ser usados. A única exigência
que se faz é que um novo termo seja canônico."*

Canonical is a property of the term, not of where it was first seen. It is the
vocabulary anyone would use to find the Ação's concept in the documents of any
PPP case. That vocabulary can come from:

- the IPMP text itself;
- the legislation and official manuals its criteria rely on (Lei 14.133/2021,
  the LRF, the Rio Manual's document names);
- established domain vocabulary.

Literal presence in the IPMP is sufficient, not necessary.

The rule excludes a term tailored to the analysed document: its own phrasing,
names, places or objects, or a sector noun of this case. It also excludes the
case document as the reason for adding a term. Sector-specific vocabulary
stays `synthetic` and experimental (ADR-0056).

**What this reverses.** Step 8 of `docs/prompts/05_retrieval-profile-validation.md`
promoted an `experimental` term to `active` when its phrase appeared in the
accepted chunks of the case — the case selected what is searched. Stage B of
Ação 1 (2026-06-18) and of Ação 3 (2026-08-28) added `real_world` terms taken
from the SMG-040 documents, and Block C of ADR-0072 (2026-10-10) added three
more to reach one dispatch page. Step 8 is amended; Block C was reverted the
same day (retrieval-only, the gate had treated the page as a coin, no measured
score depended on it).

**Legacy terms — inventory and measured consequence, decision pending.** 56
`real_world` terms remain (43 active), in Ações 1, 3, 4, 5 and 28. 24 of them
also occur in the IPMP text of some Ação (a source outside the document
exists); 32 have the document as their only source, 27 of them active
(e.g. "harmonização contratual", "término da vigência", "segurança pública",
"Lei Complementar Municipal", "bens tombados", "parcelamento da solução").
A retrieval-only probe (no GPU) shows what removing the 43 active ones would
cost in this case: chunks accepted in every one of nine independent processes
leave the examined pool of 1a (`_1` p.4), 1c (`_1` p.3, `_2` p.160), 3a
(`_2` p.159), 4a (`_2` p.247) and 4c (`_1` p.331/409/214), plus 4d `_2` p.160
(8/9) and 28.3 `_2` p.136 (7/9). The terms carry a real part of Ações 1, 3, 4
and 28's evidence on this case — which is exactly what the ruling says a
query must not do. Two ways out, both measured across independent processes
before shipping: (A) remove every `real_world` term; (B) keep every legacy term
that is canonical in the sense above: the 24 with an IPMP source, and those of
the other 32 whose source is legislation, an official manual or general domain
vocabulary. These are relabelled `canonical` with the source named; the terms
tailored to this case are removed.

On 2026-10-10 the user followed the recommendation (B), with the rule that only
what measures as more consistent across independent processes is adopted.

**Option B as classified and measured (2026-10-10).** The 56 legacy terms
were classified one by one by canonicity
(`scripts/diagnostics/candidates_legacy_terms.py`: each term with its source,
or the reason it fails). 37 are canonical: kept and relabelled `canonical`,
source named (the IPMP text of some Ação; Lei 14.133/2021 art. 18 §1; Lei
8.987/1995 art. 6; LC 101/2000; Decreto-Lei 25/1937; the Rio Manual; general
contract vocabulary of a re-procurement motive). 17 are tailored and removed:
1a "harmonização contratual" ×2 (this case's own phrase); 1b's eleven finance
and benchmarking terms (the vocabulary of this case's economic study, read as
the 1b panorama); 1c's three goals of this case; 1d
`NEAR(concessão, serviço, público)` (this case's contracting model). 2 are
sector terms that 1d does not name ("mobilidade urbana" ×2): `synthetic`,
experimental, `sector_hint` transporte_publico (ADR-0056). All 15 that change
retrieval (active, then removed or demoted) are in Ação 1. In Ações 3, 4, 5 and
28 only the provenance label changes; the status, which is what the search
reads, does not.

Measured across independent processes before anything was written
(`reproducibility.py --runs 1 --acoes 1`, ledger off, the candidate applied in
memory through `--candidates`/`--apply`; five current-state and five candidate
processes, interleaved): identical batch per pair of processes 10 % → 100 %
(29 % over eleven current-state processes, six of them earlier), product bits
40 % → 100 %, verdicts constant 97.7 % → 100 %, score 1 in all ten. The 1b
coin leaves the examined pool: `_1` p.192/p.298, the economic study that the
finance terms had brought in, accepted in 4 of 11 current-state processes. 1b
is now constant not-evidenced, the content gap recorded since 2026-07-01. 1a
rests on one chunk instead of two. `_2` p.157 (the preliminary technical
study's statement of the re-procurement motive) was accepted 5/5. `_1`
p.3/p.4 (the edital's own justification, reached through "harmonização
contratual") now fall outside the 16 examined. That makes 1a fragile in
ADR-0068's sense, with floor 1 and no review signal. **Adopted** under the
user's rule and applied by textual edit. For every product of the five Ações,
the written profiles build the same BM25 query as the measured candidate. 0
`real_world` terms remain, and the gate digest is unchanged
(`2663212a7b9c87f9`).

**The 3a concept: measured, not adopted.** A scan of every `evidence_intent`
and concept looked for words absent from all IPMP and Rio Manual texts and
frequent in the case. It found one case noun inside a field the search reads:
"mobiliário" in 3a's `concrete_solution_description`. The rewrite to 3a's own
intent wording ("elementos, tipos de solução, lotes ou etapas") was measured
the same way (five + five processes, `--acoes 3`). Identical batch per pair
dropped 100 % → 60 % and verdicts 100 % → 97.5 %. The new vector query brings
`_1` p.394 into the examined pool: the characterisation of the bike-station
lot, accepted in 1 of 5 processes. Score 3 in all ten. Less constant, so not
adopted under the rule. Whether canonicity should prevail over this measured
cost is the user's decision; the concept keeps the case noun until then.

**Two more case-derived texts in gate-read fields, found on 2026-10-10 and not
changed.** (i) 1d's first negative pattern names this case's sector: "sem
correspondência com o setor de mobiliário urbano (PNL, PDE, Plansab, PNLP são
inaplicáveis a este setor)". It was written on 2026-06-19, before the
overfitting audit existed. A scan of the negative patterns of all 164 products
found no other sector noun of the case; the other hits are general concession
vocabulary (concessionária, poder concedente, outorga). For a sanitation
project, this pattern would tell the gate to reject the Plansab, an instrument
1d's own criterion lists. (ii) Three of 1b's four concepts were written in
Ação 1's Stage B from the case's economic study: `economic_viability_study`,
`benchmarking` and `investment_scale`. The IPMP 1b criterion asks for the
panorama "considerando os cenários econômico, social e ambiental relevantes".
Both fixes change a gate prompt; neither is made without the user. 1b and 1d
are constant not-evidenced in this case, so a measurement can at best show no
change here. The reason for the fix is the next document, not this one.

**Accepted the same day; 1d applied, 1b measured and not written.** The user
accepted both fixes (*"Vou acatar todas as sugestões"*). The statement above
that a measurement could at best show no change was too strong for 1b: its
concepts enter the vector query, so new texts change the pool. Both were
measured across independent processes before writing
(`scripts/diagnostics/candidates_acao01_canonical.py`, applied in memory;
ledger off). The gate walks 1a, 1b, 1c and 1d in that order and each product
has its own pool, so one joint run separates the two changes.

- **1b, not written.** Five current and five candidate processes,
  interleaved. The criterion's three scenarios change 1b's pool: 11 chunks
  enter and 10 leave. One entrant, the edital's justification of the
  procurement (`_1` p.2), was accepted for 1b in 1 of 5 processes. The
  gate's reasoning took 1b for 1a's IPMP text, the target confusion recorded
  in ADR-0071, and the same process accepted the page for 1c. The score
  stayed 1 in all ten processes, but the batch delivered to the scorer was
  identical in 30 % of the candidate pairs, against 100 % in eleven
  current-state processes. Less constant, so under the user's rule the
  concepts stay as they are. Canonicity against this measured cost is the
  user's decision, the same one as for the 3a concept.
- **1d, written.** Its pool did not change, and its 16 examined chunks were
  rejected in every process. Five more processes with the 1d pattern alone
  gave the same batch in all five, equal to that of the eleven current-state
  processes, and 16/16 rejections for 1d. It was written by textual edit,
  together with the two dormant logic notes that matched it. Only 1d's gate
  prompt changed. The written profile builds the same 164 gate prompts as the
  candidate applied in memory. Global digest `2663212a7b9c87f9` →
  `6919edcc672b8027`, leakage 0.
- One candidate process rejected 1a's only accepted chunk (`_2` p.157). That
  is not attributed to either change: 1a's prompt is byte-identical between
  the arms and is gated before any changed prompt. It is the server-state coin
  of ADR-0071, seen once in 21 processes.

**Correction on 2026-10-11: the constancy figures above come from
single-Ação processes.** Option B's gain (identical batch per pair 10 % →
100 %) and the costs of the 1b and 3a candidates (100 % → 30 % and 100 % →
60 %) were measured in processes that ran Ação 1 or Ação 3 alone. Test cycle 2
showed that such processes replay and full processes do not (ADR-0071,
2026-10-11). In full processes Ação 1's batch was identical in 6 of 15 pairs
with the old profile (six processes, 2026-10-09 and 10) and in 15 of 45 with
the current one (ten processes); its product bits in 7/15 and 29/45; its score
was 1 in all. The direction stands: with option B the 1b finance-term coin left
the pool, and the 1b and 3a candidates bring in a chunk that the current
profile never examines and that the gate sometimes accepts. Option B therefore
stands on this ADR's rule, canonicity, and not on a measured constancy gain.
The 1b and 3a decisions stay with the user, with the cost stated as a new coin
rather than as a percentage.

**What this does not cover.** `negative_evidence_patterns` are gate content,
not queries. Which confound classes got a pattern was learned from false
accepts in this corpus, but the wording is the IPMP's criterion language at
class level and passes the overfitting audit (no 3–5-word n-gram absent from
the Ação's IPMP and present in the corpus) before it ships — every pattern written
since that audit exists; the one older exception, recorded above, was rewritten on
2026-10-10; `_meta` notes may
cite case pages as documentation and never reach a prompt (leakage check, 0 in
164 products). Block B of ADR-0072 is inside the rule by construction: all 272
tokens of its 78 terms come from the IPMP texts of the citing and the cited
Ação (245 literal, 27 inflections of IPMP words), the corpus was used only to
confirm they change nothing here.
