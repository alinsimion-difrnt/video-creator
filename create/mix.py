"""C12 mix (motion route, ADR 0032): the graded render + narration + music bed + the build's SFX.

The bed sits at `bed_db` and is ducked under the voice (sidechain), each SFX cue is placed at its time and
gain (panned toward its reveal when the cue has an `x`), and the whole mix is normalised to the middle of the
destination's loudness band with the true peak kept under its ceiling. Writes
data/create/<project>/motion/final/<project>.mp4 (the render's video, copied).
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import yaml

from create.direction import film_s
from lens.schemas.config import LensConfig
from lens.schemas.create import Brief, SfxCue, Timeline


def pan(x: float, width: float) -> float:
    """Stereo balance (-1 left .. 1 right) for a reveal centred at `x` (share of the frame width)."""
    return round((2 * x - 1) * width, 3)


def run_mix(root: Path, project: str, cfg: LensConfig) -> tuple[Path, list[str]]:
    """Returns the final file and notes (what was missing)."""
    base = root / "projects" / project
    data = root / "data" / "create" / project
    brief = Brief.model_validate(yaml.safe_load((base / "brief.yaml").read_text()))
    timeline = Timeline.model_validate_json((base / "timeline.json").read_text())
    dur = film_s(brief, timeline, cfg.create.motion.final_hold_s)
    mx = cfg.create.mix
    target = cfg.targets.loudness[brief.destination]
    lufs = (target.min_lufs + target.max_lufs) / 2
    tp = target.max_true_peak_dbtp - mx.true_peak_margin_db
    render = data / "motion" / "render"
    video, voice, bed = render / "video.mp4", data / "timing" / "narration.mp3", data / "music" / "bed.mp3"
    for need, stage in ((video, "create grade"), (voice, "create timing")):
        if not need.exists():
            raise FileNotFoundError(f"{need.relative_to(root)} is missing; run `{stage} {project}`")
    sfx_path = base / "motion" / "sfx.json"
    cues = [SfxCue.model_validate(c) for c in json.loads(sfx_path.read_text())] if sfx_path.exists() else []
    notes: list[str] = []

    fmt = "aformat=sample_rates=48000:channel_layouts=stereo"
    inputs = ["-i", str(video), "-i", str(voice)]
    chains = [f"[1:a]{fmt},apad,atrim=0:{dur}"]
    labels = []
    if bed.exists():
        inputs += ["-i", str(bed)]
        chains[0] += ",asplit=2[v][key]"
        chains += [
            f"[2:a]{fmt},apad,atrim=0:{dur},volume={mx.bed_db}dB,"
            f"afade=t=out:st={max(0.0, dur - mx.bed_fade_s)}:"
            f"d={mx.bed_fade_s}[bedq]",
            f"[bedq][key]sidechaincompress={mx.duck}[bed]",
        ]
        labels += ["[v]", "[bed]"]
    else:
        chains[0] += "[v]"
        labels.append("[v]")
        notes.append(
            f"no music bed at {bed.relative_to(root)} (run `create music {project}`); voice and SFX only"
        )
    for i, c in enumerate(cues):
        f = render / "assets" / "sfx" / f"{c.sfx}.mp3"
        if not f.exists():
            notes.append(f"SFX {c.sfx!r} is not in the render bundle; skipped")
            continue
        idx = inputs.count("-i")  # this cue's input index
        inputs += ["-i", str(f)]
        ms = round(c.t * 1000)
        bal = "" if c.x is None else f",stereotools=balance_out={pan(c.x, mx.sfx_pan_width)}"
        chains.append(f"[{idx}:a]{fmt},volume={c.gain_db}dB{bal},adelay={ms}|{ms}[s{i}]")
        labels.append(f"[s{i}]")
    chains.append(
        "".join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=first,atrim=0:{dur},"
        f"loudnorm=I={lufs}:TP={tp}:LRA={mx.lra}[mix]"
    )
    out = data / "motion" / "final" / f"{project}.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            *inputs,
            "-filter_complex",
            ";".join(chains),
            "-map",
            "0:v",
            "-map",
            "[mix]",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            f"{mx.audio_kbps}k",
            "-ar",
            "48000",
            "-t",
            f"{dur}",
            str(out),
        ],
        check=True,
    )
    return out, notes
