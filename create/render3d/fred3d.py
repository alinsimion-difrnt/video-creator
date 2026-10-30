"""Fred in 3D (create/render3d/sdf.py): the upright fish as smooth-unioned volumes, posable and turnable.

Model space: y up, Fred faces +x (to the right on screen at yaw 0), the camera looks down -z. Poses are a
few numbers (fin angles, squash, hop height), so animations are frame lists of poses like the pixel sprites.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
from PIL import Image

from create.render3d import sdf
from create.render3d.sdf import Material, Prim, render

# the frames cache key: the model's and the renderer's source as loaded. Hashed at import, so a process
# never files frames from code it has not run under the key of newer code on disk (lab v07)
VERSION = hashlib.sha256(Path(__file__).read_bytes() + Path(sdf.__file__).read_bytes()).hexdigest()[:12]

# the carp (Robert's first catch): an olive back, olive-gold flanks, a golden belly, scales; orange fins and
# a forked orange tail; peach lips and barbels; a gold-ringed eye
BACK, FLANK, BELLY = np.array((0.22, 0.22, 0.08)), np.array((0.52, 0.47, 0.17)), np.array((0.93, 0.7, 0.3))
SHIFT = 0.36  # frame() lowers the model by this much (the tail on the box's bottom edge)


def carp_skin(pose: Pose) -> Material:
    """Body material: counter-shaded across him (his back is -x, he faces +x) and scaled below the gill line.
    Pinned to the body (lift, squash), so the scales never slide over him in a hop (pixel-art rule: no
    boiling)."""
    sy = 1 - pose.squash * 0.18

    def tex(p: np.ndarray) -> np.ndarray:
        x, y, z = p[:, 0], (p[:, 1] + SHIFT - pose.lift) / sy, p[:, 2]
        t = np.clip(0.52 + x / 1.0 + 0.15 * z * (x > 0), 0, 1)[:, None]  # 0 back .. 1 belly
        col = np.where(
            t < 0.5, BACK + (FLANK - BACK) * (t / 0.5), FLANK + (BELLY - FLANK) * ((t - 0.5) / 0.5)
        )
        # scales: rows 0.1 tall, staggered; each scale's free edge is an arc convex toward the tail (down)
        arc = np.arctan2(z, x - 0.1) * 0.6
        cw, ch = 0.12, 0.1
        row = np.floor(y / ch)
        u = arc / cw + 0.5 * (row % 2)
        fu, fv = u - np.floor(u) - 0.5, y / ch - row
        d = np.hypot(fu, fv - 1.1)
        edge = np.clip(1 - np.abs(d - 0.62) / 0.1, 0, 1)
        body = (y < 0.3 - 0.35 * np.clip(x, 0, None)) & (y > -0.75)  # below the gill line, above the tail
        dark = (edge * body * 0.5)[:, None]
        lit = (np.clip(1 - np.abs(d - 0.45) / 0.12, 0, 1) * body * 0.12)[:, None]  # a sheen inside each scale
        out: np.ndarray = col * (1 - dark) + lit * np.array((1.0, 0.92, 0.6))
        return out

    return Material(tuple(FLANK), 0.35, 30, texture=tex)


def mats(pose: Pose) -> list[Material]:
    return [
        carp_skin(pose),  # 0 body
        Material((0.95, 0.72, 0.33), 0.25, 20),  # 1 belly gold
        Material((1.0, 0.48, 0.06), 0.25, 24),  # 2 fins orange
        Material((0.97, 0.97, 0.97), 0.6, 60),  # 3 eye white
        Material((0.05, 0.04, 0.07), 0.9, 80),  # 4 pupil / moustache / hat
        Material((0.85, 0.12, 0.2), 0.3, 30),  # 5 hat band red
        Material((0.95, 0.55, 0.42), 0.15, 12),  # 6 lips and barbels, peach
        Material((0.7, 0.74, 0.8), 0.9, 60),  # 7 steel (automail)
        Material((0.9, 0.68, 0.16), 0.6, 60),  # 8 iris gold
        Material((0.55, 0.38, 0.14), 0.25, 24),  # 9 dorsal fin, olive-amber (as on the photo)
    ]


W, H = 240, 348  # aspect 1.45, as the SVG rig's box


@dataclass(frozen=True)
class Pose:
    yaw: float = 0.0
    fin_f: float = 0.0  # near fin, radians (+ forward / up)
    fin_b: float = 0.0
    squash: float = 0.0  # + squash, - stretch
    lift: float = 0.0  # hop height (model units)
    look: float = 0.0  # pupil offset up (+)


def model(pose: Pose, acc: frozenset[str] = frozenset()) -> list[Prim]:
    sy = 1 - pose.squash * 0.18
    sx = 1 + pose.squash * 0.12
    y0 = pose.lift
    steel = "automail" in acc
    fin = 7 if steel else 2
    prims = [
        Prim("ellipsoid", (0.0, 0.15 * sy + y0, 0.0), (0.62 * sx, 0.95 * sy, 0.56 * sx), 0),
        # dorsal fin: long, down his back (a carp's), a stalk and a big forked tail he stands on
        Prim("ellipsoid", (-0.6, 0.3 * sy + y0, 0.0), (0.15, 0.5, 0.04), 9, rot=(0, 0, -0.2), blend=0.05),
        Prim("ellipsoid", (0.0, -0.86 * sy + y0, 0.0), (0.2, 0.22, 0.13), 7 if steel else 2, blend=0.08),
        Prim(
            "ellipsoid", (-0.32, -1.1 + y0 * 0.6, 0.0), (0.48, 0.17, 0.08), fin, rot=(0, 0, 0.6), blend=0.05
        ),
        Prim(
            "ellipsoid", (0.32, -1.1 + y0 * 0.6, 0.0), (0.48, 0.17, 0.08), fin, rot=(0, 0, -0.6), blend=0.05
        ),
        # eyes: round, a gold iris ring around a big pupil; the near one big, the far one peeking past
        Prim("ellipsoid", (0.36, 0.52 * sy + y0, 0.38), (0.2, 0.21, 0.14), 3),
        Prim("ellipsoid", (0.42, 0.52 * sy + 0.04 * pose.look + y0, 0.47), (0.13, 0.13, 0.06), 8),
        Prim("ellipsoid", (0.45, 0.52 * sy + 0.04 * pose.look + y0, 0.505), (0.075, 0.08, 0.04), 4),
        Prim("ellipsoid", (0.42, 0.52 * sy + y0, -0.3), (0.15, 0.18, 0.1), 3),
        # peach lips at the snout, a smile under them, two barbels hanging from the corners
        Prim("ellipsoid", (0.6, 0.22 * sy + y0, 0.12), (0.1, 0.07, 0.17), 6, blend=0.04),
        Prim("ellipsoid", (0.6, 0.15 * sy + y0, 0.12), (0.06, 0.02, 0.12), 4),
        Prim("ellipsoid", (0.56, 0.06 * sy + y0, 0.3), (0.025, 0.11, 0.025), 6, rot=(0, 0, 0.25)),
        Prim("ellipsoid", (0.62, 0.06 * sy + y0, -0.06), (0.025, 0.11, 0.025), 6, rot=(0, 0, 0.25)),
    ]
    # fins: paddles hinged at the shoulder; theta 0 hangs straight down, + swings forward and up
    for side, ang, mat in ((1, pose.fin_f, 7 if steel else 2), (-1, pose.fin_b, 2)):
        th = -0.35 + ang
        sx0, sy0 = 0.14, 0.14 * sy + y0  # the shoulder sits behind the eye
        cx, cy = sx0 + 0.3 * math.sin(th), sy0 - 0.3 * math.cos(th)
        cz = side * (0.5 + 0.2 * abs(math.sin(th)))  # a raised fin swings out from the body, not across it
        prims.append(
            Prim("ellipsoid", (cx, cy, cz), (0.17, 0.36, 0.07), mat, rot=(0.25 * side, 0, th), blend=0.04)
        )
    top = 0.15 * sy + 0.95 * sy + y0
    if "top_hat" in acc:
        prims += [
            Prim("box", (0.02, top + 0.33, 0.0), (0.27, 0.3, 0.27), 4, rot=(0, 0, -0.12), round=0.04),
            Prim("box", (0.0, top + 0.12, 0.0), (0.285, 0.06, 0.285), 5, rot=(0, 0, -0.12), round=0.02),
            Prim("ellipsoid", (-0.02, top + 0.02, 0.0), (0.55, 0.05, 0.5), 4, rot=(0, 0, -0.12)),
        ]
    if "moustache" in acc:
        prims += [
            # a handlebar: two fat sweeps from under the nose, curling up at the tips (v03: two dots)
            Prim("ellipsoid", (0.6, 0.27 * sy + y0, 0.3), (0.08, 0.065, 0.2), 4, rot=(0.45, -0.5, 0)),
            Prim("ellipsoid", (0.64, 0.27 * sy + y0, 0.02), (0.08, 0.065, 0.2), 4, rot=(-0.45, -0.5, 0)),
            Prim("ellipsoid", (0.5, 0.36 * sy + y0, 0.48), (0.05, 0.08, 0.05), 4, blend=0.03),
            Prim("ellipsoid", (0.62, 0.36 * sy + y0, -0.14), (0.05, 0.08, 0.05), 4, blend=0.03),
        ]
    return prims


def frame(pose: Pose, acc: frozenset[str] = frozenset(), size: tuple[int, int] = (W, H)) -> Image.Image:
    # a three-quarter view (yaw -0.45) shows his face and his volume; pose.yaw turns him from there
    # framed like the SVG rig: the tail on the bottom edge, the body filling the box (v03 filled half of it,
    # so 3D Fred looked smaller than his other styles); room above for a hat on a hop
    prims = [replace(p, center=(p.center[0], p.center[1] - 0.36, p.center[2])) for p in model(pose, acc)]
    return render(prims, mats(pose), size, yaw=pose.yaw - 0.45, pitch=0.1, dist=3.9, fov=0.5)


FPS = {"turn": 18, "idle": 8, "hop": 12, "wave": 10}


def poses(anim: str) -> list[Pose]:
    """turn: a full turntable (he shows he is 3D); idle: breathing and fins; hop; wave."""
    if anim == "turn":
        return [Pose(yaw=k / 16 * 2 * math.pi) for k in range(16)]
    if anim == "idle":
        out = []
        for k in range(6):
            s = math.sin(k / 6 * 2 * math.pi)
            out.append(Pose(squash=0.03 * s, fin_f=0.15 * s, fin_b=-0.12 * s, look=1))
        return out
    if anim == "hop":
        rows = [
            (0.4, 0.0, 0.3),
            (-0.3, 0.15, 1.2),
            (-0.1, 0.35, 1.6),
            (0.0, 0.4, 1.4),
            (-0.1, 0.2, 0.9),
            (0.45, 0.0, 0.3),
        ]
        return [Pose(squash=sq, lift=lf, fin_f=f, fin_b=f) for sq, lf, f in rows]
    if anim == "wave":
        return [Pose(fin_f=a, look=1) for a in (-1.4, -1.95, -1.6, -2.0, -1.6, -0.8)]  # up and back
    raise ValueError(f"unknown 3D Fred animation {anim!r}")


def frames(anim: str, acc: frozenset[str] = frozenset()) -> list[Image.Image]:
    return [frame(p, acc) for p in poses(anim)]
