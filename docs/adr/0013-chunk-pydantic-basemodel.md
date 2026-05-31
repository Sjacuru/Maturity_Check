# Chunk modelled as pydantic.BaseModel

The Chunk object is the cross-module contract between the extraction module, the BM25 retrieval layer, the LLM evaluation layer, and the future indexing layer. It carries provenance-sensitive metadata whose fields (`ocr_used`, `source_type`, `page_number`) may be returned as loosely typed values by `unstructured` depending on PDF structure and OCR behaviour. A typed, self-documenting, validated model reduces the risk of silent type mismatches propagating across module boundaries.

Pydantic is already the standard modelling approach in the ingestion layer (`AcaoIPMP`, `AcaoRioManual`). Applying the same pattern to Chunk avoids conceptual fragmentation across modules and provides stable serialisation via `.model_dump()` for the SQLite indexing layer.

## Considered Options

- **`dataclasses.dataclass`**: lighter, faster construction, but no runtime validation; silent type errors from `unstructured` output would reach downstream modules undetected.
- **`typing.TypedDict`**: zero overhead, trivially serialisable, but loses attribute-access ergonomics and construction-time validation entirely.
- **`pydantic.BaseModel`** ← chosen: construction-time validation, consistent with Module 1, stable serialisation, self-documenting schema. Performance is not a concern — extraction is offline, OCR dominates runtime cost, and PPP evaluation is not a high-frequency streaming workload.

## Consequences

The `Chunk` class lives in the extraction module (`src/extraction/`) and is the sole structured type exposed in its public interface. The schema is expected to evolve progressively as the extraction subsystem matures; Pydantic field definitions are the source of truth for schema evolution across modules.
