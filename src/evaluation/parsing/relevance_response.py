from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass
class RelevanceVerdict:
    relevant: bool
    parse_failed: bool
    failure_reason: str | None = None
    """Why no usable verdict was obtained, when parse_failed is True.

    'parse'     — the response was not JSON, or lacked a boolean "relevant".
    'truncated' — the server stopped at its token cap before finishing.
    'transport' — the call itself failed (connection, timeout, busy).

    None when parse_failed is False. Callers must NOT treat a failure as a
    "not relevant" verdict: until 2026-09-27 they did, silently, so a broken
    call and a genuine rejection were indistinguishable in the audit trail
    (evidence_selection counts these separately now).
    """


def parse_relevance_response(raw: str) -> RelevanceVerdict:
    """Parse the relevance gate's structured JSON response (ADR-0053).

    Expects an object with a "relevant" boolean field — the shape enforced
    by evaluation.schemas.GATE_SCHEMA when the provider supports
    grammar-constrained output. parse_failed=True means the JSON could not
    be parsed or the field was missing/wrong-typed. relevant is False in that
    case as a safe default, but callers should branch on parse_failed first:
    a failed call is not evidence that the chunk is irrelevant.
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return RelevanceVerdict(relevant=False, parse_failed=True, failure_reason="parse")

    if not isinstance(data, dict):
        return RelevanceVerdict(relevant=False, parse_failed=True, failure_reason="parse")

    relevant = data.get("relevant")
    if not isinstance(relevant, bool):
        return RelevanceVerdict(relevant=False, parse_failed=True, failure_reason="parse")

    return RelevanceVerdict(relevant=relevant, parse_failed=False)
