# Assessment scope derived from IPMPStore, not hardcoded

The orchestration service determines which Ações to evaluate by iterating the Ações present in the loaded `IPMPStore` (`get_ipmp_store()`), not from a hardcoded list inside orchestration logic:

```python
for acao in get_ipmp_store().acoes:
    result = evaluate(acao.acao_id, process_number, chunks)
    ...
```

Adding a new source-of-truth artifact (e.g., `data/ipmp/acao_02.json`) expands the assessment scope automatically at the next service restart, with no orchestration code change. This is consistent with the progressive enrichment principle established in Module 1 (ADR implicit) and the single-source-of-truth ownership of IPMP data by the ingestion module.

## Scope vs. aggregation

This decision resolves **assessment scope** only — which Ações are evaluated in a single assessment run.

It does not resolve:
- How Final Scores are aggregated across Ações
- Dimensional scoring (per-Dimensão rollups)
- Overall maturity computation or reporting

Those concerns are deferred to a future architectural decision. No aggregation, dimensional scoring, or maturity reporting logic should be introduced into Module 5 orchestration on the basis of this ADR.

## Consequences

- `run_assessment()` is decoupled from knowledge of which specific Ações exist. It operates on whatever the ingestion module exposes.
- A malformed or missing IPMP artifact reduces scope silently (Module 1's operational continuity — ADR-0010 equivalent — applies upstream).
- The orchestration service makes one `evaluate()` call per Ação in the store, in store-iteration order. Ordering of returned `list[EvaluationResult]` follows store order.

## Considered options

- **Hardcoded `acao_ids = [1]`:** Explicit and simple in Phase 1. Rejected: creates a code-change dependency every time a new Ação source-of-truth artifact is defined, contradicting Module 1's progressive enrichment design.
