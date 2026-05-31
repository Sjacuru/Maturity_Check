# Two-stage per-page extraction: native text first, OCR as primary pipeline stage

PPP procurement documents include image-only PDFs (fully scanned), mixed PDFs where some pages have embedded text and others have only images, and digitally-created PDFs with native text. Treating OCR purely as an error-recovery mechanism would silently drop valid content from entire scanned documents. The extraction module applies two stages per page: (1) attempt native text extraction; (2) if the result contains insufficient readable text, automatically apply OCR. Both paths are normal operation — OCR is a primary pipeline stage, not an exception handler.

## Considered Options

- **OCR as exceptional fallback only**: simpler stack, but silently produces empty Chunks for image-only pages and entire scanned documents — unacceptable given the expected document corpus.
- **OCR-only (skip native text)**: consistent path but discards higher-quality native text when it exists, and is slower.
- **Two-stage per page** ← chosen: native text when available (faster, higher fidelity), OCR when necessary. Both paths produce valid Chunks with accurate `ocr_used` and `source_type` metadata.

## Consequences

`unstructured[pdf]` must be configured to support both native-text extraction and OCR (Tesseract or equivalent). The `ocr_used` and `source_type` fields in the Chunk metadata model preserve operational provenance for debugging and future OCR quality analysis. OCR adds processing time and an OCR engine dependency to the stack; this is an accepted Phase 1 cost. Page-level failures (both stages fail) are non-fatal: structured log entry, skip page, continue extraction. Fatal errors (file not found, unreadable file, invalid PDF, unrecoverable parser failure) terminate immediately.
