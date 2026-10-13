---
Status: accepted (2026-10-13)
---

# Instrument text leaves before the gate: the document's genre, from a canonical document index

On 2026-10-12 the user ruled that contract, edital and termo de referência text
must not reach the gate, nor through it the scorer, for any Expected Product
whose IPMP criterion is not the instrument itself:

> *"Precisamos eliminar esses chunks da análise. É puro lixo. Até mesmo para os
> elementos que não oscilam. Retirar esses pedaços antes de chegarem ao GATE de
> validação inclusive, pois ele pode validar o chunk e trazer seus vizinhos, que
> também são partes de contratos. […] A opção do uso de mapa manual está afastada
> por enquanto."*

The ruling answered the class analysis of test cycle 2 (ten full processes,
2026-10-10/11). Of the 101 (product, page) pairs that were confounds and that the
gate accepted in some processes and not in others, 90 were instrument text:

| Instrument text class | Pairs |
|---|---|
| risk-matrix rows | 26 |
| standing duties of the parties | 15 |
| operational obligations | 12 |
| object and definitions | 10 |
| rebalancing | 10 |
| edital | 8 |
| specification | 5 |
| guarantee | 4 |

Patching those pairs one negative pattern at a time is the per-Ação route the
user has ruled out. Removing the class is not.

The user's answers of the same day (message L) set the shape:

- the exemption list is right;
- the 14 lost pairs are accepted;
- variant A2;
- genre by the whole document, from an index kept "de forma canônica";
- neighbour expansion back on, but only for neighbours the genre classifier does
  not mark as instrument text.

This ADR records what was built.

## Decision

**1. Genre.** Every chunk takes the genre of the document it belongs to.

- **INSTRUMENTO**: a contract or minuta, an edital, a termo de referência, and
  their normative annexes (risk matrix, specification, performance indicators,
  payment mechanism, forms).
- **OUTRO**: studies, the ETP, opinions, notes, reports, justifications, acts and
  correspondence.

A document's genre is the type its title names, when the title names a known
type. Otherwise it is the majority of its chunks' own labels, and a tie is OUTRO.
"In doubt, OUTRO": excluding a legitimate passage costs more than keeping one of
instrument text.

**2. A canonical document index** (`src/retrieval/genre/`), derived from the
chunks and persisted next to them.

- **`classifier.py`** labels each chunk from the general drafting conventions of
  Brazilian instruments, weighed against the voice of analysis (study verbs and
  figures) and of administrative acts (despacho, certidão, ofício, a dateline).
  The instrument markers are:
  - self-reference ("deste CONTRATO");
  - a defined party in capitals as the subject of a deontic or future verb;
  - prescriptive voice;
  - numbered and titled clauses, definitions and form placeholders;
  - matrix rows and risk allocated to a party;
  - clause cross-references and semicolon lists;
  - the share of capitals.

  A short, silent chunk inherits its label from chunk 0 of its page; failing
  that, from the strict majority of firm labels within two pages of the same
  file; failing that, it is OUTRO.
- **`segmentation.py`** recovers where each document starts and ends inside a
  bundled PDF. A document opens at:
  - a title line opening with a known document type, found after the printed
    page number and the letterhead;
  - a cover page: short, and followed by a SUMÁRIO/ÍNDICE or by printed page 2;
  - the printed numbering restarting at 1.

  A printed page number that continues the previous one never opens a document,
  and a title equal to the current one is a running header. Generic headings
  (DECLARAÇÃO, CRONOGRAMA, PLANO, MANUAL, DIRETRIZES) are untyped on purpose, so
  their document is decided by its own passages.
- **`index.py`** stores three tables:
  - the documents (`document_index`);
  - the genre of every chunk (`chunk_genre`);
  - the state the index was built from (`document_index_state`: chunk count, a
    sha256 over the chunk keys and lengths, and `GENRE_RULES_VERSION`).

  A read rebuilds the index whenever the chunks or the rules have changed, so a
  read never returns an index of other chunks or other rules, and the same chunks
  and rules always give the same index. A new or replaced file, and a forced case
  replacement, also drop the index explicitly.
- **Canonical by construction.** Nothing in the index names a page, a document,
  an organ or a city of a case. The prototype's act dateline named the case's
  city; production matches any "Cidade, 12 de março" dateline. On SMG-040 this
  changes nothing: 84 marks either way.

**3. Exemptions.** The file is `data/ipmp/isencoes_genero.json`, loaded by
`ingestion.get_genre_exemption_store()`. It lists the 17 Expected Products whose
criterion is the instrument itself, each with its IPMP sentence and the reason:
22.1, 22.2, 22.2a, 22.2b, 23.1–23.4, 25a–25e, 37, 42d, 45 and 46.1.

