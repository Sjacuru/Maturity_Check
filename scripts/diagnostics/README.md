# scripts/diagnostics/

Repeatable measurements for the retrieval + gate + scorer pipeline.

These exist because the verification tooling from the 2026-09 investigation
passes was written into an untracked `scratchpad/` directory and was lost — all
17 scripts CLAUDE.md references are gone from disk. Anything whose result is
quoted in CLAUDE.md or an ADR belongs **here**, tracked, not in scratchpad.

## Offline (no GPU, no LLM call)

| script | answers |
|---|---|
| `measure_profile_coverage.py` | Does every scored IPMP product have a profile product with an active query term? What fraction of active query terms actually occur in the indexed corpus? |
| `measure_retrieval_lanes.py` | For each product: how many BM25 hits vs vector hits, how much the two lanes overlap, what the gated top-N is made of, and which chunks are retrieval hubs. |
| `measure_embedding_window.py` | How much of each chunk and each vector query the embedding model actually sees before truncation. |

Run with the `rel_voto` env; they read `data/app.db` and `data/lancedb`
directly and never call an LLM:

    python scripts/diagnostics/measure_profile_coverage.py --process SMG-040_101607_2024

## Requires the canonical GPU machine

| script | answers |
|---|---|
| `reproducibility.py` | Across N full runs of the same case, how often does each Ação produce the same score and the same accepted-evidence set? |

`reproducibility.py` is the acceptance test for the stabilisation work: the
target is >=90% modal agreement per Ação across 10 runs. It calls the real
pipeline (`_retrieve_and_select` + `evaluate`) but deliberately does **not**
persist, so a measurement run never clobbers `evaluation_results`.
