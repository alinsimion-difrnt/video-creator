"""S3 deterministic signals: run video, audio and speech analysis for one video and write outputs.

Writes (declared in lens/stages.py):
    data/signals/<id>/signals.json          full detail (events, beats, SFX features, words)
    data/signals/<id>/curves.npz            per-frame diff and global motion
    videos/<id>/signals.summary.json        compact summary (committed, validated)
    data/state/<id>/s3_signals.json         cache marker
"""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from lens import __version__
from lens.hashing import cache_key
from lens.ingest import read_marker, write_marker
from lens.schemas import LensConfig, SourceEntry
from lens.schemas.common import Annotator, Provenance
from lens.schemas.signals import (
    AudioSummary,
    CaptionSummary,
    EventOut,
    HoldOut,
    LoudnessOut,
    SfxOut,
    ShotOut,
    SignalsSummary,
    SpeechSummary,
    TransitionOut,
    VideoSummary,
)
from lens.schemas.video import VideoMeta
from lens.signals import audio as audio_mod
from lens.signals import speech as speech_mod
from lens.signals import video as video_mod

STAGE = "s3_signals"


class SignalsError(RuntimeError):
    pass


def _agrees(a: str, b: str) -> bool:
    from lens.signals.clap import agree

    return agree(a, b)


def _share(flags: list[bool]) -> float | None:
    return round(sum(flags) / len(flags), 3) if flags else None


def _span_offset(t: float, spans: list[tuple[float, float]]) -> float:
    """Signed distance from t to the nearest scene change: 0 inside a transition span (an SFX that
    fires during a dissolve or push belongs to that scene change), else to its nearer edge."""
    best = 0.0
    for i, (a, b) in enumerate(spans):
        off = t - a if t < a else t - b if t > b else 0.0
        if i == 0 or abs(off) < abs(best):
            best = off
    return best


def cross_metrics(
    fps: float,
    scene_spans_s: list[tuple[float, float]],
    boundary_s: list[float],
    landings_s: list[float],
    sfx: list[audio_mod.SfxCandidate],
    beat_times: list[float] | None,
    cfg: LensConfig,
    clap_labels: list[Any] | None = None,
) -> tuple[list[SfxOut], float | None, float | None, float | None]:
    """SFX placement against the picture, and cuts against the beat."""
    frame = 1.0 / fps
    window = cfg.signals.sfx_reveal_window_s
    out: list[SfxOut] = []
    for i, c in enumerate(sfx):
        cl = clap_labels[i] if clap_labels else None
        final, source = c.label, c.label_source
        if cl is not None and c.label == "unsure" and cl.score >= cfg.signals.clap.min_score:
            final, source = cl.label, "clap"
        scene_off = _span_offset(c.sync_s, scene_spans_s)
        reveal_off = None
        if landings_s:
            lands = np.asarray(landings_s)
            nearest = float(lands[np.argmin(np.abs(lands - c.sync_s))])
            if abs(c.sync_s - nearest) <= window:
                reveal_off = round((c.sync_s - nearest) * 1000, 1)
        out.append(
            SfxOut(
                id=c.id,
                sync_s=c.sync_s,
                label=final,
                label_source=source,
                rules_label=c.label,
                clap_label=cl.label if cl else None,
                clap_score=cl.score if cl else None,
                agreement=_agrees(c.label, cl.label) if cl and c.label != "unsure" else None,
                on_beat=c.on_beat,
                reveal_offset_ms=reveal_off,
                scene_start_offset_ms=round(scene_off * 1000, 1),
                at_scene_start=abs(scene_off) <= cfg.signals.scene_start_tolerance_frames * frame,
            )
        )
    at_start = _share([s.at_scene_start for s in out])
    near_reveal = _share([s.reveal_offset_ms is not None for s in out])
    on_beat = None
    if beat_times:
        beats = np.asarray(beat_times)
        tol = cfg.signals.cut_on_beat_tolerance_frames * frame
        on_beat = _share([bool(np.min(np.abs(beats - t)) <= tol) for t in boundary_s])
    return out, at_start, near_reveal, on_beat