The loader refuses three things, so the list cannot drift silently from the
criteria it exempts:

- a product that is not a scored Produto Esperado of its Ação;
- a duplicate;
- a sentence that no longer equals the IPMP text.

**4. The filter, variant A2** (`evidence_selection.select_evidence`). For a
non-exempt product, candidates whose document is instrument text are removed
from the ranked list (20 from BM25 and 20 from the vector lane, fused by RRF).
The removal happens before the near-duplicate prefilter and before the
`_MAX_EXAMINED` cut. The examined pool is therefore the best-ranked candidates
that are not instrument text, inside the current candidate window. Nothing is
refilled from deeper lanes, and a chunk the index does not know is kept.

**5. Neighbour expansion back on** (`EXPANSION_ENABLED = True`). This partially
supersedes point 1 of ADR-0069.

- A neighbour of an accepted chunk is gated only when its document is not
  instrument text. The rule applies to every product, exempt ones included; this
  is the literal reading of message L. Decided after cycle 3 (2026-10-13): an
  exempt product takes no instrument neighbours either. The exempt products
  already hold 42 of the 65 coins of cycle 3, and instrument neighbours would
  add more verdicts on the same class of text.
- A neighbour already judged for the product in the pass is not asked again:
  either a member of the product's examined pool, or the neighbour of an earlier
  anchor.
- `_EVIDENCE_BUDGET_CHARS` follows the evaluator's 70 000, since expansion can
  reach that budget again.

**6. The focal route** (Step A/B, `filter_focal_document`). On this route one
document reaches the scorer ungated, with no product block of its own. Its
instrument text therefore cannot be kept for one product and removed for another.

| Focal document | Outcome |
|---|---|
| no instrument chunk, or every scored product exempt | passes as it is |
| some products exempt and some not | gives way to the per-product hybrid route |
| no product exempt | its instrument chunks are dropped; if nothing is left, the hybrid route runs |

**7. Telemetry and switches.**

- `ProductGateReport` gains two counters:
  - `n_genre_excluded`: candidates removed before the cut. Always 0 for an exempt
    product.
  - `n_neighbors_genre_excluded`: neighbours not gated as instrument text.
- `reproducibility.py`:
  - takes `--no-genre-filter` and `--no-expansion`;
  - records both switches and `GENRE_RULES_VERSION` in its JSON;
  - appends the two counters to the per-product vector as its 7th and 8th
    elements.
- `strip_extraction_noise` moved from evaluation to `src/extraction/noise.py`.
  The classifier reads the same cleaned text the gate reads, and retrieval cannot
  import evaluation.

## Measured before the GPU

- **Chunk classifier, evaluated without a page map.** These are figures for the
  prototype v4; the production port gives identical labels on all 1 429 chunks of
  SMG-040.
  - Chunks of documents that the process's own structure marks as normative:
    362/365 labelled INSTRUMENTO.
  - Chunks of studies, opinions and acts: 0/150 labelled INSTRUMENTO.
  - Against the cycle-2 class map: 114/120 and 17/18.
  - A blind sample: 56/58 and 2/2.
- **Document index of SMG-040.**
  - 59 documents, 30 of them instrument text, holding 1 257 of the 1 429 chunks
    (88 %).
  - The production index equals the prototype: 59/59 documents and 1 429/1 429
    chunk genres.
  - Built in 2.8 s; re-read in 0.02 s.
- **The production path reproduces the projection exactly.** The check ran
  `assessment.service._retrieve_and_select` with a gate that rejects everything,
  ledger off.
  - 164 products, with no pool different in content or in order.
  - 71 empty pools.
  - 464 gate calls per process instead of 2 310.
  - 2 956 candidates removed before the cut.
  - No Ação of the case takes the focal route.
- **Projection over the ten processes of cycle 2.** It uses the recorded
  verdicts, with no new call; a pair never judged for its product is unknown.
  - Batch identical in all ten: 15 → 30 of 46 Ações.
  - Evidenced bits identical in all ten: 19 → 32 Ações.
  - Points identical in all ten: 26 recorded today. Under the filter, 30 can be
    known to be constant and 5 to vary; 11 depend on a verdict that does not
    exist yet.
  - The user's criterion (same points in 9 or more of 10): 31 → between 30
    and 41.
  - Of the 106 confusion pairs, 93 leave and 13 stay: 4 on exempt products,
    9 in documents of genre OUTRO.
  - 17 (product, chunk) pairs enter pools without ever having been judged.
- **Correctness cost, accepted by the user.** 14 legitimate or debatable pairs
  leave with the instrument text: 1c ×3, 4a ×5, 4b ×2, 15a ×2, 15c and 36a.
  This takes Ação 4 from 3 to 1, and Ações 15 and 36 from 1 to 0.

