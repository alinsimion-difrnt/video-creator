"""Bullet time (tournament n05): the 2.5D warp and the camera arc (the depth model itself is not run here)."""

import numpy as np

from create.footage import depth as dp


def test_no_move_is_the_identity() -> None:
    img = (np.random.default_rng(1).random((60, 40, 3)) * 255).astype(np.uint8)
    out = dp.warp(img, np.random.default_rng(2).random((60, 40)).astype(np.float32), 0, 0, 1.0)
    assert np.abs(out.astype(int) - img.astype(int)).max() <= 1


def test_near_moves_more_than_far() -> None:
    img = np.zeros((40, 100, 3), np.uint8)
    img[:, 48:52] = 255  # a bright post in the middle
    near = np.zeros((40, 100), np.float32)
    near[:, 40:60] = 1.0  # the post is near
    out = dp.warp(img, near, dx=6, dy=0, zoom=1.0)
    col = int(np.argmax(out[20, :, 0]))
    assert 53 <= col <= 57  # shifted by about dx
    far = np.zeros((40, 100), np.float32)
    assert int(np.argmax(dp.warp(img, far, 6, 0, 1.0)[20, :, 0])) == 48  # far: it stays


def test_orbit_swings_and_pushes_in() -> None:
    o = dp.orbit(31, amp=40, push=0.1)
    assert o[0][0] == -40 and abs(o[-1][0] - 40) < 1e-9 and abs(o[15][0]) < 1e-9
    assert o[0][2] == 1.0 and abs(o[-1][2] - 1.1) < 1e-9


def test_time_look_drains_colour_and_darkens_the_corners() -> None:
    img = np.zeros((50, 50, 3), np.uint8)
    img[...] = (200, 60, 60)
    out = dp.time_look(img, drain=0.5, cool=0.1, vignette=0.5).astype(int)
    assert out[25, 25, 0] - out[25, 25, 1] < 140  # less red than before (140 apart)
    assert out[0, 0].sum() < out[25, 25].sum()  # the corner is darker
