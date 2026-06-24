from __future__ import annotations

import json
import urllib.request


class OllamaClient:
    def __init__(
        self,
        model: str,
        base_url: str | None = None,
        num_predict: int = 2048,
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
        self._timeout = timeout

    def complete(self, system: str, user: str) -> str:
        url = f"{self._base_url}/api/chat"
        payload = json.dumps(
            {
                "model": self._model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                # Mistral 7B's real native context window (see ADR-0019 amendment, 2026-06-23).
                # Was hardcoded to 8192 — a quarter of the model's real capacity — which
                # silently undermined the evidence-cap calculation in evaluator.py.
                "options": {
                    "temperature": 0,
                    "num_ctx": 32768,
                    "num_predict": self._num_predict,
                },
                "stream": False,
            }
        ).encode()

        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self._timeout) as resp:
            body = json.loads(resp.read().decode())
        return body["message"]["content"]