def run_signals(entry: SourceEntry, root: Path, cfg: LensConfig, force: bool = False) -> str:
    meta_path = root / "videos" / entry.id / "meta.json"
    if not meta_path.exists():
        return "skipped"
    meta = VideoMeta.model_validate_json(meta_path.read_text(encoding="utf-8"))
    key = cache_key(
        {"stage": STAGE, "tool": __version__, "proxy": meta.proxy.sha256, "signals": cfg.signals.model_dump()}
    )
    summary_path = root / "videos" / entry.id / "signals.summary.json"
    marker = read_marker(root, entry.id, STAGE)
    if not force and marker and marker.get("cache_key") == key and summary_path.exists():
        return "cached"

    media = root / "data" / "media" / entry.id
    proxy = media / "proxy.mp4"
    if not proxy.exists():
        raise SignalsError(f"{entry.id}: proxy missing at {proxy}; run `lens frames` (or pull media)")
    fps = meta.proxy.fps
    v = cfg.signals.video

    fs = video_mod.scan(proxy, fps, meta.proxy.width, meta.proxy.height, v)
    cuts = video_mod.detect_cuts(fs, v)
    transitions = video_mod.detect_transitions(fs, cuts, v)
    shots = video_mod.build_shots(fs.n, transitions)
    events = video_mod.detect_events(fs, shots, v)
    holds = video_mod.detect_holds(fs, shots, events, v, cfg.signals.dead_hold_min_s)
    pace = video_mod.pace_curve(fs, shots, events)

    def t(frame: int) -> float:
        return round(frame / fps, 4)

    words: list[speech_mod.Word] = []
    audio_summary = speech_summary = None
    detail: dict[str, Any] = {}
    wav = media / "audio.wav"
    if meta.audio is not None and wav.exists():
        vocals: Path | None = None
        bed: Path | None = None
        if cfg.signals.stems.enabled:
            from lens.signals.stems import separate

            vocals, bed = separate(
                wav, root / "data" / "signals" / entry.id / "stems", cfg.signals.stems.model
            )
        loud, beats, sfx = audio_mod.analyse(wav, cfg.signals.audio, bed=bed)
        clap_labels: list[Any] = []
        if cfg.signals.clap.enabled and sfx:
            from lens.signals import clap

            clap_labels = clap.label(bed or wav, [(c.onset_s, c.sync_s) for c in sfx], cfg.signals.clap)
        steady = beats.confidence >= cfg.signals.audio.beat_min_confidence
        boundaries = [t(s.start_f) for s in shots[1:]]
        sfx_out, at_start, near_reveal, cuts_on_beat = cross_metrics(
            fps,
            # Scene changes as spans: a cut is a point, a dissolve/push runs until its clean frame.
            [(t(s.start_f), t(s.transition_in.end_f if s.transition_in else s.start_f)) for s in shots],
            boundaries,
            # Reveal anchors: where a change begins (a pop, a fade starting) and where it lands.
            sorted({t(e.start_f) for e in events} | {t(e.end_f) for e in events}),
            sfx,
            beats.times if steady else None,
            cfg,
            clap_labels,
        )
        minutes = fs.n / fps / 60
        if entry.media.value == "full":
            voice = vocals or wav
            mono = speech_mod.load_mono(voice)
            words = speech_mod.tighten(
                speech_mod.transcribe(voice, cfg.signals.speech), mono, speech_mod.SR, cfg.signals.speech
            )
            p = speech_mod.prosody(words, mono, speech_mod.SR, cfg.signals.speech)
            if p is not None and len(words) >= cfg.signals.speech_min_words:
                per_shot = [speech_mod.wpm_in(words, t(s.start_f), t(s.end_f)) for s in shots]
                spoken = [w for w in per_shot if w]
                cv = round(float(np.std(spoken) / np.mean(spoken)), 3) if len(spoken) >= 2 else None
                speech_summary = SpeechSummary(**asdict(p), wpm_cv_across_shots=cv)
            detail["words"] = [asdict(w) for w in words]
        ducking = None
        if bed is not None and speech_summary is not None:
            from lens.signals.stems import ducking_db

            ducking = ducking_db(
                bed, [(w.start_s, w.end_s) for w in words], cfg.signals.stems.ducking_guard_s
            )
        agreements = [s.agreement for s in sfx_out if s.agreement is not None]
        audio_summary = AudioSummary(
            stems=bed is not None,
            ducking_db=ducking,
            loudness=LoudnessOut(**asdict(loud)),
            bpm=beats.bpm,
            beat_confidence=beats.confidence,
            sfx=sfx_out,
            sfx_per_min=round(len(sfx) / minutes, 2) if minutes else 0.0,
            label_agreement_share=_share(agreements),
            sfx_at_scene_start_share=at_start,
            sfx_near_reveal_share=near_reveal,
            cuts_on_beat_share=cuts_on_beat,
        )
        detail["beats"] = asdict(beats)
        detail["sfx"] = [asdict(c) for c in sfx]

    caption_summary = None
    if cfg.signals.captions.enabled:
        from lens.signals import captions as captions_mod

        groups = captions_mod.detect(proxy, fps, meta.proxy.width, meta.proxy.height, cfg.signals.captions)
        cs = captions_mod.stats(groups, fps, fs.n, [w.start_s for w in words], cfg.signals.captions)
        caption_summary = CaptionSummary(**asdict(cs)) if cs else None
        detail["captions"] = [asdict(g) for g in groups]

    energies = np.asarray([float(r["motion_energy"]) for r in pace])
    pace_cv = (
        float(np.std(energies) / np.mean(energies)) if energies.size >= 2 and energies.mean() > 0 else 0.0
    )
    shot_out = []
    for s, row in zip(shots, pace, strict=True):
        tr = s.transition_in
        shot_out.append(
            ShotOut(
                id=s.id,
                start_s=t(s.start_f),
                end_s=t(s.end_f),
                transition_in=TransitionOut(
                    kind=tr.kind,
                    start_s=t(tr.start_f),
                    duration_s=t(tr.end_f - tr.start_f),
                    direction=tr.direction,
                )
                if tr
                else None,
                motion_energy=float(row["motion_energy"]),
                events_per_s=float(row["events_per_s"]),
                wpm=speech_mod.wpm_in(words, t(s.start_f), t(s.end_f)) if words else None,
            )
        )
    by_kind: dict[str, int] = {}
    for tr in transitions:
        by_kind[tr.kind] = by_kind.get(tr.kind, 0) + 1
    cams: dict[str, int] = {}
    for e in events:
        if e.camera_move != "none":
            cams[e.camera_move] = cams.get(e.camera_move, 0) + 1
    dead = [h for h in holds if h.dead]
    video_summary = VideoSummary(
        fps=fps,
        duration_s=t(fs.n),
        shots=shot_out,
        transitions_by_kind=by_kind,
        mean_shot_s=round(float(np.mean([s.end_s - s.start_s for s in shot_out])), 3),
        events=[
            EventOut(
                id=e.id,
                shot=e.shot,
                kind=e.kind,
                start_s=t(e.start_f),
                end_s=t(e.end_f),
                bbox=e.bbox,
                camera_move=e.camera_move,
            )
            for e in events
        ],
        camera_moves=cams,
        holds=[HoldOut(shot=h.shot, start_s=t(h.start_f), end_s=t(h.end_f), dead=h.dead) for h in holds],
        dead_hold_count=len(dead),
        dead_hold_s=round(sum((h.end_f - h.start_f) / fps for h in dead), 3),
        pace_cv=round(pace_cv, 3),
    )
    now = datetime.now(UTC)
    summary = SignalsSummary(
        provenance=Provenance(
            tool_version=__version__, stage=STAGE, annotator=Annotator.CODE, input_hash=key, created_at=now
        ),
        video_id=entry.id,
        video=video_summary,
        audio=audio_summary,
        speech=speech_summary,
        captions=caption_summary,
    )
    out_dir = root / "data" / "signals" / entry.id
    out_dir.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out_dir / "curves.npz", diff=fs.diff, tx=fs.tx, ty=fs.ty, scale=fs.scale)
    detail["transitions"] = [asdict(x) for x in transitions]
    detail["events"] = [asdict(x) for x in events]
    (out_dir / "signals.json").write_text(json.dumps(detail, indent=1, default=float), encoding="utf-8")
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(summary.model_dump_json(indent=2) + "\n", encoding="utf-8")
    write_marker(
        root, entry.id, STAGE, {"cache_key": key, "tool_version": __version__, "created_at": now.isoformat()}
    )
    return "analysed"
