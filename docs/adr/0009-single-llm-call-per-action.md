# One LLM call per action, not one call per sub-item

IPMP scoring rubrics and scored examples are defined at the action level — they describe how a full set of documents looks at each score level (0/1/3), not how individual sub-items score in isolation. Splitting evaluation by sub-item would require an aggregation rule (sum, average, rule-based) that does not exist in the IPMP and would sometimes contradict expert human judgement. A single LLM call receives all retrieved chunks from all sub-item queries, the full action criteria, and the three IPMP scored examples, and produces one score. The LLM's reasoning can still address each sub-item explicitly (for auditor traceability) before concluding with the single score.

**Considered Options:** per-sub-item calls with aggregation — rejected because aggregation logic is not grounded in the IPMP framework and introduces a second source of scoring bias.
