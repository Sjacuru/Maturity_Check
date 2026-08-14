# Grammar-constrained JSON output for both LLM interaction points

**Status:** accepted — supersedes ADR-0020's rejection of "Provider JSON mode"

Both LLM calls in Module 4 — the relevance gate and the final scorer — now request
structured JSON output via each provider's schema/grammar-constrained decoding
(`response_format: json_schema` on Groq, `format: <schema>` on Ollama), instead of
free text with a regex-parsed sentinel block (`SCORE:`/`UNCERTAINTY:` for the
scorer, `RELEVANT: yes|no` for the gate). The scorer's Groq model changes from
`llama-3.3-70b-versatile` to `openai/gpt-oss-20b`.

## Why

ADR-0020 rejected provider JSON mode with the reasoning: "JSON mode behavior
varies across Ollama and Groq; sentinel parsing works identically on any
text-completion endpoint with no provider dependency." That was correct for the
*basic* JSON mode available at the time. Schema/grammar-constrained structured
output (not just "valid JSON," but JSON matching an exact schema, enforced at
the token-sampling level) is now available on both providers and was tested
empirically against real production prompts (the exact system/user prompt pair
from a real Ação 1 assessment, reused byte-for-byte across all trials):

**Scorer, free-text sentinel format, 30 calls across multiple batches**
(external llama.cpp test server, `gpt-oss-20b`, before the model/provider
question was settled): 25/30 valid (83%), 5/30 parse failures (17%). Failure
modes were inconsistent: one was a 174.5s/23,230-character runaway generation
that never reached a final answer; four failed at normal length/timing with no
sentinel block at all — no pattern tied to any tested variable (interleaving
gate calls before the scorer call was tested and ruled out as a cause).

**Scorer, grammar-constrained JSON schema** (`{reasoning: string, score:
integer enum [0,1,3], uncertainty: boolean}`): 5/5 valid (100%) in initial
testing, notably faster (5.5–7.5s vs. 6–174.5s) and more consistent (4/5 had
identical `reasoning` length).

**Gate, free-text (`RELEVANT: yes/no`)**: 20/20 valid — already reliable, no
motivating failure on its own. Converted anyway per explicit decision: the
structural guarantee (relevant is exactly `true`/`false`, never an
unparseable variant) is worth more going forward than the cost of the change,
even without a current failure to fix. **Gate, JSON schema**
(`{relevant: boolean}`): 5/5 valid, comparable latency (~2.0–2.6s vs.
1.1–5.6s).

This is a structural fix, not a prompt-wording fix: tightening the free-text
prompt's instructions was considered and explicitly not the chosen direction —
grammar-constrained decoding makes an out-of-rubric `score` (e.g. `SCORE: 2`,
observed even from Groq's `llama-3.3-70b-versatile` under the old format)
impossible to emit, rather than merely instructed against.

## Model change: `llama-3.3-70b-versatile` → `openai/gpt-oss-20b`

Groq's `response_format: json_schema` is not supported by every model it
hosts. Confirmed via direct API call: `llama-3.3-70b-versatile` rejects
`json_schema` with `400 — This model does not support response format
json_schema` and only supports the looser `json_object` mode (valid JSON
syntax, but no schema/enum enforcement — `score` could still be `2` or a
string). `openai/gpt-oss-20b` (and `-120b`) support full `json_schema` on
Groq's hosted infrastructure. The relevance gate's model (`qwen2.5:7b` via
local Ollama) already supports schema-constrained `format` without a model
change.

## Considered options

- **Keep `llama-3.3-70b-versatile`, use `json_object` mode** — rejected as the
  primary path: does not structurally prevent an out-of-rubric score, only
  guarantees syntactically valid JSON. The `LLMClient.complete()` schema
  parameter is generic enough that any Groq model can still be configured
  this way if needed in the future; it is simply not the default.
- **Tighten the free-text prompt instructions instead of changing format** —
  rejected: still a request the model can ignore, not a structural guarantee;
  the empirical failure modes (silent sentinel omission, runaway generation)
  are not obviously wording problems.
- **Automatic runtime fallback (detect json_schema unsupported, degrade to
  json_object or free text)** — rejected: no reliable way to probe provider
  model support ahead of a call without an extra request; adds a code path
  that is hard to test meaningfully. The caller is responsible for
  configuring a schema-capable model when passing a schema.

## Consequences

- `LLMClient.complete()` protocol gains an optional `schema: dict | None`
  parameter (`src/evaluation/llm/protocol.py`, `ollama.py`, `groq.py`). This
  extends rather than reverses ADR-0021's minimal two-message interface — the
  fixed `system` + `user` shape is unchanged.
- New `src/evaluation/schemas.py`: `SCORER_SCHEMA`, `GATE_SCHEMA` — single
  source of truth passed by both the caller (`evaluator.py`,
  `evidence_selection.py`) and (implicitly, via prompt wording) the prompt
  builders.
- `evaluation/parsing/response.py` and `evaluation/parsing/relevance_response.py`
  parse JSON (`json.loads` + type/enum validation) instead of regex. Both
  still validate defensively — a provider that degrades to a looser JSON mode
  is not guaranteed to honour the schema, and `bool` being a subclass of
  `int` in Python means an accidental boolean in the `score` field must be
  rejected explicitly rather than silently read as `1`.
- `evaluation/prompt/builder.py`'s `_SCORING_INSTRUCTION` and
  `evaluation/prompt/relevance_builder.py`'s `_INSTRUCTIONS` describe the JSON
  fields instead of a sentinel block; the IPMP scoring rules themselves are
  unchanged (they still cannot be expressed by the schema alone).
- `main.py`: `configure_llm(provider="groq", model="openai/gpt-oss-20b")`.
  `configure_gate_llm(provider="ollama", model="qwen2.5:7b", ...)` unchanged.
- Existing tests (`test_response_parser.py`, `test_relevance_response.py`,
  `test_prompt_builder.py`, `test_evaluate_orchestration.py`,
  `test_evidence_selection.py`) updated to JSON-formatted stub responses — no
  backward-compatibility parsing for the old sentinel format was kept.
