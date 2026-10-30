"""S3 video signals against frame-exact synthetic explainers (BUILD_PLAN 11.1)."""

import shutil
from pathlib import Path

import pytest

from lens.config import load_config
from lens.signals.video import build_shots, detect_cuts, detect_events, detect_holds, detect_transitions, scan
from tests.fixtures.scenes import EXPLAINER_DEAD_HOLD, encode, explainer, frames_of

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")

CFG = load_config()


@pytest.fixture(scope="module", params=[24.0, 25.0, 30.0, 60.0], ids=lambda f: f"{f:g}fps")
def analysed(request, tmp_path_factory):
    fps = request.param
    frames, truth = frames_of(*explainer(fps))
    path = encode(frames, fps, tmp_path_factory.mktemp("v") / "explainer.mp4")
    v = CFG.signals.video
    fs = scan(Path(path), fps, 640, 360, v)
    cuts = detect_cuts(fs, v)
    transitions = detect_transitions(fs, cuts, v)
    shots = build_shots(fs.n, transitions)
    events = detect_events(fs, shots, v)
    holds = detect_holds(fs, shots, events, v, CFG.signals.dead_hold_min_s)
    return fps, truth, fs, transitions, shots, events, holds


def test_frame_count(analysed):
    _, truth, fs, *_ = analysed
    assert fs.n == truth["frames"]


def test_transitions_type_and_timing(analysed):
    _fps, truth, _, transitions, *_ = analysed
    assert [t.kind for t in transitions] == [t["kind"] for t in truth["transitions"]]
    for got, want in zip(transitions, truth["transitions"], strict=True):
        assert abs(got.start_f - want["start"]) <= 1, (got, want)
        assert abs((got.end_f - got.start_f) - want["frames"]) <= 2, (got, want)
    push = next(t for t in transitions if t.kind == "push")
    assert push.direction == "left"


def test_shots_follow_scenes(analysed):
    _, truth, _, _, shots, *_ = analysed
    assert [s.start_f for s in shots] == pytest.approx(truth["scene_starts"], abs=1)


def test_every_motion_found_with_exact_start(analysed):
    _, truth, _, _, _, events, _ = analysed
    assert len(events) == len(truth["motions"])
    for got, want in zip(events, truth["motions"], strict=True):
        assert abs(got.start_f - want["f0"]) <= 1, (got, want)
        assert got.end_f <= want["f1"] + 1
        assert got.kind == "motion" and got.camera_move == "none"


def test_dead_hold_found(analysed):
    fps, truth, _, _, _shots, _, holds = analysed
    dead = [h for h in holds if h.dead]
    assert len(dead) == 1
    hold = dead[0]
    scene_start = truth["scene_starts"][EXPLAINER_DEAD_HOLD["scene"]]
    assert abs(hold.start_f - (scene_start + round(EXPLAINER_DEAD_HOLD["start_s"] * fps))) <= 2
    assert abs(hold.end_f - (scene_start + round(EXPLAINER_DEAD_HOLD["end_s"] * fps))) <= 2


def test_pace_curve_handles_a_one_frame_shot():
    """A flash between two cuts gives a 1-frame shot: no frame-to-frame motion inside it, not NaN."""
    import math

    import numpy as np

    from lens.signals.video import FrameSeries, Transition, pace_curve

    n = 10
    fs = FrameSeries(
        fps=30.0,
        diff=np.linspace(0, 0.1, n),
        thumbs=np.zeros((n, 36, 64), np.float32),
        mids=np.zeros((n, 72, 128), np.uint8),
        bboxes=np.full((n, 4), np.nan),
        tx=np.zeros(n),
        ty=np.zeros(n),
        scale=np.ones(n),
    )
    shots = build_shots(n, [Transition("hard_cut", 4, 4), Transition("hard_cut", 5, 5)])
    assert [(s.start_f, s.end_f) for s in shots] == [(0, 4), (4, 5), (5, 10)]
    rows = pace_curve(fs, shots, [])
    assert all(not math.isnan(float(r["motion_energy"])) for r in rows)
    assert rows[1]["motion_energy"] == 0.0
