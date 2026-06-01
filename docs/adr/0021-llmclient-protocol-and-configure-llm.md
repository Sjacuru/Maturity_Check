# `LLMClient` protocol and `configure_llm()` initialisation pattern

Module 4 defines a minimal `LLMClient` Protocol with one method:

```python
class LLMClient(Protocol):
    def complete(self, system: str, user: str) -> str: ...
```

Two concrete implementations — `OllamaClient` and `GroqClient` — are instantiated through a module-level initialisation call that mirrors Module 3's `configure(db_path)` pattern:

```python
configure_llm(provider: str, model: str, base_url: str | None = None) -> None
```

The effective `provider` and `model` are recorded in every `EvaluationResult` for reproducibility. Prompt construction, score parsing, uncertainty handling, and `EvaluationResult` creation are completely provider-agnostic — they interact only with the `LLMClient` interface.

## Considered options

- **Environment variable only (`LLM_PROVIDER=ollama|groq`)** — rejected: hides the configuration choice from code; makes provider wiring invisible and untestable without environment manipulation.
- **Caller-supplied client (pass as argument to `evaluate()`)** — rejected: leaks provider wiring into the orchestrator; violates the module-level initialisation pattern established in Module 3.
- **Generic chat abstraction (message objects, role arrays, capability negotiation)** — rejected: Module 4 has a fixed two-message interaction pattern (`system` + `user`). Generality not justified by current requirements; adds surface area without benefit.

## Consequences

No additional abstraction layers are introduced unless a third materially different provider creates a demonstrated need. Provider defaults for model name are permitted, but the effective pair must always appear in evaluation metadata and audit logs.
