"""F5 framing: steady per-segment crops that follow the face, alternate punch-ins, square bubble crops."""

import pytest

from create.footage.reframe import fill_crop, median_face, pip_crop, primary_face
from lens.config import REPO_ROOT, load_config

R = load_config(REPO_ROOT / "config" / "lens.yaml").create.footage.reframe


def test_primary_face_is_the_largest_confident_one():
    faces = [[133, 53, 28, 36, 0.92], [547, 86, 211, 280, 0.95], [900, 90, 300, 300, 0.4]]
    assert primary_face(faces, R.min_score) == [547, 86, 211, 280]
    assert primary_face([], R.min_score) is None


def test_median_face_ignores_missing_samples():
    assert median_face([None, [10, 10, 100, 100], [30, 10, 100, 100], [20, 12, 100, 100]]) == [
        20,
        10,
        100,
        100,
    ]
    assert median_face([None, None]) is None


def test_landscape_to_vertical_crop_follows_the_face_and_stays_inside():
    face = [1400, 300, 200, 260]  # right of centre on a 1920x1080 master
    c = fill_crop(1920, 1080, 1080, 1920, face, zoom=1.0, eye_line=R.eye_line)
    assert (c.w, c.h) == (607, 1080) or abs(c.w / c.h - 1080 / 1920) < 0.01
    assert c.x <= 1400 + 100 <= c.x + c.w  # the face centre is in the crop
    assert abs((c.x + c.w / 2) - 1500) <= 2  # and centred on it
    edge = fill_crop(1920, 1080, 1080, 1920, [1850, 300, 60, 80], zoom=1.0, eye_line=R.eye_line)
    assert edge.x + edge.w == 1920  # clamped to the master


def test_punch_in_shrinks_the_crop_around_the_eyes():
    face = [860, 300, 200, 260]
    a = fill_crop(1920, 1080, 1920, 1080, face, zoom=1.0, eye_line=R.eye_line)
    b = fill_crop(1920, 1080, 1920, 1080, face, zoom=1.12, eye_line=R.eye_line)
    assert (a.w, a.h) == (1920, 1080)
    assert b.w == pytest.approx(1920 / 1.12, abs=2) and b.x > 0


def test_no_face_means_centre_crop():
    c = fill_crop(1920, 1080, 1080, 1920, None, zoom=1.0, eye_line=R.eye_line)
    assert abs((c.x + c.w / 2) - 960) <= 1 and c.y == 0


def test_pip_crop_is_a_square_around_the_face():
    c = pip_crop(1920, 1080, [860, 300, 200, 260], R.pip_face_scale)
    assert c.w == c.h and c.w == pytest.approx(200 * R.pip_face_scale, abs=2)
    assert c.x <= 960 <= c.x + c.w and c.y <= 430 <= c.y + c.h
    big = pip_crop(1920, 1080, [700, 100, 600, 800], R.pip_face_scale)
    assert big.h <= 1080 and big.y >= 0  # never larger than the master


def test_bubble_sits_in_the_safe_corner_above_the_captions():
    from create.footage.pip import bubble_position

    design = load_config(REPO_ROOT / "config" / "lens.yaml").create.design
    v = design.frames["vertical"]
    x, y = bubble_position(v, 380, R.pip_margin, "br")
    assert any(r.contains(x, y, x + 380, y + 380) for r in v.safe)  # fully inside one safe rect
    assert y + 380 <= v.caption_band.y0  # never under the burned-in captions
    lx, _ = bubble_position(design.frames["landscape"], 340, R.pip_margin, "br")
    assert lx + 340 == design.frames["landscape"].safe[0].x1 - R.pip_margin
    tx, ty = bubble_position(v, 380, R.pip_margin, "tl")
    assert (tx, ty) == (v.safe[0].x0 + R.pip_margin, v.safe[0].y0 + R.pip_margin)


def _layout_inputs():
    from lens.schemas.create import Edl, Framing, Timeline

    prov = {
        "schema_version": 1,
        "tool_version": "0",
        "stage": "x",
        "annotator": "code",
        "input_hash": "0" * 64,
        "created_at": "2026-10-09T00:00:00Z",
    }
    timeline = Timeline.model_validate(
        {
            "provenance": prov,
            "project": "demo",
            "fps": 30,
            "total_s": 10.0,
            "scenes": [
                {"scene": "s01", "start_s": 0, "end_s": 5, "voice_start_s": 0.2, "voice_end_s": 4.8},
                {"scene": "s02", "start_s": 5, "end_s": 10, "voice_start_s": 5.2, "voice_end_s": 9.8},
            ],
            "words": [
                {"i": 0, "text": "Hi", "start_s": 0.2, "end_s": 0.5, "scene": "s01"},
                {"i": 1, "text": "there", "start_s": 5.2, "end_s": 5.5, "scene": "s02"},
            ],
        }
    )
    seg = {"take": "t1", "src_in": 0, "src_out": 300, "rec_in": 0}
    edl = Edl.model_validate(
        {
            "provenance": prov,
            "project": "demo",
            "fps": 30,
            "applied": [],
            "duration_frames": 300,
            "segments": [seg],
        }
    )
    framing = Framing.model_validate(
        {
            "provenance": prov,
            "project": "demo",
            "frame": "vertical",
            "width": 1080,
            "height": 1920,
            "segments": [
                {
                    "segment": 0,
                    "take": "t1",
                    "face": [1400, 300, 200, 260],
                    "zoom": 1.0,
                    "full": {"x": 1196, "y": 0, "w": 608, "h": 1080},
                    "pip": {"x": 0, "y": 0, "w": 10, "h": 10},
                }
            ],
        }
    )
    return timeline, edl, framing


