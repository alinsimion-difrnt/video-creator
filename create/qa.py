"""C13 `create qa`: a finished video checked against its destination's rules (TikTok, Reels, Shorts ...).

Measured on the file (ffprobe, ebur128) and on what the pipeline put on screen (the render's .meta.json
from `create burn`, with the layout and overlay sidecars it carried over, plus the project's timeline, edit
and framing). Thresholds: config create.qa, targets.loudness, create.design.frames.
Writes projects/<p>/qa/<name>.json.
"""

from __future__ import annotations

import json
import struct
from datetime import UTC, datetime
from itertools import pairwise
from pathlib import Path
from typing import Any

import yaml

from create.footage.media import loudness, probe, video_stream
from create.footage.overlays import face_box_at
from lens import __version__
from lens.hashing import cache_key
from lens.schemas.common import Annotator, Provenance
from lens.schemas.config import CreateFrame, LensConfig
from lens.schemas.create import Edl, Framing, QaCheck, QaReport, Timeline

STAGE = "c13_qa"


def moov_first(path: Path) -> bool:
    """True when the MP4's index (moov) comes before the media data (faststart: plays while downloading)."""
    with path.open("rb") as f:
        while True:
            head = f.read(8)
            if len(head) < 8:
                return False
            size, kind = struct.unpack(">I4s", head)
            if kind == b"moov":
                return True
            if kind == b"mdat":
                return False
            if size == 0:  # the box runs to the end of the file: no moov after it
                return False
            if size == 1:
                size = struct.unpack(">Q", f.read(8))[0] - 8
            f.seek(size - 8, 1)


def visual_events(meta: dict[str, Any], edl: Edl | None) -> list[float]:
    """Times something changes on screen: cuts in the edit, layout changes, graphics in and out."""
    ev: list[float] = []
    if edl is not None:
        ev += [s.rec_in / edl.fps for s in edl.segments[1:]]
    scenes = (meta.get("layout") or {}).get("scenes", [])
    ev += [b["start_s"] for a, b in pairwise(scenes) if a["layout"] != b["layout"]]
    for it in (meta.get("overlays") or {}).get("items", []):
        ev += [it["t0"], it["t1"]]
    return sorted(ev)


def _check(cid: str, ok: bool, value: str, target: str, note: str = "") -> QaCheck:
    return QaCheck(id=cid, ok=ok, value=value, target=target, note=note)


def caption_placed(
    cy: float, half: float, frame: CreateFrame, seam: float | None, zone: str = "band"
) -> bool:
    """A caption group sits in its zone: the frame's caption band, the band above the head (`top`), or, in a
    split scene (`seam` = the product's bottom edge), inside the safe area and above the seam."""
    y0, y1 = cy - half, cy + half
    if seam is not None:
        return y1 <= seam + 1 and any(r.y0 - 1 <= y0 and y1 <= r.y1 + 1 for r in frame.safe)
    rect = frame.caption_top if zone == "top" and frame.caption_top is not None else frame.caption_band
    return rect.y0 - 1 <= y0 and y1 <= rect.y1 + 1


def on_body(
    cy: float, half: float, face: tuple[float, float, float, float], hair: float, chin: float | None = None
) -> bool:
    """In a full-frame shot the presenter fills the frame below the top of their head (face box raised by
    `hair` face-heights): a caption that reaches below it sits on the face or the chest. With `chin` (a plan's
    `caption_shirt`, band captions only) the shirt is allowed: the caption must start that many face-heights
    below the chin instead."""
    _, fy0, _, fy1 = face
    if chin is not None:
        return cy - half < fy1 + chin * (fy1 - fy0)
    return cy + half > fy0 - hair * (fy1 - fy0)


