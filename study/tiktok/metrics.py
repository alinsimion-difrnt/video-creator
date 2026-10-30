"""Pure measures for the TikTok study (studies/README.md). Inputs are plain numbers from the decoders in
study/tiktok/measure.py (OCR boxes, face boxes, word times, the lens frame series); outputs are summaries.
Code measures, Claude names: nothing here guesses what a video means."""

from __future__ import annotations

import re
from dataclasses import dataclass
from itertools import pairwise
from statistics import median

import numpy as np

from study.tiktok.config import Measure


@dataclass(frozen=True)
class Box:
    """A box in 0..1 of the frame, seen at time t (s). `text` is empty for faces."""

    t: float
    x0: float
    y0: float
    x1: float
    y1: float
    text: str = ""

    @property
    def cy(self) -> float:
        return (self.y0 + self.y1) / 2

    @property
    def h(self) -> float:
        return self.y1 - self.y0

    @property
    def area(self) -> float:
        return max(0.0, self.x1 - self.x0) * max(0.0, self.y1 - self.y0)


def _r(v: float | None, n: int = 3) -> float | None:
    return None if v is None else round(float(v), n)


def _band(y: float, thirds: tuple[float, float]) -> str:
    return "top" if y < thirds[0] else "middle" if y < thirds[1] else "bottom"


def _outside(b: Box, core: tuple[float, float, float, float]) -> bool:
    x0, y0, x1, y1 = core
    return b.x0 < x0 or b.y0 < y0 or b.x1 > x1 or b.y1 > y1


def is_watermark(text: str) -> bool:
    """TikTok's own burned-in mark on downloaded copies: the logo text and the creator's @handle."""
    t = text.strip().lower()
    if re.search(r"tik\s*tok", t) or re.fullmatch(r"@[\w.]+", t):
        return True
    return bool(re.fullmatch(r"[tiko\s]+(lite)?", t))  # OCR misreads of the logo: "kok", "tikok", "ok"


def text_layout(boxes: list[Box], samples: list[float], cfg: Measure) -> dict[str, object]:
    """Where on-screen text sits and how much of the video carries it (TikTok's watermark left out)."""
    kept = [b for b in boxes if len(b.text.strip()) >= cfg.ocr_min_chars and not is_watermark(b.text)]
    n = max(1, len(samples))
    times = sorted({b.t for b in kept})
    bands = {"top": 0.0, "middle": 0.0, "bottom": 0.0}
    for b in kept:
        bands[_band(b.cy, cfg.thirds)] += b.area
    total = sum(bands.values())
    per_frame_words = [sum(len(b.text.split()) for b in kept if b.t == t) for t in times]
    per_frame_area = [sum(b.area for b in kept if b.t == t) for t in times]
    return {
        "text_share": _r(len(times) / n),
        "band_share": {k: _r(v / total) if total else None for k, v in bands.items()},
        "text_height_median": _r(median(b.h for b in kept)) if kept else None,
        "words_on_screen_median": _r(median(per_frame_words), 1) if per_frame_words else None,
        "text_area_median": _r(median(per_frame_area)) if per_frame_area else None,
        "outside_safe_share": _r(sum(_outside(b, cfg.safe_core) for b in kept) / len(kept)) if kept else None,
        "first_text_s": _r(times[0], 2) if times else None,
        **_captions(kept, n, cfg),
    }


def _captions(kept: list[Box], n: int, cfg: Measure) -> dict[str, object]:
    """Caption-sized text only (burned-in captions, titles), apart from small UI or code text."""
    big = [b for b in kept if b.h >= cfg.caption_min_height]
    bands = {"top": 0, "middle": 0, "bottom": 0}
    for b in big:
        bands[_band(b.cy, cfg.thirds)] += 1
    return {
        "caption_share": _r(len({b.t for b in big}) / n),
        "caption_band_share": {k: _r(v / len(big)) if big else None for k, v in bands.items()},
        "caption_height_median": _r(median(b.h for b in big)) if big else None,
    }


def face_summary(faces: list[Box], samples: list[float], cfg: Measure) -> dict[str, object]:
    """The talking head: how often a face is on screen, how big and where (the largest face per sample)."""
    big: dict[float, Box] = {}
    for f in faces:
        if f.h >= cfg.face_min_height and (f.t not in big or f.h > big[f.t].h):
            big[f.t] = f
    n = max(1, len(samples))
    fs = list(big.values())
    return {
        "face_share": _r(len(fs) / n),
        "face_height_median": _r(median(f.h for f in fs)) if fs else None,
        "face_cx_median": _r(median((f.x0 + f.x1) / 2 for f in fs)) if fs else None,
        "face_cy_median": _r(median(f.cy for f in fs)) if fs else None,
        "face_height_spread": _r(
            float(np.percentile([f.h for f in fs], 90) - np.percentile([f.h for f in fs], 10))
        )
        if len(fs) >= 2
        else None,
    }


