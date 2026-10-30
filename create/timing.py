"""C5 timing: scene bounds from the real voice, real silence between scenes, every word on one clock.

Scene k starts where scene k-1 ends. The first scene opens with the pre-roll (music before the first
word); every scene ends `scene_tail_s` after its audio, the last one `close_tail_s` after it. Silence is
placed in the edit rather than asked of the voice (ADR 0018: pauses ran short).
"""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import yaml

from lens import __version__
from lens.hashing import cache_key
from lens.schemas.common import Annotator, Provenance
from lens.schemas.config import CreateTiming
from lens.schemas.create import Brief, Script, Timeline, TimelineScene, TimelineWord, Voice

STAGE = "c5_timing"


def build_timeline(project: str, script: Script, voice: Voice, timing: CreateTiming) -> Timeline:
    by_scene = {v.scene: v for v in voice.scenes}
    scenes: list[TimelineScene] = []
    words: list[TimelineWord] = []
    t = 0.0
    for k, sc in enumerate(script.scenes):
        v = by_scene[sc.id]
        start = t
        voice_start = start + (timing.pre_roll_s if k == 0 else 0.0)
        voice_end = voice_start + v.duration_s
        tail = timing.close_tail_s if k == len(script.scenes) - 1 else timing.scene_tail_s
        end = voice_end + tail
        scenes.append(
            TimelineScene(
                scene=sc.id,
                start_s=round(start, 3),
                end_s=round(end, 3),
                voice_start_s=round(voice_start, 3),
                voice_end_s=round(voice_end, 3),
            )
        )
        for w in v.words:
            words.append(
                TimelineWord(
                    scene=sc.id,
                    i=len(words),
                    text=w.text,
                    start_s=round(voice_start + w.start_s, 3),
                    end_s=round(voice_start + w.end_s, 3),
                )
            )
        t = round(end, 3)
    return Timeline(
        provenance=Provenance(
            tool_version=__version__,
            stage=STAGE,
            annotator=Annotator.CODE,
            input_hash=cache_key(
                {"voice": voice.model_dump(mode="json")["scenes"], "timing": timing.model_dump()}
            ),
            created_at=datetime.now(UTC),
        ),
        project=project,
        fps=timing.fps,
        total_s=scenes[-1].end_s,
        scenes=scenes,
        words=words,
    )


def narration_preview(root: Path, project: str, timeline: Timeline, voice: Voice) -> Path | None:
    """data/create/<project>/timing/narration.mp3: the chosen takes placed on the timeline (for listening)."""
    if shutil.which("ffmpeg") is None:
        return None
    audio = {v.scene: root / v.audio for v in voice.scenes}
    if not all(p.exists() for p in audio.values()):
        return None
    out = root / "data" / "create" / project / "timing" / "narration.mp3"
    out.parent.mkdir(parents=True, exist_ok=True)
    inputs: list[str] = []
    chains: list[str] = []
    for k, s in enumerate(timeline.scenes):
        inputs += ["-i", str(audio[s.scene])]
        ms = round(s.voice_start_s * 1000)
        chains.append(f"[{k}:a]aresample=44100,aformat=channel_layouts=mono,adelay={ms}|{ms}[a{k}]")
    mix = "".join(f"[a{k}]" for k in range(len(timeline.scenes)))
    graph = (
        ";".join(chains)
        + f";{mix}amix=inputs={len(timeline.scenes)}:normalize=0,apad=whole_dur={timeline.total_s}"
    )
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        *inputs,
        "-filter_complex",
        graph,
        "-t",
        str(timeline.total_s),
        str(out),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError:
        return None  # a listening aid only; the timeline does not depend on it
    return out


def run_timing(root: Path, project: str, timing: CreateTiming) -> tuple[Path, Timeline, Brief, Path | None]:
    base = root / "projects" / project
    script = Script.model_validate(yaml.safe_load((base / "script.yaml").read_text()))
    voice = Voice.model_validate(json.loads((base / "voice.json").read_text()))
    brief = Brief.model_validate(yaml.safe_load((base / "brief.yaml").read_text()))
    timeline = build_timeline(project, script, voice, timing)
    path = base / "timeline.json"
    path.write_text(timeline.model_dump_json(indent=1) + "\n")
    preview = narration_preview(root, project, timeline, voice)
    return path, timeline, brief, preview