## Considered options

- **A — filter the pool of 16 after the cut.** It costs fewer calls (503), but
  the pool is not refilled with the next-best candidates that are not instrument
  text. Superseded by A2.
- **B — refill each pool to 16 from deeper lanes** (2 228 calls). Rejected:
  1 726 (product, chunk) pairs would never have been judged, on 134 chunks, and
  the procurement's justification page would be judged by 80 products. It would
  concentrate coins instead of removing them.
- **Chunk genre instead of document genre.** A page of a minuta that reads like
  prose (definitions, an annex description) keeps its OUTRO label and slips
  through, and a study that quotes a clause is filtered. The user chose the
  document. That requires knowing where each document starts and ends, which the
  chunk table did not record, so the index was built.
- **A hand-made page map.** Ruled out by the user.
- **Hiding instrument text from the scorer only.** The gate would still accept
  it and, with expansion, bring its neighbours. The user's rule is before the
  gate.

## Consequences

- In this case 71 of the 164 products have an empty pool. Their "no evidence"
  is now decided deterministically, without a gate call. A process needs a
  fifth of the gate calls it needed before.
- A new case's documents may carry titles outside the type lexicon. Such a
  document is decided by its own passages, and doubt keeps the text.
- Any change to the markers, the lexicon or the segmentation rules must bump
  `GENRE_RULES_VERSION`, or old indexes stay in use.
- The exemption list is tied to the IPMP texts. When a criterion changes, the
  loader refuses to start until the list is reviewed.
- **Limitation, pre-existing.** `strip_extraction_noise` removes only the case
  organisation's own header, signature block and version tag (the Rio de Janeiro
  SMG header, `SMGPRO…`). Another organisation's letterhead stays in the text.
  The segmentation's letterhead rule is generic and skips it before looking for
  a title, but the classifier still sees it. Generalising the noise patterns is a
  separate change.
- **Test cycle 3** (ten full processes, ledger off) measures what the projection
  could not:
  - the gate and the scorer on the new pools;
  - what the filtered expansion costs in constancy;
  - the 17 pairs that were never judged.

## Test cycle 3 (2026-10-13)

Ten independent full processes of the 46 Ações, run one after another with the
ledger off and with the genre filter and the filtered expansion on (11:30 to
14:00; `scratchpad/acc/ciclo3_run{1..10}`). There were no errors and no gate
failures in 4 990 gate calls. Cycle 2 (2026-10-10/11, the code before this ADR)
is the reference, not a target.

| Measure (points, with `sem evidência` read as 0) | Cycle 2 | Cycle 3 |
|---|---|---|
| Ações with the same points in all ten | 26 | 38 |
| Ações with the same points in 9 or more of 10 (the criterion of the user) | 31 | 41 |
| Mean agreement with the modal outcome | 87.4 % | 95.7 % |
| Consistent / tolerable / inconsistent (0 / 1–2 / more than 2 changes) | 26 / 9 / 11 | 38 / 4 / 4 |
| Batch identical, mean over the 45 pairs of processes | 26.0 | 36.5 |
| Batch identical in all ten | 15 | 31 |
| Evidenced bits identical in all ten | 19 | 34 |
| Coin pairs (accepted in some processes, rejected in others) | 155 | 65 |
| Point changes (Ação × pair of processes) | 366 | 136 |
| Gate accepts per process | 62–78 | 34–45 |
| Gate calls per process | 2 310 | 492–506 |
| Minutes per process | about 41 | 14.5–15.6 |

- **The filter held in production.** In no process was instrument text accepted
  for a non-exempt product, and no instrument neighbour was gated.
- **The projection held.** The batch identical in all ten was projected at 30
  and measured at 31; the evidenced bits at 32 and 34. The criterion of the
  user was projected between 30 and 41 and measured at 41.
- **The 17 pairs never judged before** did not turn into coins: 13 were
  rejected in all ten, 3 accepted in all ten (1a `_1` p.3, 1a `_2` p.156, 4a
  `_1` p.3), and one is a coin (2c `_2` p.156, 2 of 10).
- **The accepted losses** happened as projected: Ação 4 scored 1 in all ten,
  and Ações 15 and 36 scored 0 in all ten. 1c kept its bit through a neighbour
  (`_1` p.3, ten of ten).
- **The cost of the filtered expansion.** Each process gated 28 to 42
  neighbours and accepted 5 to 8 of them; 21 to 34 more were not gated because
  they are instrument text. Without the accepted neighbours, the identical
  batch per pair would be 37.1 instead of 36.5, and the batch identical in all
  ten 32 instead of 31. The difference is Ação 10, and no change of points
  comes from the neighbour there: the scorer varies with it present and absent.
