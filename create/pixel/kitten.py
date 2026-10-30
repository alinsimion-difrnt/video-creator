"""Pixie, a tiny kitten seen from the side, facing right (an original drawing; homage in spirit to the kitten
of Ben Hed's "Pixie and Brutus"). Native 48 x 40 pixels, drawn from shapes by create/pixel/core.py.

Animations (frames, frames per second):
- idle 8 @ 8: breathing (chest up a pixel), a tail sway, one blink;
- walk 8 @ 12: diagonal pairs (near front with far back), a pixel of bob on the passing positions;
- run 6 @ 14: a gallop, stretched then gathered, the body tilting with it;
- grab 4 @ 10: head down, mouth open, back up (something in the mouth from then on: `grabbed`);
- look 2: the head turned to camera (a blink of surprise);
- pounce 6 @ 10: crouch, two butt wiggles, the leap, the landing (played into a carry: the grab lands on it);
- jump 6 @ 10: crouch, the leap held, the landing (a move up or down to another surface).
"""

from __future__ import annotations

import math
from typing import Any

from PIL import Image

from create.pixel.core import Canvas, Shape, ramp

W, H = 48, 40
INK = (43, 29, 20, 255)  # the warm dark ink shared with Fred and the fish icons
GROUND = 38
# Homage to Pixie of "Pixie and Brutus" (Ben Hed, Pet Foolery): pale peach fur with bold dark tabby stripes,
# big light-blue eyes, a white muzzle with two tiny fangs and a pink plaid bandana. Drawn here, not traced.
DEFAULT = {
    "fur": "#f7d9b0",
    "stripe": "#2e2734",
    "belly": "#fffaf3",
    "nose": "#f29aa0",
    "eyes": "#16121c",
    "iris": "#9ff0fb",
    "bandana": "#ef7f86",
}
FPS = {"idle": 8, "walk": 12, "run": 14, "grab": 10, "look": 6, "pounce": 10, "jump": 10}


def ramps(colors: dict[str, str] | None = None) -> dict[str, list[tuple[int, int, int, int]]]:
    c = DEFAULT | (colors or {})
    return {
        "fur": _soft(ramp(c["fur"], 5, 3, spread=0.4, lean=0.18)),
        "stripe": ramp(c["stripe"], 4, 2),
        "belly": ramp(c["belly"], 4, 3, spread=0.4),
        "nose": ramp(c["nose"], 3, 1),
        "bandana": ramp(c["bandana"], 4, 2),
    }


def _soft(r: list[tuple[int, int, int, int]]) -> list[tuple[int, int, int, int]]:
    """Pale fur: the first shade step halfway to the base. A pale base's ramp drops hard into a mauve, and
    the shaded half of a round head (the face, lit from the top left) read as mud (lab v03)."""
    mid = tuple(round((a + b) / 2) for a, b in zip(r[2][:3], r[3][:3], strict=True))
    return [r[0], r[1], (mid[0], mid[1], mid[2], 255), r[3], r[4]]


def leg(hx: float, hy: float, angle_deg: float, lift: float, near: bool, length: float = 7.5) -> list[Shape]:
    """A leg from the hip, swung `angle_deg` from vertical (+ forward), the foot raised `lift` pixels."""
    a = math.radians(angle_deg)
    fx = hx + length * math.sin(a)
    fy = min(GROUND - 1.5, hy + length * math.cos(a)) - lift
    z = 3 if near else 0
    part = "near" if near else "far"
    lv = 0 if near else -1
    return [
        Shape(
            "capsule", "fur", z, part + "leg", a=(hx, hy), b=(round(fx), round(fy)), r0=2.4, r1=1.9, lift=lv
        ),
        Shape(
            "ellipse",
            "belly",
            z,
            part + "leg",
            cx=round(fx) + 0.6,
            cy=round(fy) + 0.6,
            rx=2.2,
            ry=1.5,
            lift=lv,
        ),
    ]


