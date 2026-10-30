"""Pixel art from shapes (ADR 0028): a sprite is a list of lit shapes rasterised at native resolution.

Why shapes and not hand-typed grids: every frame of an animation is re-drawn from its pose, so limbs turn
without rotation blur, shading always follows one light, and the same rules (palette ramps, selective
outlines, contact shadows, orphan cleanup) apply to every sprite. The rules come from pixel-art practice:
- **Ramps, not tints.** Each material is a ramp of 4-6 colours; darker steps shift hue toward blue/purple and
  gain saturation, lighter steps shift toward yellow and lose it (hue shifting), so shadows are not grey.
- **One light** (top left, in front). Shapes are domes or tubes: the normal at each pixel picks the ramp step,
  so clusters are big and shaped like the form (no pillow shading).
- **Selective outline (sel-out).** The silhouette is drawn in the darkest step of the colour it borders, and a
  step lighter on the lit side; one dark ink colour only where contrast must be strong.
- **Contact shadows.** Where a part in front overlaps a part behind, the part behind darkens a step along the
  edge: limbs read against the body without black internal lines.
- **No orphans.** A lone pixel of a step none of its four neighbours share is merged into its neighbours
  (noise reads as dirt at 1x).
- **Integer moves.** Positions snap to whole pixels; parts that do not move are drawn the same every frame
  (no boiling).
Output is upscaled by an integer with nearest-neighbour only.
"""

from __future__ import annotations

import colorsys
import math
from dataclasses import dataclass, field

import numpy as np
from PIL import Image

RGBA = tuple[int, int, int, int]
LIGHT = np.array([-0.25, -0.62, 0.74])  # from above, a little left, toward the viewer
LIGHT = LIGHT / np.linalg.norm(LIGHT)


def hex_rgb(c: str) -> tuple[int, int, int]:
    return (int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16))


SHADOW = "#2e2747"  # one shadow colour every ramp leans toward: the sprite's palette reads as one


def ramp(
    base: str,
    steps: int = 5,
    mid: int | None = None,
    shift: float = 0.045,
    spread: float = 0.62,
    shadow: str = SHADOW,
    lean: float = 0.45,
) -> list[RGBA]:
    """A hue-shifted ramp from dark to light with `base` at index `mid`: darker steps move hue toward blue
    (h 0.66), gain saturation and lean toward the shared `shadow` colour; lighter steps move toward yellow
    (h 0.16) and lose saturation."""
    r, g, b = (v / 255 for v in hex_rgb(base))
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    mid = steps // 2 if mid is None else mid
    out: list[RGBA] = []
    for k in range(steps):
        d = (k - mid) / max(1, steps - 1) * 2  # -1 .. 1 roughly
        target = 0.16 if d > 0 else 0.66
        # move the hue the short way round toward the target
        dh = ((target - h + 0.5) % 1.0) - 0.5
        hh = (h + dh * min(1.0, abs(d) * shift * 6)) % 1.0
        ss = min(1.0, max(0.0, s * (1 - 0.35 * d) if d > 0 else s + (1 - s) * 0.25 * -d))
        vv = min(1.0, max(0.05, v + d * spread * (1 - v if d > 0 else v) * 0.95))
        rr, gg, bb = colorsys.hsv_to_rgb(hh, ss, vv)
        if d < 0:  # dark steps lean toward the shared shadow
            t = min(1.0, -d * lean)
            sr, sg, sb = (c / 255 for c in hex_rgb(shadow))
            rr, gg, bb = rr + (sr - rr) * t, gg + (sg - gg) * t, bb + (sb - bb) * t
        out.append((round(rr * 255), round(gg * 255), round(bb * 255), 255))
    return out


