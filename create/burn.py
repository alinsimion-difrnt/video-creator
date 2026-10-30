"""Burn captions onto a finished plate (C12, from the Acme v2 final; create/kit/captions.html).

`create burn <project> --plate film.mp4 [--audio mix.m4a]`: builds a HyperFrames composition with the plate
as a muted <video>, the project's captions.json and the brand's caption style for the frame, renders it,
muxes the audio (the --audio file, else the plate's own), and checks the output has the plate's frame count.
Everything is written to data/create/<project>/render/ (never committed).
"""

from __future__ import annotations

import html
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from create.bundle import fonts, gsap
from create.sketches import hyperframes
from lens.schemas.config import CreateFrame, CreateRender
from lens.schemas.create import Captions, Edl, Framing, Timeline, Tokens

KIT = Path(__file__).parent / "kit"


def _rgba(hex_color: str, alpha: float) -> str:
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r},{g},{b},{alpha:g})"


def caption_vars(tokens: Tokens, frame: CreateFrame) -> dict[str, str]:
    c = tokens.captions
    if c is None:
        raise ValueError(f"the brand has no caption style for the {tokens.frame} frame (video.yaml captions)")
    col = tokens.colors
    fam = tokens.families[c.family]
    band = frame.caption_band
    return {
        "--w": f"{frame.width}px",
        "--h": f"{frame.height}px",
        "--band-cx": f"{(band.x0 + band.x1) / 2:g}px",
        "--band-cy": f"{(band.y0 + band.y1) / 2:g}px",
        "--max-w": f"{c.max_width_px}px",
        "--pad-y": f"{c.padding_px[0]}px",
        "--pad-x": f"{c.padding_px[1]}px",
        "--font": f'"{fam.family}", {fam.fallback}',
        "--weight": str(c.weight),
        "--size": f"{c.size_px:g}px",
        "--lh": f"{c.line_height:g}",
        "--tracking": f"{c.tracking_em:g}em",
        "--transform": "uppercase" if c.uppercase else "none",
        "--text": col[c.text],
        "--bg": _rgba(col[c.background], c.background_alpha) if c.background else "transparent",
        "--radius": f"{c.radius_px}px",
        "--dim": f"{c.dim_opacity:g}",
        "--stroke": col[c.stroke] if c.stroke else "transparent",
        "--stroke-w": f"{c.stroke_px:g}px",
    }


def render_comp(render: CreateRender, comp: Path, frame_format: str = "png") -> Path:
    """Lint and render a HyperFrames project to comp/video.mp4. PNG frame extraction keeps colours exact
    (UI recordings); `frame_format="jpg"` is for camera footage. The extraction cache is off, because it is
    never cleaned up (it reached 25 GB in the cloud sandbox)."""
    hyperframes(render, "telemetry", "disable", cwd=comp)
    args_render = (
        "render",
        ".",
        "-o",
        "video.mp4",
        "--quiet",
        "--video-frame-format",
        frame_format,
        "--frames-cache-dir",
        "off",
    )
    for args in (("lint", "."), args_render):
        res = hyperframes(render, *args, cwd=comp)
        if res.returncode != 0:
            raise RuntimeError(f"hyperframes {args[0]} failed\n{res.stdout[-1500:]}{res.stderr[-1500:]}")
    return comp / "video.mp4"


def chin_at(t: float, edl: Edl, framing: Framing, width: int) -> tuple[float, float] | None:
    """(chin y, face height) in output pixels at edited time `t`, or None without a face."""
    from create.footage.framing import face_box

    box = face_box(t, edl, framing, width)
    return None if box is None else (box[3], box[3] - box[1])


