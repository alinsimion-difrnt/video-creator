"""A tiny 3D renderer for props (ADR 0029): signed distance fields ray-marched with numpy, no GPU, no API.

Why: the earlier `toon3d` look was a lighting filter over a flat drawing, and it barely read as 3D next to the
illustrated style. Rendering real volumes (smooth-unioned ellipsoids) gives true form, shading that turns
with the object, soft shadows and a rim light, and lets a prop show it is 3D by turning (a turntable).

The model is a list of primitives (ellipsoids, rounded boxes), each with a material and a smooth-union
radius. Rendering marches every pixel's ray at once (vectorised), shades with a key light (wrapped Lambert,
toon-stepped a little for a stylised "3D cartoon" look), a cool fill, a warm rim and ambient occlusion, then
supersamples 2x for clean edges. Output is RGBA with a soft ground shadow, ready to sit on a real lap.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from PIL import Image


@dataclass(frozen=True)
class Prim:
    kind: str  # ellipsoid | box
    center: tuple[float, float, float]
    size: tuple[float, float, float]  # radii (ellipsoid) or half extents (box)
    mat: int  # index into the materials
    rot: tuple[float, float, float] = (0.0, 0.0, 0.0)  # Euler angles (radians) about x, y, z
    blend: float = 0.0  # smooth-union radius with what came before (0 = hard union)
    round: float = 0.0  # box corner radius


@dataclass(frozen=True)
class Material:
    color: tuple[float, float, float]  # linear-ish 0..1
    shine: float = 0.25  # specular strength
    rough: float = 24.0  # specular exponent
    # an optional colour per hit point in model space (N x 3 -> N x 3): counter-shading, scales; it turns with
    # the model, so a pattern stays on the body in a turntable
    texture: Callable[[np.ndarray], np.ndarray] | None = None


def _rot(rx: float, ry: float, rz: float) -> np.ndarray:
    cx, sx, cy, sy, cz, sz = (
        math.cos(rx),
        math.sin(rx),
        math.cos(ry),
        math.sin(ry),
        math.cos(rz),
        math.sin(rz),
    )
    mx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    my = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    mz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    m: np.ndarray = mz @ my @ mx
    return m


def _sd(p: np.ndarray, prim: Prim) -> np.ndarray:
    q = p - np.array(prim.center, dtype=p.dtype)
    if any(prim.rot):
        q = q @ _rot(*prim.rot).astype(p.dtype)  # into the primitive's frame
    if prim.kind == "ellipsoid":
        r = np.array(prim.size, dtype=p.dtype)
        k0 = np.linalg.norm(q / r, axis=-1)
        k1 = np.linalg.norm(q / (r * r), axis=-1)
        out: np.ndarray = k0 * (k0 - 1.0) / np.maximum(k1, 1e-6)
        return out
    b = np.array(prim.size, dtype=p.dtype) - prim.round
    d = np.abs(q) - b
    box: np.ndarray = np.linalg.norm(np.maximum(d, 0), axis=-1) + np.minimum(d.max(axis=-1), 0) - prim.round
    return box


def scene(p: np.ndarray, prims: list[Prim]) -> tuple[np.ndarray, np.ndarray]:
    """Distance to the model and the material id at each point (smooth unions blend materials too)."""
    d = np.full(p.shape[:-1], 1e9, dtype=p.dtype)
    m = np.zeros(p.shape[:-1], dtype=np.int8)
    for prim in prims:
        di = _sd(p, prim)
        if prim.blend > 0:
            h = np.clip(0.5 + 0.5 * (di - d) / prim.blend, 0, 1)
            nd = di * (1 - h) + d * h - prim.blend * h * (1 - h)
            m = np.where(h < 0.5, prim.mat, m)
            d = nd
        else:
            m = np.where(di < d, prim.mat, m)
            d = np.minimum(d, di)
    return d, m


def render(
    prims: list[Prim],
    mats: list[Material],
    size: tuple[int, int],
    yaw: float = 0.0,
    pitch: float = 0.12,
    dist: float = 4.2,
    fov: float = 0.55,
    ss: int = 2,
    steps: int = 80,
    toon: float = 0.35,
    shadow: bool = True,
) -> Image.Image:
    """Render `prims` (model space: y up, z toward the viewer at yaw 0) to an RGBA image of `size` (w, h).
    `yaw` turns the model about y (a turntable), `toon` steps the key light (0 smooth .. 1 hard bands).

    Only rays still marching are evaluated each step (the background drops out after a few steps, v2 of
    this renderer took ~1 min a frame; this one a few seconds), and lighting runs on hit pixels only."""
    w, h = size[0] * ss, size[1] * ss
    aspect = w / h
    ys, xs = np.mgrid[0:h, 0:w].astype(float)
    u = ((xs + 0.5) / w * 2 - 1).ravel()
    v = (1 - (ys + 0.5) / h * 2).ravel()
    world = _rot(pitch, yaw, 0.0)  # turn the model, not the camera: rays go into model space
    ro = np.array([0.0, 0.0, dist]) @ world
    rd = np.stack([u * fov * aspect, v * fov, -np.ones_like(u)], axis=-1)
    rd /= np.linalg.norm(rd, axis=-1, keepdims=True)
    rd = (rd @ world).astype(np.float32)  # float32 halves the memory traffic; the result is unchanged
    # rays that miss a sphere around the model never march
    radius = max(float(np.linalg.norm(pr.center)) + max(pr.size) for pr in prims) + 0.3
    b = (ro * rd).sum(-1)
    disc = b * b - ((ro * ro).sum() - radius * radius)
    live = np.nonzero(disc > 0)[0]
    t = np.zeros(u.shape)
    t[live] = np.maximum(-b[live] - np.sqrt(disc[live]), 0.0)
    hit = np.zeros(u.shape, dtype=bool)
    far = dist + radius * 2
    for _ in range(steps):
        if live.size == 0:
            break
        p = (ro + rd[live] * t[live, None]).astype(np.float32)
        d, _ = scene(p, prims)
        done = d < 0.0015
        hit[live[done]] = True
        t[live] += np.where(done, 0.0, d * 0.92)
        live = live[~done & (t[live] < far)]
    idx = np.nonzero(hit)[0]
    rgba = np.zeros((u.size, 4))
    if idx.size:
        p = (ro + rd[idx] * t[idx, None]).astype(np.float32)
        _, mat = scene(p, prims)
        # normals from four samples on a tetrahedron (six central differences cost 50% more)
        eps = 0.0015
        n = np.zeros(p.shape)
        for k in ((1, -1, -1), (-1, -1, 1), (-1, 1, -1), (1, 1, 1)):
            e = np.array(k, dtype=np.float32)
            n += e * scene(p + e * eps, prims)[0][:, None]
        n /= np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-9)
        key = np.array([-0.55, 0.75, 0.55]) @ world
        key /= np.linalg.norm(key)
        fill = np.array([0.7, 0.1, 0.5]) @ world
        fill /= np.linalg.norm(fill)
        view = -rd[idx]
        wrap = np.clip(((n * key).sum(-1) + 0.25) / 1.25, 0, 1)
        diff = wrap * (1 - toon) + np.round(wrap * 3) / 3 * toon
        fill_d = np.clip((n * fill).sum(-1), 0, 1) * 0.28
        rim = np.clip(1 - (n * view).sum(-1), 0, 1) ** 3 * 0.55
        half = key + view
        half /= np.linalg.norm(half, axis=-1, keepdims=True)
        ao = np.ones(idx.size)
        for step in range(1, 5):
            dk = 0.04 * step
            ao -= (dk - scene((p + n * dk).astype(np.float32), prims)[0]) * (0.5 / step)
        ao = np.clip(ao, 0.45, 1)
        sh = np.ones(idx.size)
        if shadow:  # soft shadow toward the key light
            ts = np.full(idx.size, 0.02)
            for _ in range(14):
                dd, _ = scene((p + key * ts[:, None]).astype(np.float32), prims)
                sh = np.minimum(sh, np.clip(10 * dd / ts, 0, 1))
                ts += np.clip(dd, 0.02, 0.2)
            sh = 0.55 + 0.45 * sh
        col = np.zeros(p.shape)
        for i, m in enumerate(mats):
            sel = mat == i
            if not sel.any():
                continue
            spec = np.clip((n[sel] * half[sel]).sum(-1), 0, 1) ** m.rough * m.shine
            c = m.texture(p[sel].astype(float)) if m.texture else np.array(m.color)
            lit = c * (0.32 + 0.85 * diff[sel, None] * sh[sel, None]) + c * fill_d[sel, None] * np.array(
                [0.7, 0.85, 1.1]
            )
            col[sel] = lit * ao[sel, None] + spec[:, None] + rim[sel, None] * np.array([1.0, 0.92, 0.8]) * 0.6
        rgba[idx, :3] = np.clip(col, 0, 1) ** (1 / 1.15)
        rgba[idx, 3] = 1.0
    img = (rgba.reshape(h, w, 4) * 255).astype(np.uint8)
    return Image.fromarray(img, "RGBA").resize(size, Image.Resampling.LANCZOS)
