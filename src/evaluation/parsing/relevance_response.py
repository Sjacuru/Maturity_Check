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

_AFFIRMATIVE = {"yes", "sim"}


@dataclass
class RelevanceVerdict:
    relevant: bool
    parse_failed: bool


def parse_relevance_response(raw: str) -> RelevanceVerdict:
    """Parse the relevance gate's RELEVANT: sentinel response (ADR-0050).

    Binary verdict only — no cleaning step (dropped 2026-06-29: empirically,
    asking the model to also regenerate a cleaned copy of the chunk text cost
    50-86s per accept vs. ~4s for a bare yes/no, and the cleaning was already
    unreliable enough that its output was rarely used in practice).
    parse_failed=True means the RELEVANT: line itself couldn't be found —
    callers should treat that as not relevant (safe default).
    """
    match = _RELEVANT_RE.search(raw)
    if not match:
        return RelevanceVerdict(relevant=False, parse_failed=True)
    relevant = match.group(1).lower() in _AFFIRMATIVE
    return RelevanceVerdict(relevant=relevant, parse_failed=False)