def group_centres(
    captions: Captions,
    tokens: Tokens,
    frame: CreateFrame,
    edl: Edl | None,
    framing: Framing | None,
    gap: float,
    layouts: list[dict[str, Any]] | None = None,
    seam: float | None = None,
    seam_gap: float = 0.0,
) -> list[float]:
    """Vertical centre of each group: the band's centre, pushed down below the presenter's chin (by `gap`
    face-heights) and never past the band's bottom. With a layout sidecar (`create pip`): in split scenes
    just above the seam (`seam_gap` px), on the product's bottom margin and clear of the presenter's head;
    the plain band in bubble scenes."""
    c = tokens.captions
    assert c is not None
    band = frame.caption_band
    half = c.size_px * c.line_height / 2 + c.padding_px[0]
    out = []
    for g in captions.groups:
        y = (band.y0 + band.y1) / 2
        layout = _layout_at(g.start, layouts)
        if layout == "split" and seam is not None:
            out.append(round(seam - seam_gap - half, 1))
            continue
        chin = chin_at(g.start, edl, framing, frame.width) if edl and framing and layout == "full" else None
        if chin is not None:
            y = max(y, chin[0] + gap * chin[1] + half)
        out.append(round(min(y, band.y1 - half), 1))
    return out


def _layout_at(t: float, layouts: list[dict[str, Any]] | None) -> str:
    for sc in layouts or []:
        if sc["start_s"] - 1e-6 <= t < sc["end_s"]:
            return str(sc["layout"])
    return "full"


def caption_comp(
    tokens: Tokens, frame: CreateFrame, captions: Captions, duration: float, lang: str,
    centres: list[float] | None = None,
) -> str:  # fmt: skip
    """The composition HTML: plate + caption track, styled from the tokens."""
    c = tokens.captions
    assert c is not None
    v = caption_vars(tokens, frame)
    data: dict[str, Any] = {
        "duration": round(duration, 6),
        "kind": c.kind,
        "has_bg": c.background is not None,
        "max_width": c.max_width_px,
        "dim": c.dim_opacity,
        "text": tokens.colors[c.text],
        "active": tokens.colors[c.active],
        "groups": [
            g.model_dump() | ({"cy": centres[i]} if centres else {}) for i, g in enumerate(captions.groups)
        ],
    }
    out = (KIT / "captions.html").read_text()
    for key, val in {
        "{{LANG}}": html.escape(lang),
        "{{CSS_VARS}}": ":root{" + ";".join(f"{k}:{x}" for k, x in v.items()) + "}",
        "{{W}}": str(frame.width),
        "{{H}}": str(frame.height),
        "{{DURATION}}": f"{duration:.6f}",
        "{{DATA}}": json.dumps(data, ensure_ascii=False).replace("</", "<\\/"),
    }.items():
        out = out.replace(key, val)
    return out


def mux(video: Path, sound: Path | None, duration: float, target: Path) -> None:
    """`video` with the audio of `sound`, cut to `duration`. Audio that already covers the video is copied:
    every AAC re-encode adds peak overshoot, so the level F6 finished stays as it was. Shorter audio is
    padded with silence (one re-encode)."""
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(video)]
    if sound is not None:
        cmd += ["-i", str(sound), "-map", "0:v", "-map", "1:a"]
        cmd += (
            ["-c:a", "copy"]
            if audio_seconds(sound) >= duration
            else ["-af", "apad", "-c:a", "aac", "-b:a", "192k"]
        )
        cmd += ["-t", f"{duration:.6f}"]  # the video's length wins
    cmd += ["-c:v", "copy", "-movflags", "+faststart", str(target)]
    subprocess.run(cmd, check=True)


def audio_seconds(path: Path) -> float:
    """Length of the first audio stream (0 when there is none)."""
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=duration",
         "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=True,
    )  # fmt: skip
    v = r.stdout.strip()
    return float(v) if v and v != "N/A" else 0.0


