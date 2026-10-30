"""A phone page where Robert corrects a presenter video himself (`create edits <p> --page`).

He watches the render he got, and per shot sees the whole camera frame with the crop the video shows: Wider
/ Tighter, arrows or a drag move it, with the result beside it. He can change the plan's zooms (the push-in,
remove a quick zoom, rescale a held zoom) and pin notes to a time. The page answers with values (JSON) that
`create edits <p> --apply` stores in projects/<p>/edits.yaml, where F5 and `create reel` use them exactly.

One self-contained HTML file, no network: a still per shot from the master and the watched render shrunk
(config create.footage.edit_page), so it can be published as an Artifact. Never committed (data/).
"""

from __future__ import annotations

import base64
import html
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from create.footage.edits import load_edits, load_plan
from create.footage.reframe import EYES_IN_FACE
from lens.schemas.config import FootageEditPage, LensConfig
from lens.schemas.create import Edits, Edl, Footage, Framing, ReelPlan, Timeline

KIT = Path(__file__).resolve().parent.parent / "kit"


def shot_rows(edl: Edl, framing: Framing, footage: Footage, edits: Edits) -> list[dict[str, Any]]:
    """Each edit segment as the page edits it: its span on the video, its crop now and the edit behind it."""
    sizes = {t.id: (t.width, t.height) for t in footage.takes}
    by_key = {(e.take, e.src_in): e for e in edits.shots}
    rows = []
    for s, f in zip(edl.segments, framing.segments, strict=True):
        e = by_key.get((s.take, s.src_in))
        t0 = s.rec_in / edl.fps
        rows.append({
            "k": f.segment, "take": s.take, "src_in": s.src_in,
            "t0": round(t0, 3), "t1": round(t0 + (s.src_out - s.src_in) / edl.fps, 3),
            "mid": round((s.src_in + s.src_out) / 2 / edl.fps, 3),  # master seconds, for the still
            "src_w": sizes[s.take][0], "src_h": sizes[s.take][1],
            "face": f.face, "crop": f.full.model_dump(),
            "zoom": e.zoom if e else f.zoom, "dx": e.dx if e else 0.0, "dy": e.dy if e else 0.0,
        })  # fmt: skip
    return rows


def plan_marks(plan: ReelPlan, timeline: Timeline) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """The plan's quick zooms and held zooms on the video's clock, named by their word."""
    words = {w.i: w for w in timeline.words}
    punches = [
        {"word": i, "t0": round(words[i].start_s, 3), "t1": round(words[i].end_s, 3), "text": words[i].text}
        for i in plan.punches
        if i in words
    ]
    zooms = [
        {"word": z.word, "until": z.until, "t0": round(words[z.word].start_s, 3),
         "t1": round(words[z.until].start_s, 3), "text": words[z.word].text, "scale": z.scale}
        for z in plan.zooms
        if z.word in words and z.until in words
    ]  # fmt: skip
    return punches, zooms


def _data_uri(path: Path, mime: str) -> str:
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


def still(master: Path, t: float, cfg: FootageEditPage, tmp: Path) -> str:
    out = tmp / f"s{len(list(tmp.iterdir()))}.jpg"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", str(master), "-frames:v", "1",
         "-vf", f"scale={cfg.still_width}:-2", "-q:v", str(cfg.still_quality), str(out)],
        check=True,
    )  # fmt: skip
    return _data_uri(out, "image/jpeg")


def proxy(video: Path, cfg: FootageEditPage, tmp: Path) -> Path:
    out = tmp / "watch.mp4"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vf", f"scale=-2:{cfg.video_height}",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", str(cfg.video_crf), "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", f"{cfg.audio_kbps}k", "-movflags", "+faststart", str(out)],
        check=True,
    )  # fmt: skip
    return out


def page(data: dict[str, Any]) -> str:
    out = (KIT / "edit.html").read_text()
    for key, val in {
        "{{PROJECT}}": html.escape(str(data["project"])),
        "{{DATA}}": json.dumps(data, ensure_ascii=False).replace("</", "<\\/"),
    }.items():
        out = out.replace(key, val)
    return out


def run_edit_page(
    root: Path,
    project: str,
    cfg: LensConfig,
    plan_path: Path | None = None,
    video: Path | None = None,
    out: Path | None = None,
) -> tuple[Path, list[str]]:
    """Write data/create/<p>/edit.html; returns it with warnings (a video left out for size)."""
    base = root / "projects" / project
    ec = cfg.create.footage.edit_page
    edl = Edl.model_validate(json.loads((base / "edl.json").read_text()))
    framing = Framing.model_validate(json.loads((base / "framing.json").read_text()))
    footage = Footage.model_validate(json.loads((base / "footage.json").read_text()))
    timeline = Timeline.model_validate(json.loads((base / "timeline.json").read_text()))
    plan_file = plan_path or base / "reel.yaml"
    plan = load_plan(base, plan_file) if plan_file.exists() else None
    rows = shot_rows(edl, framing, footage, load_edits(base))
    masters = {t.id: root / t.master for t in footage.takes}
    warnings: list[str] = []
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for r in rows:
            r["still"] = still(masters[r["take"]], r["mid"], ec, tmp)
        clip = None
        if video is not None:
            small = proxy(video, ec, tmp)
            mb = small.stat().st_size / 1e6
            if mb > ec.max_mb:
                warnings.append(f"video left out: {mb:.1f} MB shrunk, over edit_page.max_mb {ec.max_mb}")
            else:
                clip = _data_uri(small, "video/mp4")
    punches, zooms = plan_marks(plan, timeline) if plan else ([], [])
    data = {
        "project": project, "plan": plan_file.name if plan else None,
        "duration": round(edl.duration_frames / edl.fps, 3), "out_w": framing.width, "out_h": framing.height,
        "eye_line": cfg.create.footage.reframe.eye_line, "eyes_in_face": EYES_IN_FACE,
        "zoom_step": ec.zoom_step, "max_zoom": ec.max_zoom, "nudge": ec.nudge,
        "push": plan.push if plan else 1.0, "punch_scale": cfg.create.footage.reel.punch_scale,
        "punches": punches, "zooms": zooms, "shots": rows, "video": clip,
        "words": [[w.i, round(w.start_s, 2), w.text] for w in timeline.words],
    }  # fmt: skip
    target = out or root / "data" / "create" / project / "edit.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(page(data))
    return target, warnings
