"""study/pixel/metrics.py on synthetic pixel art."""

from __future__ import annotations

import numpy as np
import pytest

from study.pixel import metrics as m
from study.pixel.config import load

CFG = load().measure


def checker_art(h: int = 12, w: int = 16) -> np.ndarray:
    rng = np.random.default_rng(3)
    pal = np.array([[20, 24, 46], [60, 90, 160], [120, 170, 220], [240, 230, 200]], dtype=np.uint8)
    return pal[rng.integers(0, 4, size=(h, w))]


def test_native_scale_finds_the_pixel_size_and_offset() -> None:
    art = checker_art()
    up = np.repeat(np.repeat(art, 4, axis=0), 4, axis=1)
    shifted = np.pad(up, ((2, 0), (1, 0), (0, 0)), mode="edge")  # a crop that starts mid-pixel
    k, ox, oy = m.native_scale(shifted, CFG)
    assert k == 4 and ox == 1 and oy == 2
    back = m.downscale(shifted, k, ox, oy)
    assert np.array_equal(back[: art.shape[0], : art.shape[1]], art)
    assert m.native_scale(art, CFG)[0] == 1


def test_palette_drops_noise_and_counts_shares() -> None:
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[:50] = (200, 40, 40)
    img[0, 0] = (1, 2, 3)  # one stray pixel: noise
    pal = m.palette(img, CFG)
    assert [c for c, _ in pal] == [(0, 0, 0), (200, 40, 40)]
    assert abs(pal[0][1] - 0.4999) < 1e-3


def test_ramps_measure_hue_shift() -> None:
    # a blue ramp that shifts towards cyan as it lightens, and a grey ramp
    blues = [(20, 20, 80), (30, 60, 150), (60, 140, 210), (150, 220, 240)]
    greys = [(30, 30, 30), (110, 110, 110), (220, 220, 220)]
    rs = m.ramps(blues + greys, CFG)
    assert len(rs) == 2
    blue = next(r for r in rs if r.colours[0] == (20, 20, 80))
    assert blue.hue_shift < -20  # 240 deg (blue) to ~195 deg (cyan): negative
    assert blue.lightness_span > 0.6
    grey = next(r for r in rs if r.colours[0] == (30, 30, 30))
    assert abs(grey.hue_shift) < 1


def test_outline_black_vs_none() -> None:
    sprite = np.zeros((10, 10, 4), dtype=np.uint8)
    sprite[2:8, 2:8] = (0, 0, 0, 255)  # black border
    sprite[3:7, 3:7] = (220, 120, 60, 255)  # orange fill
    out = m.outline(sprite, CFG)
    assert out["style"] == "black" and float(out["dark_share"]) > 0.9
    flat = sprite.copy()
    flat[2:8, 2:8] = (220, 120, 60, 255)
    assert m.outline(flat, CFG)["style"] == "none"
    assert m.outline(sprite[..., :3], CFG)["style"] == "unknown"


def test_dither_share() -> None:
    a, b = (10, 10, 10), (200, 200, 200)
    img = np.zeros((8, 8, 3), dtype=np.uint8)
    for y in range(8):
        for x in range(8):
            img[y, x] = a if (x + y) % 2 == 0 else b
    assert m.dither_share(img) == 1.0
    assert m.dither_share(np.zeros((8, 8, 3), dtype=np.uint8)) == 0.0


def test_animation_holds_and_squash() -> None:
    def frame(h: int, w: int) -> np.ndarray:
        f = np.zeros((16, 16, 4), dtype=np.uint8)
        f[16 - h :, 8 - w // 2 : 8 + w // 2, 3] = 255
        return f

    tall, flat = frame(12, 6), frame(6, 12)
    frames = [tall, tall, flat, tall]
    out = m.animation(frames, [100, 100, 50, 100])
    assert out["frames"] == 4 and out["drawings"] == 3
    assert out["hold_ms_max"] == 200 and out["hold_ms_min"] == 50
    assert out["cycle_ms"] == 350
    assert out["squash_stretch"] == 4.0  # 12/6 against 6/12


def test_holds_finds_animation_on_twos() -> None:
    fps = 60.0
    diff = np.zeros(121)
    diff[4::4] = 0.05  # a new drawing every 4 frames at 60 fps: "on 2s" at 30 fps, 15 drawings/s
    out = m.holds(diff, fps, CFG.change_threshold)
    assert out["hold_ms_median"] == pytest.approx(66.7, abs=0.1)
    assert out["on_frames"] == 2.0
    assert out["drawings_per_s"] == pytest.approx(30 / 2.017, abs=0.2)
    assert m.holds(np.zeros(10), fps, CFG.change_threshold)["hold_ms_median"] is None
