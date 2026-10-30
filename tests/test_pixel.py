"""create/pixel (ADR 0028): ramps, the renderer's rules, and the sprites' frames."""

import colorsys

import numpy as np
import pytest

from create.pixel import fishes, fred, kitten
from create.pixel.core import Canvas, Shape, ramp


def _hue(c: tuple[int, int, int, int]) -> float:
    return colorsys.rgb_to_hsv(*(v / 255 for v in c[:3]))[0]


def test_ramps_go_dark_to_light_and_shift_hue():
    r = ramp("#ff8a24", 5, 3)
    lum = [0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2] for c in r]
    assert lum == sorted(lum)  # dark to light
    assert r[3][:3] == (255, 138, 36)  # the base sits at its index
    assert _hue(r[0]) < _hue(r[3]) or _hue(r[0]) > 0.5  # shadows move away from orange (toward red/purple)


def test_render_outlines_shades_and_cleans():
    cv = Canvas(20, 20, {"m": ramp("#3a6fc8", 5, 3)})
    img = np.asarray(cv.render([Shape("ellipse", "m", cx=10, cy=10, rx=6, ry=6)]))
    a = img[..., 3]
    assert a[10, 10] == 255 and a[0, 0] == 0
    assert a[10, 3] == 255  # the outline ring sits just outside the shape
    colors = {tuple(img[y, x]) for y in range(4, 17) for x in range(4, 17) if a[y, x]}
    assert len(colors) >= 3  # lit, mid and shade


def test_edges_mark_a_limb_in_front():
    ramps = {"b": ramp("#ff8a24", 4, 2), "f": ramp("#ef4a22", 4, 2)}
    body = Shape("ellipse", "b", 1, "body", cx=10, cy=10, rx=8, ry=8)
    limb = Shape("capsule", "f", 2, "limb", a=(8, 8), b=(12, 12), r0=2, r1=2)
    plain = np.asarray(Canvas(20, 20, ramps).render([body, limb]))
    edged = np.asarray(Canvas(20, 20, ramps).render([body, Shape(**{**limb.__dict__, "edge": True})]))
    assert (plain != edged).any()


@pytest.mark.parametrize("anim", list(kitten.FPS))
def test_kitten_frames(anim: str):
    frames = kitten.frames(anim, {"fur": "#f2a65a"})
    assert frames and all(f.size == (kitten.W, kitten.H) for f in frames)


@pytest.mark.parametrize("anim", list(fred.FPS))
def test_fred_frames_with_accessories(anim: str):
    frames = fred.frames(anim, {"top_hat", "moustache", "automail"})
    assert frames and all(f.size == (fred.W, fred.H) for f in frames)
    plain = fred.frames(anim)
    assert np.asarray(frames[0]).tolist() != np.asarray(plain[0]).tolist()


@pytest.mark.parametrize("name", list(fishes.SPECIES))
def test_fish_icons_have_an_ink_outline_and_texture(name: str):
    img = np.asarray(fishes.fish(name))
    a = img[..., 3]
    assert img.shape[:2] == (fishes.H, fishes.W) and a.sum() > 0
    ink = (img[..., :3] == fishes.INK[:3]).all(axis=2) & (a > 0)
    assert ink.sum() > 40  # the silhouette is ringed in the warm ink
    colors = {tuple(p) for p in img[a > 0].tolist()}
    assert len(colors) >= 8  # ramps, fins and texture, not flat fills
    assert np.asarray(fishes.frames(name)[0]).tolist() != np.asarray(fishes.frames(name)[1]).tolist()


def test_counter_shading_darkens_the_back():
    from create.pixel.core import blend

    cv = Canvas(30, 30, {"b": blend("#3a5a1a", "#f0d090", 5)}, mode="ink")
    img = np.asarray(cv.render([Shape("spine", "b", pts=[(5, 15), (25, 15)], radii=[6, 6], shade="counter")]))
    lum = img[..., :3].astype(int).sum(axis=2)
    assert lum[11, 15] < lum[19, 15]  # above the spine (its left: the back) is darker than below (the belly)
