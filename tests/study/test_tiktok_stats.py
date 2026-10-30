"""study/tiktok/stats.py on synthetic rows."""

from __future__ import annotations

from study.tiktok import stats as s


def test_get_and_summary() -> None:
    m = {"shots": {"cuts_per_min": 12.0}, "loop": 0.8, "flag": True}
    assert s.get(m, ("shots", "cuts_per_min")) == 12.0
    assert s.get(m, ("shots", "missing")) is None
    assert s.get(m, ("flag",)) is None  # booleans are not numbers here
    out = s.summary([1.0, 2.0, 3.0, 4.0, None])  # type: ignore[list-item]
    assert out == {"n": 4, "median": 2.5, "p25": 1.75, "p75": 3.25}
    assert s.summary([]) is None


def test_split_top_by_plays() -> None:
    rows = [{"id": str(i), "plays": p} for i, p in enumerate([10, 500, 30, 400, 20, 300, 1, 2])]
    top, rest = s.split_top(rows, 0.25)
    assert [r["plays"] for r in top] == [500, 400]
    assert len(rest) == 6


def test_counts_lists_and_values() -> None:
    notes = [
        {"format": "talking_head", "graphics": {"devices": ["zoom_punch", "b_roll"]}},
        {"format": "talking_head", "graphics": {"devices": ["zoom_punch"]}},
        {"format": "skit", "graphics": {"devices": []}},
    ]
    assert s.counts(notes, ("format",)) == {"talking_head": 0.667, "skit": 0.333}
    assert s.counts(notes, ("graphics", "devices")) == {"zoom_punch": 0.667, "b_roll": 0.333}


def test_engagement() -> None:
    assert s.engagement({"likes": 50, "plays": 1000}) == 0.05
    assert s.engagement({"likes": 5, "plays": 0}) == 0.0
