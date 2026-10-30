"""Fred in pixel art: the upright fish (standing on his tail, fins as arms) drawn from shapes by
create/pixel/core.py, for his `pixel` style. Native 40 x 56 pixels, facing right.

Animations (frames, frames per second):
- idle 6 @ 8: breathing (a pixel of rise), fins drifting, a blink;
- hop 6 @ 12: squash, launch (stretch), up, top, down, land (squash): travelling on his tail;
- wave 6 @ 10: the front fin goes up and waves;
- clap 4 @ 10: both fins up over his head, together, apart;
- row 4 @ 8: rowing (for the boat; the boat itself is drawn in the page).
Accessories (top_hat, moustache, sunglasses, crown, bow_tie, automail) are shapes too, so they are lit and
outlined like the rest.
"""

from __future__ import annotations

import math
from typing import Any

from PIL import Image

from create.pixel.core import Canvas, Shape, blend, ramp

W, H = 40, 64
OY = 8  # headroom above him for hats and the top of a hop
FPS = {"idle": 8, "hop": 12, "wave": 10, "clap": 10, "row": 8}


def ramps() -> dict[str, list[tuple[int, int, int, int]]]:
    return {
        # the carp (Robert's first catch): an olive back to a golden belly, orange fins and tail
        "body": blend("#5f5c26", "#e8bf5e", 5),  # a darker back, a lighter front (counter-shading)
        "fin": ramp("#ff861a", 4, 2),
        "dorsal": ramp("#9c6a24", 4, 3),
        "belly": ramp("#e9bf5c", 4, 2, spread=0.4),
        "eye": [(255, 255, 255, 255)] * 2,
        "hat": ramp("#2a2638", 4, 2, spread=0.3),  # a black hat, not a purple one
        "band": ramp("#d6283c", 3, 1),
        "gold": ramp("#f8c62a", 4, 2),
        "steel": ramp("#a3adba", 5, 3),
        "tie": ramp("#d6283c", 3, 1),
    }


def fin(
    px: float, py: float, angle_deg: float, near: bool, steel: bool = False, length: float = 7.0
) -> list[Shape]:
    """A fin-arm from the shoulder, `angle_deg` from hanging straight down (+ swings toward his face): a fan,
    narrow at the shoulder, wide and notched at the tip."""
    a = math.radians(angle_deg)
    ux, uy = math.sin(a), math.cos(a)  # along the fin
    vx, vy = -uy, ux  # across it
    tip = (px + length * ux, py + length * uy)
    notch = (px + length * 0.78 * ux, py + length * 0.78 * uy)
    pts = [
        (px + vx * 1.3, py + vy * 1.3),
        (tip[0] + vx * 2.9, tip[1] + vy * 2.9),
        notch,
        (tip[0] - vx * 2.9, tip[1] - vy * 2.9),
        (px - vx * 1.3, py - vy * 1.3),
    ]
    mat = "steel" if steel and near else "fin"
    part = "nearfin" if near else "farfin"
    return [
        Shape(
            "poly",
            mat,
            6 if near else 0,
            part,
            pts=pts,
            flat=0.6,
            lift=0,
            edge=near,
        ),
        Shape(
            "ellipse",
            mat,
            6 if near else 0,
            part,
            cx=px,
            cy=py,
            rx=1.8,
            ry=1.8,
            lift=0 if near else -1,
            edge=near,
        ),
    ]


def body(dy: int = 0, sq: float = 0.0, steel: bool = False) -> list[Shape]:
    """Torso and tail. `sq` squashes (+) or stretches (-) him; the tail stays on the ground."""
    ry, rx = 15 * (1 - sq * 0.12), 11 * (1 + sq * 0.1)
    cy = 27 + dy + sq * 2
    tail = "steel" if steel else "fin"
    air = min(0, dy + 1)  # off the ground: the tail goes up with him (a hop, not a stretch)
    return [
        Shape(
            "poly",
            tail,
            1,
            "tail",
            pts=[
                (20, 38 + dy),
                (12, 54 + air),
                (19, 51 + air),
                (20, 49 + air),
                (21, 51 + air),
                (28, 54 + air),
            ],
            flat=0.6,
            lift=-1,
        ),
        # a long dorsal fin down his back (carp), muted like the photo's
        Shape(
            "poly",
            "dorsal",
            2,
            "body",
            pts=[(12, 16 + cy - 27), (7, 16 + cy - 27), (6, 25 + cy - 27), (10, 22 + cy - 27)],
            level=3,
        ),
        # the ellipse turned a quarter: its local "down" points to his front, so counter-shading darkens his
        # back and lights his belly side; scales and a pale rim along the belly, as in fishing-game icons
        Shape(
            "ellipse",
            "body",
            3,
            "body",
            cx=20,
            cy=cy,
            rx=ry,
            ry=rx,
            angle=-math.pi / 2,
            shade="counter",
            rim=True,
            pattern="net",
        ),
        Shape("ellipse", "belly", 4, "body", cx=24, cy=cy + 5, rx=rx * 0.45, ry=ry * 0.5, flat=0.8, lift=-1),
    ]


