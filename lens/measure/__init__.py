"""S7 measurement core (BUILD_PLAN 7.5): track an element, extract its x/y/scale/opacity progress,
fit timing curves, and measure text stagger and SFX offset. Code measures; Claude only names.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from lens.measure.fit import FitResult, JointFit, fit_joint, fit_progress
from lens.measure.track import Box, Channel, Track, progress_channel, track
from lens.schemas.config import Measure


@dataclass(frozen=True)
class ChannelFit:
    channel: Channel
    fit: FitResult


@dataclass(frozen=True)
class ElementMeasure:
    track: Track
    channels: list[ChannelFit]
    timing: JointFit | None = None  # one GSAP ease + timing shared by all channels

    @property
    def primary(self) -> ChannelFit | None:
        """The channel that best describes the motion: a position or scale channel (measured in
        pixels) before opacity (a proxy), then the best fit quality."""
        if not self.channels:
            return None
        return max(self.channels, key=lambda c: (c.channel.name != "opacity", round(c.fit.fit_quality, 3)))


def _inside(tr: Track, size: tuple[int, int], frame_size: tuple[int, int]) -> np.ndarray:
    hw, hh = size[0] * tr.scale / 2, size[1] * tr.scale / 2
    w, h = frame_size
    return np.asarray((tr.cx - hw >= 0) & (tr.cy - hh >= 0) & (tr.cx + hw <= w) & (tr.cy + hh <= h))


def _channels(
    tr: Track, fps: float, cfg: Measure, size: tuple[int, int], frame_size: tuple[int, int]
) -> list[Channel]:
    tol = cfg.progress_end_tolerance
    good = tr.confidence >= cfg.track_min_confidence
    out: list[Channel] = []
    for name, values, floor in (
        ("x", tr.cx, cfg.min_position_change_px),
        ("y", tr.cy, cfg.min_position_change_px),
        ("scale", tr.scale, cfg.min_scale_change),
    ):
        if good.sum() < 3:
            continue
        # Before the element is placed confidently (e.g. still nearly transparent) its position is
        # unknown: those frames are left out and the fit estimates the unseen part of the travel.
        first = int(np.argmax(good))
        ch = progress_channel(
            name, tr.frames[first:], values[first:], fps, floor, tol, observed_start=first == 0
        )
        if ch is not None:
            out.append(ch)
    inside = _inside(tr, size, frame_size)
    if tr.alpha is not None and (good & inside).sum() >= 3:
        # Opacity is read where the element is fully in frame. Frames where it is too faint to place
        # count too (read where it was first placed) unless it travels further than its own size; then
        # that place may simply be empty and would read as transparent (a slide-in, not a fade).
        # Held frames are only informative for a fade: if the element was already opaque when first
        # placed (a slide-in), the place it was first seen may simply have been empty before.
        travel = float(np.hypot(np.ptp(tr.cx[good]), np.ptp(tr.cy[good])))
        first = int(np.argmax(good))
        still_fading = bool(tr.alpha[first] < 1 - cfg.min_opacity_change)
        held_ok = travel <= cfg.opacity_hold_max_travel * max(size) and (first == 0 or still_fading)
        idx = np.flatnonzero(inside & (good | held_ok))
        frames = [tr.frames[i] for i in idx]
        ch = progress_channel(
            "opacity",
            frames,
            tr.alpha[idx],
            fps,
            cfg.min_opacity_change,
            tol,
            observed_start=bool(idx[0] == 0),
        )
        if ch is not None:
            out.append(ch)
    return out


def measure_element(
    frames: Sequence[np.ndarray], first_frame: int, fps: float, box: Box, search: Box, cfg: Measure
) -> ElementMeasure:
    tr = track(
        frames,
        first_frame,
        box,
        search,
        cfg.track_scale_steps,
        cfg.min_alpha_contrast,
        cfg.track_min_confidence,
        cfg.track_coarse_px,
        cfg.track_coarse_min_template_px,
    )
    fits = [
        ChannelFit(
            ch,
            fit_progress(
                ch.t,
                ch.progress,
                margin=cfg.model_selection_margin,
                end_tolerance=cfg.progress_end_tolerance,
                gsap_class_ratio=cfg.gsap_class_ratio,
                free_amplitude=not ch.observed_start,
            ),
        )
        for ch in _channels(
            tr, fps, cfg, (box[2] - box[0], box[3] - box[1]), (frames[0].shape[1], frames[0].shape[0])
        )
    ]
    timing = None
    if fits:
        timing = fit_joint(
            [
                (
                    c.channel.frames_start / fps + c.channel.t,
                    c.channel.progress,
                    not c.channel.observed_start,
                    c.channel.name == "opacity",
                )
                for c in fits
            ]
        )
    return ElementMeasure(tr, fits, timing)


@dataclass(frozen=True)
class Stagger:
    reveal_frames: list[int | None]  # per unit (word), where its opacity passes the threshold
    unit: str  # word | all | none
    stagger_ms: float | None


def text_stagger(
    frames: Sequence[np.ndarray], first_frame: int, fps: float, word_boxes: Sequence[Box], cfg: Measure
) -> Stagger:
    """Per-word reveal frames from each word's opacity proxy; stagger = median gap between them."""
    background, end = frames[0].astype(np.float32), frames[-1].astype(np.float32)
    reveals: list[int | None] = []
    for x0, y0, x1, y1 in word_boxes:
        e, b = end[y0:y1, x0:x1], background[y0:y1, x0:x1]
        d = e - b
        if float(np.mean(np.abs(d))) < cfg.min_alpha_contrast / 4:  # thin glyphs: little mean contrast
            reveals.append(None)
            continue
        den = max(float(np.sum(d * d)), 1e-9)
        alpha = [float(np.sum((f[y0:y1, x0:x1].astype(np.float32) - b) * d) / den) for f in frames]
        hit = np.flatnonzero(np.asarray(alpha) >= cfg.stagger_reveal_alpha)
        reveals.append(first_frame + int(hit[0]) if hit.size else None)
    known = sorted(r for r in reveals if r is not None)
    if len(known) < 2:
        return Stagger(reveals, "none", None)
    gaps = np.diff(known)
    if float(np.median(gaps)) < 1:
        return Stagger(reveals, "all", 0.0)
    return Stagger(reveals, "word", round(float(np.median(gaps)) / fps * 1000, 1))


def sfx_offset_ms(sfx_onset_s: float, landing_frame: int, fps: float) -> float:
    """Negative: the sound leads the visual landing (BUILD_PLAN 7.5 step 7)."""
    return round((sfx_onset_s - landing_frame / fps) * 1000, 1)
