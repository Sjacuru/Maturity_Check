# Document Artifact storage layout: process-number-scoped directory, metadata-driven classification

PPP cases arrive with highly heterogeneous document delivery: a single large PDF may contain multiple logical documents mixed together, filenames may be arbitrary or uninformative, and document taxonomy may be incomplete or unknown. The filesystem layout must not attempt to encode semantic document classification — it must only represent Case identity.

Document Artifacts are stored under `data/cases/{process_number}/`, where the `process_number` directory is the sole organisational boundary. The filesystem makes the Case → Document Artifact grouping physically visible and verifiable. No subdirectory hierarchy below `process_number` is used.

Semantic interpretation — document names, suggested classifications derived from IPMP/Rio Manual terminology, contract-related metadata, user annotations — is metadata-driven and belongs to higher layers (SQLite, orchestration), not the filesystem.

## Considered Options

- **Two-level hierarchy (`{process_number}/{contract_number}/`)**: rejected — `contract_number` is optional; many PDFs contain mixed pre-contract and contract material; filesystem hierarchy cannot reliably represent logical document segmentation.
- **Flat unstructured drop zone**: rejected — removes Case grouping from the filesystem, reducing operational traceability and making debugging harder.
- **`{process_number}/` with metadata-driven classification** ← chosen: provenance-first organisation, tolerates arbitrary filenames and heterogeneous delivery, extensible via metadata at higher layers.

## Consequences

The indexing layer attaches semantic metadata (optional user-provided document names, suggested classifications, contract flags, annotations) to Document Artifacts in SQLite, not in the filesystem path. The extraction module receives a `Path` and is unaware of the directory convention — it remains a pure transformation layer. Operators can deliver PDFs with arbitrary filenames; Case identity is determined by directory, not filename.
