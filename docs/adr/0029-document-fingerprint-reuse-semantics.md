# Document fingerprint-based extraction reuse and replacement semantics

Document identity within a Case is defined by the SHA-256 hash of the uploaded PDF bytes. The assessment module persists one fingerprint per `(process_number, filename)` pair in a `document_fingerprints` table (Module 5-owned under ADR-0024).

## Reuse/replacement decision at assessment time

When `run_assessment(process_number, document_paths)` is called with uploaded PDFs:

1. Compute SHA-256 for each uploaded file.
2. For each `(process_number, filename)`, look up the stored fingerprint.
3. **Fingerprint matches for all files:** skip Extract + Index; use existing chunks.
4. **Any fingerprint differs (or no prior fingerprint exists):** treat the upload as a replacement corpus for that file — delete existing chunks for `(process_number, filename)`, re-extract, re-index, update stored fingerprint.

Replacement is per-file, not per-Case: unchanged files within the same Case are reused even when some files are replaced.

## Why fingerprints, not INSERT OR IGNORE

`INSERT OR IGNORE` on the chunks table silently preserves stale chunks when a file is re-uploaded with different content but the same filename. This produces a provenance mismatch: the indexed text no longer corresponds to the uploaded document. Fingerprint comparison makes the staleness visible and forces explicit replacement.

## Table ownership and schema (Module 5)

```sql
CREATE TABLE IF NOT EXISTS document_fingerprints (
    process_number TEXT    NOT NULL,
    filename       TEXT    NOT NULL,
    sha256         TEXT    NOT NULL,
    indexed_at     TEXT    NOT NULL,   -- ISO-8601 UTC timestamp
    PRIMARY KEY (process_number, filename)
);
```

This table lives in the shared SQLite database (ADR-0024) and is owned by Module 5. The retrieval module must not read or write it.

## What "stale" means

Indexed artifacts for a `(process_number, filename)` pair are considered stale when the SHA-256 of a newly uploaded file for that filename differs from the stored fingerprint. Staleness is always resolved by explicit replacement, never by accumulation.

## Consequences

- Reuse is safe: identical fingerprints guarantee the indexed text is byte-for-byte identical to the current upload.
- Replacement is explicit: changed files trigger a deterministic DELETE + re-extract + re-index sequence.
- No file-size heuristics, no timestamp comparisons, no reliance on INSERT OR IGNORE for synchronisation.
- Partial replacement is supported: a Case with three Document Artifacts can replace one without disturbing the other two.

## Considered options

- **Unconditional re-extraction:** Always re-extract and re-index on every assessment call. Rejected: wasteful when documents are unchanged; does not prevent INSERT OR IGNORE accumulation without additional cleanup logic.
- **File-size heuristic:** Use file size as a proxy for identity. Rejected: two files with identical size but different content would incorrectly trigger reuse.
- **INSERT OR IGNORE as sync mechanism:** Rely on the uniqueness constraint `(process_number, filename, page_number, chunk_index)` to prevent duplicates. Rejected: preserves stale chunks from a prior upload without surfacing the mismatch.
