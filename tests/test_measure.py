"""M4 measurement core (BUILD_PLAN 7.5, 11.1): curves golden-tested against GSAP and Remotion, fits on
exact curves, and tracking + fitting on rendered UI fixtures at 24/25/30/60 fps."""

import itertools
import json
import math

import cv2
import numpy as np
import pytest

from lens.config import REPO_ROOT, load_config
from lens.measure import measure_element, sfx_offset_ms, text_stagger
from lens.measure.curves import Spring, bezier_class, cubic_bezier, gsap_ease
from lens.measure.fit import fit_joint, fit_progress
from lens.measure.run import word_boxes
from tests.fixtures.motion import Anim, H, W, ease_progress, render, spring_progress, word_reveal

CFG = load_config().measure
GOLDEN = json.loads((REPO_ROOT / "tests" / "fixtures" / "golden-curves.json").read_text())
FIT = {
    "margin": CFG.model_selection_margin,
    "end_tolerance": CFG.progress_end_tolerance,
    "gsap_class_ratio": CFG.gsap_class_ratio,
}


# --- curves against the real libraries -------------------------------------------------------------


@pytest.mark.parametrize("name", sorted(GOLDEN["eases"]))
def test_gsap_ease_matches_gsap(name):
    t = np.asarray(GOLDEN["t"])
    assert np.max(np.abs(gsap_ease(name)(t) - np.asarray(GOLDEN["eases"][name]))) < 1e-6


@pytest.mark.parametrize("i", range(len(GOLDEN["springs"])))
def test_spring_matches_remotion(i):
    s = GOLDEN["springs"][i]
    spring = Spring.from_physical(**s["config"])
    frames = np.arange(len(s["values"]))
    drawn = spring.as_remotion_renders()(frames / s["fps"])
    assert np.max(np.abs(drawn - np.asarray(s["values"]))) < 1e-6
    # The config we export draws the same curve in Remotion (exactly when not overdamped).
    back = Spring.from_physical(**spring.remotion())
    assert back.zeta == pytest.approx(spring.zeta, rel=1e-3)
    assert spring.remotion_exact == (spring.zeta <= 1)


def test_spring_overshoot_and_settle():
    s = Spring(0.45, 14.0)
    t = np.linspace(0, 3, 30001)
    assert s.overshoot() == pytest.approx(float(s(t).max()) - 1, abs=1e-4)
    settle = s.settle_s(0.02)
    after = t >= settle
    assert np.all(np.abs(s(t[after]) - 1) <= 0.02 + 1e-9)
    assert Spring(1.0, 20).overshoot() == 0


def test_cubic_bezier_and_class():
    t = np.linspace(0, 1, 11)
    assert np.allclose(cubic_bezier(0, 0, 1, 1)(t), t, atol=1e-6)
    ease = cubic_bezier(0.42, 0, 0.58, 1)(t)
    assert np.allclose(ease + ease[::-1], 1, atol=1e-6)  # symmetric
    assert bezier_class(0.42, 0, 0.58, 1) == "ease_in_out"
    assert bezier_class(0, 0, 0.58, 1) == "ease_out"
    assert bezier_class(0.42, 0, 1, 1) == "ease_in"
    assert bezier_class(0.33, 0.33, 0.67, 0.67) == "linear"


# --- fitting exact curves ----------------------------------------------------------------------------


def _sampled(name: str, dur: float, fps: float = 30, t0: float = 0.1, noise: float = 0.0):
    t = np.arange(0, t0 + dur + 0.4, 1 / fps)
    p = gsap_ease(name)(np.clip((t - t0) / dur, 0, 1))
    return t, p + np.random.default_rng(1).normal(0, noise, len(t))


@pytest.mark.parametrize(
    ("name", "dur", "cls"),
    [
        ("none", 0.5, "linear"),
        ("power2.out", 0.45, "ease_out"),
        ("back.out(1.4)", 0.3, "ease_out"),
        ("power2.inOut", 0.6, "ease_in_out"),
        ("power2.in", 0.4, "ease_in"),
    ],
)
def test_fit_recovers_named_ease(name, dur, cls):
    t, p = _sampled(name, dur, noise=0.005)
    r = fit_progress(t, p, **FIT)
    assert r.gsap.name == name
    assert r.cls == cls
    assert abs(r.gsap.duration_s - dur) <= 1 / 30
    assert abs(r.gsap.t0 - 0.1) <= 1 / 30


