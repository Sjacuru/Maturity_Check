# POST /assess returns per-document lifecycle metadata

`POST /cases/{process_number}/assess` returns per-document disposition alongside the assessment summary. The module that owns lifecycle decisions reports them; consumers display them, not infer them.

Response shape:
```json
{
  "process_number": "...",
  "acao_ids_assessed": [1],
  "count": 1,
  "documents": [
    {"filename": "EVTEA.pdf", "disposition": "new"},
    {"filename": "DFE.pdf",   "disposition": "reused"},
    {"filename": "EIA.pdf",   "disposition": "replaced"}
  ]
}
```

Disposition values: `"new"` (first-time indexing), `"reused"` (fingerprint match — no re-extraction), `"replaced"` (fingerprint mismatch — stale chunks deleted and re-indexed).

`AssessmentService.run_assessment()` is extended to return `list[tuple[str, str]]` (filename, disposition) alongside `list[EvaluationResult]`, or via a small result dataclass. The route assembles the final response.

**Why:** `AssessmentService._process_file` already computes all three dispositions and currently discards that information. Surfacing it is a minimal backend change that materially improves Auditor understanding of why a particular evaluation result exists.

**Rejected:** Client-side inference from pre/post GET comparisons. Reconstructing authoritative lifecycle events from client-side state diff weakens provenance and creates opportunities for incorrect interpretation.
