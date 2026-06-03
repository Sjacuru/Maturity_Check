# EvaluationResult serialised directly as Phase 1 HTTP response

GET routes returning evaluation data (`GET /cases/{process_number}/evaluations` and `GET /cases/{process_number}/evaluations/{acao_id}`) serialise `EvaluationResult` directly via `.model_dump()`. No shaped response DTO is introduced.

`EvaluationResult` is treated as both the Module 4 domain contract and the Phase 1 HTTP response contract. All fields are exposed: `retrieved_chunks` (full `RetrievedChunk` serialisation), `system_prompt`, `user_prompt`, `raw_llm_response`, `reasoning`, status flags, provenance metadata. Nothing is filtered or renamed at the HTTP boundary.

`api/schemas.py` is reserved for write-side concerns: review submission request bodies, transport-specific validation payloads. It must not contain parallel read-response DTOs that duplicate `EvaluationResult` fields.

## Consequences

- The 7 Auditor review elements (IPMP criteria, retrieval query, chunks, prompts, reasoning, uncertainty flag, proposed score) are all present in the serialised `EvaluationResult` without a mapping layer.
- If `EvaluationResult` adds or removes fields in a future module revision, the HTTP response changes automatically. This is acceptable while there is no external API consumer with a versioning requirement.
- Response shaping (field selection, renaming, embedding IPMP display text alongside the result) may be introduced later if a frontend, external integration, or API versioning requirement emerges.

## Considered options

- **Separate shaped response model in `api/schemas.py`:** Explicit HTTP contract decoupled from the domain model. Rejected for Phase 1: no demonstrated mismatch between the domain model and what HTTP consumers need; adds a translation layer with no benefit in a single-developer, single-consumer context.
