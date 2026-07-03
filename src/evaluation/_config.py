from __future__ import annotations

from evaluation.llm.protocol import LLMClient

_SUPPORTED_PROVIDERS = {"ollama", "groq"}

_client: LLMClient | None = None
_provider: str | None = None
_model: str | None = None

# Relevance gate (ADR-0050) uses a separate, independently-configured client —
# always local Ollama in practice, decoupled from whatever provider handles
# final scoring (Groq's account-level rate limit can't absorb the gate's call
# volume). Mirrors the configure_llm()/get_llm_client() pair above.
_gate_client: LLMClient | None = None


def configure_llm(
    provider: str,
    model: str,
    base_url: str | None = None,
    num_predict: int | None = None,
    num_ctx: int | None = None,
    timeout: float | None = None,
) -> None:
    global _client, _provider, _model
    if provider not in _SUPPORTED_PROVIDERS:
        raise ValueError(
            f"Unsupported LLM provider '{provider}'. "
            f"Supported providers: {sorted(_SUPPORTED_PROVIDERS)}"
        )
    from evaluation.llm.ollama import OllamaClient
    from evaluation.llm.groq import GroqClient

    if provider == "ollama":
        kwargs = {"model": model, "base_url": base_url}
        if num_predict is not None:
            kwargs["num_predict"] = num_predict
        if num_ctx is not None:
            kwargs["num_ctx"] = num_ctx
        if timeout is not None:
            kwargs["timeout"] = timeout
        _client = OllamaClient(**kwargs)
    else:
        _client = GroqClient(model=model)
    _provider = provider
    _model = model


def get_llm_client() -> LLMClient:
    if _client is None:
        raise RuntimeError(
            "LLM client not initialised. Call configure_llm() before evaluate()."
        )
    return _client


def get_provider() -> str:
    if _provider is None:
        raise RuntimeError("LLM client not initialised.")
    return _provider


def get_model() -> str:
    if _model is None:
        raise RuntimeError("LLM client not initialised.")
    return _model


def configure_gate_llm(
    provider: str,
    model: str,
    base_url: str | None = None,
    num_predict: int | None = None,
    num_ctx: int | None = None,
    timeout: float | None = None,
) -> None:
    global _gate_client
    if provider not in _SUPPORTED_PROVIDERS:
        raise ValueError(
            f"Unsupported LLM provider '{provider}'. "
            f"Supported providers: {sorted(_SUPPORTED_PROVIDERS)}"
        )
    from evaluation.llm.ollama import OllamaClient
    from evaluation.llm.groq import GroqClient

    if provider == "ollama":
        kwargs = {"model": model, "base_url": base_url}
        if num_predict is not None:
            kwargs["num_predict"] = num_predict
        if num_ctx is not None:
            kwargs["num_ctx"] = num_ctx
        if timeout is not None:
            kwargs["timeout"] = timeout
        _gate_client = OllamaClient(**kwargs)
    else:
        _gate_client = GroqClient(model=model)


def get_gate_llm_client() -> LLMClient:
    if _gate_client is None:
        raise RuntimeError(
            "Gate LLM client not initialised. Call configure_gate_llm() before select_evidence()."
        )
    return _gate_client


def _reset() -> None:
    """Reset module state — for test isolation only."""
    global _client, _provider, _model, _gate_client
    _client = None
    _provider = None
    _model = None
    _gate_client = None
