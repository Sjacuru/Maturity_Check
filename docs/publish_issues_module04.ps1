# publish_issues_module04.ps1
# Prerequisites: gh auth login (https://cli.github.com/)
# Run: pwsh -File docs\publish_issues_module04.ps1
# Issues are created in dependency order so blockers can reference real issue numbers.

$REPO = "Sjacuru/Maturity_Check"

# --- Ensure labels exist ---
function Ensure-Label($name, $color, $desc) {
    $existing = gh label list --repo $REPO --json name | ConvertFrom-Json | Where-Object { $_.name -eq $name }
    if (-not $existing) {
        gh label create $name --repo $REPO --color $color --description $desc
        Write-Host "Created label: $name"
    }
}
Ensure-Label "ready-for-agent"    "0075ca" "AFK slice — can be implemented without human interaction"
Ensure-Label "module:evaluation"  "5319e7" "Module 4 — LLM evaluation layer"

# --- Issue 16: EvaluationResult contract + configure_llm() + LLMClient protocol ---
$issue16 = gh issue create `
  --repo $REPO `
  --title "Evaluation: EvaluationResult contract + configure_llm() + LLMClient protocol" `
  --label "ready-for-agent,module:evaluation" `
  --body @'
**What to build**

Lay the structural foundation for Module 4: the `EvaluationResult` Pydantic model, the `LLMClient` Protocol, and the `configure_llm()` initialisation function. No prompt construction, no LLM calling, no response parsing — only the contracts and wiring.

**Deliver:**

1. `src/evaluation/__init__.py` — re-exports `configure_llm`, `evaluate` (stub), `EvaluationResult`
2. `src/evaluation/_config.py` — module-level client storage: `configure_llm()` / `get_llm_client()`
3. `src/evaluation/interfaces/__init__.py` (empty)
4. `src/evaluation/interfaces/contracts.py` — `EvaluationResult` Pydantic `BaseModel`
5. `src/evaluation/llm/__init__.py` (empty)
6. `src/evaluation/llm/protocol.py` — `LLMClient` Protocol

**`EvaluationResult` fields (all required):**

```python
class EvaluationResult(BaseModel):
    acao_id: int
    process_number: str
    provider: str
    model: str
    retrieved_chunks: list[RetrievedChunk]   # from retrieval module
    evidence_char_count: int
    system_prompt: str | None
    user_prompt: str | None
    raw_llm_response: str | None
    reasoning: str | None
    proposed_score: int | None    # 0, 1, or 3 only — Pydantic validator enforces the set
    uncertainty_flag: bool
    parse_failed: bool
    no_evidence_found: bool
```

`proposed_score` must be validated via a Pydantic validator (not just type annotation) to reject any value outside `{0, 1, 3}` and `None`.

**`LLMClient` Protocol:**

```python
class LLMClient(Protocol):
    def complete(self, system: str, user: str) -> str: ...
```

**`configure_llm()` signature:**

```python
def configure_llm(provider: str, model: str, base_url: str | None = None) -> None
```

