"""Presenter layouts over a background (`create pip`): full frame, corner bubble or off, per timeline scene.

One edited full-frame video is used throughout. For the bubble it is clipped to a circle around the face
and scaled into the corner, so moving between layouts is one continuous move, never a cut
(create/kit/layout.html).
The face position per scene comes from F5 framing; without it the frame centre is used. The bubble's size,
corner and ring come from config and the frame's safe area, and it always sits above the caption band.
"""

from __future__ import annotations

import json
import math
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

import yaml

from create.bundle import gsap
from create.burn import mux, probe, render_comp
from create.footage.framing import face_box
from create.footage.media import display_size, video_stream
from create.footage.media import probe as media_probe
from create.footage.pip import bubble_position
from lens.schemas.config import CreateFrame, LensConfig
from lens.schemas.create import Edl, Framing, LayoutPlan, Timeline, Tokens

KIT = Path(__file__).resolve().parent.parent / "kit"


@dataclass(frozen=True)
class Pose:
    """The presenter layer's transform (origin top-left) and its circular clip, in output pixels."""

    t: float  # when this pose is reached (a scene start)
    layout: str
    top: float  # the layer is clipped above this screen y (split: the product's bottom edge; else 0)
    x: float
    y: float
    scale: float
    r: float  # clip radius in the layer's own pixels
    cx: float  # clip centre (the face) in the layer's own pixels
    cy: float


def face_at(t: float, edl: Edl, framing: Framing | None, w: int, h: int) -> tuple[float, float, float]:
    """(centre x, centre y, width) of the face at edited time `t`, in output pixels."""
    box = face_box(t, edl, framing, w) if framing is not None else None
    if box is None:
        return w / 2, h * 0.38, w * 0.25
    x0, y0, x1, y1 = box
    return (x0 + x1) / 2, (y0 + y1) / 2, x1 - x0


def poses(
    timeline: Timeline, plan: LayoutPlan, edl: Edl, framing: Framing | None, frame: CreateFrame, d: int,
    margin: int, face_scale: float, seam: float | None = None, split_offset: float = 260,
    avoid_band: bool = True,
) -> list[Pose]:  # fmt: skip
    """One pose per scene. `seam` is the product's bottom edge on screen (split layouts)."""
    bx, by = bubble_position(frame, d, margin, plan.corner, avoid_band)
    w, h = frame.width, frame.height
    seam_y = seam if seam is not None else h / 2
    out = []
    for sc in timeline.scenes:
        layout = plan.scenes.get(sc.scene, plan.default)
        mid = (sc.start_s + sc.end_s) / 2
        cx, cy, fw = face_at(mid, edl, framing, w, h)
        if layout in ("full", "split"):
            dy = max(0.0, seam_y + split_offset - cy) if layout == "split" else 0.0
            # the smallest circle around the face that still covers the frame (here: no visible circle)
            cover = max(math.hypot(cx - x, cy - y) for x in (0, w) for y in (-dy, h))
            top = seam_y if layout == "split" else 0.0
            out.append(Pose(sc.start_s, layout, top, 0, dy, 1, cover + 2, cx, cy))
            continue
        k = d / (fw * face_scale)
        if layout == "off":
            k *= 0.6  # shrinks away into the corner as it fades
        out.append(
            Pose(sc.start_s, layout, 0.0, bx + d / 2 - k * cx, by + d / 2 - k * cy, k, d / (2 * k), cx, cy)
        )
    return out


Fit = Literal["auto", "cover", "contain"]
CONTAIN_WHEN = 1.15  # auto: a background this much wider or taller (aspect ratio) than the frame is contained


def background_rect(bw: int, bh: int, frame: CreateFrame, fit: Fit) -> tuple[str, int, int, int, int]:
    """(mode, x, y, w, h): where the background lands on the frame.

    cover: scaled to fill the frame and centre-cropped (for footage).
    contain: whole, never cropped, on the brand canvas. A wide product video fills the frame's width at the
    top of the safe area, leaving the lower frame for the presenter (split, bubble) and captions.
    auto: contain when the aspects differ by more than CONTAIN_WHEN, else cover."""
    w, h = frame.width, frame.height
    ratio = (bw / bh) / (w / h)
    if fit == "auto":
        fit = "contain" if ratio > CONTAIN_WHEN or ratio < 1 / CONTAIN_WHEN else "cover"
    if fit == "cover":
        return "cover", 0, 0, w, h
    if ratio >= 1:  # wider than the frame: full width
        cw, ch = w, round(w * bh / bw / 2) * 2
        y = frame.safe[0].y0 if frame.safe[0].y0 + ch <= h else (h - ch) // 2
        return "contain", 0, y, cw, ch
    cw = round(h * bw / bh / 2) * 2
    return "contain", (w - cw) // 2, 0, cw, h


def background_filter(bw: int, bh: int, frame: CreateFrame, fit: Fit, canvas: str) -> str:
    """ffmpeg filters that put a background on the frame (see background_rect)."""
    mode, x, y, cw, ch = background_rect(bw, bh, frame, fit)
    w, h = frame.width, frame.height
    if mode == "cover":
        return f"scale={w}:{h}:force_original_aspect_ratio=increase:flags=lanczos,crop={w}:{h},setsar=1"
    return f"scale={cw}:{ch}:flags=lanczos,setsar=1,pad={w}:{h}:{x}:{y}:color=0x{canvas.lstrip('#')}"