def test_fit_recovers_spring_parameters():
    s = Spring(0.45, 14.0)
    t = np.arange(0, 1.6, 1 / 30)
    p = np.where(t > 0.1, s(np.maximum(t - 0.1, 0)), 0) + np.random.default_rng(2).normal(0, 0.005, len(t))
    r = fit_progress(t, p, **FIT)
    assert r.cls == "spring"
    assert r.spring.spring.zeta == pytest.approx(0.45, rel=0.03)
    assert r.spring.spring.omega0 == pytest.approx(14.0, rel=0.03)
    assert r.overshoot_pct == pytest.approx(100 * s.overshoot(), abs=2)


def test_joint_fit_recovers_timing_when_the_start_is_unseen():
    """A word fades in while it rises (v1): position is only measurable once it is visible."""
    t, p = _sampled("expo.out", 0.45)
    seen = t >= 0.1 + 2 / 30
    pos = p[seen]
    pos = (pos - pos[0]) / (1 - pos[0])  # progress from the first visible frame
    j = fit_joint([(t[seen], pos, True, False), (t, p, False, True)])
    assert j.name == "expo.out"
    assert abs(j.t0 - 0.1) <= 1 / 30
    assert abs(j.duration_s - 0.45) <= 1 / 30
    assert j.amplitudes[0] == pytest.approx(1 / (1 - p[seen][0]), rel=0.05)


# --- tracking and fitting rendered UI ------------------------------------------------------------------


@pytest.mark.parametrize("fps", [24, 25, 30, 60])
def test_slide_with_ease_out(fps):
    fr, box = render(Anim(ease_progress("power2.out", 0.2, 0.6), (100, 140), (420, 140)), fps, 1.4)
    m = measure_element(fr, 0, fps, box, (0, 0, W, H), CFG)
    (x,) = [c for c in m.channels if c.channel.name == "x"]
    assert x.fit.cls == "ease_out"
    assert m.timing is not None and m.timing.name == "power2.out"
    assert abs(m.timing.t0 - 0.2) * fps <= 1
    assert abs(m.timing.duration_s - 0.6) * fps <= 1
    assert not [c for c in m.channels if c.channel.name == "opacity"]  # no fake fade


@pytest.mark.parametrize("fps", [24, 30])
def test_linear_slide(fps):
    fr, box = render(Anim(ease_progress("none", 0.2, 0.5), (100, 140), (420, 140)), fps, 1.2)
    m = measure_element(fr, 0, fps, box, (0, 0, W, H), CFG)
    assert m.primary is not None and m.primary.fit.cls == "linear"
    assert m.timing is not None and abs(m.timing.duration_s - 0.5) * fps <= 1


@pytest.mark.parametrize("fps", [24, 30, 60])
def test_spring_with_overshoot(fps):
    fr, box = render(Anim(spring_progress(Spring(0.45, 14), 0.2), (150, 180), (380, 180)), fps, 1.6)
    m = measure_element(fr, 0, fps, box, (0, 0, W, H), CFG)
    (x,) = [c for c in m.channels if c.channel.name == "x"]
    assert x.fit.cls == "spring"
    assert x.fit.spring.spring.zeta == pytest.approx(0.45, rel=0.05)
    assert x.fit.spring.spring.omega0 == pytest.approx(14.0, rel=0.05)


@pytest.mark.parametrize("fps", [24, 30])
def test_fade_in(fps):
    fr, box = render(
        Anim(ease_progress("power2.out", 0.2, 0.4), (320, 180), (320, 180), start_alpha=0), fps, 1.0
    )
    m = measure_element(fr, 0, fps, box, (0, 0, W, H), CFG)
    assert [c.channel.name for c in m.channels] == ["opacity"]
    assert m.timing is not None and m.timing.name == "power2.out"
    assert abs(m.timing.duration_s - 0.4) * fps <= 1


@pytest.mark.parametrize("fps", [24, 25, 30, 60])
def test_scale_pop(fps):
    anim = Anim(
        ease_progress("back.out(1.4)", 0.2, 0.3), (320, 180), (320, 180), start_scale=0.6, start_alpha=0
    )
    fr, box = render(anim, fps, 1.0)
    m = measure_element(fr, 0, fps, box, (0, 0, W, H), CFG)
    assert m.timing is not None and m.timing.name.startswith("back.out(")
    assert abs(m.timing.t0 - 0.2) * fps <= 1
    assert abs(m.timing.duration_s - 0.3) * fps <= 1


