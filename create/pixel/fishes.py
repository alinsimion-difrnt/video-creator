"""Fish icons in pixel art (ADR 0028 addendum): a study set and the "pixel art" look of a picture of a fish.

Drawn the way premium fishing-game icons are (Robert's reference sheet, studied, nothing copied): 32 x 32, one
warm dark ink outline, a body bent along a curve (head up and right, tail down and left), counter-shading (a
dark back, a light belly, a pale rim on the belly), texture instead of smooth shading (mottled patches of a
second hue, single-pixel spots, fins with rays), fins in a contrasting colour, a tiny two-pixel eye.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from PIL import Image

from create.pixel.core import Canvas, Shape, blend, ramp

W = H = 32
INK = (43, 29, 20, 255)  # warm dark brown: the outline of every icon


@dataclass(frozen=True)
class Species:
    back: str  # the darkest body colour (along the back)
    belly: str
    fin: str
    pattern: str = "mottle"  # mottle | spots | scales | ""
    accent: str = ""  # mottle / spots colour
    density: float = 0.3
    girth: float = 1.0  # body thickness
    bend: float = 1.0  # how much the body curves (negative: the other way, a curl)
    accent2: str = ""  # a second mottle hue


SPECIES: dict[str, Species] = {
    "perch": Species("#4f6a1e", "#f1c27d", "#ef6a2b", "mottle", "#2a6f6a", 0.3, 1.05, 0.8, "#a7a33a"),
    "trout": Species("#55603a", "#e9c79a", "#d9542c", "spots", "#f5a623", 0.06, 0.95),
    "goldfish": Species("#c4471c", "#ffd08a", "#ff8a2e", "scales", "", 0.3, 1.1, 0.8),
    "bluefin": Species("#1f6f86", "#d8c25a", "#9a6a2e", "mottle", "#3bb0c2", 0.35, 0.85, -1.3, "#c9b44a"),
    "salmon": Species("#6b6f7a", "#f3b08a", "#c9473c", "spots", "#2b2a33", 0.05, 0.95, 1.3),
}


def _spine(bend: float, girth: float) -> tuple[list[tuple[float, float]], list[float]]:
    """Tail (lower left) to head (upper right), curving like an S by `bend`."""
    pts = []
    for k in range(6):
        t = k / 5
        x = 8.5 + t * 18
        y = 23.5 - t * 17
        off = math.sin(t * math.pi) * 2.6 * bend  # one gentle arc, belly out (a fish flopping)
        pts.append((x + off * 0.7, y + off * 0.7))
    radii = [g * girth for g in (1.7, 3.6, 5.4, 5.9, 5.0, 2.9)]
    return pts, radii


def _norm(x: float, y: float) -> tuple[float, float]:
    d = math.hypot(x, y) or 1
    return x / d, y / d


def fish(name: str, flip_tail: float = 0.0) -> Image.Image:
    """One fish icon. `flip_tail` (-1..1) swings the tail fan (for a two-frame flop)."""
    sp = SPECIES[name]
    ramps: dict[str, Any] = {
        "body": blend(sp.back, sp.belly, 5),
        "fin": ramp(sp.fin, 4, 2),
    }
    if sp.accent:
        ramps["accent"] = ramp(sp.accent, 4, 2)
    if sp.accent2:
        ramps["accent2"] = ramp(sp.accent2, 4, 2)
    pts, radii = _spine(sp.bend, sp.girth)
    shapes = [Shape("spine", "body", 3, "body", pts=pts, radii=radii, shade="counter", rim=True,
                    pattern=sp.pattern, pattern_mat="accent" if sp.accent else "", density=sp.density, seed=3,
                    pattern_mat2="accent2" if sp.accent2 else "")]  # fmt: skip
    # direction along the body near the tail and the head; back is to the left of travel
    tx, ty = _norm(pts[0][0] - pts[1][0], pts[0][1] - pts[1][1])
    hx, hy = _norm(pts[-1][0] - pts[-2][0], pts[-1][1] - pts[-2][1])
    bx, by = hy, -hx  # the back side (left of the head's direction)
    # tail fan: forked, swung by flip_tail
    a = math.atan2(ty, tx) + flip_tail * 0.35
    ux, uy = math.cos(a), math.sin(a)
    px, py = -uy, ux
    base = pts[0]
    tail = [
        (base[0] + px * 1.5, base[1] + py * 1.5),
        (base[0] + ux * 7 + px * 5.5, base[1] + uy * 7 + py * 5.5),
        (base[0] + ux * 4, base[1] + uy * 4),
        (base[0] + ux * 7 - px * 5.5, base[1] + uy * 7 - py * 5.5),
        (base[0] - px * 1.5, base[1] - py * 1.5),
    ]
    shapes.append(
        Shape("poly", "fin", 2, "tail", pts=tail, flat=0.5, pattern="rays", ray_angle=a, edge=False)
    )
    # dorsal fin along the back between the 2nd and 4th points
    p1, p3 = pts[1], pts[3]
    r1, r3 = radii[1], radii[3]
    p2 = pts[2]
    r2 = radii[2]
    dorsal = [  # spiny: three ray tips
        (p1[0] + bx * (r1 - 0.5), p1[1] + by * (r1 - 0.5)),
        (p1[0] + bx * (r1 + 3.2), p1[1] + by * (r1 + 3.2)),
        ((p1[0] + p2[0]) / 2 + bx * ((r1 + r2) / 2 + 1.8), (p1[1] + p2[1]) / 2 + by * ((r1 + r2) / 2 + 1.8)),
        (p2[0] + bx * (r2 + 4.6), p2[1] + by * (r2 + 4.6)),
        ((p2[0] + p3[0]) / 2 + bx * ((r2 + r3) / 2 + 2.0), (p2[1] + p3[1]) / 2 + by * ((r2 + r3) / 2 + 2.0)),
        (p3[0] + bx * (r3 + 3.4), p3[1] + by * (r3 + 3.4)),
        (p3[0] + bx * (r3 - 0.5), p3[1] + by * (r3 - 0.5)),
    ]
    shapes.append(
        Shape(
            "poly",
            "fin",
            2,
            "dorsal",
            pts=dorsal,
            flat=0.5,
            pattern="rays",
            ray_angle=math.atan2(-by, -bx) + 1.5,
        )
    )
    # belly fins (pelvic, anal) and a pectoral fin over the body behind the gill
    for k, size in ((2, 4.2), (1, 3.4)):
        pk, rk = pts[k], radii[k]
        fin = [
            (pk[0] - bx * (rk - 0.6) + hx * 1.5, pk[1] - by * (rk - 0.6) + hy * 1.5),
            (pk[0] - bx * (rk + size) - hx * 1.2, pk[1] - by * (rk + size) - hy * 1.2),
            (pk[0] - bx * (rk - 0.6) - hx * 1.8, pk[1] - by * (rk - 0.6) - hy * 1.8),
        ]
        shapes.append(Shape("poly", "fin", 2, f"belly{k}", pts=fin, flat=0.5, lift=-1))
    p4 = pts[4]
    pect = [
        (p4[0] - hx * 1.0, p4[1] - hy * 1.0),
        (p4[0] - hx * 6.0 - bx * 3.0, p4[1] - hy * 6.0 - by * 3.0),
        (p4[0] - hx * 4.5 + bx * 0.5, p4[1] - hy * 4.5 + by * 0.5),
    ]
    shapes.append(Shape("poly", "fin", 4, "pect", pts=pect, flat=0.7, lift=1))
    # a gill line: a curved darker band just behind the head
    p4, r4 = pts[4], radii[4]
    shapes.append(Shape("capsule", "body", 3, "body", a=(p4[0] + bx * (r4 - 1), p4[1] + by * (r4 - 1)),
                        b=(p4[0] - bx * (r4 - 1.5) + hx * 0.8, p4[1] - by * (r4 - 1.5) + hy * 0.8),
                        r0=0.45, r1=0.45, level=1))  # fmt: skip
    cv = Canvas(W, H, ramps, ink=INK, mode="ink")
    img = cv.render(shapes, contact=True)
    # the mouth: an ink notch at the snout, on the belly side
    tip = pts[-1]
    mx, my = (
        round(tip[0] + hx * (radii[-1] - 0.5) - bx * 1.0),
        round(tip[1] + hy * (radii[-1] - 0.5) - by * 1.0),
    )
    if 0 <= mx < W and 0 <= my < H and img.getchannel("A").getpixel((mx, my)):
        img.putpixel((mx, my), INK)
    # the eye: two pixels (light, dark) near the head on the back side, and a gill line
    head = pts[-1]
    ex, ey = round(head[0] - hx * 1.5 + bx * 1.2), round(head[1] - hy * 1.5 + by * 1.2)
    img.putpixel((ex, ey), (250, 236, 200, 255))
    img.putpixel((ex + 1, ey), INK)
    return img


def sheet(names: list[str] | None = None) -> list[Image.Image]:
    return [fish(n) for n in names or list(SPECIES)]


FPS = {name: 4 for name in SPECIES}  # `create pixel fishes`: each species flops its tail (two frames)


def frames(anim: str) -> list[Image.Image]:
    """A species as a two-frame flop (the tail swings), for previews and Easter eggs."""
    if anim not in SPECIES:
        raise ValueError(f"unknown fish {anim!r} (one of {', '.join(SPECIES)})")
    return [fish(anim, -0.6), fish(anim, 0.6)]
