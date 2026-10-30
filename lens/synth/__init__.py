"""S9 synth (BUILD_PLAN 8.1-8.2): weighted corpus statistics from the records, and clusters of the
`other` patterns as taxonomy proposals.

Reads videos/<id>/record.json and signals.summary.json only (no media). Writes corpus/stats/
{motion,sound,pacing,patterns}.json and taxonomy/proposals.yaml. Weights come from config `synth.weights`:
tier x overall score / 5, times the fit quality for measured motion.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from lens import __version__
from lens.hashing import cache_key, sha256_file
from lens.schemas import LensConfig
from lens.schemas.common import Annotator, Provenance
from lens.schemas.corpus import (
    MotionStats,
    PacingStats,
    PatternExample,
    PatternsFile,
    PatternStats,
    SoundStats,
    SpringCluster,
    Stat,
    Weighting,
)
from lens.schemas.record import RecordElement, RecordFile
from lens.schemas.signals import SignalsSummary
from lens.synth.cluster import Embed, propose
from lens.synth.stats import kmeans, shares, stat, weighted_quantile

STAGE = "s9_synth"
OUTPUTS = ("motion", "sound", "pacing", "patterns")
UI_SHOTS = ("ui_closeup", "ui_full", "ui_recreated", "screen_recording")


@dataclass(frozen=True)
class Video:
    record: RecordFile
    signals: SignalsSummary
    weight: float


def load_corpus(root: Path, cfg: LensConfig) -> list[Video]:
    """Every video with a record and signals, weighted; weight-0 videos (our own) are left out."""
    w = cfg.synth.weights
    out = []
    for p in sorted((root / "videos").glob("*/record.json")):
        rec = RecordFile.model_validate_json(p.read_text("utf-8"))
        sig_path = p.parent / "signals.summary.json"
        if not sig_path.exists():
            continue
        tier = w.tier.get(rec.tier, 0.0)
        score = None
        if rec.summary is not None:
            score = getattr(rec.summary.scores, w.score_from).score
        weight = tier * (score / 5 if score else w.score_missing)
        if weight > 0:
            sig = SignalsSummary.model_validate_json(sig_path.read_text("utf-8"))
            out.append(Video(rec, sig, weight))
    return out


def _weighting(cfg: LensConfig) -> Weighting:
    w = cfg.synth.weights
    return Weighting(tier=w.tier, score_from=w.score_from, score_missing=w.score_missing, quality=w.quality)


class _Acc:
    """Collects (value, weight, video) observations under keys."""

    def __init__(self) -> None:
        self.v: dict[str, list[tuple[float, float, str]]] = defaultdict(list)

    def add(self, key: str, value: float | None, weight: float, video: str) -> None:
        if value is not None and np.isfinite(value) and weight > 0:
            self.v[key].append((float(value), weight, video))

    def stat(self, key: str, mk: Callable[..., Stat]) -> Stat:
        rows = self.v.get(key, [])
        return mk([r[0] for r in rows], [r[1] for r in rows], [r[2] for r in rows])

    def stats(self, mk: Callable[..., Stat]) -> dict[str, Stat]:
        return {k: self.stat(k, mk) for k in sorted(self.v)}


def _measured(el: RecordElement) -> bool:
    return el.timing is not None and el.timing.source == "measured"


def _ew(v: Video, el: RecordElement, cfg: LensConfig) -> float:
    q = el.timing.quality if (cfg.synth.weights.quality and el.timing and el.timing.quality) else 1.0
    return v.weight * q


def _median_bezier(points: list[tuple[list[float], float]]) -> str:
    """Weighted median of each control point coordinate, as a CSS cubic-bezier."""
    w = np.array([p[1] for p in points])
    c = np.array([p[0] for p in points])
    med = [weighted_quantile(c[:, i], w, 0.5) for i in range(4)]
    return "cubic-bezier({:.3f}, {:.3f}, {:.3f}, {:.3f})".format(*med)


def motion_stats(
    corpus: list[Video], cfg: LensConfig, prov: Provenance, mk: Callable[..., Stat]
) -> MotionStats:
    by_role, by_change, stagger, over = _Acc(), _Acc(), _Acc(), _Acc()
    easing: list[tuple[str, float]] = []
    eases: list[tuple[str, float]] = []
    easing_role: dict[str, list[tuple[str, float]]] = defaultdict(list)
    ease_cls: dict[str, list[tuple[str, float]]] = defaultdict(list)
    bez: dict[str, list[tuple[list[float], float]]] = defaultdict(list)
    springs: list[tuple[float, float, float, float, float, str]] = []  # zeta, settle, k, c, w, video
    n_el = 0
    over_flags: list[tuple[str, float]] = []
    for v in corpus:
        vid = v.record.video
        for e in v.record.events:
            for el in e.elements:
                if not _measured(el) or el.timing is None:
                    continue
                n_el += 1
                t, w = el.timing, _ew(v, el, cfg)
                by_role.add(el.role, t.duration_ms, w, vid)
                for c in sorted(set(el.change_types) | set(t.changes)):
                    by_change.add(c, t.duration_ms, w, vid)
                if t.easing_class:
                    easing.append((t.easing_class, w))
                    easing_role[el.role].append((t.easing_class, w))
                if t.ease:
                    eases.append((t.ease, w))
                    if t.easing_class:
                        ease_cls[t.easing_class].append((t.ease, w))
                if t.bezier and t.easing_class:
                    m_ = re.fullmatch(r"cubic-bezier\(([^)]*)\)", t.bezier)
                    if m_:
                        bez[t.easing_class].append(([float(x) for x in m_.group(1).split(",")], w))
                if t.overshoot_pct is not None:
                    over_flags.append(("overshoot" if t.overshoot_pct > 0 else "none", w))
                    if t.overshoot_pct > 0:
                        over.add("pct", t.overshoot_pct, w, vid)
                if t.stagger_unit and t.stagger_ms is not None:
                    stagger.add(t.stagger_unit, t.stagger_ms, w, vid)
                sp = t.spring
                if sp and sp.get("stiffness") and t.duration_ms:
                    m = sp.get("mass", 1.0)
                    zeta = sp["damping"] / (2 * np.sqrt(sp["stiffness"] * m))
                    springs.append((zeta, t.duration_ms, sp["stiffness"], sp["damping"], w, vid))
    clusters: list[SpringCluster] = []
    if springs:
        pts = np.log(np.array([[s[0], s[1]] for s in springs]))
        labels = kmeans(pts, cfg.synth.spring_clusters)
        for j in sorted(set(labels.tolist())):
            mem = [s for s, lab in zip(springs, labels, strict=True) if lab == j]
            ws, vids = [s[4] for s in mem], [s[5] for s in mem]
            k_med = mk([s[2] for s in mem], ws, vids).median or 0.0
            c_med = mk([s[3] for s in mem], ws, vids).median or 0.0
            clusters.append(
                SpringCluster(
                    n=len(mem),
                    zeta=mk([s[0] for s in mem], ws, vids),
                    settle_ms=mk([s[1] for s in mem], ws, vids),
                    remotion={"mass": 1.0, "stiffness": round(k_med, 2), "damping": round(c_med, 2)},
                )
            )
    flags = shares(over_flags)
    return MotionStats(
        provenance=prov,
        weighting=_weighting(cfg),
        videos=len({v.record.video for v in corpus}),
        elements=n_el,
        duration_ms_by_role=by_role.stats(mk),
        duration_ms_by_change=by_change.stats(mk),
        easing_mix=shares(easing),
        easing_by_role={r: shares(p) for r, p in sorted(easing_role.items())},
        ease_mix=shares(eases),
        ease_by_class={c: next(iter(shares(p))) for c, p in sorted(ease_cls.items()) if shares(p)},
        bezier_by_class={c: _median_bezier(p) for c, p in sorted(bez.items())},
        overshoot_share=flags.get("overshoot", 0.0) if flags else None,
        overshoot_pct=over.stat("pct", mk),
        springs=clusters,
        stagger_ms_by_unit=stagger.stats(mk),
    )


def sound_stats(
    corpus: list[Video], cfg: LensConfig, prov: Provenance, mk: Callable[..., Stat]
) -> SoundStats:
    acc, off = _Acc(), _Acc()
    labels: list[tuple[str, float]] = []
    beat: list[tuple[str, float]] = []
    for v in corpus:
        vid, a = v.record.video, v.signals.audio
        acc.add("sfx_per_min", a.sfx_per_min if a else None, v.weight, vid)
        if a is not None:
            acc.add("lufs", a.loudness.integrated_lufs, v.weight, vid)
            acc.add("peak", a.loudness.true_peak_dbtp, v.weight, vid)
            acc.add("lra", a.loudness.lra_lu, v.weight, vid)
            acc.add("ducking", a.ducking_db, v.weight, vid)
        for x in v.record.sfx:
            labels.append((x.label, v.weight))
            beat.append(("on" if x.on_beat else "off", v.weight))
            off.add(x.label, x.reveal_offset_ms, v.weight, vid)
    b = shares(beat)
    return SoundStats(
        provenance=prov,
        weighting=_weighting(cfg),
        videos=len(corpus),
        sfx_per_min=acc.stat("sfx_per_min", mk),
        sfx_label_mix=shares(labels),
        reveal_offset_ms_by_label=off.stats(mk),
        sfx_on_beat_share=b.get("on", 0.0) if b else None,
        integrated_lufs=acc.stat("lufs", mk),
        true_peak_dbtp=acc.stat("peak", mk),
        lra_lu=acc.stat("lra", mk),
        ducking_db=acc.stat("ducking", mk),
    )


def pacing_stats(
    corpus: list[Video], cfg: LensConfig, prov: Provenance, mk: Callable[..., Stat]
) -> PacingStats:
    acc, shot_fmt, dur_fmt = _Acc(), _Acc(), _Acc()
    pause_mix: list[tuple[str, float]] = []
    for v in corpus:
        rec, sig, vid = v.record, v.signals, v.record.video
        for s in rec.shots:
            shot_fmt.add(rec.format, s.end_s - s.start_s, v.weight, vid)
            acc.add("shot_s", s.end_s - s.start_s, v.weight, vid)
        dur_fmt.add(rec.format, rec.duration_s, v.weight, vid)
        acc.add("pace_cv", sig.video.pace_cv, v.weight, vid)
        if sig.audio is not None:
            acc.add("cuts_on_beat", sig.audio.cuts_on_beat_share, v.weight, vid)
        ui = [s.start_s for s in rec.shots if s.annotation and s.annotation.shot_type in UI_SHOTS]
        acc.add("first_ui", min(ui) if ui else None, v.weight, vid)
        if sig.speech is not None:
            acc.add("wpm", sig.speech.wpm, v.weight, vid)
            acc.add("pitch", sig.speech.pitch_std_semitones, v.weight, vid)
            acc.add("pause", sig.speech.pause_mean_ms, v.weight, vid)
            acc.add("artic", sig.speech.articulation_wpm, v.weight, vid)
            acc.add("pause90", sig.speech.pause_p90_ms, v.weight, vid)
            acc.add("energy", sig.speech.energy_std_db, v.weight, vid)
            acc.add("phrase_cv", sig.speech.phrase_rate_cv, v.weight, vid)
            for k, n in sig.speech.pauses_by_length.items():
                pause_mix.append((k, n * v.weight))
        if sig.captions is not None and sig.captions.groups:
            acc.add("caption_words", sig.captions.words_per_group_mean, v.weight, vid)
    return PacingStats(
        provenance=prov,
        weighting=_weighting(cfg),
        videos=len(corpus),
        shot_s_by_format=shot_fmt.stats(mk),
        shot_s=acc.stat("shot_s", mk),
        pace_cv=acc.stat("pace_cv", mk),
        cuts_on_beat_share=acc.stat("cuts_on_beat", mk),
        time_to_first_ui_s=acc.stat("first_ui", mk),
        wpm=acc.stat("wpm", mk),
        pitch_std_semitones=acc.stat("pitch", mk),
        pause_mean_ms=acc.stat("pause", mk),
        articulation_wpm=acc.stat("artic", mk),
        pause_p90_ms=acc.stat("pause90", mk),
        energy_std_db=acc.stat("energy", mk),
        phrase_rate_cv=acc.stat("phrase_cv", mk),
        pause_length_mix=shares(pause_mix),
        caption_words_per_group=acc.stat("caption_words", mk),
        duration_s_by_format=dur_fmt.stats(mk),
    )


def pattern_stats(
    corpus: list[Video],
    cfg: LensConfig,
    prov: Provenance,
    mk: Callable[..., Stat],
    assigned: dict[str, str] | None = None,
) -> PatternsFile:
    """Per-pattern stats. `assigned` maps `other` events to the pattern G4 gave them."""
    assigned = assigned or {}
    groups: dict[str, list[tuple[Video, Any]]] = defaultdict(list)
    other = 0
    for v in corpus:
        for e in v.record.events:
            if e.status != "annotated" or e.pattern is None:
                continue
            pid = assigned.get(f"{v.record.video}/{e.id}", e.pattern.id)
            if pid == "other":
                other += 1
            else:
                groups[pid].append((v, e))
    out = []
    for pid, members in sorted(groups.items()):
        dur, off = _Acc(), _Acc()
        easing: list[tuple[str, float]] = []
        change: list[tuple[str, float]] = []
        role: list[tuple[str, float]] = []
        sfx: list[tuple[str, float]] = []
        ranked = []
        for v, e in members:
            vid = v.record.video
            labels = {x.id: x.label for x in v.record.sfx}
            for xid in e.sfx:
                sfx.append((labels.get(xid, "unsure"), v.weight))
            q = []
            for el in e.elements:
                role.append((el.role, v.weight))
                for c in el.change_types:
                    change.append((c, v.weight))
                for o in el.sfx_offset_ms.values():
                    off.add("o", o, v.weight, vid)
                if _measured(el) and el.timing is not None:
                    w = _ew(v, el, cfg)
                    dur.add("d", el.timing.duration_ms, w, vid)
                    if el.timing.easing_class:
                        easing.append((el.timing.easing_class, w))
                    q.append(el.timing.quality or 0.0)
            ranked.append((v.weight * (1 + (max(q) if q else 0.0)), vid, e.id, v))
        ranked.sort(key=lambda r: (-r[0], r[1], r[2]))
        examples = []
        seen: set[str] = set()
        for _, vid, eid, v in ranked:  # prefer different videos
            if vid in seen:
                continue
            seen.add(vid)
            score = v.record.summary.scores.overall.score if v.record.summary else None
            examples.append(PatternExample(video=vid, event=eid, score=score))
            if len(examples) >= cfg.synth.max_examples:
                break
        out.append(
            PatternStats(
                id=pid,
                events=len(members),
                videos=len({v.record.video for v, _ in members}),
                weight=round(sum(v.weight for v, _ in members), 4),
                duration_ms=dur.stat("d", mk),
                easing_mix=shares(easing),
                change_mix=shares(change),
                role_mix=shares(role),
                sfx_label_mix=shares(sfx),
                sfx_offset_ms=off.stat("o", mk),
                examples=examples,
            )
        )
    out.sort(key=lambda p: (-p.weight, p.id))
    return PatternsFile(provenance=prov, weighting=_weighting(cfg), patterns=out, other_events=other)


def synth_key(root: Path, cfg: LensConfig) -> str:
    paths = sorted(
        [*(root / "videos").glob("*/record.json"), *(root / "videos").glob("*/signals.summary.json")]
    )
    return cache_key(
        {
            "stage": STAGE,
            "version": __version__,
            "synth": cfg.synth.model_dump(mode="json"),
            "inputs": {p.relative_to(root).as_posix(): sha256_file(p) for p in paths},
            "g4": g4_assignments(root),
        }
    )


PROPOSALS_HEADER = "# Written by s9_synth (pattern clustering). Reviewed by Robert at gate G4.\n"


def other_patterns(root: Path) -> list[tuple[str, str, str]]:
    """(<video>/<event>, proposed name, description) of every annotated `other` event."""
    out = []
    for p in sorted((root / "videos").glob("*/record.json")):
        rec = RecordFile.model_validate_json(p.read_text("utf-8"))
        for e in rec.events:
            if e.status == "annotated" and e.pattern is not None and e.pattern.id == "other":
                out.append((f"{rec.video}/{e.id}", e.pattern.proposed_name or "", e.pattern.description))
    return out


def write_proposals(root: Path, cfg: LensConfig, embed: Embed) -> tuple[int, int]:
    """Cluster the `other` patterns into taxonomy/proposals.yaml. Proposals already decided at G4 are kept
    as they are and their events are not clustered again; open ones keep their plain description,
    recommendation and status when they keep their id. Returns (open proposals, events left out)."""
    from lens.schemas.taxonomy import Taxonomy

    tax = Taxonomy.model_validate(yaml.safe_load((root / "taxonomy" / "v1.yaml").read_text("utf-8")))
    path = root / "taxonomy" / "proposals.yaml"
    old = yaml.safe_load(path.read_text("utf-8")) if path.exists() else []
    kept = ("plain", "recommendation", "why", "status")  # written by Claude and Robert, not by clustering
    prior = {
        o["id"]: {k: o[k] for k in kept if o.get(k)} for o in old or [] if isinstance(o, dict) and "id" in o
    }
    tiers = cfg.synth.weights.tier
    brand_of: dict[str, str | None] = {}
    for p in sorted((root / "videos").glob("*/record.json")):
        rec = RecordFile.model_validate_json(p.read_text("utf-8"))
        brand_of[rec.video] = rec.brand.lower() if tiers.get(rec.tier, 0.0) > 0 else None
    decided = [o for o in old or [] if isinstance(o, dict) and o.get("status", "proposed") != "proposed"]
    settled = {m for o in decided for m in o.get("members", [])}
    items = [i for i in other_patterns(root) if i[0] not in settled]
    proposals, left = propose(items, list(tax.patterns), cfg.synth.cluster, embed, brand_of)
    rows = decided + [p.model_copy(update=prior.get(p.id, {})).model_dump(mode="json") for p in proposals]
    path.write_text(
        PROPOSALS_HEADER + yaml.safe_dump(rows, sort_keys=False, allow_unicode=True, width=110), "utf-8"
    )
    return len(proposals), left


def g4_assignments(root: Path) -> dict[str, str]:
    """<video>/<event> -> pattern id for `other` events of proposals approved (their own id) or merged
    (`merged:<id>`) at G4."""
    path = root / "taxonomy" / "proposals.yaml"
    rows = (yaml.safe_load(path.read_text("utf-8")) if path.exists() else None) or []
    out: dict[str, str] = {}
    for o in rows:
        status = o.get("status", "proposed")
        target = (
            o["id"]
            if status == "approved"
            else status.split(":", 1)[1]
            if status.startswith("merged:")
            else None
        )
        if target:
            out.update(dict.fromkeys(o.get("members", []), target))
    return out


def run_synth(root: Path, cfg: LensConfig, force: bool = False) -> dict[str, str]:
    """Write corpus/stats/*.json. Returns {name: "built"|"cached"}."""
    key = synth_key(root, cfg)
    out_dir = root / "corpus" / "stats"
    paths = {n: out_dir / f"{n}.json" for n in OUTPUTS}
    if not force and all(p.exists() for p in paths.values()):
        try:
            if all(
                json.loads(p.read_text("utf-8"))["provenance"]["input_hash"] == key for p in paths.values()
            ):
                return dict.fromkeys(OUTPUTS, "cached")
        except (KeyError, ValueError):
            pass
    corpus = load_corpus(root, cfg)
    s = cfg.synth

    def mk(values: list[float], weights: list[float], videos: list[str]) -> Stat:
        return stat(values, weights, videos, min_n=s.min_n, bootstrap=s.bootstrap, ci=s.ci, seed=s.seed)

    prov = Provenance(
        tool_version=__version__,
        stage=STAGE,
        annotator=Annotator.CODE,
        input_hash=key,
        created_at=datetime.now(UTC),
    )
    files = {
        "motion": motion_stats(corpus, cfg, prov, mk),
        "sound": sound_stats(corpus, cfg, prov, mk),
        "pacing": pacing_stats(corpus, cfg, prov, mk),
        "patterns": pattern_stats(corpus, cfg, prov, mk, g4_assignments(root)),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    for n, model in files.items():
        paths[n].write_text(model.model_dump_json(indent=1) + "\n", "utf-8")
    return dict.fromkeys(OUTPUTS, "built")
