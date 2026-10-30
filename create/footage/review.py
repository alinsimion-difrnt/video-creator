"""`create review`: what a fresh-eyes reviewer needs to judge a finished presenter video (ADR 0026).

Writes, next to nothing else (data/create/<p>/review/<video>/):
- sheet.png: one frame every `every_s` seconds, tiled 11 wide (the whole video at a glance);
- motion.png: 8 frames 0.1 s apart from three widget entrances (is it a build or a fade?);
- brief.md: the rubric, the platform's UI zones, the client's notes (projects/<p>/notes.md if present) and the
  file paths. A reviewer with no other context (the review-reel skill) reads only these.
The reviewer's report is advice: fixes still go through the plan, `create reel --check` and `create qa`.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from lens.schemas.config import CreateFrame

RUBRIC = (
    "relevance of the graphics to the words",
    "motion and energy",
    "caption placement and legibility (never on the face or chest)",
    "visual polish and brand consistency",
    "platform safe zones",
    "pacing and dead moments",
    "flow: cards hand over into each other and the top half moves with the cuts (ADR 0033)",
)


def sheet(video: Path, out: Path, every_s: float, cols: int = 11, tile: tuple[int, int] = (216, 384)) -> Path:
    dur = float(
        subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
            capture_output=True, text=True, check=True,
        ).stdout
    )  # fmt: skip
    rows = max(1, -(-int(dur / every_s) // cols))
    w, h = tile
    # round=up: the default (near) samples each tile ~half an interval late, so the stamps were 1.25 s early
    stamp = (  # each frame shows its time, so a reviewer can say where without counting tiles
        "drawtext=font=DejaVu Sans:text='%{pts\\:hms}':x=6:y=6:fontsize=20:fontcolor=white"
        ":box=1:boxcolor=black@0.6:boxborderw=4"
    )
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vf",
         f"fps=1/{every_s:g}:round=up,scale={w}:{h},setpts=N*{every_s:g}/TB,{stamp},tile={cols}x{rows}",
         "-frames:v", "1", str(out)],
        check=True,
    )  # fmt: skip
    return out


def crops(video: Path, items: list[dict[str, Any]], out: Path, n: int = 8, height: int = 420) -> Path | None:
    """Each widget at full resolution once built (60% through its time), side by side: text size can be
    judged here, not on the shrunk sheet."""
    picks = sorted(items, key=lambda i: float(i["t0"]))
    if len(picks) > n:
        picks = [picks[round(k * (len(picks) - 1) / (n - 1))] for k in range(n)]
    if not picks:
        return None
    inputs: list[str] = []
    chains = []
    # zones are frame pixels (1080 wide); a --draft render is smaller: scale them to the video
    width = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width",
         "-of", "csv=p=0", str(video)], capture_output=True, text=True, check=True,
    ).stdout  # fmt: skip
    k_draft = int(width) / 1080
    for k, it in enumerate(picks):
        x0, y0, x1, y1 = (int(float(v) * k_draft) for v in it["zone"])
        t = float(it["t0"]) + 0.6 * (float(it["t1"]) - float(it["t0"]))
        inputs += ["-ss", f"{t:.2f}", "-i", str(video)]
        chains.append(f"[{k}:v]trim=end_frame=1,crop={x1 - x0}:{y1 - y0}:{x0}:{y0},scale=-2:{height}[c{k}]")
    stack = "".join(f"[c{k}]" for k in range(len(picks)))
    graph = ";".join(chains) + f";{stack}hstack=inputs={len(picks)}" if len(picks) > 1 else chains[0][:-4]
    cmd = ["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", graph, "-frames:v", "1", str(out)]
    subprocess.run(cmd,
                   check=True)  # fmt: skip
    return out


def edit_type(meta: dict[str, Any]) -> str:
    """What kind of edit this is, in words, from the sidecar's layout blocks."""
    scenes = (meta.get("layout") or {}).get("scenes", [])
    secs: dict[str, float] = {}
    for sc in scenes:
        secs[sc["layout"]] = secs.get(sc["layout"], 0.0) + float(sc["end_s"]) - float(sc["start_s"])
    if secs.get("split"):
        split = f"{secs['split']:.0f} s"
        return f"LAYOUT edit: product area on top, presenter below, for {split}; full shots between."
    cut = sum(1 for sc in scenes if sc["layout"] == "off")
    extra = f", with {cut} full-screen product cutaways ({secs.get('off', 0):.0f} s in all)" if cut else ""
    return f"OVERLAY edit: widgets over the presenter's own video{extra}."


def entrance_times(meta: dict[str, Any], n: int = 3) -> list[float]:
    """Entrances of `n` widgets spread over the video (second, middle, last)."""
    items: list[dict[str, Any]] = []
    for group in ("overlays", "product"):
        items += (meta.get(group) or {}).get("items", [])
    t0s = sorted(float(i["t0"]) for i in items)
    if len(t0s) <= n:
        return t0s
    return [t0s[1], t0s[len(t0s) // 2], t0s[-1]]


def motion(video: Path, times: list[float], out: Path, frames: int = 8, step: float = 0.1) -> Path:
    ts = [round(t + k * step, 2) for t in times for k in range(frames)]
    sel = "+".join(f"between(t,{t - 0.016},{t + 0.017})" for t in ts)
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vf",
         f"select='{sel}',scale=216:384,tile={frames}x{max(1, len(times))}", "-vsync", "vfr",
         "-frames:v", "1", str(out)],
        check=True,
    )  # fmt: skip
    return out