def test_layout_poses_move_the_face_into_the_bubble():
    from create.footage.layout import poses
    from create.footage.pip import bubble_position
    from lens.schemas.create import LayoutPlan

    design = load_config(REPO_ROOT / "config" / "lens.yaml").create.design
    v = design.frames["vertical"]
    timeline, edl, framing = _layout_inputs()
    full, pip = poses(
        timeline, LayoutPlan(scenes={"s02": "pip"}), edl, framing, v, 380, R.pip_margin, R.pip_face_scale
    )
    assert (full.layout, full.scale, full.x, full.y) == ("full", 1, 0, 0)
    corners = [((full.cx - x) ** 2 + (full.cy - y) ** 2) ** 0.5 for x in (0, 1080) for y in (0, 1920)]
    assert max(corners) < full.r < max(corners) + 5  # just covers the frame
    bx, by = bubble_position(v, 380, R.pip_margin, "br")
    s = 1080 / 608  # master -> output
    cx, cy, fw = (1500 - 1196) * s, 430 * s, 200 * s
    assert pip.scale == pytest.approx(380 / (fw * R.pip_face_scale))
    assert pip.x + pip.scale * cx == pytest.approx(bx + 190)  # the face lands in the bubble's centre
    assert pip.y + pip.scale * cy == pytest.approx(by + 190)
    assert pip.r * pip.scale == pytest.approx(190)  # and the clip is the bubble


def test_layout_plan_must_name_timeline_scenes():
    from create.footage.layout import check_plan
    from lens.schemas.create import LayoutPlan

    timeline, _, _ = _layout_inputs()
    assert check_plan(LayoutPlan(scenes={"s02": "pip"}), timeline) == []
    assert check_plan(LayoutPlan(scenes={"s09": "pip"}), timeline)


def test_a_wide_product_video_is_contained_not_cropped():
    from create.footage.layout import background_filter

    v = load_config(REPO_ROOT / "config" / "lens.yaml").create.design.frames["vertical"]
    f = background_filter(1920, 1080, v, "auto", "#F5F7FA")
    assert (
        "scale=1080:608" in f and "pad=1080:1920:0:288" in f and "crop" not in f
    )  # whole width, top of safe
    assert "crop=1080:1920" in background_filter(1080, 1920, v, "auto", "#F5F7FA")  # same shape: cover
    assert "crop" in background_filter(1920, 1080, v, "cover", "#F5F7FA")  # asked for


def test_split_moves_the_presenter_below_the_product():
    from create.footage.layout import background_rect, poses
    from lens.schemas.create import LayoutPlan

    v = load_config(REPO_ROOT / "config" / "lens.yaml").create.design.frames["vertical"]
    mode, _, y, _, h = background_rect(1920, 1080, v, "auto")
    seam = y + h
    assert mode == "contain" and seam == 288 + 608
    timeline, edl, framing = _layout_inputs()
    plan = LayoutPlan(scenes={"s02": "split"})
    full, split = poses(
        timeline, plan, edl, framing, v, 380, R.pip_margin, R.pip_face_scale, seam, R.split_face_offset
    )
    assert full.top == 0 and split.top == seam  # clipped above the product's bottom edge
    assert split.scale == 1 and split.cy + split.y == pytest.approx(
        seam + R.split_face_offset
    )  # face moved lower


def test_overlay_zones_keep_clear_of_the_face_and_captions():
    from create.footage.overlays import place, zones
    from lens.schemas.create import OverlayItem

    v = load_config(REPO_ROOT / "config" / "lens.yaml").create.design.frames["vertical"]
    face = (380.0, 560.0, 700.0, 960.0)  # Robert's take: face centred, top at y 560
    zs = zones(v, face, 28)
    top = zs["top"]
    assert top is not None and top.y1 <= 560 - 28 and (top.x0 + top.x1) / 2 == 540  # above the head, centred
    assert zs["left"] is None and zs["right"] is None  # no room beside a centred face
    keyword = OverlayItem(word=0, kind="keyword", title="Google Maps")
    assert place(keyword, v, face, 28) == top
    side = (560.0, 560.0, 860.0, 960.0)  # face to the right: the left side opens up
    z = place(OverlayItem(word=0, kind="card", title="Ask for context", position="left"), v, side, 28)
    assert z.x1 <= 560 - 28 and z.y1 <= v.caption_band.y0 - 28


def test_crops_never_pass_the_source_edge():
    from create.footage.reframe import fill_crop

    for zoom in (1.0, 1.07, 1.12, 1.13):
        for fx in (0.0, 900.0, 1500.0, 1919.0):
            c = fill_crop(1920, 1080, 1080, 1920, [fx, 300.0, 200.0, 240.0], zoom, 0.42)
            assert c.x >= 0 and c.x + c.w <= 1920 and c.y >= 0 and c.y + c.h <= 1080


def test_a_segment_with_no_face_sample_uses_the_nearest_ones():
    from create.footage.reframe import nearest_face

    track = [
        (0.0, [100.0, 100.0, 50.0, 60.0]),
        (0.2, None),
        (0.4, [110.0, 100.0, 50.0, 60.0]),
        (5.0, [900.0, 0, 1, 1]),
    ]
    assert nearest_face(track, 0.25, n=2) == [105.0, 100.0, 50.0, 60.0]
    assert nearest_face([(0.0, None)], 0.0) is None
