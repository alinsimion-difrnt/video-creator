"""C10 music: a bed built for the video (phase2-plan section 7), one Eleven Music chunk per scene.

`create music <project>` turns the timeline into a composition plan (config `create.music`: the chosen
funk-pop style, a section text per scene position), generates it once (cached by the plan's hash, so a rerun
costs no credits) and checks the bed's level per second for dropouts (a generated bed once went silent for
6 s at a section boundary). Writes data/create/<project>/music/bed.mp3 and bed.json.
"""

from __future__ import annotations

import json
import os
import subprocess
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from create.direction import film_s
from lens.hashing import cache_key
from lens.schemas.config import CreateMusic, LensConfig
from lens.schemas.create import Brief, Timeline

API = "https://api.elevenlabs.io/v1/music?output_format={fmt}"


def music_plan(timeline: Timeline, dur: float, m: CreateMusic) -> dict[str, Any]:
    """One chunk per scene (clipped to the film), short scenes merged into the one before."""
    spans: list[list[float]] = []
    for sc in timeline.scenes:
        a, z = sc.start_s, min(sc.end_s, dur)
        if a >= dur:
            break
        if spans and (z - a) * 1000 < m.min_chunk_ms:
            spans[-1][1] = z
        else:
            spans.append([a, z])
    if len(spans) > 1 and (spans[0][1] - spans[0][0]) * 1000 < m.min_chunk_ms:
        spans[1][0] = spans.pop(0)[0]
    ms = [round(z * 1000) - round(a * 1000) for a, z in spans]
    ms[-1] += round(dur * 1000) - sum(ms)
    chunks = []
    for i, d in enumerate(ms):
        if d > m.max_chunk_ms:
            raise ValueError(f"scene chunk {i} is {d / 1000:g} s, over the API's {m.max_chunk_ms / 1000:g} s")
        text = m.sections.first if i == 0 else m.sections.last if i == len(ms) - 1 else m.sections.middle
        chunk: dict[str, Any] = {"text": text, "duration_ms": d, "context_adherence": "high"}
        if i == 0:
            chunk["positive_styles"] = m.positive_styles
            chunk["negative_styles"] = m.negative_styles
        chunks.append(chunk)
    return {"chunks": chunks}


def levels_db(path: Path) -> list[float]:
    """RMS level of each second (mono, 8 kHz), in dBFS."""
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", "8000", "-f", "f32le", "-"],
        capture_output=True,
        check=True,
    ).stdout
    a = np.frombuffer(raw, np.float32)
    return [
        float(20 * np.log10(np.sqrt(np.mean(a[i : i + 8000] ** 2)) + 1e-9)) for i in range(0, len(a), 8000)
    ]


def dropouts(levels: list[float], dur: float, m: CreateMusic) -> list[int]:
    """Seconds quieter than `dropout_db` before the bed's ending."""
    return [i for i, db in enumerate(levels) if i < dur - m.ending_s and db < m.dropout_db]


def post_music(body: dict[str, Any], m: CreateMusic) -> bytes:
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        raise RuntimeError("ELEVENLABS_API_KEY is not set")
    req = urllib.request.Request(
        API.format(fmt=m.output_format),
        data=json.dumps(body).encode(),
        headers={"xi-api-key": key, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        return bytes(resp.read())


def plan_for(root: Path, project: str, cfg: LensConfig) -> tuple[dict[str, Any], float]:
    base = root / "projects" / project
    brief = Brief.model_validate(yaml.safe_load((base / "brief.yaml").read_text()))
    timeline = Timeline.model_validate_json((base / "timeline.json").read_text())
    dur = film_s(brief, timeline, cfg.create.motion.final_hold_s)
    return {
        "composition_plan": music_plan(timeline, dur, cfg.create.music),
        "model_id": cfg.create.music.model_id,
    }, dur


def run_music(
    root: Path,
    project: str,
    cfg: LensConfig,
    post: Callable[[dict[str, Any], CreateMusic], bytes] = post_music,
) -> tuple[Path, list[int]]:
    """Generate (or reuse) the bed; returns its path and any dropout seconds."""
    m = cfg.create.music
    body, dur = plan_for(root, project, cfg)
    out = root / "data" / "create" / project / "music"
    out.mkdir(parents=True, exist_ok=True)
    bed, side = out / "bed.mp3", out / "bed.json"
    key = cache_key(body)
    cached = side.exists() and json.loads(side.read_text()).get("plan_hash") == key and bed.exists()
    if not cached:
        bed.write_bytes(post(body, m))
    holes = dropouts(levels_db(bed), dur, m)
    side.write_text(
        json.dumps({"plan_hash": key, "plan": body, "duration_s": dur, "dropouts_s": holes}, indent=1)
    )
    return bed, holes
