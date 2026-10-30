"""F7 matte (ADR 0027): the presenter cut out of the edited video, only where the reel plan needs it.

Props behind the presenter and anime backgrounds need the presenter's own pixels on top of what is drawn
behind them. HyperFrames' `remove-background` does this locally (u2net_human_seg, ONNX Runtime; CoreML on a
Mac, ~0.8 s a frame on the cloud CPU), writing VP9 WebM with alpha. Cutting out a whole take is slow, so each
span the plan needs (padded by `pad_s`) is cut from the edited video frame-exactly and matted on its own:
data/create/<p>/footage/matte/<p>-<first>-<last>.webm, listed in matte.json. A span already matted is kept.
"""

from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path
from typing import Any

from create.burn import probe
from create.footage.edits import load_plan
from create.sketches import hyperframes
from lens.schemas.config import LensConfig
from lens.schemas.create import ReelPlan, Timeline

Span = tuple[int, int]  # first frame, end frame (exclusive) on the edited clock


def matte_spans(plan: ReelPlan, timeline: Timeline, fps: float, frames: int, pad_s: float) -> list[Span]:
    """Frames that need the cut-out: props behind the presenter, anime effects, alchemy circles (on the
    floor, under his feet) and a black hole that pulls the presenter in, padded and merged."""
    words = {w.i: w for w in timeline.words}
    raw: list[tuple[float, float]] = []
    for p in plan.props:
        if p.behind and p.word in words and p.until in words:
            raw.append((words[p.word].start_s, words[p.until].end_s))
    for e in plan.fx:
        if e.kind == "anime" and e.until is not None and e.word in words and e.until in words:
            raw.append((words[e.word].start_s, words[e.until].end_s))
        if e.kind == "clone" and e.until in words:  # a second presenter from another moment (n03)
            src = words[int(e.spec.get("from_word", e.word))].start_s + float(e.spec.get("delay_s", 0.0))
            raw.append((src, src + words[e.until].end_s - words[e.word].start_s))
        if e.kind == "blocky" and e.spec.get("room_only") and e.until in words:  # the room only (n02)
            raw.append((words[e.word].start_s, words[e.until].end_s))
        if e.kind == "blackhole" and e.spec.get("presenter") and e.until in words:  # he is pulled in too
            raw.append((words[e.word].end_s, words[e.until].start_s))  # (tournament n01)
        if e.kind == "alchemy" and e.word in words:  # the circle is on the floor, under his feet (Robert)
            end = words[e.word].start_s + 2.4
            if e.until is not None and e.until in words:
                end = words[e.until].end_s
            raw.append((words[e.word].start_s, end))
    spans = sorted(
        (max(0, math.floor((a - pad_s) * fps)), min(frames, math.ceil((b + pad_s) * fps))) for a, b in raw
    )
    out: list[Span] = []
    for a, b in spans:
        if out and a <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


def covering(index: dict[str, Any], need: list[Span]) -> list[dict[str, Any]]:
    """The matted clips that cover every needed span; raises if one is missing."""
    have: list[dict[str, Any]] = index.get("clips", [])
    out = []
    for a, b in need:
        clip = next((c for c in have if c["start"] <= a and c["end"] >= b), None)
        if clip is None:
            raise FileNotFoundError(f"no matte for frames {a}-{b}: run `create matte <project>`")
        if clip not in out:
            out.append(clip)
    return out


def matte_dir(root: Path, project: str) -> Path:
    return root / "data" / "create" / project / "footage" / "matte"


def load_index(root: Path, project: str) -> dict[str, Any]:
    p = matte_dir(root, project) / "matte.json"
    return json.loads(p.read_text()) if p.exists() else {"clips": []}


def run_matte(root: Path, project: str, cfg: LensConfig, plan_path: Path | None = None) -> list[Path]:
    """Cut out the presenter for every span the reel plan needs; returns the clips written now."""
    base = root / "projects" / project
    plan = load_plan(base, plan_path)
    timeline = Timeline.model_validate(json.loads((base / "timeline.json").read_text()))
    plate = root / "data" / "create" / project / "footage" / "edited" / f"{project}-edited.mp4"
    frames, fps, _ = probe(plate)
    mc = cfg.create.footage.matte
    need = matte_spans(plan, timeline, fps, frames, mc.pad_s)
    out_dir = matte_dir(root, project)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = f"{plate.stat().st_size}-{int(plate.stat().st_mtime)}"
    index = load_index(root, project)
    clips = [c for c in index.get("clips", []) if index.get("plate") == stamp]
    written = []
    hyperframes(cfg.create.render, "telemetry", "disable", cwd=out_dir)
    for a, b in need:
        if any(c["start"] <= a and c["end"] >= b and (out_dir / c["file"]).exists() for c in clips):
            continue
        cut = out_dir / f".cut-{a}-{b}.mp4"
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-i", str(plate), "-vf",
             f"trim=start_frame={a}:end_frame={b},setpts=PTS-STARTPTS", "-an", "-c:v", "libx264",
             "-crf", "12", "-pix_fmt", "yuv420p", str(cut)],
            check=True,
        )  # fmt: skip
        name = f"{project}-{a}-{b}.webm"
        res = subprocess.run(
            ["npx", "--yes", f"hyperframes@{cfg.create.render.hyperframes_version}", "remove-background",
             str(cut), "-o", str(out_dir / name), "--device", mc.device, "--quality", mc.quality, "--json"],
            capture_output=True, text=True, timeout=mc.timeout_s, check=False,
        )  # fmt: skip
        cut.unlink(missing_ok=True)
        if res.returncode != 0:
            raise RuntimeError(f"remove-background failed\n{res.stdout[-1500:]}{res.stderr[-1500:]}")
        got, _, _ = probe(out_dir / name)
        if got != b - a:
            raise RuntimeError(f"matte {name}: {got} frames, expected {b - a}")
        clips = [c for c in clips if not (a <= c["start"] and c["end"] <= b)] + [
            {"start": a, "end": b, "file": name}
        ]
        written.append(out_dir / name)
    (out_dir / "matte.json").write_text(
        json.dumps(
            {
                "project": project,
                "plate": stamp,
                "fps": fps,
                "clips": sorted(clips, key=lambda c: c["start"]),
            },
            indent=1,
        )
    )
    return written


def alpha_at(root: Path, project: str, frame: int) -> Any:
    """The presenter's matte (alpha, 0..255, the plate's size) at an edited-clock frame, or None when no
    matted clip covers it. Used to place props behind the presenter where they can be seen."""
    import numpy as np

    index = load_index(root, project)
    plate = root / "data" / "create" / project / "footage" / "edited" / f"{project}-edited.mp4"
    if not plate.exists() or index.get("plate") != f"{plate.stat().st_size}-{int(plate.stat().st_mtime)}":
        return None  # a matte of an older plate would place props against the wrong person (audit)
    clip = next((c for c in index.get("clips", []) if c["start"] <= frame < c["end"]), None)
    if clip is None:
        return None
    path = matte_dir(root, project) / clip["file"]
    res = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    )  # fmt: skip
    w, h = (int(v) for v in res.stdout.strip().split(",")[:2])
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-c:v", "libvpx-vp9", "-i", str(path), "-vf",
         f"select=eq(n\\,{frame - clip['start']}),alphaextract", "-frames:v", "1", "-f", "rawvideo",
         "-pix_fmt", "gray", "-"],
        capture_output=True, check=True,
    ).stdout  # fmt: skip
    if len(raw) < w * h:
        return None
    return np.frombuffer(raw[: w * h], np.uint8).reshape(h, w)