def blend(base: str, to: str, steps: int = 5, shadow: str = SHADOW) -> list[RGBA]:
    """A ramp from a dark `base` (a fish's back) to a light `to` (its belly): the colours between, a step
    darker leaning to the shared shadow at the bottom, and a light top step. For counter-shaded bodies."""
    a, b = hex_rgb(base), hex_rgb(to)
    sh = hex_rgb(shadow)
    out: list[RGBA] = []
    for k in range(steps):
        t = (k - 1) / max(1, steps - 2)
        if k == 0:  # the shadow step: the back colour leaning to the shared shadow
            c = tuple(round(x + (y - x) * 0.45) for x, y in zip(a, sh, strict=True))
        else:
            t = min(1.0, t)
            c = tuple(round(x + (y - x) * t) for x, y in zip(a, b, strict=True))
        out.append((c[0], c[1], c[2], 255))
    return out


@dataclass
class Shape:
    """A lit shape. kind: ellipse (a dome), capsule (a tube from a to b), poly (flat, `level` fixed).
    `mat` names a ramp; `z` orders drawing (higher in front); `part` groups shapes for contact shadows."""

    kind: str
    mat: str
    z: int = 0
    part: str = ""
    cx: float = 0
    cy: float = 0
    rx: float = 1
    ry: float = 1
    angle: float = 0.0  # ellipse rotation, radians
    a: tuple[float, float] = (0, 0)
    b: tuple[float, float] = (0, 0)
    r0: float = 1
    r1: float = 1
    pts: list[tuple[float, float]] = field(default_factory=list)
    level: int | None = None  # force a ramp step (flat shapes, eyes)
    flat: float = 0.0  # 0 = a full dome, 1 = flat (lit evenly at its base step)
    lift: int = 0  # shift every ramp step up (+) or down (-) for this shape
    edge: bool = False  # an internal outline where this part lies over another (a limb in front of a body)
    radii: list[float] = field(default_factory=list)  # spine: the radius at each point of `pts`
    shade: str = (
        "light"  # light: lit as a form; counter: dark back, light belly (fish), along its local "down"
    )
    pattern: str = ""  # mottle | spots | rays | scales | net (texture inside the shape)
    pattern_mat: str = ""  # mottle and spots use this ramp (another hue); default: a step darker / lighter
    density: float = 0.3  # how much of the shape a mottle or spots pattern covers
    pattern_mat2: str = ""  # mottle: a second hue of patches (perch: teal and olive)
    ray_angle: float = 0.0  # rays: their direction (radians)
    rim: bool = False  # a light line just inside the belly edge (bounce light, counter-shaded shapes)
    seed: int = 0