def tail(base: tuple[float, float], sway: float, up: float = 1.0) -> list[Shape]:
    """Four segments curling up from the rump; `sway` bends it (radians), `up` lifts it."""
    out = []
    x, y = base
    ang = math.radians(-118) + sway * 0.3
    for k in range(4):
        ln = 3.6 - k * 0.3
        nx, ny = x + ln * math.cos(ang), y + ln * math.sin(ang) * up
        out.append(
            Shape("capsule", "fur", 1, "tail", a=(x, y), b=(nx, ny), r0=2.0 - k * 0.2, r1=1.8 - k * 0.2)
        )
        x, y = nx, ny
        ang += 0.42 + sway * 0.25
    out.append(Shape("ellipse", "stripe", 1, "tail", cx=x, cy=y, rx=1.6, ry=1.6, level=1))
    return out


def body(dy: int = 0, tilt: float = 0.0, stretch: float = 0.0) -> list[Shape]:
    return [
        Shape("ellipse", "fur", 2, "body", cx=20, cy=28 + dy, rx=11 + stretch, ry=6.5, angle=tilt),
        Shape(
            "ellipse",
            "belly",
            2,
            "body",
            cx=22,
            cy=31.5 + dy,
            rx=8 + stretch * 0.7,
            ry=3.2,
            angle=tilt,
            flat=0.3,
        ),
        Shape(
            "ellipse", "fur", 2, "body", cx=27, cy=25 + dy, rx=5.5, ry=5.5, flat=0.4
        ),  # chest: joins the head
        Shape(
            "poly", "stripe", 2, "body", pts=[(14, 22.6 + dy), (16.4, 22.6 + dy), (15.4, 25.5 + dy)], level=1
        ),
        Shape(
            "poly", "stripe", 2, "body", pts=[(18.5, 22.3 + dy), (20.9, 22.3 + dy), (19.9, 25 + dy)], level=1
        ),
    ]


def head(dx: int = 0, dy: int = 0, mouth_open: bool = False) -> list[Shape]:
    """The big round head with tall ears (white inside, dark tips), bold stripes on top, a white muzzle and
    the bandana tied under it."""
    cx, cy = 32 + dx, 17 + dy
    out = [
        Shape("ellipse", "fur", 4, "head", cx=cx, cy=cy, rx=10, ry=8.6, flat=0.8),  # the face stays lit
        Shape("poly", "fur", 4, "head", pts=[(cx - 7.5, cy - 4), (cx - 5.5, cy - 13), (cx - 1, cy - 7)]),
        Shape("poly", "fur", 4, "head", pts=[(cx + 2, cy - 7), (cx + 6.5, cy - 14), (cx + 8.5, cy - 4)]),
        Shape(
            "poly",
            "belly",
            5,
            "head",
            pts=[(cx + 3.6, cy - 7.4), (cx + 6.2, cy - 11.6), (cx + 7.2, cy - 6)],
            level=3,
        ),
        Shape(
            "poly",
            "stripe",
            5,
            "head",
            pts=[(cx + 5.3, cy - 13.4), (cx + 6.6, cy - 14.2), (cx + 7.1, cy - 11)],
            level=1,
        ),
        Shape(
            "poly",
            "stripe",
            5,
            "head",
            pts=[(cx - 6.4, cy - 11), (cx - 5.6, cy - 13.2), (cx - 4.2, cy - 10)],
            level=1,
        ),
        # three bold stripes on the crown
        Shape(
            "poly",
            "stripe",
            5,
            "head",
            pts=[(cx - 3.6, cy - 8.2), (cx - 1.6, cy - 8.6), (cx - 2.4, cy - 4.6)],
            level=1,
        ),
        Shape(
            "poly",
            "stripe",
            5,
            "head",
            pts=[(cx - 0.6, cy - 8.7), (cx + 1.4, cy - 8.7), (cx + 0.3, cy - 4.4)],
            level=1,
        ),
        Shape(
            "poly",
            "stripe",
            5,
            "head",
            pts=[(cx + 2.4, cy - 8.4), (cx + 4.2, cy - 8), (cx + 2.9, cy - 5)],
            level=1,
        ),
        Shape("ellipse", "belly", 5, "head", cx=cx + 3.5, cy=cy + 4.6, rx=5.4, ry=3.4, flat=0.9),
        # the bandana: a pink triangle knotted under the chin
        Shape(
            "poly",
            "bandana",
            5,
            "bandana",
            pts=[(cx - 6, cy + 6), (cx + 4.5, cy + 7.2), (cx - 1, cy + 12.5)],
            flat=0.45,
        ),
        Shape("ellipse", "bandana", 5, "bandana", cx=cx - 4.5, cy=cy + 6.8, rx=1.8, ry=1.4, flat=0.4),
    ]
    if mouth_open:
        out.append(Shape("ellipse", "nose", 6, "head", cx=cx + 7.3, cy=cy + 5.8, rx=1.7, ry=1.5, level=0))
    return out


