from __future__ import annotations

import json
from dataclasses import dataclass

_VALID_SCORES = {0, 1, 3}


@dataclass
class ParsedResponse:
    raw_llm_response: str
    reasoning: str | None
    proposed_score: int | None
    uncertainty_flag: bool
    parse_failed: bool


def _failed(raw: str) -> ParsedResponse:
    return ParsedResponse(
        raw_llm_response=raw,
        reasoning=None,
        proposed_score=None,
        uncertainty_flag=False,
        parse_failed=True,
    )


def parse_llm_response(raw: str) -> ParsedResponse:
    """Parse the scorer's structured JSON response (ADR-0053).

    Expects an object with "reasoning" (string), "score" (integer, one of
    0/1/3), and "uncertainty" (boolean) — the shape enforced by
    evaluation.schemas.SCORER_SCHEMA when the provider supports
    grammar-constrained output. Still validated defensively here: a provider
    without structured-output support, or one that degrades to a looser JSON
    mode, is not guaranteed to honour the schema.
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return _failed(raw)

    if not isinstance(data, dict):
        return _failed(raw)

    score = data.get("score")
    uncertainty = data.get("uncertainty")
    reasoning = data.get("reasoning")

    # bool is a subclass of int in Python — isinstance(True, int) is True and
    # True == 1, so an accidental boolean in the score field must be rejected
    # explicitly rather than silently accepted as score=1.
    if isinstance(score, bool) or not isinstance(score, int) or score not in _VALID_SCORES:
        return _failed(raw)
    if not isinstance(uncertainty, bool):
        return _failed(raw)
    if not isinstance(reasoning, str):
        return _failed(raw)

    return ParsedResponse(
        raw_llm_response=raw,
        reasoning=reasoning.strip() or None,
        proposed_score=score,
        uncertainty_flag=uncertainty,
        parse_failed=False,
    )
