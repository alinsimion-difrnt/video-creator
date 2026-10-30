"""lens eval: answer-key mapping (GSAP tween -> change types, ease -> class), overlap, scores."""

from __future__ import annotations

import pytest

from lens.config import load_config
from lens.eval import ease_class, iou, ratio, true_changes


def test_tween_props_name_the_change():
    rise = {"from": {"y": 50, "opacity": 0}, "to": {"y": 0, "opacity": 1}}
    assert true_changes(rise) == [{"fade"}, {"slide_up"}]
    left = {"from": {}, "to": {"x": "-40px"}}
    assert true_changes(left) == [{"slide_left"}]
    pop = {"from": {"scale": 0.8}, "to": {"scale": 1}}
    assert true_changes(pop) == [{"scale_up", "pop"}]
    bar = {"from": {"scaleX": 0}, "to": {"scaleX": 1}}
    assert "draw_on" in true_changes(bar)[0]
    blur = {"from": {"filter": "blur(10px)"}, "to": {"filter": "blur(0px)"}}
    assert true_changes(blur) == [{"blur_in"}]
    assert true_changes({"from": {}, "to": {"display": "none"}}) == []


@pytest.mark.parametrize(
    "ease,cls",
    [
        ("expo.out", "ease_out"),
        ("power2.inOut", "ease_in_out"),
        ("power3.in", "ease_in"),
        ("back.out(1.4)", "spring_overshoot"),
        ("none", "linear"),
        (None, "ease_out"),
    ],
)
def test_ease_class(ease, cls):
    assert ease_class(ease) == cls


def test_iou_and_ratio():
    assert iou((0, 0, 10, 10), (0, 0, 10, 10)) == 1
    assert iou((0, 0, 10, 10), (5, 0, 15, 10)) == pytest.approx(1 / 3)
    assert iou((0, 0, 1, 1), (2, 2, 3, 3)) == 0
    assert ratio(1, 4).value == 0.25 and ratio(0, 0).value is None


def test_eval_config_maps_every_answer_key_sfx_file():
    import json

    from lens.config import REPO_ROOT

    ak = load_config().eval.answer_key
    key = json.loads((REPO_ROOT / ak.path).read_text("utf-8"))
    assert {c["file"] for c in key["sfx"]} <= set(ak.sfx_labels)
