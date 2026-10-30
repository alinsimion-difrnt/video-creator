"""Measure one TikTok (studies/README.md, "Measure"). Decoders here, numbers in study/tiktok/metrics.py.

Writes studies/tiktok/measure/<id>.json (numbers only, committed) and data/study/tiktok/work/<id>/
(transcript, OCR text, frame samples: third-party words and pictures, never committed)."""

from __future__ import annotations

import json
import subprocess
import tempfile
from datetime import UTC, datetime
from functools import cache
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from lens import __version__
from lens.config import load_config
from lens.hashing import sha256_file
from lens.media import iter_frames_rgb, probe, scaled_size
from lens.signals import audio, speech, video
from lens.signals.captions import _ocr
from study.tiktok import metrics as m
from study.tiktok.config import MEDIA, ROOT, STUDY, StudyConfig

STAGE = "tiktok_measure"


@cache
def _faces(model: str, min_score: float) -> Any:
    return cv2.FaceDetectorYN.create(str(ROOT / model), "", (320, 320), min_score, 0.3, 5000)


def _samples(path: Path, w: int, h: int, cfg: StudyConfig) -> tuple[list[float], list[m.Box], list[m.Box]]:
    """OCR boxes and face boxes on frames sampled at `sample_fps` (boxes in 0..1)."""
    mc = cfg.measure
    sw, sh = scaled_size(w, h, mc.sample_width)
    times: list[float] = []
    texts: list[m.Box] = []
    faces: list[m.Box] = []
    for i, rgb in iter_frames_rgb(path, mc.sample_fps, sw, sh):
        t = round(i / mc.sample_fps, 2)
        times.append(t)
        out = _ocr()(rgb)
        for box, txt, score in zip(
            out.boxes if out.boxes is not None else [], out.txts or (), out.scores or (), strict=False
        ):
            if score < mc.ocr_min_score:
                continue
            xs, ys = [p[0] for p in box], [p[1] for p in box]
            texts.append(
                m.Box(
                    t,
                    float(min(xs)) / sw,
                    float(min(ys)) / sh,
                    float(max(xs)) / sw,
                    float(max(ys)) / sh,
                    str(txt),
                )
            )
        det = _faces(mc.face_model, mc.face_min_score)
        det.setInputSize((sw, sh))
        _, found = det.detect(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
        for f in [] if found is None else found:
            x, y, fw, fh = (float(v) for v in f[:4])
            faces.append(m.Box(t, x / sw, y / sh, (x + fw) / sw, (y + fh) / sh))
    return times, texts, faces


def _wav(path: Path, out: Path, sr: int, channels: int) -> bool:
    r = subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-i",
            str(path),
            "-vn",
            "-ac",
            str(channels),
            "-ar",
            str(sr),
            str(out),
        ],
        check=False,
    )
    return r.returncode == 0 and out.exists()


def real_length(vid: str) -> float | None:
    """The video's own length from the embed metadata (whole seconds): the embed copy appends a ~4 s TikTok
    end slate after it."""
    for f in (MEDIA / f"{vid}.json", MEDIA / "meta" / f"{vid}.json"):
        if f.exists():
            d = json.loads(f.read_text()).get("duration_s")
            return float(d) if d else None
    return None


def trimmed(vid: str, slack_s: float) -> Path:
    """data/study/tiktok/<id>.cut.mp4: the copy without the end slate (stream copy, made once)."""
    src, cut = MEDIA / f"{vid}.mp4", MEDIA / f"{vid}.cut.mp4"
    length = real_length(vid)
    if length is None:
        return src
    if not cut.exists():
        subprocess.run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-y",
                "-i",
                str(src),
                "-t",
                f"{length + slack_s:.2f}",
                "-c",
                "copy",
                str(cut),
            ],
            check=True,
        )
    return cut


