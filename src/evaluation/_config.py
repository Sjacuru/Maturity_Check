from __future__ import annotations

from evaluation.llm.protocol import LLMClient

# The only provider is the owner's GPU server (LlamaCppClient, ADR-0059);
# main.py builds both clients and registers them here. The Groq and Ollama
# clients and the ADR-0054 fallback chain were deleted on 2026-11-15.

_client: LLMClient | None = None
_provider: str | None = None
_model: str | None = None

# Relevance gate (ADR-0050) uses a separate client instance on the same
# server: it needs a tighter token cap, a longer read timeout and one call in
# flight (ADR-0065). Mirrors the configure_llm_client()/get_llm_client() pair.
_gate_client: LLMClient | None = None

# Gate verdict ledger (ADR-0067). None = off: every gate call reaches the model.
# main.py wires one on the shared app DB; measurement runs leave it off.
_gate_ledger = None


def configure_llm_client(client: LLMClient, provider: str, model: str) -> None:
    """Register the scorer's LLMClient. provider/model are the labels recorded
    at configure time; evaluate() prefers the client's own last_model_used
    (the name the server reports) when present."""
    global _client, _provider, _model
    _client = client
    _provider = provider
    _model = model


def configure_gate_llm_client(client: LLMClient) -> None:
    """Gate counterpart to configure_llm_client()."""
    global _gate_client
    _gate_client = client


def get_llm_client() -> LLMClient:
    if _client is None:
        raise RuntimeError(
            "LLM client not initialised. Call configure_llm_client() before evaluate()."
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


def configure_gate_ledger(ledger) -> None:
    """Register the GateLedger that select_evidence() consults before calling
    the gate model, or None to switch it off (ADR-0067)."""
    global _gate_ledger
    _gate_ledger = ledger


def get_gate_ledger():
    return _gate_ledger


def get_gate_llm_client() -> LLMClient:
    if _gate_client is None:
        raise RuntimeError(
            "Gate LLM client not initialised. Call configure_gate_llm_client() before select_evidence()."
        )
    return _gate_client


def _reset() -> None:
    """Reset module state — for test isolation only."""
    global _client, _provider, _model, _gate_client, _gate_ledger
    _client = None
    _provider = None
    _model = None
    _gate_client = None
    _gate_ledger = None