def _rgba(c: str) -> tuple[int, int, int, int]:
    return (int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16), 255)


def face(
    dx: int, dy: int, blink: bool, colors: dict[str, str] | None
) -> list[tuple[int, int, list[str], dict[str, Any]]]:
    """Big light-blue eyes (a ring of iris round a black pupil, a white shine), a pink nose, a mouth with two
    tiny white fangs, plaid checks on the bandana."""
    c = DEFAULT | (colors or {})
    pal = {"k": _rgba(c["eyes"]), "c": _rgba(c["iris"]), "w": (255, 255, 255, 255), "n": _rgba(c["nose"]),
           "m": (70, 46, 60, 255), "f": (255, 255, 255, 255), "p": (255, 196, 200, 255)}  # fmt: skip
    x, y = 32 + dx, 17 + dy
    # a three-quarter face (turned toward the viewer, as Pixie is drawn): both big eyes inside the head,
    # the far one a little narrower: big dark eyes with a 2x2 shine on top and the light-blue iris below
    # (the comic kitten's look; a closed eye is a happy arc)
    if blink:
        near, far, oy = ["k    k", " kkkk "], ["k   k", " kkk "], 4
    else:
        near = [
            " kkkk ",
            "kkwwkk",
            "kkwwkk",
            "kkkkkk",
            "kcckck",
            "kcccck",
            " kkkk ",
        ]
        far = [" kkk ", "kwwkk", "kkkkk", "kcckk", "kccck", " kkk "]
        oy = 0
    return [
        (x - 5, y - 3 + oy, far, pal),
        (x + 1, y - 4 + oy, near, pal),
        (x + 4, y + 3, ["nn"], pal),
        (x + 3, y + 4, ["m mm", " f f"], pal),
        (x - 4, y + 8, ["p p", " p "], pal),
    ]


# Walk: a cat's diagonal gait over 8 frames. Each row: far back, near back, far front, near front leg angles,
# body bob, and how high each foot lifts (the one swinging forward).
WALK = [
    (-24, 18, 20, -22, 0, (0, 0, 0, 0)),
    (-12, 6, 8, -10, -1, (0, 2, 0, 0)),
    (0, -6, -4, 4, -1, (0, 2.5, 0, 2)),
    (12, -18, -16, 16, 0, (0, 0, 0, 2.5)),
    (18, -24, -22, 20, 0, (0, 0, 0, 0)),
    (6, -12, -10, 8, -1, (2, 0, 0, 0)),
    (-6, 0, 4, -4, -1, (2.5, 0, 2, 0)),
    (-18, 12, 16, -16, 0, (0, 0, 2.5, 0)),
]
# Gallop over 6 frames: gathered, back legs push, stretched in the air, front reach, front plant, gather.
# Rows: far back, near back, far front, near front, body dy, tilt (radians), stretch, head dy.
RUN = [
    (28, 20, -26, -20, 0, 0.06, 0.0, 1),
    (-30, -38, -10, -4, -1, -0.04, 0.8, 0),
    (-48, -52, 44, 50, -3, -0.1, 2.0, -1),
    (-30, -24, 40, 30, -2, 0.0, 1.2, 0),
    (6, 14, -6, 4, 0, 0.08, 0.3, 2),
    (24, 30, -24, -14, 0, 0.08, 0.0, 1),
]


