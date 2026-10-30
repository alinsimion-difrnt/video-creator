"""Words on a room surface (tournament n08): the wood mask, the plane's quad and the homography."""

import numpy as np

from create.footage import surface as sf


def test_homography_maps_the_four_corners_and_is_projective() -> None:
    src = [(0, 0), (600, 0), (600, 1600), (0, 1600)]
    dst = [(100, 50), (700, 180), (690, 1500), (110, 1700)]
    h = sf.homography(src, dst)
    for s, d in zip(src, dst, strict=True):
        assert np.allclose(sf.apply(h, *s), d, atol=1e-6)
    # straight lines stay straight: the card's middle lands on the line between the quad's edge midpoints
    mid = sf.apply(h, 300, 0)
    assert dst[0][0] < mid[0] < dst[1][0]


def test_css_matrix3d_is_column_major_with_z_untouched() -> None:
    h = sf.homography([(0, 0), (1, 0), (1, 1), (0, 1)], [(0, 0), (2, 0), (2, 3), (0, 3)])  # a scale
    vals = [float(v) for v in sf.css_matrix3d(h)[len("matrix3d(") : -1].split(",")]
    assert np.allclose(vals, [2, 0, 0, 0, 0, 3, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1], atol=1e-9)


def test_wood_mask_and_plane_quad_find_a_receding_slat_wall() -> None:
    img = np.full((400, 300, 3), 235, np.uint8)  # a cream wall
    for x in range(40, 260):
        top = int(20 + (x - 40) * 0.3)  # the top rail slopes down to the right
        bot = int(380 - (x - 40) * 0.1)
        if (x // 8) % 2 == 0:  # slats with dark gaps
            img[top:bot, x] = (160, 100, 50)  # wood
        else:
            img[top:bot, x] = (40, 35, 30)
    m = sf.wood_mask(img, hue=(15, 40), sat_min=0.35, val=(0.25, 0.95))
    assert m[200, 48] and not m[200, 40] and not m[5, 100]  # a slat, a gap, the wall above
    q = sf.plane_quad(m, 40, 260)
    assert abs(q[0][1] - 20) < 3 and abs(q[1][1] - (20 + 220 * 0.3)) < 3
    assert abs(q[3][1] - 379) < 4 and abs(q[2][1] - (379 - 220 * 0.1)) < 4  # its last row is bot - 1