EXPRESSIONS = ("shock", "smug", "terror", "happy", "angry")  # face "accessories": they redraw eye and mouth


def face(
    dy: int, blink: bool, look: int = 0, expr: str | None = None
) -> list[tuple[int, int, list[str], dict[str, Any]]]:
    """His eye, lips and smile; `expr` (EXPRESSIONS) redraws the eye and the mouth (tournament n10: Fred
    reacts word by word). Each reads at 1x: one big shape change (eye size, lid, mouth), not detail."""
    pal = {
        "w": (255, 255, 255, 255),
        "k": (29, 26, 36, 255),
        "s": (255, 255, 255, 255),
        "m": (110, 40, 40, 255),
        "c": (255, 130, 110, 255),
        "g": (232, 184, 64, 255),  # the carp's gold iris
        "p": (236, 160, 120, 255),  # peach lips and barbels
    }
    pal |= {"r": (226, 48, 48, 255), "b": (130, 200, 255, 255), "W": (255, 255, 255, 255)}
    lips = (30, 22 + dy, ["pp", "mp", " p", " p"], pal)  # peach lips at the snout, a barbel hanging down
    big = [" ggggg ", "gWWWWWg", "gWWWWWg", "gWWkWWg", "gWWWWWg", "gWWWWWg", " ggggg "]
    # the moustache covers his mouth and the hat brim his brow: an expression lives in the eye and in marks
    # on open skin (the back of his head, beside the eye) -- lab: mouth and brow changes were invisible
    if expr == "shock":  # a big round eye with a pinprick pupil, a "!" behind his head
        return [
            (21, 14 + dy, big, pal),
            lips,
            (26, 23 + dy, [" m ", "mkm", " m "], pal),
            (15, 15 + dy, ["W", "W", "W", " ", "W"], pal),
        ]
    if expr == "terror":  # the shock eye, two big sweat drops behind his head, blue under the eye
        return [
            (21, 14 + dy, big, pal),
            (16, 15 + dy, [" b ", "bbb", "bbb", " b "], pal),
            (13, 21 + dy, [" b", "bb", "bb"], pal),
            (22, 21 + dy, ["bbbbb"], pal),
            lips,
        ]
    if expr == "smug":  # a heavy dark lid over the top half of the eye, eyebrow raised
        return [
            (22 + look, 16 + dy, [" kkk ", "kkkkk", "gkksg", " ggg "], pal),
            lips,
            (26, 23 + dy, ["  m", "mm "], pal),
            (27, 21 + dy, ["c"], pal),
        ]
    if expr == "happy":  # the eye closed in a dark arc, blush on the cheek, a sparkle
        return [
            (21, 17 + dy, [" kkk ", "k   k", "     "], pal),
            lips,
            (25, 23 + dy, ["m   m", " mmm "], pal),
            (24, 21 + dy, ["cc"], pal),
            (17, 14 + dy, [" W ", "WWW", " W "], pal),
        ]
    if expr == "angry":  # a red anger mark behind his head, the eye half shut and narrowed
        return [
            (12, 13 + dy, ["rr rr", "r   r", "     ", "r   r", "rr rr"], pal),
            (22 + look, 17 + dy, ["kkkkk", "gkksg", " ggg "], pal),
            lips,
            (26, 24 + dy, ["mmm"], pal),
        ]
    eye = ["ggggg"] if blink else [" ggg ", "gkkkg", "gkksg", "gkkkg", " ggg "]
    out = [(22 + look, 16 + dy + (2 if blink else 0), eye, pal)]
    out.append(lips)
    out.append((27, 24 + dy, ["mm"], pal))  # the smile
    out.append((27, 21 + dy, ["c"], pal))
    return out


