"""S11 compare, targets-only mode (M4.5): place a video against absolute house targets.

No corpus and no Claude: every number comes from `signals.summary.json`, every fix is a measured
gap with timestamps. Corpus percentiles (M9) and Claude's A4 fix list replace the templates later.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from lens import __version__
from lens.hashing import cache_key
from lens.schemas import LensConfig
from lens.schemas.common import Annotator, Provenance
from lens.schemas.compare import BaselineCheck, CompareReport, Fix, MetricResult
from lens.schemas.config import Baseline, MetricTarget
from lens.schemas.signals import SignalsSummary
from lens.schemas.video import VideoMeta

ADVICE = {
    "loudness": "Normalise the master to the destination target (e.g. ffmpeg loudnorm, two-pass).",
    "true_peak": "Add a true-peak limiter at -1 dBTP on the master.",
    "sfx_at_scene_start": "Move SFX off scene cuts onto the reveals they belong to (cue map + offsets).",
    "sfx_on_reveals": (
        "Tie each SFX to a visual event: whooshes peak 40-80 ms before a landing, "
        "clicks and pops on the reveal frame."
    ),
    "sfx_density": "Add more purposeful SFX on key reveals (lists, cards, counters).",
    "cuts_on_beat": "Snap scene changes to the beat grid (or pick a track whose tempo fits the edit).",
    "ducking": "Duck the music bed under the voice (sidechain or a level envelope), releasing in the gaps.",
    "dead_holds": "Bring content in sooner, or animate the empty placeholder: no frame waits on empty space.",
    "pace_variation": "Shape the pace: alternate dense, fast sections with calmer beats, not uniform motion.",
    "speaking_rate": "Bring the voiceover into range (re-time the script or the TTS speed).",
    "pause_variety": "Vary pauses: short breaths inside sentences, longer beats before key points.",
    "intonation": "Use a more expressive voice or direction (pitch movement on key words).",
    "rate_variation": "Vary speaking pace between phrases (slow down on key claims).",
    "caption_chunking": "Show captions in fuller phrases (about 4-7 words) instead of 2-3 word flashes.",
    "caption_sync": "Switch caption groups on spoken word starts (use the TTS word timestamps).",
}


def _get(summary: dict[str, Any], path: str) -> Any:
    cur: Any = summary
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _available(s: SignalsSummary) -> set[str]:
    have: set[str] = set()
    if s.captions is not None:
        have.add("captions")
    if s.speech is not None:
        have.add("voice")
    if s.audio is not None:
        if s.audio.cuts_on_beat_share is not None:
            have.add("beat")
        if s.audio.sfx:
            have.add("sfx")
        if s.audio.stems:
            have.add("stems")
    return have


def _gap(value: float, lo: float | None, hi: float | None) -> float:
    if lo is not None and value < lo:
        return lo - value
    if hi is not None and value > hi:
        return value - hi
    return 0.0


def _evaluate(t: MetricTarget, s: SignalsSummary, data: dict[str, Any], have: set[str]) -> MetricResult:
    missing = [r for r in t.requires if r not in have]
    value = _get(data, t.path)
    if missing or value is None:
        reason = f"needs {', '.join(missing)}" if missing else "not measured"
        return MetricResult(
            id=t.id,
            value=None,
            unit=t.unit,
            min=t.min,
            max=t.max,
            status="n/a",
            gap=None,
            source=t.source,
            note=reason,
        )
    gap = _gap(float(value), t.min, t.max)
    return MetricResult(
        id=t.id,
        value=round(float(value), 3),
        unit=t.unit,
        min=t.min,
        max=t.max,
        status="pass" if gap == 0 else "fail",
        gap=round(gap, 3),
        source=t.source,
        note=None,
    )


def stamp(seconds: float) -> str:
    return f"{int(seconds // 60)}:{seconds % 60:05.2f}"


def _evidence(metric: str, s: SignalsSummary) -> list[str]:
    """Timestamps that show the problem, so a fix can be found in the timeline."""
    if metric == "dead_holds":
        return [
            f"{stamp(h.start_s)}-{stamp(h.end_s)} ({h.end_s - h.start_s:.1f}s, shot {h.shot})"
            for h in s.video.holds
            if h.dead
        ]
    if metric == "sfx_at_scene_start" and s.audio:
        return [
            f"{stamp(x.sync_s)} {x.label} on a scene start ({x.scene_start_offset_ms:+.0f} ms)"
            for x in s.audio.sfx
            if x.at_scene_start
        ]
    if metric == "sfx_on_reveals" and s.audio:
        return [
            f"{stamp(x.sync_s)} {x.label} not tied to any reveal"
            for x in s.audio.sfx
            if x.reveal_offset_ms is None
        ]
    if metric == "pace_variation":
        shots = sorted(s.video.shots, key=lambda sh: sh.motion_energy)
        if not shots:
            return []
        calm, busy = shots[0], shots[-1]
        return [
            f"calmest shot {calm.id} at {stamp(calm.start_s)}, busiest {busy.id} at {stamp(busy.start_s)}"
        ]
    return []


def target_text(lo: float | None, hi: float | None, unit: str) -> str:
    if lo is not None and hi is not None:
        return f"{lo:g} to {hi:g} {unit}"
    return f"at least {lo:g} {unit}" if lo is not None else f"at most {hi:g} {unit}"


def _scale(t: MetricTarget) -> float:
    """Normalise gaps: a gap of one 'scale' is a full-weight problem."""
    if t.min is not None and t.max is not None:
        return max(abs(t.max - t.min), 1e-6)
    ref = t.min if t.min is not None else t.max
    return max(abs(ref or 0.0) * 0.5, 1.0 if t.unit in ("s", "dB", "dBTP", "per min", "wpm") else 0.2)


def baseline_check(meta: VideoMeta, s: SignalsSummary, base: Baseline) -> list[BaselineCheck]:
    """Does the tool reproduce the known values of a reference render? (BUILD_PLAN 9)"""
    checks: list[BaselineCheck] = []

    def add(name: str, got: float | None, want: float, tol: float) -> None:
        ok = got is not None and abs(got - want) <= tol
        checks.append(BaselineCheck(name=name, measured=got, expected=want, tolerance=tol, ok=ok))

    add("duration_s", meta.proxy.duration_s, base.duration_s.value, base.duration_s.tolerance)
    add("fps", meta.proxy.fps, base.fps, 0.01)
    add("frames", float(meta.proxy.frames), float(base.frames), 1.0)
    if s.audio:
        add(
            "integrated_lufs",
            s.audio.loudness.integrated_lufs,
            base.integrated_lufs.value,
            base.integrated_lufs.tolerance,
        )
        add(
            "sample_peak_dbfs",
            s.audio.loudness.sample_peak_dbfs,
            base.sample_peak_dbfs.value,
            base.sample_peak_dbfs.tolerance,
        )
        add(
            "sfx_at_scene_start_share",
            s.audio.sfx_at_scene_start_share,
            1.0,
            1.0 - base.sfx_at_scene_start_min_share,
        )
    n_trans = sum(v for k, v in s.video.transitions_by_kind.items())
    checks.append(
        BaselineCheck(
            name="transitions",
            measured=float(n_trans),
            expected=float(base.transitions),
            tolerance=float(base.transitions - base.transitions_min_detected),
            ok=base.transitions_min_detected <= n_trans <= base.transitions + 1,
        )
    )
    if s.speech:
        add("wpm", s.speech.wpm, base.wpm.value, base.wpm.tolerance)
    return checks


def compare_targets(
    meta: VideoMeta, summary: SignalsSummary, cfg: LensConfig, destination: str | None = None
) -> CompareReport:
    dest = destination or cfg.targets.default_destination
    if dest not in cfg.targets.loudness:
        raise ValueError(f"unknown destination {dest!r}; known: {', '.join(cfg.targets.loudness)}")
    data = summary.model_dump()
    have = _available(summary)
    metrics: list[MetricResult] = []
    if summary.audio is not None:
        lt = cfg.targets.loudness[dest]
        value = summary.audio.loudness.integrated_lufs
        gap = _gap(value, lt.min_lufs, lt.max_lufs)
        metrics.append(
            MetricResult(
                id="loudness",
                value=value,
                unit="LUFS",
                min=lt.min_lufs,
                max=lt.max_lufs,
                status="pass" if gap == 0 else "fail",
                gap=round(gap, 2),
                source=f"{dest} ({lt.source} target)",
                note=None,
            )
        )
    by_id = {t.id: t for t in cfg.targets.metrics}
    metrics += [_evaluate(t, summary, data, have) for t in cfg.targets.metrics]

    fixes: list[Fix] = []
    for m in metrics:
        if m.status != "fail" or m.gap is None:
            continue
        t = by_id.get(m.id)
        weight = t.weight if t else 3.0
        effort = t.effort if t else "S"
        scale = _scale(t) if t else 2.0
        severity = round(weight * min(3.0, m.gap / scale + 0.5), 2)
        target = target_text(m.min, m.max, m.unit)
        fixes.append(
            Fix(
                metric=m.id,
                problem=f"{m.id.replace('_', ' ').capitalize()} is {m.value:g} {m.unit}; target {target}",
                evidence=_evidence(m.id, summary),
                target=target,
                change=ADVICE.get(m.id, "See the metric definition."),
                effort=effort,
                severity=severity,
            )
        )
    fixes.sort(key=lambda f: (-f.severity, f.effort))
    base = next((b for b in cfg.baselines if b.video == summary.video_id), None)
    key = cache_key(
        {"summary": summary.provenance.input_hash, "targets": cfg.targets.model_dump(), "dest": dest}
    )
    return CompareReport(
        provenance=Provenance(
            tool_version=__version__,
            stage="s11_compare",
            annotator=Annotator.CODE,
            input_hash=key,
            created_at=datetime.now(UTC),
        ),
        video_id=summary.video_id,
        mode="targets-only",
        destination=dest,
        metrics=metrics,
        fixes=fixes[:10],
        baseline=baseline_check(meta, summary, base) if base else None,
        not_yet_measured=[
            "easing/spring fits and stagger (S7, M4)",
            "SFX label accuracy (gold set, G2)",
            "corpus percentiles (M9)",
        ],
    )