def check_plan(plan: LayoutPlan, timeline: Timeline) -> list[str]:
    known = {s.scene for s in timeline.scenes}
    return [
        f"layout.yaml names scene {s!r}, which is not in the timeline" for s in plan.scenes if s not in known
    ]


def layout_comp(
    frame: CreateFrame, ps: list[Pose], d: int, xy: tuple[int, int], ring: str, ring_w: int,
    transition_s: float, duration: float, lang: str,
) -> str:  # fmt: skip
    v = {"--w": f"{frame.width}px", "--h": f"{frame.height}px", "--d": f"{d}px", "--bx": f"{xy[0]}px",
         "--by": f"{xy[1]}px", "--ring": ring, "--ring-w": f"{ring_w}px"}  # fmt: skip
    data = {"poses": [asdict(p) for p in ps], "transition": transition_s, "duration": round(duration, 6)}
    out = (KIT / "layout.html").read_text()
    for key, val in {
        "{{LANG}}": lang, "{{W}}": str(frame.width), "{{H}}": str(frame.height),
        "{{DURATION}}": f"{duration:.6f}", "{{DATA}}": json.dumps(data),
        "{{CSS_VARS}}": ":root{" + ";".join(f"{k}:{x}" for k, x in v.items()) + "}",
    }.items():  # fmt: skip
        out = out.replace(key, val)
    return out


def run_layout(
    root: Path, project: str, background: Path, cfg: LensConfig, out: Path | None = None, lang: str = "en",
    corner: str | None = None, fit: Fit = "auto",
) -> Path:  # fmt: skip
    base = root / "projects" / project
    tokens = Tokens.model_validate(json.loads((base / "tokens.json").read_text()))
    timeline = Timeline.model_validate(json.loads((base / "timeline.json").read_text()))
    edl = Edl.model_validate(json.loads((base / "edl.json").read_text()))
    framing_path = base / "framing.json"
    framing = Framing.model_validate(json.loads(framing_path.read_text())) if framing_path.exists() else None
    plan_path = base / "layout.yaml"
    raw = yaml.safe_load(plan_path.read_text()) if plan_path.exists() else {"default": "pip"}
    if corner is not None:
        raw = {**(raw or {}), "corner": corner}
    plan = LayoutPlan.model_validate(raw or {})
    problems = check_plan(plan, timeline)
    if problems:
        raise ValueError("; ".join(problems))
    frame = cfg.create.design.frames[tokens.frame]
    rc = cfg.create.footage.reframe
    plate = root / "data" / "create" / project / "footage" / "edited" / f"{project}-edited.mp4"
    frames, fps, _ = probe(plate)
    duration = frames / fps
    comp = root / "data" / "create" / project / "render" / "layout"
    (comp / "assets").mkdir(parents=True, exist_ok=True)
    shutil.copy(gsap(root / "data" / "create" / "_cache"), comp / "assets" / "gsap.min.js")
    shutil.copy(plate, comp / "presenter.mp4")
    bv = video_stream(media_probe(background))
    bw, bh = display_size(bv)
    shape = background_filter(bw, bh, frame, fit, tokens.colors["canvas"])
    mode, _, by0, _, bh0 = background_rect(bw, bh, frame, fit)
    seam = float(by0 + bh0) if mode == "contain" and by0 + bh0 < frame.height else None
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(background), "-vf",
         f"fps={fps:g},{shape},tpad=stop_mode=clone:stop_duration={duration:.3f}",
         "-t", f"{duration:.6f}", "-an",
         "-c:v", "libx264", "-crf", "16", "-g", str(round(fps)), "-pix_fmt", "yuv420p",
         str(comp / "background.mp4")],
        check=True,
    )  # fmt: skip
    d = rc.pip_size[tokens.frame]
    xy = bubble_position(frame, d, rc.pip_margin, plan.corner)
    ps = poses(
        timeline, plan, edl, framing, frame, d, rc.pip_margin, rc.pip_face_scale, seam, rc.split_face_offset
    )
    html = layout_comp(
        frame, ps, d, xy, tokens.colors["surface"], rc.pip_ring, plan.transition_s, duration, lang
    )
    (comp / "index.html").write_text(html)
    render_comp(cfg.create.render, comp)
    target = out or root / "data" / "create" / project / "render" / f"{project}-layout.mp4"
    mux(comp / "video.mp4", plate, duration, target)
    got, _, _ = probe(target)
    if got != frames:
        raise RuntimeError(f"frame count mismatch: output {got}, presenter {frames}")
    sidecar = {  # read by `create burn`: captions sit on the seam in split scenes, plain in bubble scenes
        "seam": seam if seam is not None else frame.height / 2,
        "scenes": [
            {"start_s": sc.start_s, "end_s": sc.end_s, "layout": plan.scenes.get(sc.scene, plan.default)}
            for sc in timeline.scenes
        ],
    }  # fmt: skip
    target.with_suffix(".layout.json").write_text(json.dumps(sidecar, indent=1))
    return target