def shot_stats(cut_times: list[float], duration: float) -> dict[str, object]:
    """Cuts per minute and shot lengths from hard-cut times (s)."""
    edges = [0.0, *sorted(t for t in cut_times if 0 < t < duration), duration]
    shots = [b - a for a, b in pairwise(edges) if b > a]
    return {
        "cuts": len(edges) - 2,
        "cuts_per_min": _r((len(edges) - 2) / duration * 60, 2) if duration > 0 else None,
        "shot_median_s": _r(median(shots), 2) if shots else None,
        "shot_longest_s": _r(max(shots), 2) if shots else None,
        "first_cut_s": _r(edges[1], 2) if len(edges) > 2 else None,
    }


def speech_stats(words: list[tuple[float, float]], duration: float) -> dict[str, object]:
    """Words per second while talking and overall, time to the first word, the share of silence."""
    if not words or duration <= 0:
        return {
            "words": 0,
            "words_per_s": 0.0,
            "words_per_s_talking": None,
            "first_word_s": None,
            "silence_share": 1.0,
        }
    spoken = sum(max(0.0, e - s) for s, e in words)
    span = words[-1][1] - words[0][0]
    return {
        "words": len(words),
        "words_per_s": _r(len(words) / duration, 2),
        "words_per_s_talking": _r(len(words) / span, 2) if span > 0 else None,
        "first_word_s": _r(words[0][0], 2),
        "silence_share": _r(max(0.0, 1 - spoken / duration)),
    }


def punch_ins(scale: np.ndarray, fps: float, cut_frames: list[int], cfg: Measure) -> list[float]:
    """Times (s) where the picture zooms: runs of per-frame scale steps (not at a cut) that add up to a
    punch-in."""
    step = np.abs(np.log(np.clip(scale, 1e-6, None)))
    on = step >= np.log1p(cfg.punch_min_step)
    for c in cut_frames:
        on[max(0, c - 1) : c + 2] = False
    out: list[float] = []
    i, n = 0, len(on)
    while i < n:
        if not on[i]:
            i += 1
            continue
        j, gap, total = i, 0, 0.0
        while j < n and gap <= cfg.punch_max_gap_frames:
            if on[j]:
                total += float(np.log(scale[j]))
                gap = 0
            else:
                gap += 1
            j += 1
        if abs(total) >= np.log1p(cfg.punch_min_total):
            out.append(round(i / fps, 2))
        i = j
    return out


def music_bed_db(mono: np.ndarray, sr: int, words: list[tuple[float, float]], cfg: Measure) -> float | None:
    """RMS level (dBFS) in the gaps between words: a music bed keeps the gaps loud. None without gaps."""
    gaps: list[np.ndarray] = []
    edges = [(0.0, words[0][0])] if words else [(0.0, len(mono) / sr)]
    edges += [(a[1], b[0]) for a, b in pairwise(words)]
    if words:
        edges.append((words[-1][1], len(mono) / sr))
    for a, b in edges:
        a, b = a + cfg.music_guard_s, b - cfg.music_guard_s
        if b - a >= cfg.music_min_gap_s:
            gaps.append(mono[int(a * sr) : int(b * sr)])
    if not gaps:
        return None
    x = np.concatenate(gaps).astype(np.float64)
    rms = float(np.sqrt(np.mean(x * x))) if x.size else 0.0
    return round(float(20 * np.log10(max(rms, 1e-9))), 1)


def loop_score(first: np.ndarray, last: np.ndarray) -> float:
    """1 = the last frame matches the first (a seamless loop); thumbnails in 0..1."""
    return round(1.0 - float(np.mean(np.abs(first.astype(np.float64) - last.astype(np.float64)))), 3)


def hook(
    words: list[tuple[float, float]],
    text_times: list[float],
    cut_times: list[float],
    event_times: list[float],
    window_s: float,
) -> dict[str, object]:
    """What happens in the first `window_s` seconds."""

    def first(ts: list[float]) -> float | None:
        return _r(min(ts), 2) if ts else None

    return {
        "first_word_s": first([s for s, _ in words]),
        "first_text_s": first(text_times),
        "words_in_window": sum(1 for s, _ in words if s < window_s),
        "cuts_in_window": sum(1 for t in cut_times if t < window_s),
        "events_in_window": sum(1 for t in event_times if t < window_s),
        "text_in_window": any(t < window_s for t in text_times),
    }


def density(event_times: list[float], punch_times: list[float], duration: float) -> dict[str, object]:
    """How busy the picture is: motion events (graphics, gestures, cuts in) and zooms per minute."""
    if duration <= 0:
        return {"events_per_min": None, "punches_per_min": None}
    return {
        "events_per_min": _r(len(event_times) / duration * 60, 2),
        "punches_per_min": _r(len(punch_times) / duration * 60, 2),
    }