def measure(vid: str, cfg: StudyConfig, force: bool = False) -> Path:
    src = trimmed(vid, cfg.measure.end_slack_s)
    out = STUDY / "measure" / f"{vid}.json"
    work = MEDIA / "work" / vid
    digest = sha256_file(src)
    if out.exists() and not force and json.loads(out.read_text())["provenance"]["input_hash"] == digest:
        return out
    lcfg = load_config()
    mc = cfg.measure
    p = probe(src)
    w, h, duration = p.width or 576, p.height or 1024, float(p.duration_s)

    vcfg = lcfg.signals.video
    sw, sh = scaled_size(w, h, vcfg.analysis_width)
    fs = video.scan(src, mc.scan_fps, sw, sh, vcfg)
    cut_f = video.detect_cuts(fs, vcfg)
    shots = video.build_shots(fs.n, video.detect_transitions(fs, cut_f, vcfg))
    events = video.detect_events(fs, shots, vcfg)
    cut_t = [round(c / fs.fps, 2) for c in cut_f]
    length = real_length(vid)
    if (
        length is not None
    ):  # the end slate starts with a hard cut near the stated length: the video ends there
        slate = [t for t in cut_t if length - mc.end_slack_s <= t <= length + mc.end_slack_s]
        duration = slate[0] if slate else min(duration, length)
        keep = [i for i, t in enumerate(cut_t) if t < duration]
        cut_f, cut_t = [cut_f[i] for i in keep], [cut_t[i] for i in keep]
    event_t = [t for t in (round(e.start_f / fs.fps, 2) for e in events) if t < duration]
    punch_t = [t for t in m.punch_ins(fs.scale, fs.fps, cut_f, mc) if t < duration]
    last = max(0, min(fs.n - 1, int(duration * fs.fps) - 1))

    with tempfile.TemporaryDirectory() as tmp:
        w16, w48 = Path(tmp) / "a16.wav", Path(tmp) / "a48.wav"
        has_audio = _wav(src, w16, speech.SR, 1) and _wav(src, w48, 48000, 2)
        words = speech.transcribe(w16, lcfg.signals.speech) if has_audio else []
        mono = speech.load_mono(w16) if has_audio else np.zeros(1)
        lufs = round(audio.loudness(*audio.load(w48)).integrated_lufs, 1) if has_audio else None
    words = [wd for wd in words if wd.start_s < duration]
    spans = [(wd.start_s, wd.end_s) for wd in words]
    samples, texts, faces = _samples(src, w, h, cfg)
    samples = [t for t in samples if t < duration]
    texts = [b for b in texts if b.t < duration]
    faces = [b for b in faces if b.t < duration]
    text_times = sorted(
        {b.t for b in texts if len(b.text.strip()) >= mc.ocr_min_chars and not m.is_watermark(b.text)}
    )

    result = {
        "provenance": {
            "schema_version": 1,
            "tool_version": __version__,
            "stage": STAGE,
            "annotator": "code",
            "input_hash": digest,
            "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        },
        "id": vid,
        "duration_s": round(duration, 2),
        "width": w,
        "height": h,
        "shots": m.shot_stats(cut_t, duration),
        "speech": m.speech_stats(spans, duration),
        "text": m.text_layout(texts, samples, mc),
        "face": m.face_summary(faces, samples, mc),
        "hook": m.hook(spans, text_times, cut_t, event_t, mc.hook_window_s),
        "density": m.density(event_t, punch_t, duration),
        "sound": {
            "loudness_lufs": lufs,
            "music_bed_db": m.music_bed_db(mono, speech.SR, spans, mc) if has_audio else None,
        },
        "loop": m.loop_score(fs.thumbs[0], fs.thumbs[last]) if fs.n > 1 else None,
        "times": {"cuts": cut_t, "events": event_t, "punches": punch_t},
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1) + "\n")
    work.mkdir(parents=True, exist_ok=True)
    (work / "words.json").write_text(json.dumps([[wd.text, wd.start_s, wd.end_s] for wd in words]))
    (work / "ocr.json").write_text(json.dumps([[b.t, b.x0, b.y0, b.x1, b.y1, b.text] for b in texts]))
    return out


def retext(vid: str, cfg: StudyConfig) -> Path:
    """Recompute the text and hook numbers from the saved OCR boxes and words (no decoding): used when the
    text rules change (the TikTok watermark filter)."""
    out = STUDY / "measure" / f"{vid}.json"
    work = MEDIA / "work" / vid
    data = json.loads(out.read_text())
    mc = cfg.measure
    duration = float(data["duration_s"])
    samples = [round(i / mc.sample_fps, 2) for i in range(int(duration * mc.sample_fps) + 1)]
    texts = [
        m.Box(t, x0, y0, x1, y1, txt)
        for t, x0, y0, x1, y1, txt in json.loads((work / "ocr.json").read_text())
    ]
    texts = [b for b in texts if b.t < duration]
    spans = [(s, e) for _, s, e in json.loads((work / "words.json").read_text()) if s < duration]
    text_times = sorted(
        {b.t for b in texts if len(b.text.strip()) >= mc.ocr_min_chars and not m.is_watermark(b.text)}
    )
    times = data["times"]
    data["text"] = m.text_layout(texts, samples, mc)
    data["hook"] = m.hook(spans, text_times, times["cuts"], times["events"], mc.hook_window_s)
    out.write_text(json.dumps(data, indent=1) + "\n")
    return out
