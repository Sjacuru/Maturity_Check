from __future__ import annotations

from typing import Hashable

# Literature-standard constant (Cormack et al. 2009), used by Elasticsearch/OpenSearch
# RRF implementations. No corpus-specific tuning — required for reproducibility (ADR-0049).
RRF_K = 60


def fuse_rankings(
    rankings: list[list[Hashable]],
    k: int = RRF_K,
) -> dict[Hashable, float]:
    """Fuse multiple ranked lists into one Reciprocal Rank Fusion score per item.

    Each ranking is a list of hashable identities, best match first (rank 1,
    1-indexed). score(item) = sum over rankings containing item of 1/(k+rank).
    An item absent from a ranking contributes nothing for that ranking.
    Higher fused score is better.
    """
    scores: dict[Hashable, float] = {}
    for ranking in rankings:
        for position, item in enumerate(ranking, start=1):
            scores[item] = scores.get(item, 0.0) + 1.0 / (k + position)
    return scores