def frames(
    anim: str, colors: dict[str, str] | None = None, grabbed: Image.Image | None = None
) -> list[Image.Image]:
    cv = Canvas(W, H, ramps(colors), ink=INK, mode="ink")
    out = []
    if anim == "idle":
        for k in range(8):
            breathe = 1 if k in (2, 3, 4) else 0
            sway = math.sin(k / 8 * 2 * math.pi) * 0.8
            shapes = body(-breathe) + head(0, -breathe) + tail((10, 26 - breathe), sway)
            shapes += leg(14, 31, 0, 0, False) + leg(27, 31, 0, 0, False)
            shapes += leg(12, 32, 0, 0, True) + leg(25, 32, 0, 0, True)
            out.append(cv.render(shapes, face(0, -breathe, k == 6, colors)))
        return out
    if anim == "walk":
        # key poses (degrees from vertical, + forward): far back, near back, far front, near front, bob, lifts
        keys = WALK
        for k, (fb, nb, ff, nf, bob, lifts) in enumerate(keys):
            sway = 0.25 + 0.2 * math.sin(
                k / len(keys) * 2 * math.pi
            )  # the tail stays curled, swaying a little
            shapes = body(bob) + head(0, bob) + tail((10, 26 + bob), sway)
            shapes += leg(14, 31 + bob, fb, lifts[0], False) + leg(27, 31 + bob, ff, lifts[2], False)
            shapes += leg(12, 32 + bob, nb, lifts[1], True) + leg(25, 32 + bob, nf, lifts[3], True)
            out.append(cv.render(shapes, face(0, bob, False, colors)))
        return out
    if anim == "run":
        for fb, nb, ff, nf, dy, tilt, stretch, hd in RUN:
            shapes = body(dy, tilt, stretch) + head(1, dy + hd) + tail((9, 25 + dy), 0.9, up=0.5)
            shapes += leg(15, 31 + dy, fb, 0.5, False) + leg(28, 31 + dy, ff, 0.5, False)
            shapes += leg(13, 32 + dy, nb, 0.5, True) + leg(26, 32 + dy, nf, 0.5, True)
            out.append(cv.render(shapes, face(1, dy + hd, False, colors)))
        return out
    if anim == "grab":
        for k, (hd, mo) in enumerate([(1, False), (3, True), (3, False), (1, False)]):
            shapes = body(0) + head(1, hd, mouth_open=mo) + tail((10, 26), 0.4 * k)
            shapes += leg(14, 31, 0, 0, False) + leg(27, 31, -8, 0, False)
            shapes += leg(12, 32, 0, 0, True) + leg(25, 32, -8, 0, True)
            out.append(cv.render(shapes, face(1, hd, k == 1, colors)))
        return out
    if anim == "pounce":
        # a cat's pounce: crouch low (anticipation), two butt wiggles, the leap stretched out, the landing
        rows = [  # body dy, tilt, stretch, head dy, back legs, front legs, hip lift, tail sway
            (2, 0.0, 0.0, 3, 0, 0, 0, 0.3),
            (2, -0.08, 0.0, 3, -6, 10, 1, 0.9),
            (2, -0.08, 0.0, 3, 6, 10, 0, -0.3),
            (2, -0.08, 0.0, 3, -6, 10, 1, 0.9),
            (-2, -0.1, 2.4, 1, -55, 55, 0, 1.2),
            (0, 0.1, 0.4, 2, 10, -10, 0, 0.6),
        ]
        for dy, tilt, stretch, hd, back, front, hip, sway in rows:
            ln = 5.5 if dy > 0 else 7.5  # crouched legs fold
            shapes = body(dy, tilt, stretch) + head(1, dy + hd - 2) + tail((10, 25 + dy - hip), sway, up=0.6)
            shapes += leg(14, 31 + dy - hip, back, 0, False, ln) + leg(27, 31 + dy, front, 0, False, ln)
            shapes += leg(12, 32 + dy - hip, back, 0, True, ln) + leg(25, 32 + dy, front, 0, True, ln)
            out.append(cv.render(shapes, face(1, dy + hd - 2, False, colors)))
        return out
    if anim == "jump":  # up or down to another surface: crouch, the leap held in the air, the landing
        p = frames("pounce", colors)
        return [p[0], p[4], p[4], p[4], p[4], p[5]]
    if anim == "look":
        shapes = body(0) + head(0, 0) + tail((10, 26), 0)
        shapes += leg(14, 31, 0, 0, False) + leg(27, 31, 0, 0, False)
        shapes += leg(12, 32, 0, 0, True) + leg(25, 32, 0, 0, True)
        return [cv.render(shapes, face(0, 0, False, colors)), cv.render(shapes, face(0, 0, True, colors))]
    raise ValueError(f"unknown kitten animation {anim!r}")