def _ellipse(s: Shape, xs: np.ndarray, ys: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    ca, sa = math.cos(s.angle), math.sin(s.angle)
    dx, dy = xs - s.cx, ys - s.cy
    u = (dx * ca + dy * sa) / s.rx
    v = (-dx * sa + dy * ca) / s.ry
    d2 = u * u + v * v
    inside = d2 <= 1.0
    nz = np.sqrt(np.clip(1 - d2, 0, 1))
    # back to frame axes
    nx = u * ca - v * sa
    ny = u * sa + v * ca
    n = np.dstack([nx, ny, nz])
    return inside, n, v


def _capsule(s: Shape, xs: np.ndarray, ys: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    ax, ay = s.a
    bx, by = s.b
    vx, vy = bx - ax, by - ay
    ll = vx * vx + vy * vy or 1e-6
    t = np.clip(((xs - ax) * vx + (ys - ay) * vy) / ll, 0, 1)
    px, py = ax + t * vx, ay + t * vy
    r = s.r0 + (s.r1 - s.r0) * t
    dx, dy = xs - px, ys - py
    d = np.sqrt(dx * dx + dy * dy)
    inside = d <= r
    q = np.clip(d / np.maximum(r, 1e-6), 0, 1)
    nz = np.sqrt(1 - q * q)
    with np.errstate(invalid="ignore", divide="ignore"):
        nx = np.where(d > 0, dx / d * q, 0)
        ny = np.where(d > 0, dy / d * q, 0)
    side = np.sign(-(xs - ax) * vy + (ys - ay) * vx)  # + on the right of a -> b
    return inside, np.dstack([nx, ny, nz]), side * q


def _poly(s: Shape, xs: np.ndarray, ys: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    inside = np.zeros(xs.shape, dtype=bool)  # even-odd rule
    pts = s.pts
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1], strict=True):
        crosses = (y0 > ys) != (y1 > ys)
        with np.errstate(invalid="ignore", divide="ignore"):
            xint = x0 + (ys - y0) * (x1 - x0) / (y1 - y0)
        inside ^= crosses & (xs < xint)
    n = np.zeros((*xs.shape, 3))
    n[..., 2] = 1
    return inside, n, np.zeros(xs.shape)


def _spine(s: Shape, xs: np.ndarray, ys: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """A tube along a curve (`pts`, `radii`): a fish body that bends. `v` is the signed distance across it
    (+ on the right of the direction of `pts`, the belly for a fish drawn tail to head)."""
    best = np.full(xs.shape, np.inf)
    v = np.zeros(xs.shape)
    rr = np.ones(xs.shape)
    for (ax, ay), (bx, by), r0, r1 in zip(s.pts, s.pts[1:], s.radii, s.radii[1:], strict=False):
        vx, vy = bx - ax, by - ay
        ll = vx * vx + vy * vy or 1e-6
        t = np.clip(((xs - ax) * vx + (ys - ay) * vy) / ll, 0, 1)
        px, py = ax + t * vx, ay + t * vy
        r = r0 + (r1 - r0) * t
        d = np.hypot(xs - px, ys - py)
        closer = d / r < best
        side = np.sign(-(xs - ax) * vy + (ys - ay) * vx)
        best = np.where(closer, d / r, best)
        v = np.where(closer, side * d / r, v)
        rr = np.where(closer, r, rr)
    inside = best <= 1.0
    nz = np.sqrt(np.clip(1 - best * best, 0, 1))
    n = np.dstack([np.zeros(xs.shape), v, nz])
    return inside, n, v


SHAPES = {"ellipse": _ellipse, "capsule": _capsule, "poly": _poly, "spine": _spine}


def _anchor(s: Shape) -> tuple[int, int]:
    """A whole-pixel point that moves with the shape (texture origin)."""
    if s.kind == "ellipse":
        return round(s.cx), round(s.cy)
    if s.kind == "capsule":
        return round(s.a[0]), round(s.a[1])
    if s.pts:
        return round(s.pts[0][0]), round(s.pts[0][1])
    return 0, 0


def _hash(xs: np.ndarray, ys: np.ndarray, seed: int) -> np.ndarray:
    """Deterministic per-cell noise in [0, 1)."""
    h = (xs.astype(np.int64) * 374761393 + ys.astype(np.int64) * 668265263 + seed * 2246822519) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return (h & 0xFFFF) / 65536.0


@dataclass
class Canvas:
    w: int
    h: int
    ramps: dict[str, list[RGBA]]
    ink: RGBA = (30, 24, 42, 255)
    levels: int = 0  # filled in render: per pixel ramp step
    mode: str = "selout"  # selout: outlines in the bordering colour; ink: one warm ink everywhere (icons)
    oy: int = 0  # headroom: shapes and stamps are drawn this many pixels lower (room for hats and hops)

    def render(
        self,
        shapes: list[Shape],
        stamps: list[tuple[int, int, list[str], dict[str, RGBA]]] | None = None,
        outline: bool = True,
        contact: bool = True,
        clean: bool = True,
        bands: tuple[float, ...] = (0.42, 0.62, 0.8, 0.93),
    ) -> Image.Image:
        """Rasterise `shapes` (pixel centres, no anti-aliasing), shade by the light, then outline, contact
        shadows, cleanup and `stamps` (hand-placed pixels: eyes, mouths) on top."""
        ys, xs = np.mgrid[0 : self.h, 0 : self.w].astype(float) + 0.5
        ys = ys - self.oy
        mat = np.full((self.h, self.w), "", dtype=object)
        lev = np.full((self.h, self.w), -1, dtype=int)
        zbuf = np.full((self.h, self.w), -(10**6), dtype=int)
        part = np.full((self.h, self.w), "", dtype=object)
        edged = {s.part or s.mat for s in shapes if s.edge}
        gx, gy = xs, ys
        for order, s in enumerate(sorted(shapes, key=lambda s: s.z)):
            xs, ys = gx, gy
            inside, n, v = SHAPES[s.kind](s, xs, ys)
            steps = len(self.ramps[s.mat])
            if s.level is not None:
                lv = np.full(inside.shape, s.level)
            else:
                if s.shade == "counter":  # dark back, light belly, a touch of the form
                    lit = 0.5 + 0.42 * v + 0.12 * (n[..., 2] - 0.5)
                else:
                    lit = (n * LIGHT).sum(
                        axis=2
                    ) * 0.5 + 0.5  # half-Lambert: the far side is shade, not black
                lit = lit * (1 - s.flat) + s.flat * 0.8
                lv = np.digitize(lit, bands[: steps - 1])
                lv = np.clip(lv + s.lift, 0, steps - 1)
            pm = np.full(inside.shape, s.mat, dtype=object)
            # textures are pinned to the shape (its anchor, in whole pixels), so they move with it
            ax, ay = _anchor(s)
            xs, ys = gx - ax, gy - ay
            if s.pattern == "mottle":  # 2 x 2 patches of another hue (or a step darker)
                hit = _hash(xs // 2, ys // 2, s.seed) < s.density
                if s.pattern_mat:  # patches sit in the middle of their own ramp, not its shadow
                    pm[hit] = s.pattern_mat
                    lv = np.where(hit, np.clip(lv, 1, len(self.ramps[s.pattern_mat]) - 1), lv)
                else:
                    lv = np.where(hit, np.maximum(lv - 1, 0), lv)
                if s.pattern_mat2:
                    hit2 = (_hash(xs // 2 + 5, ys // 2 + 3, s.seed + 11) < s.density * 0.7) & ~hit
                    pm[hit2] = s.pattern_mat2
                    lv = np.where(hit2, np.clip(lv + 1, 1, len(self.ramps[s.pattern_mat2]) - 1), lv)
            elif s.pattern == "spots":  # single bright dots, away from the edge
                hit = (_hash(xs, ys, s.seed + 7) < s.density) & (np.abs(v) < 0.75)
                if s.pattern_mat:
                    pm[hit] = s.pattern_mat
                    lv = np.where(hit, len(self.ramps[s.pattern_mat]) - 1, lv)
                else:
                    lv = np.where(hit, steps - 1, lv)
            elif s.pattern == "rays":  # fin rays: stripes along `ray_angle`
                p = -xs * math.sin(s.ray_angle) + ys * math.cos(s.ray_angle)
                lv = np.where(np.floor(p / 1.6) % 2 == 0, np.maximum(lv - 1, 0), lv)
            elif s.pattern == "net":  # a carp's scales: scallops of darker pixels
                # scallops 4 px wide, 3 rows tall, every other row shifted by 2: a "U" of darker pixels each
                row = np.floor(ys / 3)
                cx_, cy_ = (xs + 2 * (row % 2)) % 4, ys % 3
                net = ((cy_ >= 2) & (cx_ >= 1) & (cx_ < 3)) | (
                    (cy_ >= 1) & (cy_ < 2) & ((cx_ < 1) | (cx_ >= 3))
                )
                lv = np.where(net & (v < 0.6) & (lv > 0), lv - 1, lv)
            elif s.pattern == "scales":  # a staggered pattern of darker pixels
                cell = (np.floor(xs / 2) + np.floor(ys / 2)) % 2 == 0
                lv = np.where(cell & (np.floor(ys) % 2 == 0) & (v < 0.3), np.maximum(lv - 1, 0), lv)
            if s.rim:
                lv = np.where(v > 0.78, steps - 1, lv)
            m = inside & (s.z * 1000 + order >= zbuf)
            mat[m], lev[m], part[m] = pm[m], lv[m], s.part or s.mat
            zbuf[m] = s.z * 1000 + order
        if clean:
            _clean(lev, mat)
        if contact:
            _contact(lev, part, zbuf)
        inked = np.zeros(lev.shape, dtype=bool)
        if edged:
            inked = _edges(lev, part, edged, self.mode == "ink")
        img = np.zeros((self.h, self.w, 4), dtype=np.uint8)
        filled = lev >= 0
        for y, x in zip(*np.nonzero(filled), strict=True):
            r = self.ramps[mat[y, x]]
            img[y, x] = self.ink if inked[y, x] else r[min(lev[y, x], len(r) - 1)]
        if outline and self.mode == "ink":
            _inkout(img, lev, self.ink)
        elif outline:
            _selout(img, lev, mat, self.ramps, self.ink)
        out = Image.fromarray(img, "RGBA")
        for x0, y0, rows, colors in [(x, y + self.oy, r, c) for x, y, r, c in stamps or []]:
            for dy, row in enumerate(rows):
                for dx, ch in enumerate(row):
                    if ch != " " and 0 <= x0 + dx < self.w and 0 <= y0 + dy < self.h:
                        out.putpixel((x0 + dx, y0 + dy), colors[ch])
        return out


N4 = ((0, 1), (0, -1), (1, 0), (-1, 0))


def _clean(lev: np.ndarray, mat: np.ndarray) -> None:
    """Merge lone pixels: a step that none of its four same-material neighbours share takes theirs."""
    h, w = lev.shape
    src = lev.copy()
    for y in range(h):
        for x in range(w):
            if src[y, x] < 0:
                continue
            nb = [src[y + dy, x + dx] for dy, dx in N4 if 0 <= y + dy < h and 0 <= x + dx < w
                  and src[y + dy, x + dx] >= 0 and mat[y + dy, x + dx] == mat[y, x]]  # fmt: skip
            if len(nb) >= 3 and src[y, x] not in nb:
                lev[y, x] = max(set(nb), key=nb.count)


def _contact(lev: np.ndarray, part: np.ndarray, zbuf: np.ndarray) -> None:
    """A part behind darkens one step where a part in front borders it."""
    h, w = lev.shape
    src_part, src_z = part.copy(), zbuf.copy()
    for y in range(h):
        for x in range(w):
            if lev[y, x] < 0:
                continue
            for dy, dx in N4:
                yy, xx = y + dy, x + dx
                inside = 0 <= yy < h and 0 <= xx < w and lev[yy, xx] >= 0
                if (
                    inside
                    and src_part[yy, xx] != src_part[y, x]
                    and src_z[yy, xx] // 1000 > src_z[y, x] // 1000
                ):
                    lev[y, x] = max(0, lev[y, x] - 1)
                    break


def _inkout(img: np.ndarray, lev: np.ndarray, ink: RGBA) -> None:
    """A one-pixel ink outline around the whole silhouette (8-connected, so corners close)."""
    h, w = lev.shape
    filled = lev >= 0
    pad = np.pad(filled, 1)
    ring = np.zeros_like(filled)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            ring |= pad[1 + dy : 1 + dy + h, 1 + dx : 1 + dx + w]  # no wrap-around at the edges
    ring &= ~filled
    img[ring] = ink


def _edges(lev: np.ndarray, part: np.ndarray, edged: set[str], ink: bool = False) -> np.ndarray:
    """Pixels of an edged part that touch another part take its darkest step (or the ink, in ink mode)."""
    h, w = lev.shape
    src = part.copy()
    inked = np.zeros(lev.shape, dtype=bool)
    for y in range(h):
        for x in range(w):
            if lev[y, x] < 0 or src[y, x] not in edged:
                continue
            for dy, dx in N4:
                yy, xx = y + dy, x + dx
                if 0 <= yy < h and 0 <= xx < w and lev[yy, xx] >= 0 and src[yy, xx] != src[y, x]:
                    lev[y, x] = 0
                    inked[y, x] = ink
                    break
    return inked


def _selout(
    img: np.ndarray, lev: np.ndarray, mat: np.ndarray, ramps: dict[str, list[RGBA]], ink: RGBA
) -> None:
    """Outline in the darkest step of the colour it borders; a step lighter facing the light (top left)."""
    h, w = lev.shape
    out = img.copy()
    for y in range(h):
        for x in range(w):
            if lev[y, x] >= 0:
                continue
            near = [
                (y + dy, x + dx, dy, dx)
                for dy, dx in N4
                if 0 <= y + dy < h and 0 <= x + dx < w and lev[y + dy, x + dx] >= 0
            ]
            if not near:
                continue
            yy, xx, dy, dx = near[0]
            r = ramps[mat[yy, xx]]
            lit_side = dy > 0 or dx > 0  # the outline pixel is above / left of the shape
            c = r[1] if lit_side and len(r) > 3 else r[0]
            # very dark ramps get the ink so the silhouette still reads
            out[y, x] = ink if sum(r[0][:3]) > 330 and not lit_side else c
    img[:] = out


def upscale(img: Image.Image, k: int) -> Image.Image:
    return img.resize((img.width * k, img.height * k), Image.Resampling.NEAREST)


def sheet(
    frames: list[Image.Image], k: int = 6, bg: RGBA = (108, 132, 160, 255), cols: int | None = None
) -> Image.Image:
    """Frames side by side, scaled `k`, on a background (for reviews)."""
    cols = cols or len(frames)
    rows = math.ceil(len(frames) / cols)
    w, h = frames[0].width * k, frames[0].height * k
    out = Image.new("RGBA", (cols * (w + 8) + 8, rows * (h + 8) + 8), bg)
    for i, f in enumerate(frames):
        out.alpha_composite(upscale(f, k), (8 + (i % cols) * (w + 8), 8 + (i // cols) * (h + 8)))
    return out


def onion(frames: list[Image.Image], k: int = 6, bg: RGBA = (230, 230, 236, 255)) -> Image.Image:
    """All frames over each other at low opacity: shows the arcs and spacing of a cycle."""
    w, h = frames[0].width * k, frames[0].height * k
    out = Image.new("RGBA", (w, h), bg)
    for f in frames:
        g = upscale(f, k)
        a = g.getchannel("A").point(lambda v: v * 70 // 255)
        g.putalpha(a)
        out.alpha_composite(g)
    return out


def save_gif(
    frames: list[Image.Image], path: str, k: int = 6, fps: float = 10, bg: RGBA = (108, 132, 160, 255)
) -> None:
    big = []
    for f in frames:
        c = Image.new("RGBA", (f.width * k, f.height * k), bg)
        c.alpha_composite(upscale(f, k))
        big.append(c.convert("RGB"))
    big[0].save(path, save_all=True, append_images=big[1:], duration=round(1000 / fps), loop=0, disposal=2)


def save_mp4(frames: list[Image.Image], path: str, k: int = 10, fps: float = 10, loops: int = 4,
             bg: RGBA = (108, 132, 160, 255)) -> None:  # fmt: skip
    """A looping preview video (H.264, even size) of a cycle played `loops` times."""
    import subprocess
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        n = 0
        for _ in range(loops):
            for f in frames:
                c = Image.new("RGBA", (f.width * k, f.height * k), bg)
                c.alpha_composite(upscale(f, k))
                c.convert("RGB").save(Path(tmp) / f"f{n:05d}.png")
                n += 1
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-framerate", f"{fps:g}", "-i", str(Path(tmp) / "f%05d.png"),
             "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
             path],
            check=True,
        )  # fmt: skip
