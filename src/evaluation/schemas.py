from __future__ import annotations

# Grammar-constrained JSON schemas for the two LLM interaction points
# (ADR-0053). Passed to LLMClient.complete() as the `schema` argument —
# the GPU server (llama.cpp's `response_format: json_schema`) enforces these
# at the token-generation level, so `score` cannot be an out-of-rubric value
# and the response cannot omit a required field the way free-text sentinel
# parsing could.

# "products" carries one verdict per scored Expected Product, and is listed
# FIRST so the grammar makes the model commit to each product individually
# before it names an overall score — the per-product judgement is the evidence
# for the score, not a rationalisation of it.
#
# parse_llm_response() COMPUTES score from these verdicts when they cover
# exactly the Ação's scored products, and otherwise falls back to the model's
# own "score" field. Both are required here so the grammar always produces
# both; the fallback covers verdicts that are present but incomplete or
# mismatched, never a missing field.
#
# To revert to the pre-2026-09-27 behaviour, remove "products" from properties
# and from required: parse_llm_response() degrades to score_source="model"
# with no other change.
SCORER_SCHEMA = {
    "type": "object",
    "properties": {
        "products": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "string"},
                    "evidenced": {"type": "boolean"},
                    "justificativa": {"type": "string"},
                },
                "required": ["product_id", "evidenced", "justificativa"],
                "additionalProperties": False,
            },
        },
        "reasoning": {"type": "string"},
        "score": {"type": "integer", "enum": [0, 1, 3]},
        "uncertainty": {"type": "boolean"},
    },
    "required": ["products", "reasoning", "score", "uncertainty"],
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
