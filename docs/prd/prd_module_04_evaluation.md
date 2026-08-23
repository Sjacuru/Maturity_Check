# PRD — Module 4: LLM Evaluation

**Status:** Ready for implementation
**Date:** 2026-06-01
**ADRs in scope:** 0001, 0004, 0005, 0008, 0009, 0019, 0020, 0021

---

## Problem Statement

The system has, for each Ação/Case pair, a list of `RetrievedChunk` objects carrying potential
evidence from case documents. Before the Auditor can validate a Maturity Score, an LLM must compare
that evidence against the IPMP rubric — criteria, expected products, scored examples, and exceptions
— and propose a score of 0, 1, or 3 with supporting reasoning. The challenge is to make this
evaluation reproducible (same input → same output), provider-agnostic (Ollama local or Groq cloud),
and fully auditable: every evaluation must carry the complete trail needed to answer "why did the
system propose this score?" without referring to any external data source at review time.

---

## Solution

Build the evaluation module (`src/evaluation/`) as a Python package with four sub-packages:
`llm/` (provider abstraction: `LLMClient` protocol, `OllamaClient`, `GroqClient`), `prompt/`
(prompt assembly from IPMP data and retrieved chunks), `parsing/` (sentinel-line response parsing
and status flag derivation), and `interfaces/` (`EvaluationResult` contract). The module exposes
two operations: `configure_llm()` (provider/model initialisation, mirrors Module 3's `configure()`)
and `evaluate()` (full evaluation flow returning `EvaluationResult`). The module receives a
pre-computed `list[RetrievedChunk]` — it never calls the retrieval module. All LLM interaction uses
temperature=0 (ADR-0004) and a single call per Ação (ADR-0009).

---

## User Stories

### `EvaluationResult` contract

1. As a developer, I want `EvaluationResult` to be a Pydantic `BaseModel` defined in
   `src/evaluation/interfaces/contracts.py`, so that field validation occurs at construction time
   and the model serves as a stable typed boundary between Module 4 and Module 5, consistent with
   `Chunk` and `RetrievedChunk` in earlier modules.

2. As a developer, I want `EvaluationResult` to carry identity fields `acao_id: int` and
   `process_number: str`, so that every evaluation artifact is unambiguously tied to the
   Ação/Case pair it represents without requiring the caller to supply context externally.

3. As a developer, I want `EvaluationResult` to carry `provider: str` and `model: str` recording
   the effective LLM used, so that the exact provider/model pair is part of the forensic record
   and future reproductions can use the same configuration (ADR-0021).

4. As a developer, I want `EvaluationResult` to carry `retrieved_chunks: list[RetrievedChunk]`
   verbatim — the full list passed to `evaluate()` — so that the Auditor review interface can
   display the exact evidence the LLM received without querying the retrieval layer.

5. As a developer, I want `EvaluationResult` to carry `evidence_char_count: int` — the total
   character length of the evidence section embedded in the user prompt — so that prompt budget
   monitoring and future architecture decisions are informed by real measured values (ADR-0019).

6. As a developer, I want `EvaluationResult` to carry `system_prompt: str | None` and
   `user_prompt: str | None` as separate fields — both `None` when `no_evidence_found` is `True`
   — so that the Auditor can inspect each prompt section independently and the architecturally
   significant system/user boundary remains visible in the audit trail (ADR-0020).

7. As a developer, I want `EvaluationResult` to carry `raw_llm_response: str | None` — the full
   unmodified string returned by the LLM; `None` when `no_evidence_found` is `True` — so that
   when `parse_failed` is `True` the Auditor has the complete LLM output available for manual
   inspection.

8. As a developer, I want `EvaluationResult` to carry `reasoning: str | None` — the text
   appearing before the sentinel block in the LLM response; `None` when `no_evidence_found` or
   `parse_failed` is `True` — so that the Auditor review interface can display the LLM's reasoning
   independently of the parsed score.

9. As a developer, I want `EvaluationResult` to carry `proposed_score: int | None` — exactly 0,
   1, or 3; `None` when `no_evidence_found` or `parse_failed` is `True` — so that downstream
   modules and the Auditor always receive a typed, validated score value and never need to parse
   the LLM response themselves.

10. As a developer, I want `EvaluationResult` to carry three orthogonal boolean status flags —
    `uncertainty_flag`, `parse_failed`, `no_evidence_found` — so that the Auditor interface can
    render a precise, condition-specific explanation for each state rather than a generic error
    message (ADR-0020).

### LLM client abstraction

11. As a developer, I want a `LLMClient` Protocol defined in `src/evaluation/llm/protocol.py`
    with a single method `complete(self, system: str, user: str) -> str`, so that all prompt
    construction, response parsing, and `EvaluationResult` creation are completely provider-agnostic
    and the rest of the module interacts only with this interface (ADR-0021).

12. As a developer, I want an `OllamaClient` implementation of `LLMClient` in
    `src/evaluation/llm/ollama.py` that calls the Ollama HTTP API with `temperature=0`, so that
    local Mistral (or any Ollama-compatible model) can be used as the default LLM provider without
    requiring a cloud API key (ADR-0004).

13. As a developer, I want a `GroqClient` implementation of `LLMClient` in
    `src/evaluation/llm/groq.py` that calls the Groq API with `temperature=0`, so that a
    cloud-based LLM can be used as an alternative provider with no code changes to the evaluation
    flow (ADR-0004, ADR-0021).

14. As a developer, I want `configure_llm(provider: str, model: str, base_url: str | None = None)`
    to instantiate the correct `LLMClient` implementation and store it at module level, so that
    callers use the same initialisation pattern as Module 3's `configure(db_path)` and never
    construct LLM clients directly (ADR-0021).

15. As a developer, I want `configure_llm()` to accept a `base_url` parameter for Ollama, so that
    non-default Ollama endpoints (e.g., remote or containerised instances) are supported without
    code changes.

16. As a developer, I want `configure_llm()` to raise an explicit exception if `provider` is not
    one of the supported values (`"ollama"`, `"groq"`), so that misconfiguration is detected at
    startup rather than at evaluation time.

### Prompt builder

17. As a developer, I want `build_system_prompt(acao_id: int) -> str` in `src/evaluation/prompt/`
    to assemble the system prompt from IPMP data via `get_ipmp_store()`, so that the rubric is
    always derived from the canonical source-of-truth artifact and never hard-coded.

18. As a developer, I want the system prompt to contain, in order: (1) role and task statement,
    (2) Ação title and `descricao_acao`, (3) `o_que_esperar`, (4) `produtos_esperados` (all items
    including parent), (5) scored examples from `exemplos` explicitly framed as illustrative,
    (6) `excecoes`, (7) scoring instruction with sentinel format, uncertainty criterion, and
    evidence-handling rules, so that the LLM has the complete evaluation framework before
    seeing the case evidence.

19. As a developer, I want the scored examples (`exemplos`) to be introduced with explicit
    framing such as "Os exemplos abaixo ilustram os níveis de pontuação em um contexto específico;
    aplique os mesmos critérios ao processo avaliado, independente do setor ou domínio", so that
    the LLM treats them as calibration anchors and not as domain requirements to match literally.

20. As a developer, I want the scoring instruction section of the system prompt to define the
    sentinel format explicitly — `SCORE: <0, 1 ou 3>` and `UNCERTAINTY: <yes ou no>` as the
    final two lines of every response — so that response parsing is deterministic and does not
    depend on natural-language interpretation of the LLM's output (ADR-0020).

21. As a developer, I want the scoring instruction to define `UNCERTAINTY: yes` as the signal
    for when the retrieved evidence does not allow confident assessment of one or more Expected
    Products (`1a`, `1b`, `1c`, `1d`), so that the uncertainty flag has a deterministic, auditable
    criterion rather than reflecting general model hesitation (ADR-0020).

22. As a developer, I want the scoring instruction to tell the LLM how to handle OCR noise (treat
    garbled text as unreliable evidence, do not score positively on the basis of it alone) and
    partial evidence (score `1` when some but not all Expected Products are evidenced), so that
    evaluation quality is controlled by the prompt rather than by undocumented model behaviour.

23. As a developer, I want `build_user_prompt(chunks: list[RetrievedChunk]) -> str` to assemble
    one evidence block per chunk — showing `filename`, `page_number`, and `text` — followed by a
    summary line showing the total chunk count and total character count, so that the Auditor can
    trace every piece of evidence to its source document and page without navigating outside the
    `EvaluationResult`.

24. As a developer, I want evidence chunks in the user prompt to appear in deterministic order:
    `filename_match` first, then `variant_match`, then `bm25` (ordered by `bm25_score` descending,
    then `rank` ascending, then `chunk_index` ascending), then `regex`; within each non-BM25 step
    by `filename` ascending, `page_number` ascending, `chunk_index` ascending, so that the same
    `list[RetrievedChunk]` always produces the same prompt and evaluation is reproducible (ADR-0019).

### Response parser

25. As a developer, I want `parse_llm_response(raw: str)` in `src/evaluation/parsing/` to extract
    the sentinel block from the end of the LLM response using regex, parse `proposed_score` as an
    integer and `uncertainty_flag` as a boolean, and return `reasoning` as all text before the
    sentinel block, so that the three structured outputs are separated cleanly from the free-text
    reasoning.

26. As a developer, I want `parse_llm_response()` to set `parse_failed=True` and return
    `proposed_score=None` and `reasoning=None` when the sentinel block is missing, malformed, or
    the parsed score is not in `{0, 1, 3}`, so that format compliance failures are represented in
    the `EvaluationResult` as a named state rather than raising an exception that would halt a
    batch run (ADR-0020).

27. As a developer, I want `parse_llm_response()` to always return `raw_llm_response` unchanged,
    so that `EvaluationResult` always carries the complete unmodified LLM output for audit
    purposes regardless of whether parsing succeeded.

### `evaluate()` orchestration

28. As a developer, I want `evaluate(acao_id: int, process_number: str, chunks: list[RetrievedChunk]) -> EvaluationResult`
    to be the sole evaluation entry point, so that downstream modules (Module 5, CLI runner) have
    a single, typed function to call and are isolated from the internal prompt/parse/client
    sub-package layout.

29. As a developer, I want `evaluate()` to short-circuit when `chunks` is empty — setting
    `no_evidence_found=True`, `proposed_score=None`, `reasoning=None`, `system_prompt=None`,
    `user_prompt=None`, `raw_llm_response=None`, `uncertainty_flag=False`, `parse_failed=False`
    — without calling the LLM, so that cases with no retrieved evidence are represented as a
    distinct named state that the Auditor interface can explain specifically.

30. As a developer, I want `evaluate()` to log the evidence section character count at `INFO` level
    on every evaluation and emit a `WARNING` log when that count exceeds a named constant
    (`EVIDENCE_CHAR_WARN_THRESHOLD`), so that prompt budget monitoring data accumulates passively
    and can justify future architectural changes without requiring a separate telemetry pipeline
    (ADR-0019).

31. As a developer, I want `evaluate()` to populate `provider` and `model` in `EvaluationResult`
    from the effective pair stored by `configure_llm()`, so that every result carries its own
    reproducibility metadata and the Auditor never needs to query module configuration to
    understand what LLM produced a score (ADR-0021).

32. As a developer, I want `evaluate()` to raise an explicit exception if `configure_llm()` has
    not been called, so that missing initialisation is detected at the first evaluation call
    rather than silently producing results with an unknown provider.

33. As a developer, I want `evaluate()` to raise an explicit exception if `acao_id` is not present
    in the loaded `IPMPStore`, so that a missing Ação configuration is surfaced immediately rather
    than producing a prompt with empty rubric sections.

34. As a developer, I want `evaluate()` not to raise when the LLM call succeeds but the response
    cannot be parsed — instead reflecting the failure in `parse_failed=True` — so that a single
    non-conforming LLM response does not abort evaluation of a full Case.

### Module interfaces

35. As a developer, I want `from evaluation import configure_llm, evaluate, EvaluationResult` to
    be the complete public surface of the module, so that downstream packages are isolated from
    internal sub-package layout changes, consistent with Modules 1–3.

36. As a developer, I want `evaluate()` to consume IPMP data only via `get_ipmp_store()` from
    the ingestion module and never read `data/ipmp/` directly, so that the ingestion module
    remains the single owner of source-of-truth artifact loading.

---

## Implementation Decisions

### Module layout

```
src/evaluation/
    __init__.py          ← sole public surface: configure_llm, evaluate, EvaluationResult
    _config.py           ← module-level LLMClient storage: configure_llm() / get_llm_client()
    interfaces/
        __init__.py
        contracts.py     ← EvaluationResult Pydantic model
    llm/
        __init__.py
        protocol.py      ← LLMClient Protocol (complete(system, user) -> str)
        ollama.py        ← OllamaClient: calls Ollama HTTP API, temperature=0
        groq.py          ← GroqClient: calls Groq API, temperature=0
    prompt/
        __init__.py
        builder.py       ← build_system_prompt(acao_id), build_user_prompt(chunks)
    parsing/
        __init__.py
        response.py      ← parse_llm_response(raw) -> ParsedResponse dataclass
    evaluator.py         ← evaluate(): orchestration — prompt → LLM → parse → EvaluationResult
```

### Public interface

```python
from evaluation import configure_llm, evaluate, EvaluationResult

configure_llm(provider: str, model: str, base_url: str | None = None) -> None
evaluate(acao_id: int, process_number: str, chunks: list[RetrievedChunk]) -> EvaluationResult
```

`RetrievedChunk` is imported from `src/retrieval/`. No other symbols are re-exported. Downstream
packages must never import from `evaluation.prompt`, `evaluation.parsing`, or `evaluation.llm`
directly.

### `EvaluationResult` model

Fields decided in grill-me session (2026-05-30 / 2026-06-01):

```python
class EvaluationResult(BaseModel):
    acao_id: int
    process_number: str
    provider: str
    model: str
    retrieved_chunks: list[RetrievedChunk]
    evidence_char_count: int
    system_prompt: str | None
    user_prompt: str | None
    raw_llm_response: str | None
    reasoning: str | None
    proposed_score: int | None       # 0, 1, or 3 only
    uncertainty_flag: bool
    parse_failed: bool
    no_evidence_found: bool
```

### Status flag invariants

- `no_evidence_found=True` implies `system_prompt=None`, `user_prompt=None`,
  `raw_llm_response=None`, `reasoning=None`, `proposed_score=None`,
  `uncertainty_flag=False`, `parse_failed=False`.
- `parse_failed=True` implies `reasoning=None`, `proposed_score=None`.
- `uncertainty_flag=True` is compatible with a valid `proposed_score` — the LLM scored and flagged
  doubt; the Auditor decides whether to accept.
- All three flags may be `False` simultaneously (normal successful evaluation).

### Sentinel output format

The scoring instruction in the system prompt requires the LLM to conclude every response with
exactly two lines, with no text after them:

```
SCORE: <0, 1 ou 3>
UNCERTAINTY: <yes ou no>
```

The parser uses regex to locate this block at the end of the response. `reasoning` is all text
before the sentinel block, with trailing whitespace stripped. Anything that does not match sets
`parse_failed=True`.

### Uncertainty criterion

The scoring instruction defines `UNCERTAINTY: yes` as: the retrieved evidence does not allow
confident assessment of one or more Expected Products (`1a`, `1b`, `1c`, `1d`). This criterion
is deterministic — it does not depend on model-specific confidence language or probability outputs.

### Evidence ordering (deterministic, from ADR-0019)

Chunks sorted before embedding in the user prompt:
1. `cascade_step` position: `filename_match` (1) → `variant_match` (2) → `bm25` (3) → `regex` (4)
2. Within `bm25`: `bm25_score` descending → `rank` ascending → `chunk_index` ascending
3. Within all other steps: `filename` ascending → `page_number` ascending → `chunk_index` ascending

### LLM client initialisation

`configure_llm()` stores the effective client and records `provider` and `model` at the module
level. Both `OllamaClient` and `GroqClient` are instantiated with the same interface;
`evaluate()` calls `client.complete(system_prompt, user_prompt)` and receives a raw `str`. No
streaming, no multi-turn, no tool calling. Temperature=0 is set inside the client, not passed by
the caller (ADR-0004).

### Prompt budget observability

`EVIDENCE_CHAR_WARN_THRESHOLD` is a named constant (initial value: 15,000 chars). `evaluate()`
logs `evidence_char_count` at `INFO` level on every call and emits `WARNING` when the threshold
is exceeded. This telemetry drives future decisions about whether a tighter `MAX_CHUNKS_PER_ACAO`
in Module 3 or an evidence-selection stage in Module 4 is warranted (ADR-0019).

### Module boundaries

**Owns:** `EvaluationResult` construction, system/user prompt assembly, LLM call lifecycle,
response parsing, sentinel extraction, status flag derivation, `configure_llm()` initialisation,
evidence ordering, `EVIDENCE_CHAR_WARN_THRESHOLD` constant.

**Does not own:** retrieval logic, SQLite access, IPMP/Rio Manual loading, Auditor interface
rendering, score persistence, vector embeddings.

**Consumes from other modules:**
- `from retrieval import RetrievedChunk` — input type for `evaluate()`
- `from ingestion import get_ipmp_store` — IPMP rubric, scored examples, expected products

---

## Testing Decisions

**What makes a good test for this module:** tests must verify behaviour observable through the
public interface (`configure_llm()`, `evaluate()`, and `EvaluationResult` fields). Tests must not
assert on internal prompt string contents, specific regex patterns used in parsing, or which
internal sub-module was invoked. A test must verify that the correct `proposed_score`,
`uncertainty_flag`, and `parse_failed` values appear in the returned `EvaluationResult`, not that
a specific HTTP call was made.

**What is tested:**

- **Unit tests — `EvaluationResult` model:** Pydantic validation for each field; construction with
  all fields valid; invariant enforcement for status flag combinations (e.g., `no_evidence_found=True`
  requires `proposed_score=None`); `proposed_score` rejects values outside `{0, 1, 3}` or `None`.
  Fast, no LLM required.

- **Unit tests — response parser:** Given raw LLM response strings covering: well-formed
  `SCORE: 0/1/3` + `UNCERTAINTY: yes/no`; missing `SCORE:` line; invalid score value (e.g., `2`);
  `SCORE:` present but followed by extra text; empty string. Assert correct `proposed_score`,
  `uncertainty_flag`, `parse_failed`, and `reasoning` values for each case. Fast, no LLM required.

- **Unit tests — prompt builder:** Given a known `AcaoIPMP` and a small synthetic
  `list[RetrievedChunk]`, assert: system prompt contains `descricao_acao` and the three scored
  example level labels; user prompt contains expected evidence blocks; evidence blocks appear in
  deterministic cascade-step order; empty chunk list produces an appropriate user prompt (handled
  by the `no_evidence_found` short-circuit upstream, so builder receives non-empty list).

- **Integration tests — `evaluate()` with stub `LLMClient`:** Use a `StubLLMClient` that returns
  a controlled string. Index a synthetic chunk set and call `evaluate()`. Assert:
  - Well-formed stub response → correct `proposed_score`, `reasoning`, `uncertainty_flag`
  - `parse_failed=True` response → `proposed_score=None`, `reasoning=None`, `parse_failed=True`
  - `UNCERTAINTY: yes` response → `uncertainty_flag=True`, `proposed_score` still set
  - Empty `chunks` list → `no_evidence_found=True`, LLM not called (verify stub call count=0)
  - `evidence_char_count` populated correctly
  - `provider` and `model` match configured values

- **`configure_llm()` unit tests:** Correct provider instantiation; raises on unknown provider;
  `evaluate()` raises if `configure_llm()` not called.

**Prior art:** `tests/test_retrieved_chunk.py` (Module 3) established the Pydantic model validation
test pattern for boundary contracts. `tests/test_bm25_retrieval.py` established the integration
test pattern with controlled fixture inputs. Module 4 integration tests follow the same structure
but substitute a `StubLLMClient` for the SQLite fixture.

**No slow marker needed** for Phase 1 evaluation tests — all tests use stub LLM clients or
pre-constructed inputs; no real LLM calls in the test suite.

---

## Out of Scope

- Dense vector (LanceDB) retrieval fallback — deferred to Module 6 (Phase 2)
- Multi-turn LLM conversations or iterative evidence refinement — single call per Ação (ADR-0009)
- Evidence-selection or filtering stage inside Module 4 — deferred until real evaluation data
  demonstrates a problem (ADR-0019)
- Score persistence to database — Module 5 / Auditor interface concern
- Auditor review interface rendering — Module 5
- Batch evaluation across multiple Cases — Module 5 / orchestration layer
- Token-count-based truncation — not introduced until provider token limits are observed in practice
- Streaming LLM responses — single complete call per Ação (ADR-0009)
- LLM output caching or memoisation — determinism comes from temperature=0, not caching
- Additional LLM provider implementations beyond `OllamaClient` and `GroqClient` — deferred until
  a third materially different provider creates a demonstrated need (ADR-0021)
- Sentence-level evidence attribution within chunks

---

## Further Notes

- **GitHub issues:** Issues for this module start at **#16**. Suggested grouping:
  - **#16** — `EvaluationResult` contract + `configure_llm()` + `LLMClient` protocol
  - **#17** — Prompt builder: `build_system_prompt()` + `build_user_prompt()` + evidence ordering
  - **#18** — Response parser: sentinel extraction, status flag derivation
  - **#19** — `evaluate()` orchestration: full flow, `no_evidence_found` short-circuit, observability
  - **#20** — `OllamaClient` + `GroqClient` concrete implementations

- **`EVIDENCE_CHAR_WARN_THRESHOLD` initial value:** 15,000 chars. Chosen to sit comfortably below
  Mistral 7B's 32K context window after accounting for the system prompt (~3,000–4,000 chars).
  The implementer documents the choice in code alongside the constant.

- **`proposed_score` Pydantic validation:** The field type is `int | None`. The valid set
  `{0, 1, 3}` must be enforced via a Pydantic validator, not just by type annotation, so that
  a parse producing `score=2` raises at construction time rather than propagating silently.

- **`StubLLMClient` for tests:** The implementer may define this in a `tests/` conftest or as a
  lightweight inner class within individual test files. It should not be part of the
  `src/evaluation/` package.

- **Prompt language:** The prompt is written in Portuguese (matching the IPMP source material and
  case documents) except for field labels and sentinel keywords, which use English for
  machine-parseable reliability. The `SCORE:` and `UNCERTAINTY:` sentinel keywords are kept in
  English to reduce the risk of accented-character or encoding issues in the parsed output.

- **No Ollama/Groq credentials in tests:** Tests use `StubLLMClient` exclusively. Actual
  `OllamaClient` and `GroqClient` are tested manually against a running instance; integration
  against a live provider is not part of the automated test suite.

- **Assumptions downstream modules must preserve:**
  1. `evaluate()` is the only evaluation entry point — no direct access to `evaluation.prompt`,
     `evaluation.parsing`, or `evaluation.llm` sub-modules.
  2. `EvaluationResult` may have `proposed_score=None` — Module 5 must handle all three status
     flag states.
  3. `retrieved_chunks` in `EvaluationResult` is the exact list passed to `evaluate()` — Module 5
     must not assume it was filtered or reordered after construction.
  4. `provider` and `model` in `EvaluationResult` are the effective values at evaluation time —
     they are not necessarily the same as the current `configure_llm()` state if reconfigured
     between calls.
