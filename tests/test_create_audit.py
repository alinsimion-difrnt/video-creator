"""Safe-zone audit (M-C): critical boxes must sit inside the frame's safe area and out of the caption band."""

import json
import shutil
from pathlib import Path

import pytest

from create.safezone import Box, violations
from lens.config import REPO_ROOT, load_config

CFG = load_config(REPO_ROOT / "config" / "lens.yaml").create.design
VERTICAL = CFG.frames["vertical"]


def _box(x0: float, y0: float, x1: float, y1: float, t: float = 1.0, kind: str = "text") -> Box:
    return Box(scene="s01", t=t, element="#a", kind=kind, text="Hello", x0=x0, y0=y0, x1=x1, y1=y1, opacity=1)


def test_inside_the_core_is_fine():
    assert violations([_box(200, 400, 700, 600)], VERTICAL, CFG.audit_tolerance_px) == []


def test_under_the_action_rail_is_flagged():
    (v,) = violations([_box(200, 900, 850, 1000)], VERTICAL, CFG.audit_tolerance_px)  # above the band
    assert v.problem == "outside_safe" and v.scene == "s01"


def test_wide_headline_above_the_rail_uses_the_upper_extension():
    assert violations([_box(130, 300, 880, 500)], VERTICAL, CFG.audit_tolerance_px) == []
    assert violations([_box(130, 300, 960, 500)], VERTICAL, CFG.audit_tolerance_px)  # past x 888


def test_under_the_bottom_ui_is_flagged():
    assert violations([_box(200, 1300, 700, 1400)], VERTICAL, CFG.audit_tolerance_px)


def test_scene_text_in_the_caption_band_is_flagged_but_captions_are_not():
    (v,) = violations([_box(320, 1100, 700, 1200)], VERTICAL, CFG.audit_tolerance_px)
    assert v.problem == "in_caption_band"
    assert violations([_box(320, 1100, 700, 1200, kind="caption")], VERTICAL, CFG.audit_tolerance_px) == []


def test_tolerance_allows_a_hairline_overflow():
    assert violations([_box(119, 400, 781, 600)], VERTICAL, 2) == []
    assert violations([_box(110, 400, 700, 600)], VERTICAL, 2)


def test_offscreen_boxes_are_ignored():
    assert violations([_box(-900, 400, -100, 600)], VERTICAL, 2) == []  # entering from outside the frame


def _has_playwright() -> bool:
    try:
        import playwright.sync_api  # noqa: F401
    except ImportError:
        return False
    from create.browser import available

    return available()


@pytest.mark.skipif(not _has_playwright(), reason="needs playwright + Chromium (uv run --with playwright)")
def test_probe_reads_boxes_from_a_built_scene(tmp_path: Path):
    from create.audit import probe_scene

    scene = tmp_path / "s01"
    (scene / "assets").mkdir(parents=True)
    shutil.copy(REPO_ROOT / "tests" / "fixtures" / "create" / "audit-scene.html", scene / "index.html")
    boxes = probe_scene(scene / "index.html", "s01", 1080, 1920, step_s=0.5, min_opacity=0.1)
    texts = {(b.text, b.t) for b in boxes}
    assert ("Safe", 0.0) in texts and ("Under the rail", 1.0) in texts
    assert ("Under the rail", 0.0) not in texts  # hidden until 0.5 s
    bad = violations(boxes, VERTICAL, 2)
    assert {v.text for v in bad} == {"Under the rail"}
    assert json.loads(json.dumps([b.model_dump() for b in boxes]))


def test_short_problems_are_motion_not_layout():
    from create.safezone import persistent

    step = 0.2
    passing = [_box(850, 900, 900, 1000, t=t) for t in (1.0, 1.2)]  # 0.4 s: an entrance
    held = [_box(850, 900, 900, 1000, t=round(2.0 + i * step, 1)) for i in range(5)]  # 1.0 s
    hits = violations(passing + held, VERTICAL, 2)
    (issue,) = persistent(hits, step, min_hold_s=0.5)
    assert (issue.t0, issue.t1, issue.problem) == (2.0, 2.8, "outside_safe")
    assert len(persistent(hits, step, min_hold_s=0.4)) == 2


def test_vertical_caption_band_is_centred_and_inside_the_core():
    band, core = VERTICAL.caption_band, VERTICAL.safe[0]
    assert (band.x0 + band.x1) / 2 == VERTICAL.width / 2  # reads as centred on a phone
    assert core.contains(band.x0, band.y0, band.x1, band.y1)
