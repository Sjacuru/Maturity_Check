from __future__ import annotations

import json
import urllib.request


class OllamaClient:
    def __init__(self, model: str, base_url: str | None = None) -> None:
        self._model = model
        self._base_url = (base_url or "http://localhost:11434").rstrip("/")

    def complete(self, system: str, user: str) -> str:
        url = f"{self._base_url}/api/chat"
        payload = json.dumps(
            {
                "model": self._model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "options": {"temperature": 0, "num_ctx": 32768},
                "stream": False,
            }
        ).encode()

        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            body = json.loads(resp.read().decode())
        return body["message"]["content"]
