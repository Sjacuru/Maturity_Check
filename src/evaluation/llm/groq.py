from __future__ import annotations

import os


class GroqClient:
    def __init__(self, model: str) -> None:
        self._model = model
        self.model_label = model
        self.last_model_used: str | None = None

    def complete(self, system: str, user: str, schema: dict | None = None) -> str:
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
        # Do not inherit HTTP(S)_PROXY from the host process.  In particular,
        # managed Windows environments can leave these variables pointing at a
        # stale local proxy after an update/restart, blocking direct Groq calls
        # before authentication is attempted.  Groq is intentionally reached
        # directly; TLS behaviour remains configurable through GROQ_SSL_VERIFY.
        http_client = httpx.Client(verify=ssl_verify, trust_env=False)

        client = Groq(api_key=api_key, http_client=http_client)
        kwargs: dict = dict(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0,
        )
        if schema is not None:
            # Grammar-constrained structured output (ADR-0053). Not every
            # model Groq hosts supports json_schema (llama-3.3-70b-versatile
            # does not, as of this writing — only json_object); the caller is
            # responsible for configuring a model that does when passing a
            # schema, since there is no reliable way to probe support ahead
            # of the call.
            kwargs["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "response", "schema": schema, "strict": True},
            }
        response = client.chat.completions.create(**kwargs)
        self.last_model_used = response.model
        return response.choices[0].message.content
