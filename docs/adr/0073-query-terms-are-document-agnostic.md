# Query terms are document-agnostic: a case document tests a profile, it never sources one

The user ruled on 2026-10-10 that the document under analysis "não pode ser o
parâmetro para a criação dos termos das queries, sob o risco de encontrarmos
documentos/chunks relevantes apenas para o processo em análise. A busca tem que
ser agnóstica em relação ao documento. Precisamos poder avaliar qualquer
documento de qualquer tipo com as queries aqui criadas." From now on a Query
Term's source lies outside the analysed case: the IPMP text (`canonical`) or a
sector pattern (`synthetic`, experimental by default, ADR-0056). A case
document is used to TEST a profile — whether a term pulls boilerplate, whether
a product has anything to find (a content gap), what the gate and the scorer
do. Literal presence of a phrase in a case document is never a reason to add a
term or to promote one to `active`. No new `real_world` term is created.

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
before shipping: (A) remove every `real_world` term; (B) keep the 24 that have
an IPMP source, relabelled `canonical` with that source named, and remove the
32 that do not. Not applied until the user chooses.

**What this does not cover.** `negative_evidence_patterns` are gate content,
not queries. Which confound classes got a pattern was learned from false
accepts in this corpus, but the wording is the IPMP's criterion language at
class level and passes the overfitting audit (no 3–5-word n-gram absent from
the Ação's IPMP and present in the corpus) before it ships; `_meta` notes may
cite case pages as documentation and never reach a prompt (leakage check, 0 in
164 products). Block B of ADR-0072 is inside the rule by construction: all 272
tokens of its 78 terms come from the IPMP texts of the citing and the cited
Ação (245 literal, 27 inflections of IPMP words), the corpus was used only to
confirm they change nothing here.
