from __future__ import annotations

from evaluation.llm.protocol import LLMClient

_SUPPORTED_PROVIDERS = {"ollama", "groq"}

_client: LLMClient | None = None
_provider: str | None = None
_model: str | None = None


def configure_llm(provider: str, model: str, base_url: str | None = None) -> None:
    global _client, _provider, _model
    if provider not in _SUPPORTED_PROVIDERS:
        raise ValueError(
            f"Unsupported LLM provider '{provider}'. "
            f"Supported providers: {sorted(_SUPPORTED_PROVIDERS)}"
        )
    from evaluation.llm.ollama import OllamaClient
    from evaluation.llm.groq import GroqClient

    if provider == "ollama":
        _client = OllamaClient(model=model, base_url=base_url)
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


def _reset() -> None:
    """Reset module state — for test isolation only."""
    global _client, _provider, _model
    _client = None
    _provider = None
    _model = None
