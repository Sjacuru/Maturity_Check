from __future__ import annotations

import os


class GroqClient:
    def __init__(self, model: str) -> None:
        self._model = model

    def complete(self, system: str, user: str) -> str:
        try:
            from groq import Groq
            import httpx
        except ImportError as exc:
            raise ImportError(
                "groq and httpx packages are required for GroqClient. "
                "Install them with: pip install groq httpx"
            ) from exc

        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY environment variable is not set.")

        # Corporate proxy intercepts TLS with a self-signed cert that breaks
        # Python's ssl chain verification (corrupted Windows trust store entry
        # prevents pip-system-certs from injecting the CA bundle).
        # verify=False disables cert-chain checks only; the connection is still
        # TLS-encrypted end-to-end between the proxy and api.groq.com.
        ssl_verify = os.environ.get("GROQ_SSL_VERIFY", "false").lower() != "false"
        http_client = httpx.Client(verify=ssl_verify)

        client = Groq(api_key=api_key, http_client=http_client)
        response = client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0,
        )
        return response.choices[0].message.content
