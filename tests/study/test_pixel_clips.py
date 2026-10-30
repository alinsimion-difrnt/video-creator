"""study/pixel/clips.py: picking pixel-art clips."""

from __future__ import annotations

from study.pixel.clips import pick


def test_pick_keeps_pixel_captions_caps_creators_and_length() -> None:
    metas = [
        {"id": "1", "handle": "a", "likes": 900, "duration_s": 20, "text": "my #pixelart walk cycle"},
        {"id": "2", "handle": "a", "likes": 800, "duration_s": 20, "text": "aseprite timelapse"},
        {
            "id": "3",
            "handle": "a",
            "likes": 700,
            "duration_s": 20,
            "text": "sprite idle",
        },  # a's 3rd: capped at 2
        {"id": "4", "handle": "b", "likes": 600, "duration_s": 300, "text": "pixel art"},  # too long
        {"id": "5", "handle": "c", "likes": 500, "duration_s": 15, "text": "cozy game vlog"},  # not pixel art
        {"id": "6", "handle": "d", "likes": 400, "duration_s": 15, "text": "16-bit boss fight"},
    ]
    assert [m["id"] for m in pick(metas, 10, 2, 90)] == ["1", "2", "6"]
    assert [m["id"] for m in pick(metas, 1, 2, 90)] == ["1"]
