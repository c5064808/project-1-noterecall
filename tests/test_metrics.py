from __future__ import annotations

import pytest

from evaluation.metrics import ndcg_at_k, precision_at_k, recall_at_k, reciprocal_rank


def test_precision_only_counts_the_top_k():
    ranked = ["a", "b", "c", "d", "e"]
    relevant = {"a", "d"}
    assert precision_at_k(ranked, relevant, 3) == pytest.approx(1 / 3)
    assert precision_at_k(ranked, relevant, 5) == pytest.approx(2 / 5)


def test_precision_divides_by_k_even_when_fewer_results_come_back():
    # Deduplicating a five-chunk ranking by note can leave fewer than k entries, and P@5
    # is meant to be penalised for that rather than quietly rescaled.
    assert precision_at_k(["a", "b"], {"a"}, 5) == pytest.approx(0.2)


def test_recall_is_over_all_relevant_documents():
    ranked = ["x", "a", "y", "b"]
    assert recall_at_k(ranked, {"a", "b", "c"}, 4) == pytest.approx(2 / 3)
    assert recall_at_k(ranked, {"a", "b", "c"}, 2) == pytest.approx(1 / 3)


def test_reciprocal_rank_uses_the_first_hit_only():
    ranked = ["x", "y", "a", "b"]
    assert reciprocal_rank(ranked, {"a", "b"}, 5) == pytest.approx(1 / 3)
    assert reciprocal_rank(ranked, {"a"}, 2) == 0.0


def test_ndcg_of_a_single_relevant_note_at_rank_three():
    # DCG = 1/log2(4) = 0.5, IDCG = 1, so nDCG@5 is exactly 0.5.
    assert ndcg_at_k(["x", "y", "a", "z", "w"], {"a"}, 5) == pytest.approx(0.5)


def test_ndcg_is_one_when_the_ranking_is_ideal():
    assert ndcg_at_k(["a", "b", "c"], {"a", "b"}, 3) == pytest.approx(1.0)


def test_ndcg_of_an_imperfect_two_hit_ranking():
    # Hits at ranks 2 and 4: DCG = 1/log2(3) + 1/log2(5) = 1.06161,
    # IDCG = 1 + 1/log2(3) = 1.63093, so nDCG@4 = 0.6509.
    assert ndcg_at_k(["x", "a", "y", "b"], {"a", "b"}, 4) == pytest.approx(0.6509, abs=1e-4)


def test_metrics_are_zero_when_nothing_relevant_was_retrieved():
    ranked = ["x", "y", "z"]
    assert precision_at_k(ranked, {"a"}, 3) == 0.0
    assert recall_at_k(ranked, {"a"}, 3) == 0.0
    assert reciprocal_rank(ranked, {"a"}, 3) == 0.0
    assert ndcg_at_k(ranked, {"a"}, 3) == 0.0


def test_a_non_positive_cutoff_is_rejected():
    with pytest.raises(ValueError, match="k must be positive"):
        precision_at_k(["a"], {"a"}, 0)
