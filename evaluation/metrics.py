"""Ranking metrics with binary relevance.

Every function takes a ranked list of ids (best first), the set of ids judged relevant for
that query, and a cutoff k. Ids are note ids in this project, so the caller is expected to
have deduplicated the ranking by note before scoring.
"""

from __future__ import annotations

import math
from collections.abc import Collection, Sequence


def precision_at_k(ranked_ids: Sequence[str], relevant_ids: Collection[str], k: int) -> float:
    """Fraction of the top k positions holding a relevant id."""
    _check_k(k)
    hits = sum(1 for rid in ranked_ids[:k] if rid in relevant_ids)
    return hits / k


def recall_at_k(ranked_ids: Sequence[str], relevant_ids: Collection[str], k: int) -> float:
    """Fraction of the relevant ids that appear in the top k."""
    _check_k(k)
    if not relevant_ids:
        return 0.0
    found = {rid for rid in ranked_ids[:k] if rid in relevant_ids}
    return len(found) / len(relevant_ids)


def reciprocal_rank(ranked_ids: Sequence[str], relevant_ids: Collection[str], k: int) -> float:
    """1 / rank of the first relevant id inside the top k, or 0 if there is none."""
    _check_k(k)
    for position, rid in enumerate(ranked_ids[:k], start=1):
        if rid in relevant_ids:
            return 1.0 / position
    return 0.0


def ndcg_at_k(ranked_ids: Sequence[str], relevant_ids: Collection[str], k: int) -> float:
    """Discounted cumulative gain over the top k, divided by the best achievable value."""
    _check_k(k)
    if not relevant_ids:
        return 0.0

    dcg = sum(
        _discount(position)
        for position, rid in enumerate(ranked_ids[:k], start=1)
        if rid in relevant_ids
    )
    # The ideal ranking puts every relevant item it can fit into the first positions.
    ideal = sum(_discount(position) for position in range(1, min(k, len(relevant_ids)) + 1))
    return dcg / ideal


def _discount(position: int) -> float:
    return 1.0 / math.log2(position + 1)


def _check_k(k: int) -> None:
    if k <= 0:
        raise ValueError(f"k must be positive, got {k}")