- **Attribution of the 136 point changes:** the gate 98 (72 %), the scorer on
  an identical batch 29 (21 %), the cap of ADR-0070 9 (7 %, Ação 3 through
  Ação 2).
- **Below 9 of 10: Ações 10, 23, 35, 37 and 45.** By class:
  - *Exempt products hesitating on their own target* (23, 37, 45). In Ação 23
    only 23.2 varies: the gate accepts it in 5 of 10 through three different
    pages, and the scorer agrees in 3 of those. Ação 37 has six coin pages,
    among them the edital, the internal conformity attestation and the
    Procuradoria opinion. Ação 45 rests on `_2` p.23, the contract recital that
    the bidding was homologated, accepted in 8 of 10. The exempt Ações (22, 23,
    25, 37, 45) hold 42 of the 65 coins; in 22 and 25 they do not move the
    points.
  - *The scorer on an identical batch* (10). 10a is judged evidenced in 4 of 10
    on `_2` p.763; in cycle 2 the same chunk alone was judged evidenced in 1 of
    8.
  - *One confusion in a document of genre OUTRO* (35). 35.2e accepts the
    justification of the procurement, `_1` p.3, in 5 of 10.
- **Tolerable:** Ações 2 and 3 (one process in which both coins of Ação 2 fell,
  and the cap followed) and 32 (the scorer once on 32a `_1` p.303, the one
  constant false credit of cycle 2 that is not instrument text).
- **The review signal of ADR-0068** fired in at least one process for 6 of the
  8 Ações whose points vary, each time on the highest outcome. The misses are
  Ação 3, whose cap notice shows the cause, and Ação 37, whose accepts vanish
  together.
- **Verdict constancy** is 95.5 %, against 97.9 % in cycle 2. The stable
  rejections of instrument text left the pools, so the remaining verdicts are a
  harder population; the coin count is the comparable figure.
- **Diagnosis of the residue**, from the gate reasoning recorded with every
  verdict:
  - The mechanism is unchanged. Two processes that sent the same prompts in the
    same order and got the same answers so far part at a byte-identical prompt.
    In 44 of the 45 pairs the first difference is in Ação 1 or 2; in 25 pairs
    it is the first coin of the run, 1a `_2` p.157.
  - The coins that move points sit on a boundary the prompt already states:
    whether a passage that carries part of what the criterion asks treats the
    element or only mentions the theme. The rejections read as sufficiency
    judgements (not the whole set, not every step), which the polarity sentence
    of ADR-0066 leaves to the scorer.
  - Wording is not the class. Products whose gate-read texts state sufficiency
    or completeness conditions coin no more than the others: 15.8 % against
    15.8 % of judged pairs among exempt products, 6.2 % against 9.6 % among the
    others.
  - The class that remains is the exempt products, which still read instrument
    text: 15.8 % of their judged pairs are coins, against 8.6 % for the other
    products; 14 of the 17 exempt products have a coin, against 12 of the 76
    other products with a non-empty pool.
  - 35.2e already carries a negative pattern for the justification of the
    procurement, with checkable markers; the gate still accepted `_1` p.3 in 5
    of 10 processes. 23.3 has no negative pattern: its constant accept of
    `_2` p.145 reads the grant fee that the concessionaire pays to the Poder
    Concedente as a rule for paying the contractor, and it is what lets the
    coin of 23.2 lift Ação 23 to 3. 32a accepts in all ten the operating staff
    costs of the concession (`_1` p.303) as the cost of the project team.

## Decisions after cycle 3 (2026-10-13)

The user accepted the four recommendations of the cycle-3 report.

- **Exempt products take no instrument neighbours** (point 5). The code
  already behaves this way; nothing changes.
- **Ações 3, 10, 37 and 45 stay as documented residue**, with no per-product
  change. Ações 10 and 45 are flagged by the review signal of ADR-0068 when
  they sit at their highest outcome, and Ação 3 by the notice of the cap of
  ADR-0070. Ação 37 is not flagged, because its accepts vanish together; this
  is a known gap of the signal, recorded here, not widened.
- **23.3 and 32a get canonical negative patterns, measured before they are
  written.** First the direction inside one process (the target and the rest of
  the examined pool of each product), then ten full processes, ledger off,
  with the patterns applied in memory. A pattern is written only if constancy
  does not fall: a pattern can turn a constant accept into a coin, and the
  constant false credit of 23.3 is what lets the coin of 23.2 lift Ação 23 to 3.
- **35.2e stays as it is.** Its negative pattern already names the class of
  `_1` p.3 with checkable markers; another round is the decision of the user.
- **The state measured in cycle 3 is committed as the baseline** of the next
  measurements.