Raises an explicit exception if `provider` is not `"ollama"` or `"groq"`. Does not instantiate client implementations yet (that is issue #20) — the stub may store a placeholder or raise `NotImplementedError` from `get_llm_client()` if called before implementations exist.

**Status flag invariants (enforced by Pydantic validators):**

- `no_evidence_found=True` → `system_prompt`, `user_prompt`, `raw_llm_response`, `reasoning`, `proposed_score` all `None`; `uncertainty_flag=False`; `parse_failed=False`
- `parse_failed=True` → `reasoning=None`, `proposed_score=None`
- `uncertainty_flag=True` is compatible with a valid `proposed_score`

**Acceptance criteria**

- [ ] `from evaluation import configure_llm, evaluate, EvaluationResult` works
- [ ] `EvaluationResult` constructs with all-valid fields without error
- [ ] `proposed_score=2` raises `ValidationError` at construction time
- [ ] `no_evidence_found=True` with `proposed_score=1` raises `ValidationError`
- [ ] `parse_failed=True` with `reasoning="text"` raises `ValidationError`
- [ ] `configure_llm("groq", "llama3-8b-8192")` stores provider/model without error
- [ ] `configure_llm("unknown", "x")` raises an explicit exception
- [ ] `tests/test_evaluation_contract.py` covers all invariant combinations — fast, no LLM required

**Blocked by**

None — can start immediately
'@

$issue16_num = ($issue16 -split '/')[-1]
Write-Host "Created Issue #${issue16_num} - EvaluationResult contract + configure_llm() + LLMClient protocol"

# --- Issue 17: Prompt builder ---
$issue17 = gh issue create `
  --repo $REPO `
  --title "Evaluation: prompt builder (build_system_prompt + build_user_prompt)" `
  --label "ready-for-agent,module:evaluation" `
  --body @"
**What to build**

Implement the prompt assembly layer in ``src/evaluation/prompt/builder.py``. Two functions — ``build_system_prompt(acao_id)`` and ``build_user_prompt(chunks)`` — produce the complete inputs for a single LLM call.

**Deliver:**

1. ``src/evaluation/prompt/__init__.py`` (empty)
2. ``src/evaluation/prompt/builder.py`` — ``build_system_prompt(acao_id: int) -> str`` and ``build_user_prompt(chunks: list[RetrievedChunk]) -> str``

**``build_system_prompt(acao_id)``**

Reads from ``get_ipmp_store()`` (ingestion module). Assembles in order:

1. Role and task statement
2. Ação title and ``descricao_acao``
3. ``o_que_esperar``
4. ``produtos_esperados`` — all items including parent (id ``"1"``), preserving full hierarchy
5. Scored examples (``exemplos``) introduced with explicit framing: *"Os exemplos abaixo ilustram os níveis de pontuação em um contexto específico; aplique os mesmos critérios ao processo avaliado, independente do setor ou domínio"*
6. ``excecoes``
7. Scoring instruction defining sentinel format, uncertainty criterion, OCR noise rule, and partial-evidence rule

The scoring instruction must specify:
- Sentinel format: ``SCORE: <0, 1 ou 3>`` and ``UNCERTAINTY: <yes ou no>`` as the **final two lines** of every response, with no text after them
- Uncertainty criterion: emit ``UNCERTAINTY: yes`` when retrieved evidence does not allow confident assessment of one or more Expected Products (``1a``, ``1b``, ``1c``, ``1d``)
- OCR noise rule: treat garbled text as unreliable; do not score positively based on OCR noise alone
- Partial evidence rule: score ``1`` when some but not all Expected Products are evidenced

**``build_user_prompt(chunks)``**

Assembles one evidence block per chunk showing ``filename``, ``page_number``, and ``text``, followed by a summary line with total chunk count and total character count.

Evidence chunks must appear in deterministic order:
1. ``cascade_step`` position: ``filename_match`` (1) → ``variant_match`` (2) → ``bm25`` (3) → ``regex`` (4)
2. Within ``bm25``: ``bm25_score`` descending → ``rank`` ascending → ``chunk_index`` ascending
3. Within all other steps: ``filename`` ascending → ``page_number`` ascending → ``chunk_index`` ascending

**Acceptance criteria**

- [ ] ``build_system_prompt(1)`` returns a non-empty string containing ``descricao_acao`` text from ``data/ipmp/acao_01.json``
- [ ] System prompt contains each of the three example level labels (``Atendido``, ``Parcialmente Atendido``, ``Não Atendido``)
- [ ] System prompt contains the illustrative framing sentence before the examples
- [ ] System prompt contains ``SCORE:`` and ``UNCERTAINTY:`` in the scoring instruction
- [ ] ``build_user_prompt(chunks)`` produces evidence blocks in correct deterministic cascade order
- [ ] Two calls with identical inputs produce identical outputs (deterministic)
- [ ] ``tests/test_prompt_builder.py`` verifies ordering and system prompt structure — fast, no LLM required

**Blocked by**

#$issue16_num
"@

$issue17_num = ($issue17 -split '/')[-1]
Write-Host "Created Issue #${issue17_num} - Prompt builder"

# --- Issue 18: Response parser ---
$issue18 = gh issue create `
  --repo $REPO `
  --title "Evaluation: response parser (sentinel extraction + status flags)" `
  --label "ready-for-agent,module:evaluation" `
  --body @"
**What to build**

Implement the response parsing layer in ``src/evaluation/parsing/response.py``. One function — ``parse_llm_response(raw)`` — extracts the sentinel block, derives status flags, and returns a typed result.

**Deliver:**

1. ``src/evaluation/parsing/__init__.py`` (empty)
2. ``src/evaluation/parsing/response.py`` — ``ParsedResponse`` dataclass and ``parse_llm_response(raw: str) -> ParsedResponse``

**``ParsedResponse`` dataclass:**

```python
@dataclass
class ParsedResponse:
    raw_llm_response: str      # always the unmodified input
    reasoning: str | None      # text before sentinel block; None on parse failure
    proposed_score: int | None # 0, 1, or 3; None on parse failure
    uncertainty_flag: bool     # True if UNCERTAINTY: yes
    parse_failed: bool         # True if sentinel block missing, malformed, or score not in {0,1,3}
```

**Parsing rules:**

- Use regex to locate the sentinel block at the **end** of the response (``SCORE: <value>\nUNCERTAINTY: <value>`` as the final two lines)
- ``reasoning`` = all text before the sentinel block, trailing whitespace stripped
- ``proposed_score`` validated against ``{0, 1, 3}`` — any other integer sets ``parse_failed=True``
- ``UNCERTAINTY: yes`` (case-insensitive) → ``uncertainty_flag=True``; ``UNCERTAINTY: no`` → ``False``
- On any parse failure: ``proposed_score=None``, ``reasoning=None``, ``parse_failed=True``, ``uncertainty_flag=False``
- ``raw_llm_response`` is always returned unchanged regardless of parse outcome

**Acceptance criteria**

- [ ] Well-formed ``SCORE: 0\nUNCERTAINTY: no`` → ``proposed_score=0``, ``uncertainty_flag=False``, ``parse_failed=False``
- [ ] Well-formed ``SCORE: 1\nUNCERTAINTY: yes`` → ``proposed_score=1``, ``uncertainty_flag=True``, ``parse_failed=False``
- [ ] Well-formed ``SCORE: 3\nUNCERTAINTY: no`` → ``proposed_score=3``, ``parse_failed=False``
- [ ] Missing ``SCORE:`` line → ``parse_failed=True``, ``proposed_score=None``, ``reasoning=None``
- [ ] ``SCORE: 2`` (invalid value) → ``parse_failed=True``, ``proposed_score=None``
- [ ] Sentinel block present but extra text after it → ``parse_failed=True``
- [ ] Empty string input → ``parse_failed=True``
- [ ] ``raw_llm_response`` always equals the input string regardless of parse outcome
- [ ] ``tests/test_response_parser.py`` covers all cases above — fast, no LLM required

**Blocked by**

#$issue16_num
"@

$issue18_num = ($issue18 -split '/')[-1]
Write-Host "Created Issue #${issue18_num} - Response parser"

# --- Issue 19: evaluate() orchestration ---
$issue19 = gh issue create `
  --repo $REPO `
  --title "Evaluation: evaluate() orchestration (full flow + observability)" `
  --label "ready-for-agent,module:evaluation" `
  --body @"
**What to build**

Implement ``evaluate()`` in ``src/evaluation/evaluator.py`` — the sole evaluation entry point that wires together prompt builder, LLM client, response parser, and ``EvaluationResult`` construction.

**Deliver:**

1. ``src/evaluation/evaluator.py`` — ``evaluate(acao_id, process_number, chunks) -> EvaluationResult``

**``evaluate()`` full flow:**

1. Guard: raise explicit exception if ``configure_llm()`` has not been called
2. Guard: raise explicit exception if ``acao_id`` not in loaded ``IPMPStore``
3. Short-circuit: if ``chunks`` is empty, return ``EvaluationResult`` with ``no_evidence_found=True`` and all nullable fields as ``None`` — do **not** call the LLM
4. Build system prompt via ``build_system_prompt(acao_id)``
5. Build user prompt via ``build_user_prompt(chunks)``
6. Compute ``evidence_char_count`` (total character length of the evidence section in the user prompt)
7. Log ``evidence_char_count`` at ``INFO`` level
8. If ``evidence_char_count > EVIDENCE_CHAR_WARN_THRESHOLD``, emit ``WARNING`` log
9. Call ``client.complete(system_prompt, user_prompt)``
10. Parse response via ``parse_llm_response(raw)``
11. Construct and return ``EvaluationResult``

**Named constant:**

```python
EVIDENCE_CHAR_WARN_THRESHOLD = 15_000
```

Document in a comment that this sits below Mistral 7B's 32K context after accounting for the system prompt (~3,000–4,000 chars).

**Status flag invariants in the returned result:**

- Short-circuit path: ``no_evidence_found=True``, ``uncertainty_flag=False``, ``parse_failed=False``, all nullable fields ``None``
- Parse failure path: ``parse_failed=True``, ``reasoning=None``, ``proposed_score=None``
- Normal path: ``parse_failed=False``, ``reasoning`` and ``proposed_score`` set

``provider`` and ``model`` in ``EvaluationResult`` come from the effective pair stored by ``configure_llm()``.

**Update ``__init__.py``** to replace the ``evaluate`` stub with the real import from ``evaluator.py``.

**Acceptance criteria**

- [ ] Empty ``chunks`` list → ``EvaluationResult`` with ``no_evidence_found=True``; stub LLM never called (verify call count = 0)
- [ ] Valid chunks + well-formed stub response → correct ``proposed_score``, ``reasoning``, ``uncertainty_flag=False``
- [ ] Valid chunks + ``UNCERTAINTY: yes`` stub → ``uncertainty_flag=True``, ``proposed_score`` still set
- [ ] Valid chunks + malformed stub response → ``parse_failed=True``, ``proposed_score=None``
- [ ] ``evaluate()`` before ``configure_llm()`` raises explicit exception
- [ ] ``evaluate()`` with unknown ``acao_id`` raises explicit exception
- [ ] ``evidence_char_count`` in result matches character count of evidence section
- [ ] ``provider`` and ``model`` in result match configured values
- [ ] ``tests/test_evaluate_orchestration.py`` covers all cases using ``StubLLMClient`` — fast, no LLM required

**Blocked by**

#$issue16_num, #$issue17_num, #$issue18_num
"@

$issue19_num = ($issue19 -split '/')[-1]
Write-Host "Created Issue #${issue19_num} - evaluate() orchestration"

# --- Issue 20: OllamaClient + GroqClient ---
$issue20 = gh issue create `
  --repo $REPO `
  --title "Evaluation: OllamaClient + GroqClient concrete implementations" `
  --label "ready-for-agent,module:evaluation" `
  --body @"
**What to build**

Implement the two concrete ``LLMClient`` providers and wire them into ``configure_llm()``.

**Deliver:**

1. ``src/evaluation/llm/ollama.py`` — ``OllamaClient`` implementing ``LLMClient``
2. ``src/evaluation/llm/groq.py`` — ``GroqClient`` implementing ``LLMClient``
3. Update ``src/evaluation/_config.py`` to instantiate the correct client in ``configure_llm()``

**``OllamaClient``:**

- Calls the Ollama HTTP API (``POST /api/chat`` or ``/api/generate``) using ``httpx`` or ``requests``
- Uses ``temperature=0`` set on the client — not passed by the caller
- Accepts ``base_url`` parameter (default: ``http://localhost:11434``) for non-default/remote instances
- ``complete(system, user) -> str`` returns the assistant message text

**``GroqClient``:**

- Calls the Groq API using the ``groq`` Python SDK
- Uses ``temperature=0`` set on the client — not passed by the caller
- API key read from ``GROQ_API_KEY`` environment variable
- ``complete(system, user) -> str`` returns the assistant message content

**``configure_llm()`` update:**

Replace the stub implementation with real instantiation:
- ``"ollama"`` → ``OllamaClient(model=model, base_url=base_url)``
- ``"groq"`` → ``GroqClient(model=model)``
- Unknown provider → raise ``ValueError`` with the unsupported provider name

**No automated tests against live providers.** Both clients are tested manually against a running instance. The automated test suite (issue #$issue19_num) uses ``StubLLMClient`` exclusively and must continue to pass after this issue is implemented.

**Acceptance criteria**

- [ ] ``configure_llm("ollama", "mistral", base_url=None)`` stores an ``OllamaClient`` instance
- [ ] ``configure_llm("groq", "llama3-8b-8192")`` stores a ``GroqClient`` instance
- [ ] ``configure_llm("unknown", "x")`` raises ``ValueError``
- [ ] ``OllamaClient.complete(system, user)`` sends ``temperature=0`` in the request body
- [ ] ``GroqClient.complete(system, user)`` sends ``temperature=0`` via the SDK
- [ ] All existing tests from issues #$issue16_num–#$issue19_num continue to pass
- [ ] No import of ``OllamaClient`` or ``GroqClient`` appears outside ``_config.py``

**Blocked by**

#$issue16_num
"@

$issue20_num = ($issue20 -split '/')[-1]
Write-Host "Created Issue #${issue20_num} - OllamaClient + GroqClient"

Write-Host ""
Write-Host "All 5 issues created. Summary:"
Write-Host "  #${issue16_num} - EvaluationResult contract + configure_llm() + LLMClient (AFK)"
Write-Host "  #${issue17_num} - Prompt builder (AFK, blocked by #${issue16_num})"
Write-Host "  #${issue18_num} - Response parser (AFK, blocked by #${issue16_num})"
Write-Host "  #${issue19_num} - evaluate() orchestration (AFK, blocked by #${issue16_num}, #${issue17_num}, #${issue18_num})"
Write-Host "  #${issue20_num} - OllamaClient + GroqClient (AFK, blocked by #${issue16_num})"
