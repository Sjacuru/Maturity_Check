from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass
class RelevanceVerdict:
    relevant: bool
    parse_failed: bool


def parse_relevance_response(raw: str) -> RelevanceVerdict:
    """Parse the relevance gate's structured JSON response (ADR-0053).

    Expects an object with a "relevant" boolean field — the shape enforced
    by evaluation.schemas.GATE_SCHEMA when the provider supports
    grammar-constrained output. parse_failed=True means the JSON could not
    be parsed or the field was missing/wrong-typed — callers should treat
    that as not relevant (safe default).
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return RelevanceVerdict(relevant=False, parse_failed=True)

    if not isinstance(data, dict):
        return RelevanceVerdict(relevant=False, parse_failed=True)

    relevant = data.get("relevant")
    if not isinstance(relevant, bool):
        return RelevanceVerdict(relevant=False, parse_failed=True)

    return RelevanceVerdict(relevant=relevant, parse_failed=False)
