"""Follow one element through its burst (BUILD_PLAN 7.5 steps 1-3).

Tracking: the element's crop on the settled end frame is matched backwards frame by frame with
normalised cross-correlation (cv2.TM_CCOEFF_NORMED), over a small set of per-frame scale changes so
scale-pops are followed. Large search areas are searched coarse to fine (see `_match`). NCC ignores
brightness and contrast changes on a flat background, so elements that fade while moving are still
placed while they are faint.

Opacity proxy: each frame's box region is modelled as alpha * end + (1 - alpha) * background, where the
background is the same region in the first burst frame; alpha is the least-squares solution, clamped.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import cv2
import numpy as np

Box = tuple[int, int, int, int]


@dataclass(frozen=True)
class Track:
    frames: list[int]  # proxy frame indices, ascending
    cx: np.ndarray  # box centre, proxy pixels
    cy: np.ndarray
    scale: np.ndarray  # relative to the end frame
    confidence: np.ndarray  # NCC of the match
    alpha: np.ndarray | None  # opacity proxy, or None when the element hardly differs from its background


def _gray(rgb: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)


def _match_at(
    hay: np.ndarray, template: np.ndarray, scale: float, steps: Sequence[float]
) -> tuple[float, float, float, float]:
    """Best (cx, cy, scale, ncc) of the template in `hay` (hay coordinates) over scale * steps."""
    best = (0.0, 0.0, scale, -1.0)
    for step in steps:
        s = float(np.clip(scale * step, 0.1, 3.0))
        th, tw = max(4, round(template.shape[0] * s)), max(4, round(template.shape[1] * s))
        if th >= hay.shape[0] or tw >= hay.shape[1]:
            continue
        t = cv2.resize(template, (tw, th), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR)
        if float(t.std()) < 1e-3:
            continue
        res = cv2.matchTemplate(hay, t, cv2.TM_CCOEFF_NORMED)
        _, v, _, loc = cv2.minMaxLoc(res)
        if v > best[3]:
            best = (loc[0] + tw / 2, loc[1] + th / 2, s, float(v))
    return best


def _window(
    cx: float, cy: float, template: np.ndarray, scale: float, steps: Sequence[float], r: int, region: Box
) -> Box:
    """The part of `region` that holds the template centred near (cx, cy), give or take `r` pixels."""
    grow = scale * max(max(steps), 1.0)
    hw, hh = template.shape[1] * grow / 2 + r, template.shape[0] * grow / 2 + r
    x0, y0, x1, y1 = region
    return (
        max(x0, int(np.floor(cx - hw))),
        max(y0, int(np.floor(cy - hh))),
        min(x1, int(np.ceil(cx + hw)) + 1),
        min(y1, int(np.ceil(cy + hh)) + 1),
    )


def _match(
    gray: np.ndarray,
    template: np.ndarray,
    region: Box,
    scale: float,
    steps: Sequence[float],
    coarse_px: int,
    coarse_min_template_px: int,
) -> tuple[float, float, float, float]:
    """Best (cx, cy, scale, ncc) of the template inside `region` over scale * steps.

    Coarse to fine: a large search area is first searched shrunk to about `coarse_px` on its long side
    (never shrinking the template below `coarse_min_template_px`), then the match is redone at full
    size in a small window around the coarse hit. The result has the full-size pixel accuracy.
    """
    x0, y0, x1, y1 = region
    hay = gray[y0:y1, x0:x1]
    smallest = min(template.shape) * scale * min(min(steps), 1.0)
    k = min(max(hay.shape) / coarse_px, smallest / coarse_min_template_px)
    if k < 2:
        bx, by, bs, bc = _match_at(hay, template, scale, steps)
        return (x0 + bx, y0 + by, bs, bc)
    size = (max(1, round(hay.shape[1] / k)), max(1, round(hay.shape[0] / k)))
    small_hay = cv2.resize(hay, size, interpolation=cv2.INTER_AREA)
    tsize = (max(1, round(template.shape[1] / k)), max(1, round(template.shape[0] / k)))
    small_t = cv2.resize(template, tsize, interpolation=cv2.INTER_AREA)
    cx, cy, cs, cc = _match_at(small_hay, small_t, scale, steps)
    if cc < 0:
        return (0.0, 0.0, scale, -1.0)
    win = _window(x0 + cx * k, y0 + cy * k, template, scale, steps, int(np.ceil(2 * k)) + 2, region)
    fx, fy, fs, fc = _match_at(gray[win[1] : win[3], win[0] : win[2]], template, scale, steps)
    if fc < 0:  # the window clipped at the region edge: keep the coarse hit
        return (x0 + cx * k, y0 + cy * k, cs, cc)
    return (win[0] + fx, win[1] + fy, fs, fc)


def _alpha(region: np.ndarray, end: np.ndarray, background: np.ndarray, min_contrast: float) -> float | None:
    # A light blur first: sub-pixel misalignment of a detailed element (after scaling or tracking)
    # would otherwise read as transparency.
    sigma = max(1.5, 0.03 * max(end.shape[:2]))
    region, end, background = (cv2.GaussianBlur(a, (0, 0), sigma) for a in (region, end, background))
    d = end - background
    energy = float(np.mean(np.abs(d)))
    if energy < min_contrast:
        return None
    a = float(np.sum((region - background) * d) / max(float(np.sum(d * d)), 1e-9))
    return float(np.clip(a, 0.0, 1.0))


def track(
    frames: Sequence[np.ndarray],
    first_frame: int,
    box: Box,
    search: Box,
    scale_steps: Sequence[float],
    min_contrast: float,
    min_confidence: float,
    coarse_px: int,
    coarse_min_template_px: int,
) -> Track:
    """`frames` are the burst (RGB, ascending from `first_frame`); `box` is the element on the last one.

    A frame matched below `min_confidence` keeps the later frame's place (its confidence is still
    recorded): a faint or hidden element is read where it was last seen, not wherever noise matches.
    """
    grays = [_gray(f) for f in frames]
    h, w = grays[0].shape
    x0, y0, x1, y1 = box
    # The template includes a thin ring of surroundings so flat-coloured elements still have edges.
    m = max(2, round(0.08 * max(x1 - x0, y1 - y0)))
    tx0, ty0, tx1, ty1 = max(0, x0 - m), max(0, y0 - m), min(w, x1 + m), min(h, y1 + m)
    template = grays[-1][ty0:ty1, tx0:tx1]
    n = len(grays)
    cx, cy, sc, conf = np.zeros(n), np.zeros(n), np.ones(n), np.zeros(n)
    cx[-1], cy[-1], sc[-1], conf[-1] = (tx0 + tx1) / 2, (ty0 + ty1) / 2, 1.0, 1.0
    # Pad the search area so an element partly outside the frame (sliding in) can still be matched: it
    # grows past every frame edge it touches. Only the search area is cut out and padded.
    pad = max(template.shape)
    sx0, sy0, sx1, sy1 = max(0, search[0]), max(0, search[1]), min(w, search[2]), min(h, search[3])
    left, top = (pad if sx0 <= 0 else 0), (pad if sy0 <= 0 else 0)
    right, bottom = (pad if sx1 >= w else 0), (pad if sy1 >= h else 0)
    ox, oy = sx0 - left, sy0 - top  # area pixel (0, 0) in frame pixels
    for i in range(n - 2, -1, -1):
        g = grays[i]
        hay = cv2.copyMakeBorder(
            g[sy0:sy1, sx0:sx1],
            top,
            bottom,
            left,
            right,
            cv2.BORDER_CONSTANT,
            value=float(np.median(g[::4, ::4])),
        )
        area = (0, 0, hay.shape[1], hay.shape[0])
        bx, by, bs, bc = _match(
            hay, template, area, sc[i + 1], scale_steps, coarse_px, coarse_min_template_px
        )
        if bc >= 0 and len(scale_steps) > 1:  # refine the scale between the coarse steps, near the hit
            fine = [1 + (s - 1) / 4 for s in scale_steps]
            win = _window(bx, by, template, bs, fine, 2, area)
            fx, fy, fs, fc = _match(hay, template, win, bs, fine, coarse_px, coarse_min_template_px)
            if fc > bc:
                bx, by, bs, bc = fx, fy, fs, fc
        bx, by = bx + ox, by + oy
        if bc < 0:  # nothing fits (template larger than the search area): hold the last estimate
            bx, by, bs, bc = cx[i + 1], cy[i + 1], sc[i + 1], 0.0
        elif bc < min_confidence:
            bx, by, bs = cx[i + 1], cy[i + 1], sc[i + 1]
        cx[i], cy[i], sc[i], conf[i] = bx, by, bs, bc
    # Template centre -> box centre (the ring may be clipped by the frame edge).
    cx += (x0 + x1) / 2 - (tx0 + tx1) / 2
    cy += (y0 + y1) / 2 - (ty0 + ty1) / 2
    # Opacity at the tracked place; background = that place in the first burst frame.
    end_rgb = frames[-1][y0:y1, x0:x1].astype(np.float32)
    alphas: list[float] = []
    for i, f in enumerate(frames):
        bw, bh = (x1 - x0) * sc[i], (y1 - y0) * sc[i]
        rx0 = int(np.clip(round(cx[i] - bw / 2), 0, w - 1))
        ry0 = int(np.clip(round(cy[i] - bh / 2), 0, h - 1))
        rx1, ry1 = int(np.clip(rx0 + round(bw), rx0 + 1, w)), int(np.clip(ry0 + round(bh), ry0 + 1, h))
        size = (x1 - x0, y1 - y0)
        region = cv2.resize(f[ry0:ry1, rx0:rx1], size).astype(np.float32)
        background = cv2.resize(frames[0][ry0:ry1, rx0:rx1], size).astype(np.float32)
        a = _alpha(region, end_rgb, background, min_contrast)
        if a is None:
            alphas = []
            break
        alphas.append(a)
    alpha = np.asarray(alphas) if len(alphas) == n else None
    return Track(list(range(first_frame, first_frame + n)), cx, cy, sc, conf, alpha)


@dataclass(frozen=True)
class Channel:
    name: str  # x | y | scale | opacity
    t: np.ndarray  # seconds from the burst start
    progress: np.ndarray  # 0 at the start value, 1 at the end value
    start_value: float
    end_value: float
    start_f: int  # first frame that left the start value (beyond the tolerance)
    end_f: int  # first frame from which the value stays within the tolerance of its end
    frames_start: int  # proxy frame at t = 0
    observed_start: bool  # False: the motion had begun before the first usable frame


def progress_channel(
    name: str,
    frames: list[int],
    values: np.ndarray,
    fps: float,
    min_change: float,
    tolerance: float,
    observed_start: bool = True,
) -> Channel | None:
    """Normalised progress of one channel, or None when it barely changes."""
    v0, v1 = float(values[0]), float(values[-1])
    if abs(v1 - v0) < min_change:
        return None
    p = (values - v0) / (v1 - v0)
    off = np.flatnonzero(np.abs(p - 1) > tolerance)
    end_i = int(off[-1] + 1) if off.size else 0
    moved = np.flatnonzero(np.abs(p) > tolerance)
    start_i = int(moved[0]) if moved.size else 0
    t = (np.asarray(frames) - frames[0]) / fps
    return Channel(
        name, t, p, v0, v1, frames[start_i], frames[min(end_i, len(frames) - 1)], frames[0], observed_start
    )
