"""Pure measures for the pixel-art study (studies/README.md, "Measure"): images are numpy arrays (H x W x 3
uint8, or H x W x 4 with alpha). Code measures, Claude names: nothing here judges whether art is good."""

from __future__ import annotations

import colorsys
from dataclasses import dataclass

import numpy as np

from study.pixel.config import Measure


def _luma(rgb: np.ndarray) -> np.ndarray:
    return (0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]) / 255.0


def _uniform_share(img: np.ndarray, k: int, ox: int, oy: int, tol: int) -> float:
    h, w = img.shape[:2]
    a = img[oy : oy + (h - oy) // k * k, ox : ox + (w - ox) // k * k, :3].astype(np.int16)
    if a.shape[0] < k or a.shape[1] < k:
        return 0.0
    b = a.reshape(a.shape[0] // k, k, a.shape[1] // k, k, 3)
    spread = b.max(axis=(1, 3)) - b.min(axis=(1, 3))
    return float((spread.max(axis=-1) <= tol).mean())


def native_scale(img: np.ndarray, cfg: Measure, crop: int = 192) -> tuple[int, int, int]:
    """(scale, x offset, y offset): the largest pixel size whose blocks are uniform. 1 = already native.
    Searched on a central crop of at most `crop` pixels a side (offsets are the same across the image)."""
    h, w = img.shape[:2]
    if max(h, w) > crop:
        y0, x0 = (h - min(h, crop)) // 2, (w - min(w, crop)) // 2
        k, ox, oy = native_scale(img[y0 : y0 + crop, x0 : x0 + crop], cfg, crop)
        return k, (ox + x0) % k, (oy + y0) % k
    best = (1, 0, 0)
    for k in range(2, cfg.max_scale + 1):
        for oy in range(k):
            for ox in range(k):
                if _uniform_share(img, k, ox, oy, cfg.block_tolerance) >= cfg.block_min_share:
                    best = (k, ox, oy)
                    break
            else:
                continue
            break
    return best


def downscale(img: np.ndarray, k: int, ox: int = 0, oy: int = 0) -> np.ndarray:
    """The native-resolution image: the centre pixel of each k x k block."""
    return img[oy + k // 2 :: k, ox + k // 2 :: k].copy()


def palette(img: np.ndarray, cfg: Measure) -> list[tuple[tuple[int, int, int], float]]:
    """Colours with their share of the visible pixels, most common first; rare colours (noise) dropped."""
    rgb = img[..., :3].reshape(-1, 3)
    if img.shape[-1] == 4:
        rgb = rgb[img[..., 3].reshape(-1) > 127]
    if rgb.size == 0:
        return []
    cols, counts = np.unique(rgb, axis=0, return_counts=True)
    share = counts / counts.sum()
    order = np.argsort(-share)
    return [
        ((int(cols[i][0]), int(cols[i][1]), int(cols[i][2])), round(float(share[i]), 4))
        for i in order
        if share[i] >= cfg.min_colour_share
    ]


@dataclass(frozen=True)
class Ramp:
    colours: list[tuple[int, int, int]]  # dark to light
    hue_shift: float  # degrees from the darkest to the lightest colour (signed, -180..180)
    lightness_span: float  # luma of the lightest minus the darkest


def _hls(c: tuple[int, int, int]) -> tuple[float, float, float]:
    return colorsys.rgb_to_hls(c[0] / 255, c[1] / 255, c[2] / 255)


def _chroma(c: tuple[int, int, int]) -> float:
    return (max(c) - min(c)) / 255


def ramps(colours: list[tuple[int, int, int]], cfg: Measure) -> list[Ramp]:
    """Group colours into ramps (near hues, or the greys) and order each by lightness. A ramp with a large
    hue shift is a hue-shifted ramp (shadows cool, lights warm, or the other way round)."""
    rest = sorted(colours, key=lambda c: _hls(c)[0])
    groups: list[list[tuple[int, int, int]]] = []
    greys = [c for c in rest if _chroma(c) < cfg.ramp_min_chroma]
    hued = [c for c in rest if _chroma(c) >= cfg.ramp_min_chroma]
    for c in hued:
        h = _hls(c)[0] * 360
        for g in groups:
            gh = np.mean([_hls(x)[0] * 360 for x in g])
            if min(abs(h - gh), 360 - abs(h - gh)) <= cfg.ramp_hue_window:
                g.append(c)
                break
        else:
            groups.append([c])
    if greys:
        groups.append(greys)
    out = []
    for g in groups:
        if len(g) < cfg.ramp_min_len:
            continue
        g = sorted(g, key=lambda c: _luma(np.array(c, dtype=float)))
        dh = (_hls(g[-1])[0] - _hls(g[0])[0]) * 360
        dh = (dh + 180) % 360 - 180
        span = float(_luma(np.array(g[-1], dtype=float)) - _luma(np.array(g[0], dtype=float)))
        out.append(Ramp(g, round(dh, 1), round(span, 3)))
    return out


def outline(img: np.ndarray, cfg: Measure) -> dict[str, float | str]:
    """On a sprite with alpha: the share of its edge pixels drawn darker than the pixel inside them, and
    whether those outlines are black or coloured."""
    if img.shape[-1] != 4:
        return {"style": "unknown", "dark_share": 0.0, "black_share": 0.0}
    a = img[..., 3] > 127
    luma = _luma(img[..., :3].astype(float))
    inside = np.zeros_like(a)
    inside[1:-1, 1:-1] = a[1:-1, 1:-1] & a[:-2, 1:-1] & a[2:, 1:-1] & a[1:-1, :-2] & a[1:-1, 2:]
    edge = a & ~inside
    ys, xs = np.nonzero(edge)
    dark = black = n = 0
    for y, x in zip(ys, xs, strict=True):
        nb = [
            luma[yy, xx]
            for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1))
            if 0 <= yy < a.shape[0] and 0 <= xx < a.shape[1] and inside[yy, xx]
        ]
        if not nb:  # a corner or a one-pixel spur: nothing inside to compare with
            continue
        n += 1
        if max(nb) - luma[y, x] >= cfg.outline_dark_delta:
            dark += 1
            black += luma[y, x] <= cfg.outline_black_luma
    n = max(1, n)
    ds, bs = dark / n, black / max(1, dark)
    style = "none" if ds < 0.3 else ("black" if bs >= 0.6 else ("selective" if ds < 0.75 else "coloured"))
    return {"style": style, "dark_share": round(ds, 3), "black_share": round(bs, 3)}


def dither_share(img: np.ndarray) -> float:
    """Share of 2x2 windows that are a two-colour checkerboard (a b / b a with a != b)."""
    rgb = img[..., :3].astype(np.int32)
    code = (rgb[..., 0] << 16) | (rgb[..., 1] << 8) | rgb[..., 2]
    if code.shape[0] < 2 or code.shape[1] < 2:
        return 0.0
    a, b = code[:-1, :-1], code[:-1, 1:]
    c, d = code[1:, :-1], code[1:, 1:]
    checker = (a == d) & (b == c) & (a != b)
    return round(float(checker.mean()), 4)


def animation(frames: list[np.ndarray], durations_ms: list[int]) -> dict[str, object]:
    """Timing of a sprite animation (a GIF's frames): drawings, how long each is held, and how much the
    silhouette squashes and stretches (bounding-box height/width of the opaque or non-background pixels)."""
    keys = [f.tobytes() for f in frames]
    holds: list[int] = []
    drawings = 0
    for i, k in enumerate(keys):
        if i == 0 or k != keys[i - 1]:
            drawings += 1
            holds.append(durations_ms[i])
        else:
            holds[-1] += durations_ms[i]
    ratios = []
    for f in frames:
        mask = f[..., 3] > 127 if f.shape[-1] == 4 else np.any(f[..., :3] != f[0, 0, :3], axis=-1)
        ys, xs = np.nonzero(mask)
        if ys.size:
            ratios.append((ys.max() - ys.min() + 1) / (xs.max() - xs.min() + 1))
    total = sum(durations_ms)
    return {
        "frames": len(frames),
        "drawings": drawings,
        "cycle_ms": total,
        "hold_ms_median": float(np.median(holds)) if holds else None,
        "hold_ms_min": min(holds) if holds else None,
        "hold_ms_max": max(holds) if holds else None,
        "drawings_per_s": round(drawings / (total / 1000), 2) if total else None,
        "squash_stretch": round(float(max(ratios) / min(ratios)), 3) if len(ratios) > 1 else None,
    }


def holds(diff: np.ndarray, fps: float, threshold: float) -> dict[str, object]:
    """How long each picture is held in a video of pixel animation: runs of frames whose difference to the
    previous frame stays under `threshold` (0..1 mean absolute difference). Hand-keyed pixel art holds
    each drawing for 2-6 frames at 30-60 fps; smooth video changes every frame."""
    changes = [i for i in range(1, len(diff)) if diff[i] > threshold]
    if len(changes) < 2:
        return {"changes": len(changes), "hold_ms_median": None, "drawings_per_s": None, "on_frames": None}
    runs = np.diff(changes)
    ms = runs / fps * 1000
    med = float(np.median(runs))
    return {
        "changes": len(changes),
        "hold_ms_median": round(float(np.median(ms)), 1),
        "hold_ms_p25": round(float(np.percentile(ms, 25)), 1),
        "hold_ms_p75": round(float(np.percentile(ms, 75)), 1),
        "drawings_per_s": round(len(changes) / (len(diff) / fps), 2),
        "on_frames": round(med * 30 / fps, 1),  # "on 2s" etc., in 30 fps frames
    }
