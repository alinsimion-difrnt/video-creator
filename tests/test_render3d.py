"""The SDF renderer (create/render3d, ADR 0029): volumes render, turn and keep a clean background."""

from __future__ import annotations

import numpy as np

from create.render3d import fred3d
from create.render3d.sdf import Material, Prim, render


def test_a_sphere_renders_lit_from_the_top_left_on_a_clear_background():
    img = np.asarray(
        render([Prim("ellipsoid", (0, 0, 0), (1, 1, 1), 0)], [Material((1, 0.5, 0.2))], (48, 48))
    )
    assert img.shape == (48, 48, 4)
    assert img[0, 0, 3] == 0 and img[24, 24, 3] == 255  # transparent corner, solid middle
    lum = img[..., :3].astype(int).sum(-1)
    assert lum[16, 16] > lum[32, 32]  # the key light comes from the top left


def test_fred_turns_and_every_animation_has_poses():
    for anim, n in (("turn", 16), ("idle", 6), ("hop", 6), ("wave", 6)):
        assert len(fred3d.poses(anim)) == n
    front = np.asarray(fred3d.frame(fred3d.Pose(), size=(40, 58)))
    back = np.asarray(fred3d.frame(fred3d.Pose(yaw=np.pi), size=(40, 58)))
    assert front[..., 3].sum() > 0 and back[..., 3].sum() > 0
    assert np.abs(front.astype(int) - back.astype(int)).mean() > 5  # the turntable shows another side


def test_accessories_add_volume_where_they_sit():
    plain = np.asarray(fred3d.frame(fred3d.Pose(), size=(40, 58)))[..., 3]
    hat = np.asarray(fred3d.frame(fred3d.Pose(), frozenset({"top_hat"}), size=(40, 58)))[..., 3]
    assert hat[:12].sum() > plain[:12].sum()  # the hat fills the top of the box


def test_carp_skin_moves_with_him_in_a_hop() -> None:
    """The scale texture is pinned to the body: lifted by a hop, the same body point keeps its colour (no
    scales sliding over him, the pixel-art boiling rule)."""
    import numpy as np

    from create.render3d.fred3d import Pose, carp_skin

    pts = np.array([[0.3, -0.2, 0.4], [-0.2, -0.5, 0.45], [0.1, 0.0, 0.5]])
    rest = carp_skin(Pose()).texture
    up = carp_skin(Pose(lift=0.37)).texture
    assert rest is not None and up is not None
    assert np.allclose(rest(pts), up(pts + np.array([0.0, 0.37, 0.0])))
    assert not np.allclose(rest(pts), rest(pts + np.array([0.0, 0.05, 0.0])))  # it is a pattern
