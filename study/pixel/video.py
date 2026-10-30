"""Measure a pixel-art clip (studies/pixel-art/tiktok.yaml or a YouTube trailer): how long drawings are held,
the native pixel scale, the palette and its ramps, dithering. Writes studies/pixel-art/clips/<id>.json
(numbers) and data/study/pixel/work/<id>/sheet.jpg (frames for the annotator, never committed)."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from lens import __version__
from lens.hashing import sha256_file
from lens.media import iter_frames_rgb, probe, scaled_size
from study.pixel import metrics as m
from study.pixel.config import MEDIA, STUDY, StudyConfig


def _frame(src: Path, t: float) -> np.ndarray | None:
    p = probe(src)
    w, h = p.width, p.height
    out = subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-ss",
            f"{t:.3f}",
            "-i",
            str(src),
            "-frames:v",
            "1",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-",
        ],
        capture_output=True,
        check=False,
    )
    if len(out.stdout) < w * h * 3:
        return None
    return np.frombuffer(out.stdout[: w * h * 3], dtype=np.uint8).reshape(h, w, 3)


def still(img: np.ndarray, cfg: StudyConfig) -> dict[str, object]:
    """Pixel scale, palette, ramps and dithering of one frame (at its native pixel size)."""
    mc = cfg.measure
    k, ox, oy = m.native_scale(img, mc)
    native = m.downscale(img, k, ox, oy) if k > 1 else img
    pal = m.palette(native, mc)
    clean = len(pal) <= mc.max_palette
    rs = m.ramps([c for c, _ in pal], mc) if clean else []
    return {
        "pixel_scale": k,
        "native_size": [int(native.shape[1]), int(native.shape[0])],
        "palette_size": len(pal),
        "clean_pixels": clean,
        "ramps": len(rs),
        "ramp_hue_shift_median": round(float(np.median([abs(r.hue_shift) for r in rs])), 1) if rs else None,
        "ramp_len_median": float(np.median([len(r.colours) for r in rs])) if rs else None,
        "dither_share": m.dither_share(native),
    }


def sheet(src: Path, times: list[float], out: Path, thumb_w: int = 240) -> None:
    p = probe(src)
    h = round(thumb_w * p.height / p.width)
    cols = 6
    rows = -(-len(times) // cols)
    img = Image.new("RGB", (cols * thumb_w, rows * (h + 22)), (18, 18, 22))
    d = ImageDraw.Draw(img)
    for i, t in enumerate(times):
        f = _frame(src, t)
        x, y = (i % cols) * thumb_w, (i // cols) * (h + 22)
        if f is not None:
            img.paste(Image.fromarray(f).resize((thumb_w, h), Image.Resampling.NEAREST), (x, y + 22))
        d.text((x + 6, y + 4), f"{t:.2f}s", fill=(255, 220, 120))
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, quality=85)


def measure(src: Path, cid: str, cfg: StudyConfig, force: bool = False) -> Path:
    out = STUDY / "clips" / f"{cid}.json"
    digest = sha256_file(src)
    if out.exists() and not force and json.loads(out.read_text())["provenance"]["input_hash"] == digest:
        return out
    mc = cfg.measure
    p = probe(src)
    meta = src.with_suffix(".json")  # the embed's own length: TikTok copies end on a blank end card
    stated = json.loads(meta.read_text()).get("duration_s") if meta.exists() else None
    duration = min(float(p.duration_s), float(stated or p.duration_s), mc.clip_seconds)
    w, h = scaled_size(p.width, p.height, mc.video_width)
    diffs: list[float] = []
    prev: np.ndarray | None = None
    for i, rgb in iter_frames_rgb(src, mc.video_fps, w, h):
        if i / mc.video_fps > duration:
            break
        g = rgb.astype(np.float32).mean(axis=-1) / 255.0
        diffs.append(0.0 if prev is None else float(np.abs(g - prev).mean()))
        prev = g
    times = [round(duration * (i + 0.5) / 12, 2) for i in range(12)]
    stills = [
        s
        for t in (times[3], times[6], times[9])
        if (f := _frame(src, t)) is not None
        for s in [still(f, cfg)]
    ]
    best = min(stills, key=lambda s: int(s["palette_size"])) if stills else None  # type: ignore[call-overload]
    result = {
        "provenance": {
            "schema_version": 1,
            "tool_version": __version__,
            "stage": "pixel_clip_measure",
            "annotator": "code",
            "input_hash": digest,
            "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        },
        "id": cid,
        "duration_s": round(float(p.duration_s), 2),
        "measured_s": round(duration, 2),
        "size": [p.width, p.height],
        "holds": m.holds(np.asarray(diffs), mc.video_fps, mc.change_threshold),
        "still": best,
        "sheet_times": times,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1) + "\n")
    sheet(src, times, MEDIA / "work" / cid / "sheet.jpg")
    return out
