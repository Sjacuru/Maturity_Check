# Neighbour expansion off, dedup per Expected Product, evidence budget sized by the GPU slot

Three changes to what reaches the scorer, decided together on 2026-10-06 because
all three decide the batch.

**1. Neighbour expansion is off by default** (`EXPANSION_ENABLED = False`), kept
switchable (`reproducibility.py --expansion`). Expansion gated the previous/next
chunk of each *accepted* chunk, so the list of questions depended on the
answers: a flip on an accept changed which chunks were asked at all, not just
how one was judged. Measured over independent clean passes of the whole case
(gate ledger off, `cache_prompt=false`, one process per pass):

| | expansion on | expansion off |
|---|---|---|
| per-product `n_examined` vector repeats | 26/46 Ações | **46/46, three passes** |
| differing (chunk, product) pairs | 98–101 | 61–74 |
| — of those, neighbours (question depended on a verdict) | 27–37 | **0** |
| gate calls per pass | 2 487–2 534 | 2 321 |
| chunks delivered to the scorer | 117–131 | 83–96 |
| Expected Products whose evidenced bit was lost | — | **none** |

The 45 neighbour chunks it contributed only ever reinforced products already
evidenced by a chunk from their own top-`_MAX_EXAMINED`; no product's bit rested
on one. The positional anchor cap (same session: the gate now walks the whole
examined pool instead of stopping at the 5th accept) is a precondition — without
it, 5–8 of the 164 products reach 5 accepts, in Ações that *change between
passes*, and the 46/46 would fall to roughly 40–42/46.

This removes the cascade, not the ambiguity: the 23 products that used
neighbours were just as unstable without them (100 % of them still varied their
batch across three passes), and 60–70 of the remaining differences are the gate
answering a byte-identical question differently. `_EXPANSION_TARGET` stays at 5;
raising it to 15 is deferred until the scorer's own stability is measured in this
configuration.

**2. The 0.70 semantic dedup is per Expected Product**, not over the whole
Ação's accepted list. It used to drop the later chunk without transferring its
attribution, so a product could lose its only evidence to a similar chunk
accepted by a *different* product — and since the score counts evidenced
products (ADR-0058), that silently turned a bit off. Measured: 39 of 160 accepted
(chunk, product) pairs did not reach the scorer, though no product was left with
nothing in the five passes examined. Each product now compares only against its
own chunks; a chunk leaves the batch only when it is a duplicate for every
product that attributed it. Deliberate consequence: the same text may appear in
two product blocks, which costs evidence budget — bounded by (3).

**3. `_MAX_EVIDENCE_CHARS` 40 000 → 70 000**, warn 30 000 → 55 000, re-measured
with the server's own tokenizer now that the prompts carry the sibling contrast
(ADR-0064), the polarity sentence (ADR-0066) and `_MAX_EXAMINED = 16`. Per-slot
`n_ctx` is 32 000 (4 slots). At the worst Ação (31, nine products, so the most
block overhead): 40 000 chars = 15 717 prompt tokens, 60 000 = 21 842, 70 000 =
25 406, 80 000 = 28 727, 90 000 = 31 473, 100 000 overflows. The scorer's output
measured 988–1 649 tokens over ten real calls and it has no `max_tokens`, so
70 000 leaves 6 594 tokens — about 4× the worst observed — where 80 000 would
leave 2×. The largest real evidence set over five full passes is 33 891 chars
(Ação 4), so the cap is a safety net, not a working limit.

**And when it fires, truncation is round-robin over Expected Products**: every
product keeps its best chunk before any product keeps a second. The score is a
count over products, so dropping a product's only chunk changes the score while
dropping its third usually does not. The previous rule sorted by
`_CASCADE_PRIORITY`, which put `vector` last — a leftover from when vector was a
fallback, which ADR-0049 made co-equal to BM25; with the fused RRF order already
encoded in the list, a lane is not a priority signal.

Reproducibility is untouched by all three: retrieval is deterministic, the
examined set is now a function of retrieval alone, and both dedup and truncation
are deterministic functions of the batch.
