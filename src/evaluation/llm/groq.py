from __future__ import annotations

import os


class GroqClient:
    def __init__(self, model: str) -> None:
        self._model = model

    def complete(self, system: str, user: str) -> str:
        try:
            from groq import Groq
        except ImportError as exc:
            raise ImportError(
                "groq package is required for GroqClient. Install it with: pip install groq"
            ) from exc

        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY environment variable is not set.")

        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0,
        )
        return response.choices[0].message.content
