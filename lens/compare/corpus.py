"""S11 corpus mode (BUILD_PLAN 9): where a video sits among premium explainers of its format.

Every metric is measured the same way on the target and on each cohort video (records + signals; code
only). The cohort is the weighted corpus with the target's format; voice metrics only use videos with a
voice-over. Placement = weighted percentile; status = inside the cohort's 25-75% band, or below/above it,
with the gap in band widths. Which metrics exist, their section, weight and effort live in config
`compare.corpus_metrics`.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from lens import __version__
from lens.compare import baseline_check
from lens.hashing import cache_key, sha256_file
from lens.schemas import LensConfig
from lens.schemas.common import Annotator, Provenance
from lens.schemas.compare import CompareReport, MetricResult
from lens.schemas.record import RecordFile
from lens.schemas.signals import SignalsSummary
from lens.schemas.video import VideoMeta
from lens.synth.stats import weighted_quantile

UI_SHOTS = ("ui_closeup", "ui_full", "ui_recreated", "screen_recording")
Extract = Callable[[RecordFile, SignalsSummary], float | None]


def _measured(rec: RecordFile) -> list:  # type: ignore[type-arg]
    return [
        el.timing for e in rec.events for el in e.elements if el.timing and el.timing.source == "measured"
    ]


def _share(rec: RecordFile, pred: Callable[[object], bool]) -> float | None:
    t = _measured(rec)
    return round(sum(1 for x in t if pred(x)) / len(t), 4) if t else None


def _minutes(s: SignalsSummary) -> float:
    return max(s.video.duration_s / 60, 1e-9)


def _first_ui(rec: RecordFile, s: SignalsSummary) -> float | None:
    ui = [x.start_s for x in rec.shots if x.annotation and x.annotation.shot_type in UI_SHOTS]
    return min(ui) if ui else None


def _median_duration(rec: RecordFile, s: SignalsSummary) -> float | None:
    d = [t.duration_ms for t in _measured(rec) if t.duration_ms]
    return float(np.median(d)) if d else None


EXTRACT: dict[str, Extract] = {
    # voice
    "wpm": lambda r, s: s.speech.wpm if s.speech else None,
    "pitch_variability": lambda r, s: s.speech.pitch_std_semitones if s.speech else None,
    "pause_variety": lambda r, s: s.speech.pause_cv if s.speech else None,
    "voice_energy_variation": lambda r, s: s.speech.energy_std_db if s.speech else None,
    # sound
    "loudness_lufs": lambda r, s: s.audio.loudness.integrated_lufs if s.audio else None,
    "true_peak": lambda r, s: s.audio.loudness.true_peak_dbtp if s.audio else None,
    "loudness_range": lambda r, s: s.audio.loudness.lra_lu if s.audio else None,
    "sfx_per_min": lambda r, s: s.audio.sfx_per_min if s.audio else None,
    "sfx_at_scene_start": lambda r, s: s.audio.sfx_at_scene_start_share if s.audio else None,
    "sfx_near_reveal": lambda r, s: s.audio.sfx_near_reveal_share if s.audio else None,
    "cuts_on_beat": lambda r, s: s.audio.cuts_on_beat_share if s.audio else None,
    "ducking_db": lambda r, s: s.audio.ducking_db if s.audio else None,
    # motion
    "linear_motion_share": lambda r, s: _share(r, lambda t: t.easing_class == "linear"),  # type: ignore[attr-defined]
    "overshoot_share": lambda r, s: _share(r, lambda t: (t.overshoot_pct or 0) > 0),  # type: ignore[attr-defined]
    "element_duration_ms": _median_duration,
    "transitions_per_min": lambda r, s: sum(s.video.transitions_by_kind.values()) / _minutes(s),
    "time_to_first_ui": _first_ui,
    "shot_length": lambda r, s: s.video.mean_shot_s,
    # rhythm
    "dead_hold_s_per_min": lambda r, s: s.video.dead_hold_s / _minutes(s),
    "pace_variation": lambda r, s: s.video.pace_cv,
    "caption_words_per_group": lambda r, s: s.captions.words_per_group_mean if s.captions else None,
    "caption_changes_per_min": lambda r, s: s.captions.changes_per_min if s.captions else None,
}


def _load(root: Path, video: str) -> tuple[RecordFile, SignalsSummary]:
    vdir = root / "videos" / video
    return (
        RecordFile.model_validate_json((vdir / "record.json").read_text("utf-8")),
        SignalsSummary.model_validate_json((vdir / "signals.summary.json").read_text("utf-8")),
    )


def cohort(
    root: Path, cfg: LensConfig, fmt: str, exclude: str
) -> list[tuple[RecordFile, SignalsSummary, float]]:
    from lens.synth import load_corpus

    out = []
    for v in load_corpus(root, cfg):
        if v.record.format == fmt and v.record.video != exclude:
            out.append((v.record, v.signals, v.weight))
    return out


def place(value: float, values: list[float], weights: list[float]) -> tuple[float, float, float, float]:
    """(percentile 0-100, p25, median, p75) of `value` among weighted cohort values."""
    v, w = np.asarray(values, float), np.asarray(weights, float)
    below = float(w[v < value].sum() + 0.5 * w[v == value].sum())
    pct = 100 * below / float(w.sum())
    return (
        round(pct, 1),
        round(weighted_quantile(v, w, 0.25), 4),
        round(weighted_quantile(v, w, 0.5), 4),
        round(weighted_quantile(v, w, 0.75), 4),
    )


def compare_corpus(root: Path, video: str, cfg: LensConfig, destination: str | None = None) -> CompareReport:
    from lens.compare import compare_targets

    rec, sig = _load(root, video)
    meta = VideoMeta.model_validate_json((root / "videos" / video / "meta.json").read_text("utf-8"))
    group = cohort(root, cfg, rec.format, video)
    if len(group) < cfg.compare.min_cohort:
        raise ValueError(
            f"only {len(group)} {rec.format} videos in the corpus (need {cfg.compare.min_cohort})"
        )
    base = compare_targets(meta, sig, cfg, destination)
    metrics: list[MetricResult] = [m for m in base.metrics if m.id == "loudness"]
    for spec in cfg.compare.corpus_metrics:
        fn = EXTRACT[spec.id]
        value = fn(rec, sig)
        raw = [(fn(r, s), w) for r, s, w in group]
        pairs: list[tuple[float, float]] = [(x, w) for x, w in raw if x is not None and np.isfinite(x)]
        if value is None or len(pairs) < cfg.compare.min_cohort:
            metrics.append(
                MetricResult(
                    id=spec.id,
                    section=spec.section,
                    value=value,
                    unit=spec.unit,
                    min=None,
                    max=None,
                    status="n/a",
                    gap=None,
                    source=f"{rec.format} corpus (n={len(pairs)})",
                    note="not measured for this video or too few cohort videos",
                )
            )
            continue
        pct, lo, med, hi = place(value, [x for x, _ in pairs], [w for _, w in pairs])
        width = hi - lo
        outside = lo - value if value < lo else value - hi if value > hi else 0.0
        # In band widths, capped: a zero-width band (e.g. no dead holds at all) has no natural scale.
        gap = (
            0.0
            if outside <= 0
            else min(cfg.compare.max_gap, outside / width if width > 0 else cfg.compare.max_gap)
        )
        metrics.append(
            MetricResult(
                id=spec.id,
                section=spec.section,
                value=round(value, 4),
                unit=spec.unit,
                min=lo,
                max=hi,
                status="pass" if gap == 0 else "fail",
                gap=round(gap, 2),
                source=f"{rec.format} corpus (n={len(pairs)})",
                note=None if gap == 0 else ("below" if value < lo else "above") + " the premium range",
                percentile=pct,
                cohort_median=med,
                cohort_n=len(pairs),
            )
        )
    inputs = [root / "videos" / video / "record.json", root / "videos" / video / "signals.summary.json"]
    inputs += [root / "videos" / r.video / "record.json" for r, _, _ in group]
    key = cache_key(
        {"inputs": [sha256_file(p) for p in inputs], "compare": cfg.compare.model_dump(mode="json")}
    )
    return CompareReport(
        provenance=Provenance(
            tool_version=__version__,
            stage="s11_compare",
            annotator=Annotator.CODE,
            input_hash=key,
            created_at=datetime.now(UTC),
        ),
        video_id=video,
        mode="corpus",
        destination=base.destination,
        metrics=metrics,
        fixes=[],
        baseline=base.baseline,
        not_yet_measured=[],
        cohort=sorted(r.video for r, _, _ in group),
    )


__all__ = ["EXTRACT", "baseline_check", "cohort", "compare_corpus", "place"]
