"""Pure geometry for S4: energy-quantile frames, crops, candidate boxes and NMS (BUILD_PLAN 7.2).

Boxes are (x0, y0, x1, y1) in proxy pixels, x1/y1 exclusive.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import cv2
import numpy as np

Box = tuple[int, int, int, int]


def quantile_frames(energy: Sequence[float], quantiles: Sequence[float]) -> list[int]:
    """Indices into `energy` where cumulative motion energy first reaches each quantile.

    Frames bunch up where things move and thin out where they settle; with no energy at all the
    frames are spread evenly in time instead.
    """
    e = np.maximum(np.asarray(energy, dtype=np.float64), 0.0)
    n = len(e)
    if n == 0:
        return []
    total = float(e.sum())
    if total <= 0:
        return [round(q * (n - 1)) for q in quantiles]
    cum = np.cumsum(e) / total
    out = []
    for q in quantiles:
        if q <= 0:
            out.append(0)
        elif q >= 1:
            out.append(n - 1)
        else:
            out.append(int(np.searchsorted(cum, q, side="left")))
    return out


def crop_box(bbox: Box, width: int, height: int, margin: float, min_px: int) -> Box:
    """`bbox` grown by `margin` of its size per side, at least `min_px` each way, inside the frame."""
    x0, y0, x1, y1 = bbox
    w, h = x1 - x0, y1 - y0
    w2 = max(w * (1 + 2 * margin), min(min_px, width))
    h2 = max(h * (1 + 2 * margin), min(min_px, height))
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    nx0 = round(min(max(cx - w2 / 2, 0), width - w2))
    ny0 = round(min(max(cy - h2 / 2, 0), height - h2))
    return (max(nx0, 0), max(ny0, 0), min(round(nx0 + w2), width), min(round(ny0 + h2), height))


def norm_to_px(bbox: Sequence[float] | None, width: int, height: int) -> Box:
    if bbox is None:
        return (0, 0, width, height)
    x0, y0, x1, y1 = bbox
    return (
        max(0, int(np.floor(x0 * width))),
        max(0, int(np.floor(y0 * height))),
        min(width, int(np.ceil(x1 * width))),
        min(height, int(np.ceil(y1 * height))),
    )


def change_mask(a: np.ndarray, b: np.ndarray, threshold: int) -> np.ndarray:
    """Pixels whose largest channel difference exceeds `threshold` (0-255)."""
    d = np.abs(a.astype(np.int16) - b.astype(np.int16)).max(axis=2)
    return d > threshold


def diff_components(mask: np.ndarray, merge_px: int, min_area: float) -> list[Box]:
    """Connected components of the change mask after closing small gaps; tiny ones dropped."""
    m: np.ndarray = mask.astype(np.uint8)
    if merge_px > 0:
        k = np.ones((2 * merge_px + 1, 2 * merge_px + 1), np.uint8)
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k)
    n, _, stats, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    floor = min_area * mask.shape[0] * mask.shape[1]
    out = []
    for i in range(1, n):
        x, y, w, h, area = (int(v) for v in stats[i])
        if area >= floor:
            out.append((x, y, x + w, y + h))
    return out


def area(b: Box) -> int:
    return max(0, b[2] - b[0]) * max(0, b[3] - b[1])


def iou(a: Box, b: Box) -> float:
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    union = area(a) + area(b) - inter
    return inter / union if union else 0.0


@dataclass(frozen=True)
class Candidate:
    box: Box
    source: str  # diff | ocr | union
    changed_px: int  # changed pixels inside the box (the ranking key)
    changed_share: float
    text: str | None = None


def score(box: Box, integral: np.ndarray) -> int:
    """Changed pixels inside `box`, from the mask's summed-area table."""
    x0, y0, x1, y1 = box
    return int(integral[y1, x1] - integral[y0, x1] - integral[y1, x0] + integral[y0, x0])


def rank_and_suppress(
    boxes: Sequence[tuple[Box, str, str | None]], mask: np.ndarray, iou_max: float, cap: int
) -> list[Candidate]:
    """Rank by overlap with the change mask, drop near-duplicates (NMS), keep at most `cap`.

    Ties go to the smaller box (the tighter description of the same change). The `union` box is a
    fallback: it never suppresses a specific box, but is dropped when one nearly duplicates it.
    """
    integral = cv2.integral(mask.astype(np.uint8))
    cands = []
    for box, source, text in boxes:
        if area(box) == 0:
            continue
        px = score(box, integral)
        cands.append(Candidate(box, source, px, round(px / area(box), 4), text))
    cands.sort(key=lambda c: (-c.changed_px, area(c.box), c.box))
    specific = [c for c in cands if c.source != "union"]
    kept: list[Candidate] = []
    for c in specific:
        if all(iou(c.box, k.box) <= iou_max for k in kept):
            kept.append(c)
    for u in (c for c in cands if c.source == "union"):
        if all(iou(u.box, k.box) <= iou_max for k in kept):
            kept.append(u)
    kept.sort(key=lambda c: (-c.changed_px, area(c.box), c.box))
    return kept[:cap]
