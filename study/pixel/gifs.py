"""Measure the animated GIF references of the pixel-art study (studies/pixel-art/sources.yaml, `type: gif`):
frame timing, holds, squash and stretch, palette, ramps, pixel scale. GIFs keep exact pixels and per-frame
delays, so these are the study's most reliable animation numbers. Writes studies/pixel-art/metrics/<id>.json
(numbers, committed) and keeps the GIFs in data/study/pixel/gif/<id>/ (never committed)."""

from __future__ import annotations

import json
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from PIL import Image, ImageSequence

from lens import __version__
from lens.hashing import sha256_file
from study.pixel import metrics as m
from study.pixel.config import MEDIA, STUDY, StudyConfig

UA = {"User-Agent": "Mozilla/5.0 (pixel-art study; research use)"}


def fetch(url: str, dest: Path) -> Path:
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=60) as r:
            dest.write_bytes(r.read())
    return dest


def frames_of(path: Path) -> tuple[list[np.ndarray], list[int]]:
    """RGB frames (composited, as a viewer sees them) and their delays in ms."""
    im = Image.open(path)
    frames, delays = [], []
    for f in ImageSequence.Iterator(im):
        frames.append(np.asarray(f.convert("RGB")))
        delays.append(int(f.info.get("duration", 100) or 100))
    return frames, delays


def one(path: Path, cfg: StudyConfig) -> dict[str, Any]:
    mc = cfg.measure
    frames, delays = frames_of(path)
    k, ox, oy = m.native_scale(frames[0], mc)
    native = [m.downscale(f, k, ox, oy) if k > 1 else f for f in frames]
    pal = m.palette(np.concatenate([f.reshape(-1, 3) for f in native])[:, None, :], mc)
    rs = m.ramps([c for c, _ in pal], mc) if len(pal) <= mc.max_palette else []
    return {
        "file": path.name,
        "size": [int(frames[0].shape[1]), int(frames[0].shape[0])],
        "pixel_scale": k,
        "native_size": [int(native[0].shape[1]), int(native[0].shape[0])],
        "animation": m.animation(native, delays),
        "delays_ms": sorted(set(delays)),
        "palette_size": len(pal),
        "ramps": [
            {"len": len(r.colours), "hue_shift": r.hue_shift, "lightness_span": r.lightness_span} for r in rs
        ],
        "dither_share": m.dither_share(native[0]),
    }


def measure_entry(entry: dict[str, Any], cfg: StudyConfig) -> Path | None:
    gifs = [r["url"] for r in entry["refs"] if r["type"] == "gif"]
    if not gifs:
        return None
    files = [fetch(u, MEDIA / "gif" / entry["id"] / u.rsplit("/", 1)[-1]) for u in gifs]
    out = STUDY / "metrics" / f"{entry['id']}.json"
    result = {
        "provenance": {
            "schema_version": 1,
            "tool_version": __version__,
            "stage": "pixel_gif_measure",
            "annotator": "code",
            "input_hash": sha256_file(files[0]),
            "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        },
        "id": entry["id"],
        "gifs": [one(f, cfg) for f in files],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1) + "\n")
    return out


def measure_all(cfg: StudyConfig) -> list[str]:
    done = []
    for e in yaml.safe_load((STUDY / "sources.yaml").read_text()):
        if measure_entry(e, cfg):
            done.append(e["id"])
    return done


def gif_sheet(path: Path, out: Path, max_frames: int = 16, cell: int = 192) -> None:
    """Frames of a GIF in a grid, each labelled with its index and delay (the annotator's view)."""
    from PIL import ImageDraw

    frames, delays = frames_of(path)
    idx = np.linspace(0, len(frames) - 1, min(max_frames, len(frames))).round().astype(int)
    cols = 4
    rows = -(-len(idx) // cols)
    img = Image.new("RGB", (cols * cell, rows * (cell + 18)), (18, 18, 22))
    d = ImageDraw.Draw(img)
    for n, i in enumerate(idx):
        f = Image.fromarray(frames[i])
        f.thumbnail((cell, cell), Image.Resampling.NEAREST)
        x, y = (n % cols) * cell, (n // cols) * (cell + 18)
        img.paste(f, (x, y + 18))
        d.text((x + 4, y + 3), f"#{i} {delays[i]}ms", fill=(255, 220, 120))
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)


def sheets() -> int:
    n = 0
    for g in sorted((MEDIA / "gif").glob("*/*")):
        gif_sheet(g, MEDIA / "work" / g.parent.name / f"{g.stem}.png")
        n += 1
    return n
