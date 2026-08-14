from __future__ import annotations

import json
import urllib.request


class OllamaClient:
    def __init__(
        self,
        model: str,
        base_url: str | None = None,
        num_predict: int = 2048,
        num_ctx: int = 32768,
        timeout: float = 180.0,
    ) -> None:
        self._model = model
        self._base_url = (base_url or "http://localhost:11434").rstrip("/")
        # Bounds generation length — without this, a temperature=0 classification-
        # style prompt can occasionally fall into repetitive/runaway generation
        # (observed: a relevance-gate call ran for hours on CPU-only inference
        # before this cap was added, ADR-0050). 2048 is generous for the main
        # evaluator's reasoning text; the gate client is configured with a
        # smaller value since it only needs to classify + lightly clean one chunk.
        self._num_predict = num_predict
        # Default 32768 matches Mistral 7B's real native context window (ADR-0019
        # amendment, 2026-06-23). NOT a safe default for every model: Bode
        # (Llama-2 7B architecture) is natively 4096 — confirmed via Ollama's
        # /api/show (llama.context_length: 4096). Requesting num_ctx beyond a
        # model's trained range forces RoPE position extrapolation, which can
        # degrade attention quality even for short prompts well within the
        # smaller window. configure_gate_llm() passes the model-appropriate
        # value explicitly; this default only suits Mistral-family models.
        self._num_ctx = num_ctx
        self._timeout = timeout
        self.model_label = model

    def complete(self, system: str, user: str, schema: dict | None = None) -> str:
        url = f"{self._base_url}/api/chat"
        body: dict = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "options": {
                "temperature": 0,
                "num_ctx": self._num_ctx,
                "num_predict": self._num_predict,
            },
            "stream": False,
        }
        if schema is not None:
            # Grammar-constrained structured output (ADR-0053) — Ollama takes
            # the JSON schema directly as the top-level `format` field.
            body["format"] = schema
        payload = json.dumps(body).encode()

        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self._timeout) as resp:
            response_body = json.loads(resp.read().decode())
        return response_body["message"]["content"]
