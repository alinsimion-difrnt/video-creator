"""C7 sketches: the settled final frame of every built scene, on one sheet (Robert locks layout and copy).

Frames are taken with `hyperframes snapshot` on the render bundle; the sheet is a PNG grid and an HTML page
with the frames inlined. Everything is written to data/create/<project>/sketches/ (never committed).
"""

from __future__ import annotations

import base64
import html
import json
import re
import shutil
import subprocess
from pathlib import Path

from lens.schemas.config import CreateRender
from lens.schemas.create import Storyboard


def hyperframes(render: CreateRender, *args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    cmd = ["npx", "--yes", f"hyperframes@{render.hyperframes_version}", *args]
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=render.timeout_s, check=False)


def scene_duration(index_html: str) -> float:
    m = re.search(r'data-duration="([\d.]+)"', index_html)
    if not m:
        raise ValueError("scene has no data-duration")
    return float(m.group(1))


def snapshot(bundle: Path, scene: str, render: CreateRender, out: Path) -> Path:
    at = max(0.0, scene_duration((bundle / scene / "index.html").read_text()) - render.sketch_before_end_s)
    tmp = out / f".{scene}"
    if tmp.exists():
        shutil.rmtree(tmp)
    res = hyperframes(
        render,
        "snapshot",
        str(bundle / scene),
        "--at",
        f"{at:.2f}",
        "--no-end",
        "--describe",
        "false",
        "-o",
        str(tmp),
        cwd=bundle,
    )
    pngs = sorted(tmp.glob("*.png"))
    if res.returncode != 0 or not pngs:
        raise RuntimeError(f"{scene}: snapshot failed\n{res.stdout[-800:]}{res.stderr[-800:]}")
    path = out / f"{scene}.png"
    shutil.move(str(pngs[0]), path)
    shutil.rmtree(tmp)
    return path


def sheet_png(frames: list[Path], columns: int, out: Path) -> Path:
    n = len(frames)
    rows = -(-n // columns)
    inputs = [x for f in frames for x in ("-i", str(f))]
    scaled = ";".join(f"[{i}:v]scale=640:360,pad=644:364:2:2:color=0xE5E7EB[v{i}]" for i in range(n))
    blanks = rows * columns - n
    pads = ";".join(f"color=c=white:s=644x364:d=1[b{j}]" for j in range(blanks))
    labels = [f"[v{i}]" for i in range(n)] + [f"[b{j}]" for j in range(blanks)]
    stacks = ";".join(
        f"{''.join(labels[r * columns : (r + 1) * columns])}hstack={columns}[r{r}]" for r in range(rows)
    )
    graph = ";".join(x for x in (scaled, pads, stacks) if x)
    graph += f";{''.join(f'[r{r}]' for r in range(rows))}vstack={rows}" if rows > 1 else ""
    if rows == 1:
        graph = graph.replace("[r0]", "")
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            *inputs,
            "-filter_complex",
            graph,
            "-frames:v",
            "1",
            str(out),
        ],
        check=True,
    )
    return out


def sheet_html(board: Storyboard, frames: dict[str, Path], title: str) -> str:
    cells = []
    for sc in board.scenes:
        if sc.scene not in frames:
            continue
        img = base64.b64encode(frames[sc.scene].read_bytes()).decode()
        cue = html.escape("; ".join(c.do for c in sc.cues[:3]))
        cells.append(
            f'<figure><img alt="{sc.scene}" src="data:image/png;base64,{img}"><figcaption>'
            f"<b>{sc.scene[1:]}</b> {html.escape(sc.archetype.replace('_', ' '))}<span>{cue}</span>"
            "</figcaption></figure>"
        )
    return (
        f"<!doctype html><meta charset=utf-8><title>{html.escape(title)}</title><style>"
        "body{margin:24px;font:14px/1.4 system-ui;background:#F5F7FA;color:#3E0863}"
        "main{display:grid;grid-template-columns:repeat(auto-fill,minmax(420px,1fr));gap:20px}"
        "figure{margin:0;background:#fff;border:1px solid #E5E7EB;border-radius:12px;overflow:hidden}"
        "img{display:block;width:100%}figcaption{padding:10px 14px}"
        "figcaption span{display:block;color:#5F6B7A}"
        f"</style><h1>{html.escape(title)}</h1><main>{''.join(cells)}</main>"
    )


def run_sketches(root: Path, project: str, render: CreateRender) -> tuple[Path, Path]:
    bundle = root / "data" / "create" / project / "bundle"
    out = root / "data" / "create" / project / "sketches"
    out.mkdir(parents=True, exist_ok=True)
    hyperframes(render, "telemetry", "disable", cwd=bundle)
    board = Storyboard.model_validate(
        json.loads((root / "projects" / project / "storyboard.json").read_text())
    )
    frames = {
        sc.scene: snapshot(bundle, sc.scene, render, out)
        for sc in board.scenes
        if (bundle / sc.scene).is_dir()
    }
    png = sheet_png([frames[s] for s in sorted(frames)], render.sketch_columns, out / "sheet.png")
    page = out / "sheet.html"
    page.write_text(sheet_html(board, frames, f"{project} sketches"))
    return png, page