def accessories(acc: set[str], dy: int, sq: float = 0.0) -> list[Shape]:
    top = 27 + dy + sq * 2 - 15 * (1 - sq * 0.12) - 2  # where hats sit: on top of his head, clear of the eye
    out: list[Shape] = []
    if "top_hat" in acc:
        out += [
            Shape(
                "poly",
                "hat",
                8,
                "hat",
                pts=[(15, top - 9), (25, top - 10), (26, top + 1), (16, top + 2)],
                flat=0.3,
            ),
            Shape(
                "poly",
                "band",
                8,
                "hat",
                pts=[(16, top - 1), (26, top - 2), (26, top + 1), (16, top + 2)],
                level=1,
            ),
            Shape("ellipse", "hat", 9, "hat", cx=21, cy=top + 2, rx=8.5, ry=1.6, flat=0.5),
        ]
    if "crown" in acc:
        pts = [
            (14, top + 2),
            (14, top - 5),
            (17, top - 2),
            (20, top - 7),
            (23, top - 2),
            (26, top - 5),
            (26, top + 2),
        ]
        out.append(Shape("poly", "gold", 8, "hat", pts=[(float(x), float(y)) for x, y in pts], flat=0.3))
    if "moustache" in acc:
        out += [
            Shape("ellipse", "hat", 9, "tache", cx=26, cy=24 + dy, rx=2.2, ry=1.1, level=0),
            Shape("ellipse", "hat", 9, "tache", cx=30, cy=24 + dy, rx=2.2, ry=1.1, level=0),
            Shape("capsule", "hat", 9, "tache", a=(24, 24 + dy), b=(23, 22 + dy), r0=1.0, r1=0.7, level=0),
            Shape("capsule", "hat", 9, "tache", a=(32, 24 + dy), b=(33, 22 + dy), r0=1.0, r1=0.7, level=0),
        ]
    if "sunglasses" in acc:
        out.append(
            Shape(
                "poly",
                "hat",
                9,
                "glasses",
                pts=[(20, 16 + dy), (28, 16 + dy), (27, 20 + dy), (21, 20 + dy)],
                level=0,
            )
        )
    if "bow_tie" in acc:
        for side in (20, 28):
            out.append(
                Shape(
                    "poly", "tie", 9, "tie", pts=[(24, 33 + dy), (side, 31 + dy), (side, 36 + dy)], flat=0.4
                )
            )
    return out


def pose(
    cv: Canvas,
    acc: set[str],
    dy: int = 0,
    sq: float = 0.0,
    near: float = -20,
    far: float = -10,
    blink: bool = False,
    reach: float = 7.0,
    far_reach: float | None = None,
) -> Image.Image:
    """Fins: angles from hanging down; + swings forward (toward the face). At rest the near fin hangs a
    little back along his side, so it never reads as a nose."""
    steel = "automail" in acc
    shapes = body(dy, sq, steel) + accessories(acc, dy, sq)
    # shoulders mid-body, below and behind the eye: v03's fin sat at mouth height and read as a duck's bill
    # the arms must break his silhouette to read as arms: the near shoulder on his front edge, the far one on
    # his back edge, both below the mouth (v03's fin at mouth height read as a duck's bill)
    shapes += fin(27, 31 + dy, near, True, steel, reach) + fin(
        12, 30 + dy, far, False, False, far_reach or reach
    )
    expr = next((e for e in EXPRESSIONS if e in acc), None)
    stamps = face(dy, blink and expr is None, 0, expr)
    if "sunglasses" in acc:  # the glasses cover the eye
        stamps = stamps[1:]
    return cv.render(shapes, stamps, bands=(0.3, 0.52, 0.72, 0.9))


INK = (43, 29, 20, 255)  # the warm dark ink of the fish icons (create/pixel/fishes.py)


def frames(anim: str, acc: set[str] | None = None) -> list[Image.Image]:
    acc = acc or set()
    cv = Canvas(W, H, ramps(), ink=INK, mode="ink", oy=OY)
    rows: list[Any]
    if anim == "idle":
        rows = [
            (0, 32, -32, False),
            (0, 36, -35, False),
            (-1, 40, -38, False),
            (-1, 40, -38, False),
            (0, 36, -35, True),
            (0, 32, -32, False),
        ]
        return [pose(cv, acc, dy, 0, n, f, b) for dy, n, f, b in rows]
    if anim == "hop":
        # squash, launch, rise, top, fall, land: the fins fling up and out (off his silhouette) on take-off
        rows = [
            (1, 0.5, 20, -40),
            (-2, -0.4, 105, -120),
            (-5, -0.2, 130, -150),
            (-6, 0, 120, -140),
            (-3, -0.2, 80, -100),
            (1, 0.6, 30, -35),
        ]
        return [pose(cv, acc, dy, sq, n, f) for dy, sq, n, f in rows]
    if anim == "wave":
        # side on, a raised near fin can only lie across his face (it read as a beak, lab v03): he waves with
        # the far fin, up behind his head where it breaks the silhouette, the near one resting
        rows = [(32, -120), (34, -160), (36, -138), (34, -165), (32, -140), (32, -70)]
        return [pose(cv, acc, 0, 0, n, f, far_reach=12) for n, f in rows]
    if anim == "clap":
        # side on, fins up over the face hide it: the far fin shoots up behind his head and the near one
        # punches forward and up in front of his chest (a cheer that reads at 40 px)
        rows = [(-1, 100, -140), (-2, 125, -168), (-2, 120, -165), (-1, 95, -140)]
        return [pose(cv, acc, dy, 0, n, f, reach=8, far_reach=13) for dy, n, f in rows]
    if anim == "row":
        rows = [(0, -30, 30), (0, 20, -20), (-1, 50, -50), (0, 10, -10)]
        return [pose(cv, acc, dy, 0, n, f) for dy, n, f in rows]
    raise ValueError(f"unknown Fred animation {anim!r}")
