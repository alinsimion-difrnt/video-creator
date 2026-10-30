"""Words painted on a surface of the room (tournament n08): the slatted partition behind Robert.

The camera is locked, so one master frame is enough. Code measures the surface: a colour mask of the wood
(`wood_mask`), its top and bottom edges fitted as lines over a column span (`plane_quad`), and the homography
that maps a flat text card onto that quad (`homography`, `css_matrix3d`: the CSS transform the page uses).
The page masks the card with the wood mask, so the gaps between the slats stay dark, as paint on slats would.
"""

from __future__ import annotations

import numpy as np

Quad = list[tuple[float, float]]  # top left, top right, bottom right, bottom left (x, y)


def wood_mask(
    rgb: np.ndarray, hue: tuple[float, float], sat_min: float, val: tuple[float, float]
) -> np.ndarray:
    """Pixels whose colour is wood (an orange-brown hue band, saturated, neither black nor blown): bool."""
    x = rgb.astype(np.float32) / 255.0
    mx, mn = x.max(axis=2), x.min(axis=2)
    d = mx - mn
    s = np.where(mx > 0, d / np.maximum(mx, 1e-6), 0.0)
    r, g, b = x[..., 0], x[..., 1], x[..., 2]
    h = np.zeros_like(mx)
    m = d > 1e-6
    rm = m & (mx == r)
    gm = m & (mx == g) & ~rm
    bm = m & ~rm & ~gm
    h[rm] = ((g - b)[rm] / d[rm]) % 6
    h[gm] = (b - r)[gm] / d[gm] + 2
    h[bm] = (r - g)[bm] / d[bm] + 4
    h *= 60.0
    return (h >= hue[0]) & (h <= hue[1]) & (s >= sat_min) & (mx >= val[0]) & (mx <= val[1])


def plane_quad(mask: np.ndarray, x0: int, x1: int, cover: float = 0.02) -> Quad:
    """The surface between columns x0 and x1: per column, its first and last masked rows (columns with less
    than `cover` of their height masked are gaps, skipped); a least-squares line through the tops and one
    through the bottoms; the quad where they meet x0 and x1."""
    xs, tops, bots = [], [], []
    for x in range(x0, x1):
        rows = np.flatnonzero(mask[:, x])
        if len(rows) < cover * mask.shape[0]:
            continue
        xs.append(x)
        tops.append(np.percentile(rows, 0.5))  # robust to a stray pixel, not biased by the span
        bots.append(np.percentile(rows, 99.5))
    if len(xs) < 2:
        raise ValueError("no surface found between those columns")
    at, bt = np.polyfit(xs, tops, 1)
    ab, bb = np.polyfit(xs, bots, 1)
    return [(x0, at * x0 + bt), (x1, at * x1 + bt), (x1, ab * x1 + bb), (x0, ab * x0 + bb)]


def homography(src: Quad, dst: Quad) -> np.ndarray:
    """The 3x3 projective map taking the four `src` points to the four `dst` points (h33 = 1)."""
    a, rhs = [], []
    for (x, y), (u, v) in zip(src, dst, strict=True):
        a.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        a.append([0, 0, 0, x, y, 1, -v * x, -v * y])
        rhs += [u, v]
    h = np.linalg.solve(np.array(a, float), np.array(rhs, float))
    return np.append(h, 1.0).reshape(3, 3)


def apply(h: np.ndarray, x: float, y: float) -> tuple[float, float]:
    p = h @ np.array([x, y, 1.0])
    return (float(p[0] / p[2]), float(p[1] / p[2]))


def css_matrix3d(h: np.ndarray) -> str:
    """The CSS `matrix3d(...)` (column-major 4x4) of a 2D homography, for an element with transform-origin
    0 0: z passes through untouched."""
    m = [
        [h[0, 0], h[0, 1], 0.0, h[0, 2]],
        [h[1, 0], h[1, 1], 0.0, h[1, 2]],
        [0.0, 0.0, 1.0, 0.0],
        [h[2, 0], h[2, 1], 0.0, h[2, 2]],
    ]
    cols = [m[r][c] for c in range(4) for r in range(4)]
    return "matrix3d(" + ",".join(f"{v:.9g}" for v in cols) + ")"
