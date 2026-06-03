# Extracted artifacts as canonical persisted document representation

Uploaded PDFs are transient upload artifacts. The canonical persisted document representation in Phase 1 is the set of extracted chunks stored in the retrieval module's `chunks` SQLite table (one row per Chunk, carrying `filename`, `page_number`, `chunk_index`, `char_offset`, `text`, `text_length`, `page_total`, `ocr_used`, `source_type`). PDFs are discarded after extraction completes.

The per-document orchestration pipeline is therefore:

```
Upload PDF (transient)
↓
Extract  →  list[Chunk]
↓
Index    →  chunks table (canonical, persistent)
↓
Discard PDF
↓
Retrieve →  list[RetrievedChunk]
↓
Evaluate →  EvaluationResult
```

Re-runs (within the replacement model defined in ADR-0026) proceed from the already-indexed chunks table:

```
Retrieve →  list[RetrievedChunk]   (from existing chunks rows)
↓
Evaluate →  EvaluationResult       (replaces prior result)
```

Re-upload of source PDFs is not required for a re-run. Extraction replay is not supported in Phase 1; if chunks for a Case are lost (e.g., database corruption), the Auditor must re-upload the source PDFs to regenerate them.

The orchestration service must detect at assessment time whether chunks are already indexed for a given `process_number`:
- If not indexed: full pipeline (Upload → Extract → Index → Retrieve → Evaluate → discard PDF).
- If indexed: Retrieve → Evaluate only, using existing chunks.

## Consequences

- No PDF storage directory is required in Phase 1. The assessment API accepts uploads as a transient I/O mechanism, not a storage operation.
- The retrieval module's `chunks` table gains a load-bearing role beyond BM25 search: it is the durable document archive. This does not change any existing retrieval module code — `index()` already provides idempotent `INSERT OR IGNORE` semantics.
- Chunk extraction parameters (word-count heuristic, OCR settings) are fixed at index time. Changing extraction behaviour requires re-upload and re-indexing.
- If the SQLite database is rebuilt from scratch, all extraction history is lost and re-upload is required for every Case.

## Considered options

- **Persistent PDF storage:** Keep uploaded PDFs at `data/cases/{process_number}/{filename}.pdf`. Enables extraction replay and direct PDF access. Rejected for Phase 1: the chunks table already captures the full text and provenance needed for all Phase 1 workflows; PDF storage adds disk management with no demonstrated benefit.
- **Ephemeral temp directory (no persistence):** Discard PDFs and rely on in-memory chunks for the current request only. Rejected: re-runs under ADR-0026 require chunks to persist across sessions.
