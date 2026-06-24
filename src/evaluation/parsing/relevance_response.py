from __future__ import annotations

import re
from dataclasses import dataclass

_RELEVANT_RE = re.compile(r"^RELEVANT:\s*(yes|no)\s*$", re.IGNORECASE | re.MULTILINE)
_CLEANED_RE = re.compile(r"^CLEANED:\s*\n", re.IGNORECASE | re.MULTILINE)


@dataclass
class RelevanceVerdict:
    relevant: bool
    cleaned_text: str | None
    parse_failed: bool


def parse_relevance_response(raw: str) -> RelevanceVerdict:
    """Parse the relevance gate's RELEVANT:/CLEANED: sentinel response (ADR-0050).

    parse_failed=True signals the caller should treat cleaned_text as
    unavailable (fall back to the original chunk text) without overriding
    a successfully-parsed relevant=True/False verdict.
    """
    match = _RELEVANT_RE.search(raw)
    if not match:
        return RelevanceVerdict(relevant=False, cleaned_text=None, parse_failed=True)

    relevant = match.group(1).lower() == "yes"
    if not relevant:
        return RelevanceVerdict(relevant=False, cleaned_text=None, parse_failed=False)

    cleaned_match = _CLEANED_RE.search(raw, match.end())
    if not cleaned_match:
        return RelevanceVerdict(relevant=True, cleaned_text=None, parse_failed=True)

    cleaned_text = raw[cleaned_match.end():].strip()
    return RelevanceVerdict(relevant=True, cleaned_text=cleaned_text or None, parse_failed=False)
