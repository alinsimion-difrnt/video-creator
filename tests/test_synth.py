"""S9 synth: weighted statistics, k-means, and clustering of `other` patterns (with a fake embedder)."""

from __future__ import annotations

import numpy as np
import pytest

from lens.schemas.config import Cluster
from lens.synth.cluster import average_link, propose, slug
from lens.synth.stats import kmeans, shares, stat, weighted_quantile

KW = {"min_n": 5, "bootstrap": 200, "ci": 0.9, "seed": 1}


def test_weighted_quantile_follows_the_weights():
    v = np.array([1.0, 2.0, 3.0])
    assert weighted_quantile(v, np.ones(3), 0.5) == pytest.approx(2.0)
    assert weighted_quantile(v, np.array([1.0, 1.0, 10.0]), 0.5) == pytest.approx(3.0, abs=0.3)


def test_stat_median_interval_and_small_samples():
    rng = np.random.default_rng(0)
    vals = rng.normal(500, 40, 200)
    s = stat(vals, np.ones(200), ["a", "b"] * 100, **KW)
    assert s.n == 200 and s.videos == 2
    assert s.median == pytest.approx(500, abs=10)
    assert s.ci is not None and s.ci[0] < s.median < s.ci[1]
    assert s.p25 is not None and s.p75 is not None and s.p25 < s.median < s.p75
    few = stat([1.0, 2.0], [1.0, 1.0], ["a", "a"], **KW)
    assert few.ci is None and few.median == pytest.approx(1.5)
    none = stat([float("nan")], [1.0], ["a"], **KW)
    assert none.n == 0 and none.median is None
    zero_weight = stat([1.0, 9.0], [1.0, 0.0], ["a", "b"], **KW)
    assert zero_weight.n == 1 and zero_weight.videos == 1


def test_shares_sum_to_one_largest_first():
    s = shares([("a", 1.0), ("b", 3.0), ("a", 1.0), ("c", 0.0)])
    assert list(s) == ["b", "a"] and sum(s.values()) == pytest.approx(1.0)
    assert shares([]) == {}


def test_kmeans_separates_groups_in_order():
    pts = np.array([[0.0, 0.0], [0.1, 0.0], [5.0, 5.0], [5.1, 5.0], [10.0, 0.0], [10.1, 0.1]])
    labels = kmeans(pts, 3)
    assert labels.tolist() == [0, 0, 1, 1, 2, 2]
    assert kmeans(pts[:1], 3).tolist() == [0]


def test_average_link_stops_at_the_threshold():
    sim = np.array([[1, 0.9, 0.1], [0.9, 1, 0.2], [0.1, 0.2, 1]])
    assert average_link(sim, 0.5) == [[0, 1], [2]]
    assert average_link(sim, 0.95) == [[0], [1], [2]]


def _embed(texts):
    """Bag of words over a tiny vocabulary: similar names -> similar vectors."""
    vocab = ["chat", "bubble", "orb", "logo", "glitch", "typing", "prompt"]
    out = np.array([[t.lower().count(w) for w in vocab] for t in texts], dtype=float) + 1e-3
    return out / np.linalg.norm(out, axis=1, keepdims=True)


def test_propose_groups_names_across_videos_and_suggests_merges():
    cfg = Cluster(model="m", revision="r", threshold=0.6, merge_similarity=0.8, min_members=2, min_brands=2)
    items = [
        ("v1/e001", "chat bubble pop", "a chat bubble pops in"),
        ("v2/e004", "chat bubble append", "bubble appended to the chat"),
        ("v1/e009", "logo glitch", "glitch on the logo"),
        ("v1/e010", "logo glitch", "logo glitches"),  # same video only: left out
        ("v3/e002", "prompt typing", "typing a prompt"),
        ("v4/e003", "simulated prompt typing", "prompt being typed"),
    ]
    proposals, left = propose(items, ["prompt_type_on"], cfg, _embed)
    by_id = {p.id: p for p in proposals}
    assert set(by_id) == {"chat_bubble_append", "prompt_typing"} or set(by_id) == {
        "chat_bubble_pop",
        "prompt_typing",
    }
    assert left == 2
    chat = next(p for p in proposals if p.id.startswith("chat"))
    assert chat.videos == 2 and sorted(chat.members) == ["v1/e001", "v2/e004"]
    typing = by_id["prompt_typing"]
    assert typing.nearest_pattern == "prompt_type_on" and typing.suggestion == "merge:prompt_type_on"


def test_slug():
    assert slug("Lens mask zoom-through") == "lens_mask_zoom_through"
    assert slug("!!!") == "pattern"
