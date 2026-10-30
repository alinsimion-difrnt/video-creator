"""Burned-in captions (BUILD_PLAN 7.1): chunking, duration, change rate and word sync.

A native-fps change signal on the caption band finds when captions switch (2 fps is too coarse
for 0.6-1 s groups); OCR runs only once per stable stretch. A band change counts only when the
rest of the frame stays calm, so scene cuts are not mistaken for caption changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from itertools import pairwise
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from lens.media import iter_frames_rgb, scaled_size
from lens.schemas.config import CaptionsConfig


@dataclass(frozen=True)
class CaptionGroup:
    start_f: int
    end_f: int  # exclusive
    text: str
    words: int


@cache
def _ocr() -> Any:
    from rapidocr import RapidOCR

    return RapidOCR(params={"Global.log_level": "error"})


def _read(band_rgb: np.ndarray, min_score: float) -> str:
    out = _ocr()(band_rgb)
    texts = out.txts or ()
    scores = out.scores or ()
    return " ".join(t for t, s in zip(texts, scores, strict=False) if s >= min_score).strip()


def detect(proxy: Path, fps: float, width: int, height: int, cfg: CaptionsConfig) -> list[CaptionGroup]:
    w, h = scaled_size(width, height, cfg.analysis_width)
    top = int(h * (1 - cfg.band_fraction))
    # Pass 1: diffs only (memory stays flat for long videos).
    band_diff: list[float] = []
    rest_diff: list[float] = []
    prev: np.ndarray | None = None
    for _, rgb in iter_frames_rgb(proxy, fps, w, h):
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        if prev is None:
            band_diff.append(0.0)
            rest_diff.append(0.0)
        else:
            d = cv2.absdiff(gray, prev)
            band_diff.append(float(d[top:].mean()) / 255)
            rest_diff.append(float(d[:top].mean()) / 255)
        prev = gray
    bd, rd = np.asarray(band_diff), np.asarray(rest_diff)
    changes = [
        t
        for t in range(1, len(bd))
        if bd[t] >= cfg.band_change_min and bd[t] >= cfg.band_ratio * max(rd[t], 1e-4)
    ]
    # Collapse multi-frame switches (fade of a few frames) into their first frame.
    starts: list[int] = [0]
    for t in changes:
        if t - starts[-1] > cfg.min_group_frames:
            starts.append(t)
    bounds = [*starts, len(bd)]
    spans = [(a, b) for a, b in pairwise(bounds) if b - a >= cfg.min_group_frames]
    # Pass 2: decode again and OCR only the middle frame of each stable stretch.
    wanted = {(a + b) // 2: (a, b) for a, b in spans}
    texts: dict[int, str] = {}
    for i, rgb in iter_frames_rgb(proxy, fps, w, h):
        if i in wanted:
            texts[i] = _read(rgb[top:], cfg.ocr_min_score)
    groups: list[CaptionGroup] = []
    for mid, (a, b) in sorted(wanted.items()):
        text = texts.get(mid, "")
        if text:
            groups.append(CaptionGroup(a, b, text, len(text.split())))
    return groups


@dataclass(frozen=True)
class CaptionStats:
    groups: int
    words_per_group_mean: float
    words_per_group_median: float
    group_duration_mean_s: float
    changes_per_min: float
    coverage: float  # share of the video with a caption on screen
    word_synced_share: float | None  # caption switches landing on a spoken word start


def stats(
    groups: list[CaptionGroup], fps: float, n_frames: int, word_starts_s: list[float], cfg: CaptionsConfig
) -> CaptionStats | None:
    if len(groups) < cfg.min_groups:
        return None
    words = np.asarray([g.words for g in groups], dtype=float)
    durations = np.asarray([(g.end_f - g.start_f) / fps for g in groups])
    synced = None
    if word_starts_s:
        ws = np.asarray(word_starts_s)
        tol = cfg.sync_tolerance_frames / fps
        switches = [g.start_f / fps for g in groups[1:]]
        if switches:
            synced = round(float(np.mean([np.min(np.abs(ws - s)) <= tol for s in switches])), 3)
    return CaptionStats(
        groups=len(groups),
        words_per_group_mean=round(float(words.mean()), 2),
        words_per_group_median=float(np.median(words)),
        group_duration_mean_s=round(float(durations.mean()), 3),
        changes_per_min=round(len(groups) / (n_frames / fps) * 60, 2),
        coverage=round(float(durations.sum()) / (n_frames / fps), 3),
        word_synced_share=synced,
    )