def brief(
    video: Path,
    files: dict[str, Path],
    frame: CreateFrame,
    notes: str,
    every_s: float,
    kind: str = "",
    strips: list[str] | None = None,
    crop_names: list[str] | None = None,
) -> str:
    core, wide = frame.safe[0], max(frame.safe, key=lambda r: r.x1)
    lines = [
        f"# Review brief: {video.name}",
        "",
        "You are a senior short-form video editor. Be blunt: find what is still weak.",
        "",
        f"**{kind}**" if kind else "",
        "",
        "## Files (view each; open nothing else)",
        f"- contact sheet, one frame every {every_s:g} s, each stamped with its time: {files['sheet']}",
        f"- motion strips, 8 frames 0.1 s apart at widget entrances: {files['motion']}",
        *[f"  - row {k + 1}: {s}" for k, s in enumerate(strips or [])],
        *(
            [
                f"- full-resolution crops of widgets once built (judge text size here): {files['crops']}",
                "  - left to right: " + "; ".join(crop_names or []),
            ]
            if "crops" in files
            else []
        ),
        *(
            [f"- settled frames, stamped with their times (each beat once it has landed): {files['settled']}"]
            if "settled" in files
            else []
        ),
        "",
        "## House rules",
        "- Captions never on the presenter's face or chest (the client's rule).",
        "- Widgets never on the face. In an overlay edit they may sit on the chest (that is the overlay",
        "  type); say so only if one hides something that matters.",
        "",
        "## Platform UI",
        f"- Critical content inside x {core.x0}-{core.x1}, y {core.y0}-{core.y1} "
        f"(x up to {wide.x1} above y {wide.y1}).",
        f"- Top tabs cover y < {core.y0}; the action rail covers x > {core.x1} below y {wide.y1}; "
        f"the description starts near y {core.y1}.",
        "",
        "## Client notes",
        notes.strip() or "(none)",
        "",
        "## Report",
        "Score 1-10 for each, and overall:",
        *[f"- {r}" for r in RUBRIC],
        "Then the remaining problems, most important first, each with its frame (row/column) on the sheet,",
        "and whether you would post it as is. Under 500 words.",
    ]
    return "\n".join(lines) + "\n"


def settled(video: Path, times: list[float], out: Path) -> Path:
    """Frame-exact frames at `times`, stamped, on one sheet: each beat once it has landed (a panel's scenes
    cross-fade, so the every-few-seconds sheet can catch them mid-way)."""
    from create.footage.panel import stills_sheet

    frames = out / "settled"
    shutil.rmtree(frames, ignore_errors=True)
    frames.mkdir(parents=True)
    num, den = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate", "-of",
         "csv=p=0", str(video)], capture_output=True, text=True, check=True,
    ).stdout.strip().split("/")  # fmt: skip
    fps = float(num) / float(den or 1)
    probe = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)]
    dur = float(subprocess.run(probe, capture_output=True, text=True, check=True).stdout)
    late = [t for t in times if t >= dur]
    if late:
        raise ValueError(
            f"--at {', '.join(f'{t:g}' for t in late)}: past the end of {video.name} ({dur:.2f} s)"
        )
    paths = []
    for k, t in enumerate(times):
        paths.append(frames / f"{k:02d}.png")
        # -ss gives the first frame starting at or after it: aim half a frame before the frame holding t
        seek = max(0.0, (int(t * fps + 1e-6) - 0.5) / fps)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{seek:.6f}", "-i", str(video),
                        "-frames:v", "1", str(paths[-1])], check=True)  # fmt: skip
    return stills_sheet(paths, times, out / "settled.png")


def run_review(
    root: Path,
    project: str,
    video: Path,
    frame: CreateFrame,
    every_s: float = 2.5,
    at: list[float] | None = None,
) -> Path:
    out = root / "data" / "create" / project / "review" / video.stem
    out.mkdir(parents=True, exist_ok=True)
    meta_p = video.with_suffix(".meta.json")
    meta = json.loads(meta_p.read_text()) if meta_p.exists() else {}
    files = {"sheet": sheet(video, out / "sheet.png", every_s)}
    if at:
        files["settled"] = settled(video, at, out)
    times = entrance_times(meta)
    if times:
        files["motion"] = motion(video, times, out / "motion.png")
    items: list[dict[str, Any]] = []
    for group in ("overlays", "product"):
        items += (meta.get(group) or {}).get("items", [])
    by_t0 = {round(float(i["t0"]), 3): i for i in items}
    strips = [f"{by_t0.get(round(t, 3), {}).get('title', 'widget')} from {t:.1f} s" for t in times]
    crop = crops(video, items, out / "crops.png")
    picked = sorted(items, key=lambda i: float(i["t0"]))
    if len(picked) > 8:
        picked = [picked[round(k * (len(picked) - 1) / 7)] for k in range(8)]
    if crop is not None:
        files["crops"] = crop
    notes_p = root / "projects" / project / "notes.md"
    text = brief(video, files | {"motion": files.get("motion", Path("(no widgets)"))}, frame,
                 notes_p.read_text() if notes_p.exists() else "", every_s, edit_type(meta), strips,
                 [f"{i['title']} ({float(i['t0']):.1f} s)" for i in picked])  # fmt: skip
    (out / "brief.md").write_text(text)
    return out