@pytest.mark.parametrize("fps", [24, 25, 30, 60])
def test_fade_and_rise_like_v1(fps):
    """Acme v1's entrance: opacity 0 -> 1 and y +26 -> 0 together, expo.out 0.45 s."""
    anim = Anim(ease_progress("expo.out", 0.2, 0.45), (320, 206), (320, 180), start_alpha=0)
    fr, box = render(anim, fps, 1.0)
    m = measure_element(fr, 0, fps, box, (0, 0, W, H), CFG)
    assert {c.channel.name for c in m.channels} == {"y", "opacity"}
    assert m.timing is not None and m.timing.name == "expo.out"
    assert abs(m.timing.t0 - 0.2) * fps <= 1
    assert abs(m.timing.duration_s - 0.45) * fps <= 1


@pytest.mark.parametrize(("fps", "stagger"), [(24, 3), (30, 3), (60, 6)])
def test_per_word_stagger(fps, stagger):
    fr, boxes, reveal = word_reveal(fps, stagger)
    s = text_stagger(fr, 0, fps, boxes, CFG)
    assert s.unit == "word"
    assert s.reveal_frames is not None
    for got, want in zip(s.reveal_frames, reveal, strict=True):
        assert got is not None and abs(got - want) <= 1
    assert s.stagger_ms == pytest.approx(stagger / fps * 1000, abs=1000 / fps)


def test_sfx_offset_sign():
    assert sfx_offset_ms(0.94, 30, 30) == -60.0  # a whoosh 60 ms before the landing leads
    assert sfx_offset_ms(1.0, 30, 30) == 0.0


def test_word_boxes_split_a_line():
    boxes = word_boxes((0, 0, 110, 20), "Every answer counts")
    assert len(boxes) == 3
    assert boxes[0][0] == 0 and boxes[-1][2] == 110
    assert all(a[2] <= b[0] for a, b in itertools.pairwise(boxes))


# --- the Acme v1 answer key --------------------------------------------------------------------------


def test_v1_answer_key_is_consistent():
    key = json.loads((REPO_ROOT / "tests" / "fixtures" / "acme-v1" / "answer-key.json").read_text())
    assert len(key["scenes"]) == 15 and len(key["transitions"]) == 14 and len(key["sfx"]) == 14
    assert key["scenes"][-1]["end_s"] == pytest.approx(144.6, abs=0.01)
    # transitions are 0.4-0.5 s overlaps, and every SFX starts on a scene start (handoff 5.9)
    assert all(0.39 <= t["duration_s"] <= 0.51 for t in key["transitions"])
    starts = {round(s["start_s"], 2) for s in key["scenes"]}
    assert all(round(s["start_s"], 2) in starts for s in key["sfx"])
    eases = {t["ease"] for t in key["tweens"] if t["duration_s"] > 0}
    for e in eases - {"custom"}:
        assert np.isfinite(gsap_ease(e)(np.linspace(0, 1, 5))).all()
    assert not any(s["timeline_errors"] for s in key["scenes"])
    assert math.isclose(sum(t["duration_s"] > 0 for t in key["tweens"]), 492, abs_tol=10)


@pytest.mark.parametrize("side", [24, 90, 300])
def test_coarse_to_fine_match_equals_the_full_search(side):
    """A large search area is searched shrunk first; the hit must be the full-size search's hit."""
    from lens.measure.track import _match

    rng = np.random.default_rng(side)
    frame = (rng.random((720, 1280)) * 40 + 100).astype(np.float32)
    patch = cv2.GaussianBlur((rng.random((side, side)) * 255).astype(np.float32), (0, 0), 1.0)
    frame[201 : 201 + side, 517 : 517 + side] = patch
    steps = CFG.track_scale_steps
    region = (0, 0, 1280, 720)
    full = _match(frame, patch, region, 1.0, steps, 10**6, CFG.track_coarse_min_template_px)
    fast = _match(frame, patch, region, 1.0, steps, CFG.track_coarse_px, CFG.track_coarse_min_template_px)
    assert fast[:3] == pytest.approx(full[:3])
    assert fast[:2] == pytest.approx((517 + side / 2, 201 + side / 2))
