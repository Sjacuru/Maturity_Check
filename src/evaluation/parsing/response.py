from __future__ import annotations

import re
from dataclasses import dataclass

_SENTINEL_RE = re.compile(
    r"^SCORE:\s*([0-9]+)\s*\nUNCERTAINTY:\s*(yes|no)\s*$",
    re.IGNORECASE | re.MULTILINE,
)

_VALID_SCORES = {0, 1, 3}


@dataclass
class ParsedResponse:
    raw_llm_response: str
    reasoning: str | None
    proposed_score: int | None
    uncertainty_flag: bool
    parse_failed: bool


def parse_llm_response(raw: str) -> ParsedResponse:
    stripped = raw.rstrip()
    match = _SENTINEL_RE.search(stripped)

    if not match:
        return ParsedResponse(
            raw_llm_response=raw,
            reasoning=None,
            proposed_score=None,
            uncertainty_flag=False,
            parse_failed=True,
        )

    # Sentinel must be at the very end of the (stripped) response
    if match.end() != len(stripped):
        return ParsedResponse(
            raw_llm_response=raw,
            reasoning=None,
            proposed_score=None,
            uncertainty_flag=False,
            parse_failed=True,
        )

    score_raw = int(match.group(1))
    if score_raw not in _VALID_SCORES:
        return ParsedResponse(
            raw_llm_response=raw,
            reasoning=None,
            proposed_score=None,
            uncertainty_flag=False,
            parse_failed=True,
        )

    uncertainty_flag = match.group(2).lower() == "yes"
    reasoning = stripped[: match.start()].rstrip() or None

    return ParsedResponse(
        raw_llm_response=raw,
        reasoning=reasoning,
        proposed_score=score_raw,
        uncertainty_flag=uncertainty_flag,
        parse_failed=False,
    )
