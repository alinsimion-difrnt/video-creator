"""S3 video signals: cuts, gradual transitions, shots, motion events, camera, holds, pace (BUILD_PLAN 7.1).

One streaming decode of the proxy at native fps. Per frame we keep only small arrays: the mean
absolute difference to the previous frame, a 64x36 thumbnail, the diff-mask bounding box and a
global-motion estimate. Everything downstream works on those.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

from lens.media import iter_frames_rgb, scaled_size
from lens.schemas.config import VideoSignalsConfig

THUMB = (64, 36)
MID = (128, 72)  # uint8 frames for edge-layout comparisons (dissolve detection)


@dataclass
class FrameSeries:
    fps: float
    diff: np.ndarray  # (n,) mean |f_t - f_{t-1}| / 255; diff[0] = 0
    thumbs: np.ndarray  # (n, 36, 64) float32 0..1
    mids: np.ndarray  # (n, 72, 128) uint8 grayscale
    bboxes: np.ndarray  # (n, 4) x0, y0, x1, y1 in 0..1 of the diff mask; nan when empty
    tx: np.ndarray  # (n,) global translation (fraction of width) from t-1 to t
    ty: np.ndarray
    scale: np.ndarray  # (n,) global scale from t-1 to t
    edges: list[np.ndarray] = field(default_factory=list)  # per-frame Canny maps are not kept

    @property
    def n(self) -> int:
        return int(self.diff.shape[0])


def _global_motion(prev: np.ndarray, cur: np.ndarray, min_response: float) -> tuple[float, float, float]:
    """Global (tx, ty) in pixels by phase correlation, and scale from sparse flow (prev→cur).

    Phase correlation works on flat UI colours where corner trackers find too few features.
    """
    a, b = prev.astype(np.float32), cur.astype(np.float32)
    (dx, dy), response = cv2.phaseCorrelate(a, b, cv2.createHanningWindow(a.shape[::-1], cv2.CV_32F))
    tx, ty = (float(dx), float(dy)) if response >= min_response else (0.0, 0.0)
    scale = 1.0
    pts = cv2.goodFeaturesToTrack(prev, maxCorners=200, qualityLevel=0.01, minDistance=4)
    if pts is not None and len(pts) >= 4:
        nxt, status, _ = cv2.calcOpticalFlowPyrLK(  # type: ignore[call-overload]
            prev, cur, pts, None, winSize=(31, 31), maxLevel=4
        )
        ok = status.reshape(-1) == 1
        if ok.sum() >= 4:
            m, inliers = cv2.estimateAffinePartial2D(
                pts[ok], nxt[ok], method=cv2.RANSAC, ransacReprojThreshold=2.0
            )
            if m is not None and inliers is not None and inliers.sum() >= 0.6 * ok.sum():
                scale = float(np.hypot(m[0, 0], m[1, 0]))
    return tx, ty, scale


def scan(proxy: Path, fps: float, width: int, height: int, cfg: VideoSignalsConfig) -> FrameSeries:
    w, h = scaled_size(width, height, cfg.analysis_width)
    diffs: list[float] = []
    thumbs: list[np.ndarray] = []
    mids: list[np.ndarray] = []
    boxes: list[tuple[float, float, float, float]] = []
    motion: list[tuple[float, float, float]] = []
    prev: np.ndarray | None = None
    for _, rgb in iter_frames_rgb(proxy, fps, w, h):
        gray = cv2.GaussianBlur(cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY), (3, 3), 0)
        thumbs.append(cv2.resize(gray, THUMB, interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0)
        mids.append(cv2.resize(gray, MID, interpolation=cv2.INTER_AREA))
        if prev is None:
            diffs.append(0.0)
            boxes.append((np.nan,) * 4)
            motion.append((0.0, 0.0, 1.0))
        else:
            delta = cv2.absdiff(gray, prev)
            diffs.append(float(delta.mean()) / 255.0)
            mask = delta > cfg.mask_threshold
            if mask.any():
                ys, xs = np.nonzero(mask)
                boxes.append((xs.min() / w, ys.min() / h, (xs.max() + 1) / w, (ys.max() + 1) / h))
            else:
                boxes.append((np.nan,) * 4)
            if diffs[-1] > cfg.event_abs_min_diff:
                tx, ty, sc = _global_motion(prev, gray, cfg.phase_min_response)
                motion.append((tx / w, ty / h, sc))
            else:
                motion.append((0.0, 0.0, 1.0))
        prev = gray
    m = np.asarray(motion, dtype=np.float64).reshape(-1, 3)
    return FrameSeries(
        fps=fps,
        diff=np.asarray(diffs, dtype=np.float64),
        thumbs=np.asarray(thumbs, dtype=np.float32),
        mids=np.asarray(mids, dtype=np.uint8).reshape(-1, MID[1], MID[0]),
        bboxes=np.asarray(boxes, dtype=np.float64).reshape(-1, 4),
        tx=m[:, 0],
        ty=m[:, 1],
        scale=m[:, 2],
    )


# ---------------------------------------------------------------------------------------------
# Cuts and gradual transitions


@dataclass(frozen=True)
class Transition:
    kind: str  # hard_cut | crossfade | push | zoom_through | other
    start_f: int  # first frame that differs from the outgoing shot
    end_f: int  # first clean frame of the incoming shot (exclusive end)
    direction: str | None = None


def _runs(mask: np.ndarray, max_gap: int = 0, min_len: int = 1) -> list[tuple[int, int]]:
    """Inclusive (start, end) runs of True, merging gaps of at most `max_gap` False frames."""
    runs: list[tuple[int, int]] = []
    idx = np.flatnonzero(mask)
    if idx.size == 0:
        return runs
    start = prev = int(idx[0])
    for i in idx[1:]:
        i = int(i)
        if i - prev - 1 > max_gap:
            runs.append((start, prev))
            start = i
        prev = i
    runs.append((start, prev))
    return [(a, b) for a, b in runs if b - a + 1 >= min_len]


def detect_cuts(fs: FrameSeries, cfg: VideoSignalsConfig) -> list[int]:
    """Frames that start a new shot via an isolated diff spike (AdaptiveDetector-style ratio test)."""
    d = fs.diff
    cuts = []
    win = max(2, round(fs.fps / 2))
    for t in range(1, fs.n):
        if d[t] < cfg.cut_min_diff:
            continue
        lo, hi = max(1, t - win), min(fs.n, t + win + 1)
        neighbours = np.concatenate([d[lo:t], d[t + 1 : hi]])
        local = float(np.median(neighbours)) if neighbours.size else 0.0
        before = d[t - 1] if t > 1 else 0.0
        after = d[t + 1] if t + 1 < fs.n else 0.0
        if d[t] >= cfg.cut_ratio * max(local, 1e-3) and max(before, after) * cfg.cut_ratio <= d[t]:
            cuts.append(t)
    return cuts


def _crossfade_residual(fs: FrameSeries, a: int, b: int) -> float:
    """Mean residual of fitting frames a..b-1 as alpha blends of frame a-1 and frame b."""
    A, B = fs.thumbs[a - 1].ravel(), fs.thumbs[b].ravel()
    diff = A - B
    denom = float(diff @ diff)
    if denom < 1e-6:
        return 1.0
    res = []
    for t in range(a, b):
        f = fs.thumbs[t].ravel()
        alpha = float(np.clip((f - B) @ diff / denom, 0, 1))
        res.append(float(np.abs(f - (B + alpha * diff)).mean()))
    return float(np.mean(res)) if res else 1.0


def classify_transition(fs: FrameSeries, a: int, b: int, cfg: VideoSignalsConfig) -> tuple[str, str | None]:
    tx, sc = fs.tx[a : b + 1], fs.scale[a : b + 1]
    moving = np.abs(tx) > cfg.push_min_shift
    if moving.mean() >= 0.6 and np.all(np.sign(tx[moving]) == np.sign(np.median(tx[moving]))):
        return "push", "left" if np.median(tx[moving]) < 0 else "right"
    if _crossfade_residual(fs, a, b) <= cfg.crossfade_max_residual:
        return "crossfade", None
    if np.mean(np.abs(sc - 1.0) > cfg.zoom_min_scale_step) >= 0.4:
        return "zoom_through", None
    return "other", None


def detect_transitions(fs: FrameSeries, cuts: list[int], cfg: VideoSignalsConfig) -> list[Transition]:
    """Hard cuts plus gradual transitions. A cut spike inside a sustained run of change, with
    motion on both sides (a zoom-through or whip that swaps scenes at its midpoint), is one
    gradual transition, not a hard cut."""
    out: list[Transition] = []
    absorbed: set[int] = set()
    active = fs.diff > cfg.transition_min_diff
    for a, b in _runs(active, max_gap=0, min_len=cfg.transition_min_frames):
        if a < 1 or b + 1 > fs.n - 1:
            continue
        inner = [c for c in cuts if a <= c <= b]
        if len(inner) > 1:
            continue
        if inner:
            c = inner[0]
            if c - a < 2 or b - c < 2:
                continue  # an isolated cut with a little motion next to it
        change = float(np.abs(fs.thumbs[a - 1] - fs.thumbs[b]).mean())
        if change < cfg.transition_min_change:
            continue
        kind, direction = classify_transition(fs, a, b, cfg)
        if inner and kind in ("crossfade", "other"):
            kind = (
                "zoom_through"
                if np.mean(np.abs(fs.scale[a : b + 1] - 1.0) > cfg.zoom_min_scale_step) >= 0.3
                else "other"
            )
        out.append(Transition(kind, a, b, direction))
        absorbed.update(inner)
    # A cut whose neighbours move globally on both sides (scale or shift) is a zoom/whip whose
    # slow ends stayed under transition_min_diff: grow it over the frames above the noise floor.
    floor = noise_floor(fs.diff, cfg)
    for c in cuts:
        if c in absorbed:
            continue
        a = c
        while a - 1 >= 1 and fs.diff[a - 1] > floor:
            a -= 1
        b = c
        while b + 1 < fs.n and fs.diff[b + 1] > floor:
            b += 1
        sides = list(range(a, c)) + list(range(c + 1, b + 1))
        if c - a < 2 or b - c < 2:
            continue
        scale_dev = np.abs(fs.scale[sides] - 1.0) > cfg.zoom_min_scale_step
        shifting = np.abs(fs.tx[sides]) > cfg.push_min_shift
        if scale_dev.mean() >= 0.3:
            out.append(Transition("zoom_through", a, b + 1))
        elif shifting.mean() >= 0.5:
            out.append(Transition("whip", a, b + 1))
        else:
            continue
        absorbed.add(c)
    out += [Transition("hard_cut", t, t) for t in cuts if t not in absorbed]
    out += detect_dissolves(fs, out, cfg)
    return sorted(out, key=lambda t: t.start_f)


def _edges(img: np.ndarray, keep_rows: int) -> np.ndarray:
    e = cv2.Canny(img[:keep_rows], 40, 120) > 0
    return e


def _retention(a: np.ndarray, b: np.ndarray, keep_rows: int) -> float:
    """Share of frame a's edge layout still present (within 2 px) in frame b. 1 = nothing replaced."""
    ea, eb = _edges(a, keep_rows), _edges(b, keep_rows)
    if ea.sum() < 20:
        return 1.0  # no layout before: content appearing on an empty frame replaces nothing
    near = cv2.dilate(eb.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    return float((ea & near).sum() / ea.sum())


def _blend_residual(fs: FrameSeries, a: int, b: int, keep: int) -> float:
    """Residual of fitting frames a..b-1 as non-negative mixes of frame a-1, frame b and the canvas
    (background colour), relative to the change between a-1 and b. Covers crossfades and fades
    through an empty canvas; ~0.0-0.15 for dissolves, ~0.5+ for an element moving."""
    from scipy.optimize import nnls

    A, B = fs.thumbs[a - 1][:keep].ravel(), fs.thumbs[b][:keep].ravel()
    canvas = np.full_like(A, float(np.median(np.concatenate([A, B]))))
    basis = np.stack([A, B, canvas], axis=1)
    res = []
    for t in range(a, b):
        f = fs.thumbs[t][:keep].ravel()
        w, _ = nnls(basis, f)
        res.append(float(np.abs(basis @ w - f).mean()))
    change = float(np.abs(A - B).mean())
    # Relative to how much changed: a lone element moving over a flat background leaves a small
    # absolute residual but one as large as the change itself.
    return float(np.mean(res)) / max(change, 1e-6) if res else 1.0


def detect_dissolves(fs: FrameSeries, known: list[Transition], cfg: VideoSignalsConfig) -> list[Transition]:
    """Slow dissolves that per-frame thresholds miss: soft UI explainers often fade the old layout out
    to the canvas and the new one in over 0.3-1.5 s, changing <2% of the frame per frame.

    A candidate is a peak of the long-baseline change (frames +-W apart, caption band excluded). It is a
    transition when (1) every frame in between is a mix of the old frame, the new frame and the canvas
    (a moving element is not), and (2) the old layout is mostly gone afterwards (a single element
    fading in keeps the rest of the layout)."""
    n = fs.n
    w = max(2, round(cfg.dissolve_baseline_s * fs.fps))
    keep_thumb = round(fs.thumbs.shape[1] * (1 - cfg.ignore_bottom_fraction))
    keep_mid = round(fs.mids.shape[1] * (1 - cfg.ignore_bottom_fraction))
    th = fs.thumbs[:, :keep_thumb]
    long = np.zeros(n)
    long[w : n - w] = np.abs(th[2 * w :] - th[: n - 2 * w]).mean(axis=(1, 2))
    floor = noise_floor(fs.diff, cfg)
    busy = [(t.start_f - w, t.end_f + w) for t in known]
    min_gap = round(cfg.min_shot_s * fs.fps)
    max_half = round(cfg.dissolve_max_s * fs.fps / 2)
    found: list[Transition] = []
    for idx in np.argsort(-long):
        c = int(idx)
        if long[c] < cfg.dissolve_min_change:
            break
        if any(lo <= c <= hi for lo, hi in busy) or any(abs(c - t.start_f) < min_gap for t in found):
            continue
        a = c
        while a - 1 > c - max_half and a - 1 >= 1 and fs.diff[a - 1] > floor:
            a -= 1
        b = c
        while b + 1 < c + max_half and b + 1 < n - 1 and fs.diff[b + 1] > floor:
            b += 1
        if b - a + 1 < cfg.transition_min_frames:
            continue
        if _retention(fs.mids[a - 1], fs.mids[b + 1], keep_mid) > cfg.dissolve_max_retention:
            continue
        kind = _dissolve_kind(fs, a, b + 1, cfg)
        # A push is proven by its shift; anything else must be a mix of old, new and canvas.
        if kind.kind != "push" and _blend_residual(fs, a, b + 1, keep_thumb) > cfg.dissolve_max_residual:
            continue
        found.append(kind)
        busy.append((a - w, b + 1 + w))
    return found


def _dissolve_kind(fs: FrameSeries, a: int, b: int, cfg: VideoSignalsConfig) -> Transition:
    """A slow transition's type from the motion inside it: the layout sliding most of a frame width
    is a push; a sustained scale change is a zoom-through; otherwise a (fade) crossfade."""
    total = float(fs.tx[a:b].sum())
    if abs(total) >= cfg.push_min_total:
        return Transition("push", a, b, "left" if total < 0 else "right")
    if int((np.abs(fs.scale[a:b] - 1.0) > cfg.zoom_min_scale_step).sum()) >= cfg.zoom_min_frames:
        return Transition("zoom_through", a, b)
    return Transition("crossfade", a, b)


# ---------------------------------------------------------------------------------------------
# Shots, events, camera, holds


@dataclass(frozen=True)
class Shot:
    id: str
    start_f: int
    end_f: int  # exclusive
    transition_in: Transition | None


@dataclass(frozen=True)
class Event:
    id: str
    shot: str
    kind: str  # motion | camera | continuous
    start_f: int
    end_f: int  # inclusive last changing frame
    energy: float
    bbox: tuple[float, float, float, float] | None
    camera_move: str


@dataclass(frozen=True)
class Hold:
    shot: str
    start_f: int
    end_f: int  # exclusive
    dead: bool  # the focal region of the next event is empty during the hold
    next_event: str | None


def build_shots(n: int, transitions: list[Transition]) -> list[Shot]:
    starts: list[tuple[int, Transition | None]] = [(0, None)] + [(t.start_f, t) for t in transitions]
    shots: list[Shot] = []
    for i, (start, tr) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else n
        if end > start:
            shots.append(Shot(f"s{len(shots) + 1:03d}", start, end, tr))
    return shots


def _camera_move(fs: FrameSeries, a: int, b: int, cfg: VideoSignalsConfig) -> str:
    total_scale = float(np.prod(fs.scale[a : b + 1]))
    tx, ty = float(fs.tx[a : b + 1].sum()), float(fs.ty[a : b + 1].sum())
    if total_scale >= 1 + cfg.camera_min_zoom:
        return "push_in"
    if total_scale <= 1 - cfg.camera_min_zoom:
        return "pull_out"
    if abs(tx) >= cfg.camera_min_pan and abs(tx) >= abs(ty):
        return "pan_left" if tx > 0 else "pan_right"  # content moves right => camera pans left
    if abs(ty) >= cfg.camera_min_pan:
        return "tilt_up" if ty > 0 else "tilt_down"
    return "none"


def noise_floor(d: np.ndarray, cfg: VideoSignalsConfig) -> float:
    med = float(np.median(d))
    mad = float(np.median(np.abs(d - med)))
    return max(cfg.event_abs_min_diff, med + cfg.event_noise_k * mad)


def detect_events(fs: FrameSeries, shots: list[Shot], cfg: VideoSignalsConfig) -> list[Event]:
    thr = noise_floor(fs.diff, cfg)
    events: list[Event] = []
    for shot in shots:
        lo = (
            shot.transition_in.end_f + 1
            if shot.transition_in and shot.transition_in.kind != "hard_cut"
            else shot.start_f + 1
        )
        hi = shot.end_f  # exclusive; the next shot's transition starts there
        if hi <= lo:
            continue
        active = fs.diff[lo:hi] > thr
        gap = round(cfg.motion_gap_merge_s * fs.fps)
        min_len = max(2, round(cfg.motion_min_s * fs.fps))
        for a, b in _runs(active, max_gap=gap, min_len=min_len):
            a, b = a + lo, b + lo
            box = fs.bboxes[a : b + 1]
            box = box[~np.isnan(box).any(axis=1)]
            # Slow changes (a fade at 60 fps) stay under the per-frame mask; the event's total
            # change (rest frame before vs last frame) still shows where it happened.
            total = _change_bbox(fs.thumbs[a - 1], fs.thumbs[b], cfg.mask_threshold / 255.0)
            if total is not None:
                box = np.vstack([box, np.asarray(total)[None]]) if box.size else np.asarray(total)[None]
            bbox = (
                (
                    float(box[:, 0].min()),
                    float(box[:, 1].min()),
                    float(box[:, 2].max()),
                    float(box[:, 3].max()),
                )
                if box.size
                else None
            )
            area = float(np.mean((box[:, 2] - box[:, 0]) * (box[:, 3] - box[:, 1]))) if box.size else 0.0
            cam = _camera_move(fs, a, b, cfg) if area >= cfg.camera_min_area else "none"
            duration_s = (b - a + 1) / fs.fps
            kind = (
                "camera"
                if cam != "none"
                else "continuous"
                if duration_s >= cfg.continuous_min_s
                else "motion"
            )
            events.append(
                Event(
                    f"e{len(events) + 1:03d}",
                    shot.id,
                    kind,
                    a - 1,
                    b,
                    float(fs.diff[a : b + 1].mean()),
                    bbox,
                    cam,
                )
            )
    return events


def _change_bbox(a: np.ndarray, b: np.ndarray, threshold: float) -> tuple[float, float, float, float] | None:
    mask = np.abs(a - b) > threshold
    if not mask.any():
        return None
    ys, xs = np.nonzero(mask)
    h, w = mask.shape
    return (xs.min() / w, ys.min() / h, (xs.max() + 1) / w, (ys.max() + 1) / h)


def _edge_density(thumb: np.ndarray, bbox: tuple[float, float, float, float]) -> float:
    img = (thumb * 255).astype(np.uint8)
    h, w = img.shape
    x0, y0, x1, y1 = (round(v) for v in (bbox[0] * w, bbox[1] * h, bbox[2] * w, bbox[3] * h))
    region = img[max(0, y0) : max(y0 + 1, y1), max(0, x0) : max(x0 + 1, x1)]
    if region.size == 0:
        return 0.0
    return float((cv2.Canny(region, 30, 90) > 0).mean())


def detect_holds(
    fs: FrameSeries, shots: list[Shot], events: list[Event], cfg: VideoSignalsConfig, min_hold_s: float
) -> list[Hold]:
    """Idle stretches (no event) of at least `min_hold_s` within a shot; dead if the next event's
    region is empty (low edge density) during the hold — a placeholder waiting for content."""
    holds: list[Hold] = []
    min_frames = round(min_hold_s * fs.fps)
    for shot in shots:
        lo = (
            shot.transition_in.end_f
            if shot.transition_in and shot.transition_in.kind != "hard_cut"
            else shot.start_f
        )
        in_shot = [e for e in events if e.shot == shot.id]
        cursor = lo
        for nxt in [*in_shot, None]:
            end = nxt.start_f if nxt else shot.end_f
            if end - cursor >= min_frames:
                dead = False
                if nxt is not None and nxt.bbox is not None:
                    dead = _edge_density(fs.thumbs[end - 1], nxt.bbox) <= cfg.empty_max_edge_density
                holds.append(Hold(shot.id, cursor, end, dead, nxt.id if nxt else None))
            if nxt is not None:
                cursor = nxt.end_f + 1
    return holds


def pace_curve(fs: FrameSeries, shots: list[Shot], events: list[Event]) -> list[dict[str, float | str]]:
    rows: list[dict[str, float | str]] = []
    for shot in shots:
        seconds = (shot.end_f - shot.start_f) / fs.fps
        n_events = sum(1 for e in events if e.shot == shot.id)
        inside = fs.diff[shot.start_f + 1 : shot.end_f]  # frame-to-frame change within the shot
        rows.append(
            {
                "shot": shot.id,
                "duration_s": round(seconds, 3),
                # a 1-frame shot (a flash between cuts) has no change within it
                "motion_energy": round(float(inside.mean()) if inside.size else 0.0, 6),
                "events_per_s": round(n_events / seconds, 3) if seconds else 0.0,
            }
        )
    return rows