def probe(path: Path) -> tuple[int, float, bool]:
    """(video frames, fps, has audio) of a media file."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-count_packets", "-show_entries",
         "stream=codec_type,nb_read_packets,r_frame_rate", "-of", "json", str(path)],
        check=True, capture_output=True, text=True,
    ).stdout  # fmt: skip
    streams = json.loads(out)["streams"]
    video = next(s for s in streams if s["codec_type"] == "video")
    num, den = (int(x) for x in video["r_frame_rate"].split("/"))
    return int(video["nb_read_packets"]), num / den, any(s["codec_type"] == "audio" for s in streams)


def run_burn(
    root: Path, project: str, plate: Path, render: CreateRender, frames_cfg: dict[str, CreateFrame],
    audio: Path | None = None, out: Path | None = None, lang: str = "en", face_gap: float = 0.35,
    seam_gap: float = 0.0,
) -> Path:  # fmt: skip
    base = root / "projects" / project
    tokens = Tokens.model_validate(json.loads((base / "tokens.json").read_text()))
    captions = Captions.model_validate(json.loads((base / "captions.json").read_text()))
    timeline = Timeline.model_validate(json.loads((base / "timeline.json").read_text()))
    frame = frames_cfg[tokens.frame]
    edl_path, framing_path = base / "edl.json", base / "framing.json"
    centres = None
    lay: dict[str, Any] = {}
    if edl_path.exists() and framing_path.exists():  # presenter video: keep captions below the face
        edl = Edl.model_validate(json.loads(edl_path.read_text()))
        framing = Framing.model_validate(json.loads(framing_path.read_text()))
        side = plate.with_suffix(".layout.json")
        lay = json.loads(side.read_text()) if side.exists() else {}
        centres = group_centres(
            captions, tokens, frame, edl, framing, face_gap, lay.get("scenes"), lay.get("seam"), seam_gap
        )
    n, fps, plate_audio = probe(plate)
    if abs(fps - timeline.fps) > 1e-6:
        raise ValueError(f"plate is {fps:g} fps, the timeline is {timeline.fps}")
    duration = n / timeline.fps
    comp = root / "data" / "create" / project / "render" / "captions"
    (comp / "assets" / "fonts").mkdir(parents=True, exist_ok=True)
    cache = root / "data" / "create" / "_cache"
    shutil.copy(gsap(cache), comp / "assets" / "gsap.min.js")
    css, files = fonts(cache, tokens.fonts_css)
    for f in files:
        shutil.copy(f, comp / "assets" / "fonts" / f.name)
    (comp / "assets" / "fonts.css").write_text(css)
    shutil.copy(plate, comp / "plate.mp4")
    (comp / "index.html").write_text(caption_comp(tokens, frame, captions, duration, lang, centres))
    render_comp(render, comp)
    target = out or root / "data" / "create" / project / "render" / f"{project}-captioned.mp4"
    mux(comp / "video.mp4", audio or (plate if plate_audio else None), duration, target)
    got, _, _ = probe(target)
    if got != n:
        raise RuntimeError(f"frame count mismatch: output {got}, plate {n}")
    c = tokens.captions
    assert c is not None

    def on_seam(t: float) -> bool:
        return lay.get("seam") is not None and _layout_at(t, lay.get("scenes")) == "split"

    meta: dict[str, Any] = {  # read by `create qa`: what is on screen, beyond the plate
        "captions": [
            {"start": g.start, "end": g.end, "words": len(g.words), "text": " ".join(w.w for w in g.words),
             "cy": centres[i] if centres else (frame.caption_band.y0 + frame.caption_band.y1) / 2,
             "zone": "seam" if on_seam(g.start) else "band"}
            for i, g in enumerate(captions.groups)
        ],
        "caption_half_height": c.size_px * c.line_height / 2 + c.padding_px[0],
    }  # fmt: skip
    for kind in ("layout", "overlays"):  # carried over from the plate (create pip, create overlay)
        side = plate.with_suffix(f".{kind}.json")
        if side.exists():
            meta[kind] = json.loads(side.read_text())
    target.with_suffix(".meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False))
    return target
