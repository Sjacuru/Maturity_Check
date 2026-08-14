from __future__ import annotations

# Grammar-constrained JSON schemas for the two LLM interaction points
# (ADR-0053). Passed to LLMClient.complete() as the `schema` argument —
# providers that support structured outputs (Ollama's `format`, Groq's
# `response_format: json_schema`) enforce these at the token-generation
# level, so `score` cannot be an out-of-rubric value and the response
# cannot omit a required field the way free-text sentinel parsing could.

SCORER_SCHEMA = {
    "type": "object",
    "properties": {
        "reasoning": {"type": "string"},
        "score": {"type": "integer", "enum": [0, 1, 3]},
        "uncertainty": {"type": "boolean"},
    },
    "required": ["reasoning", "score", "uncertainty"],
    "additionalProperties": False,
}

GATE_SCHEMA = {
    "type": "object",
    "properties": {
        "relevant": {"type": "boolean"},
    },
    "required": ["relevant"],
    "additionalProperties": False,
}
