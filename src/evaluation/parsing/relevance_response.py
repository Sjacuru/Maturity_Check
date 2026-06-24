from __future__ import annotations

import re
from dataclasses import dataclass

# Leading whitespace tolerated — local models often prefix a line with a
# stray space as a completion artifact; strict ^-anchoring rejected those
# otherwise-well-formed responses as parse failures.
# Portuguese-finetuned models often answer "sim"/"não" despite being told to
# use the literal English tokens — accept both rather than treating a
# correctly-understood-but-differently-worded answer as a parse failure.
_RELEVANT_RE = re.compile(
    r"^[ \t]*RELEVANT:\s*(yes|no|sim|n[aã]o)\s*$", re.IGNORECASE | re.MULTILINE
)
_CLEANED_RE = re.compile(r"^[ \t]*CLEANED:\s*\n", re.IGNORECASE | re.MULTILINE)

_AFFIRMATIVE = {"yes", "sim"}


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

    relevant = match.group(1).lower() in _AFFIRMATIVE
    if not relevant:
        return RelevanceVerdict(relevant=False, cleaned_text=None, parse_failed=False)

    cleaned_match = _CLEANED_RE.search(raw, match.end())
    if not cleaned_match:
        return RelevanceVerdict(relevant=True, cleaned_text=None, parse_failed=True)

    cleaned_text = raw[cleaned_match.end():].strip()
    return RelevanceVerdict(relevant=True, cleaned_text=cleaned_text or None, parse_failed=False)