def run_qa(root: Path, project: str, video: Path, cfg: LensConfig) -> tuple[Path, QaReport]:
    base = root / "projects" / project
    brief = yaml.safe_load((base / "brief.yaml").read_text())
    destination = brief["destination"]
    _, frame = cfg.create.design.frame_for(destination)
    q = cfg.create.qa
    band_l = cfg.targets.loudness[destination]
    info = probe(video)
    v = video_stream(info)
    a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    duration = float(info["format"]["duration"])
    num, den = (int(x) for x in v["r_frame_rate"].split("/"))
    fps = num / den
    loud = loudness(video)
    meta_path = video.with_suffix(".meta.json")
    meta: dict[str, Any] = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    timeline = Timeline.model_validate(json.loads((base / "timeline.json").read_text()))
    edl = (
        Edl.model_validate(json.loads((base / "edl.json").read_text()))
        if (base / "edl.json").exists()
        else None
    )
    fr_p = base / "framing.json"
    framing = Framing.model_validate(json.loads(fr_p.read_text())) if fr_p.exists() else None
    words = timeline.words
    fast = moov_first(video)
    checks = [
        _check(
            "frame",
            (v["width"], v["height"]) == (frame.width, frame.height),
            f"{v['width']}x{v['height']}",
            f"{frame.width}x{frame.height}",
        ),
        _check(
            "fps",
            abs(fps - timeline.fps) < 1e-3 and v.get("r_frame_rate") == v.get("avg_frame_rate"),
            f"{fps:g} ({v.get('avg_frame_rate')} avg)",
            f"constant {timeline.fps}",
        ),
        _check(
            "codec",
            v["codec_name"] == "h264" and v.get("pix_fmt") == "yuv420p",
            f"{v['codec_name']} {v.get('pix_fmt')}",
            "h264 yuv420p",
        ),
        _check(
            "audio",
            a is not None and a["codec_name"] == "aac" and a.get("sample_rate") == "48000",
            f"{a['codec_name']} {a.get('sample_rate')} Hz" if a else "none",
            "aac 48000 Hz",
        ),
        _check("faststart", fast, "moov first" if fast else "moov last", "moov first"),
        _check("duration", duration <= q.max_duration_s, f"{duration:.1f} s", f"<= {q.max_duration_s:g} s"),
        _check(
            "loudness",
            band_l.min_lufs <= loud["lufs"] <= band_l.max_lufs,
            f"{loud['lufs']:.1f} LUFS",
            f"{band_l.min_lufs:g}..{band_l.max_lufs:g} LUFS ({band_l.source})",
        ),
        _check(
            "true_peak",
            loud["true_peak"] <= q.true_peak_max_db,
            f"{loud['true_peak']:.1f} dBTP",
            f"<= {q.true_peak_max_db:g} dBTP",
        ),
        _check(
            "first_word",
            words[0].start_s <= q.first_word_max_s,
            f"{words[0].start_s:.2f} s",
            f"<= {q.first_word_max_s:g} s",
            "no dead air before the hook",
        ),
    ]
    gaps = [(b.start_s - a_.end_s, a_.end_s) for a_, b in pairwise(words)]
    worst_gap = max(gaps, default=(0.0, 0.0))
    checks.append(
        _check(
            "word_gaps",
            worst_gap[0] <= q.max_word_gap_s,
            f"{worst_gap[0]:.2f} s at {worst_gap[1]:.1f} s",
            f"<= {q.max_word_gap_s:g} s",
        )
    )
    tail = duration - words[-1].end_s
    checks.append(_check("tail", tail <= q.max_tail_s, f"{tail:.2f} s", f"<= {q.max_tail_s:g} s"))
    ev = visual_events(meta, edl)
    first = ev[0] if ev else duration
    checks.append(
        _check(
            "hook_visual",
            first <= q.first_visual_max_s,
            f"{first:.2f} s",
            f"<= {q.first_visual_max_s:g} s",
            "first cut, layout change or graphic",
        )
    )
    marks = [0.0, *[t for t in ev if 0 < t < duration], duration]
    static = max(((b - a_, a_) for a_, b in pairwise(marks)), default=(duration, 0.0))
    checks.append(
        _check(
            "pacing",
            static[0] <= q.max_static_s,
            f"{static[0]:.1f} s from {static[1]:.1f} s",
            f"<= {q.max_static_s:g} s with nothing new on screen",
        )
    )
    caps = meta.get("captions", [])
    half = float(meta.get("caption_half_height", 0))
    band = frame.caption_band
    split_seam = (meta.get("layout") or {}).get("seam")

    def seam_of(c: dict[str, Any]) -> float | None:
        return float(split_seam) if split_seam is not None and c.get("zone") == "seam" else None

    off_band = [
        c for c in caps if not caption_placed(float(c["cy"]), half, frame, seam_of(c), c.get("zone", "band"))
    ]
    scenes = (meta.get("layout") or {}).get("scenes", [])
    hair = cfg.create.footage.reframe.hair_above_face
    shirt = cfg.create.design.caption_face_gap if meta.get("caption_shirt") else None

    def full_at(t: float) -> bool:  # judged at a group's midpoint: the layout most of it plays in
        return next((s["layout"] for s in scenes if s["start_s"] - 1e-6 <= t < s["end_s"]), "full") == "full"

    body_hits = [
        c for c in caps
        if edl is not None and framing is not None and full_at((c["start"] + c["end"]) / 2)
        and on_body(float(c["cy"]), half, face_box_at(c["start"], edl, framing, frame.width, frame.height),
                    hair, shirt if c.get("zone") == "band" else None)
    ]  # fmt: skip
    checks.append(_check("captions_present", bool(caps), f"{len(caps)} groups", ">= 1 group (burned in)"))
    checks.append(
        _check(
            "captions_in_band",
            not off_band,
            f"{len(off_band)} outside",
            "0",
            off_band[0]["text"] if off_band else "",
        )
    )
    checks.append(
        _check(
            "captions_clear_body",
            not body_hits,
            f"{len(body_hits)} on the presenter",
            "0 (Robert: never on the face or chest)",
            body_hits[0]["text"] if body_hits else "",
        )
    )
    bad_ov = []
    for it in (meta.get("overlays") or {}).get("items", []):
        x0, y0, x1, y1 = it["zone"]
        inside = any(r.contains(x0, y0, x1, y1, tol=1) for r in frame.safe)
        fx0, fy0, fx1, fy1 = face_box_at((it["t0"] + it["t1"]) / 2, edl, framing, frame.width, frame.height)
        on_face = x0 < fx1 and x1 > fx0 and y0 < fy1 and y1 > fy0
        # the captions on screen while the graphic is: their band's width, at the height burn or reel chose
        on_caps = any(
            c["start"] < it["t1"]
            and c["end"] > it["t0"]
            and y0 < c["cy"] + half
            and y1 > c["cy"] - half
            and x0 < band.x1
            and x1 > band.x0
            for c in caps
        )
        if not inside or on_face or on_caps:
            bad_ov.append(it["title"])
    checks.append(_check("overlays_placed", not bad_ov, f"{len(bad_ov)} misplaced", "0", ", ".join(bad_ov)))
    report = QaReport(
        provenance=Provenance(
            tool_version=__version__,
            stage=STAGE,
            annotator=Annotator.CODE,
            input_hash=cache_key({"video": str(video), "size": video.stat().st_size, "meta": meta}),
            created_at=datetime.now(UTC),
        ),
        project=project,
        video=str(video),
        destination=destination,
        checks=checks,
        ok=all(c.ok for c in checks),
    )
    out = base / "qa" / f"{video.stem}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(report.model_dump_json(indent=1) + "\n")
    return out, report
