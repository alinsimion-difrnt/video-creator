"""C10 music and C12 mix (motion route, ADR 0032), on synthetic audio."""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from create.mix import pan, run_mix
from create.music import dropouts, music_plan, run_music
from lens.config import REPO_ROOT, load_config
from lens.schemas.create import Timeline

CFG = load_config()
TL = Timeline.model_validate_json((REPO_ROOT / "projects/demo25/timeline.json").read_text())


def test_plan_has_one_chunk_per_scene_and_covers_the_film():
    plan = music_plan(TL, 25.0, CFG.create.music)
    chunks = plan["chunks"]
    assert len(chunks) == len(TL.scenes)
    assert sum(c["duration_ms"] for c in chunks) == 25000
    assert chunks[0]["text"] == CFG.create.music.sections.first
    assert chunks[-1]["text"] == CFG.create.music.sections.last
    assert chunks[0]["positive_styles"] == CFG.create.music.positive_styles
    assert chunks[0]["negative_styles"] == CFG.create.music.negative_styles
    assert all(c["duration_ms"] >= CFG.create.music.min_chunk_ms for c in chunks)


def test_a_short_scene_merges_into_the_one_before():
    raw = TL.model_dump(mode="json")
    raw["scenes"][1]["end_s"] = raw["scenes"][1]["start_s"] + 1.0  # 1 s scene: under the API's 3 s minimum
    raw["scenes"][1]["voice_end_s"] = raw["scenes"][1]["end_s"]
    raw["scenes"][2]["start_s"] = raw["scenes"][2]["voice_start_s"] = raw["scenes"][1]["end_s"]
    raw["words"] = [w for w in raw["words"] if w["scene"] != "s02"]
    tl = Timeline.model_validate(raw)
    chunks = music_plan(tl, 25.0, CFG.create.music)["chunks"]
    assert len(chunks) == 2 and sum(c["duration_ms"] for c in chunks) == 25000


def test_dropouts_ignore_the_ending():
    m = CFG.create.music
    levels = [-20.0] * 25
    levels[10] = -70.0  # a hole mid-bed
    levels[24] = -80.0  # the final chord has rung out
    assert dropouts(levels, 25.0, m) == [10]


def _tone(path: Path, expr: str, dur: float) -> None:
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"{expr}:d={dur}", "-ac", "2", str(path)],
        check=True,
    )


@pytest.fixture
def project(tmp_path: Path) -> Path:
    (tmp_path / "config").mkdir()
    shutil.copy(REPO_ROOT / "config/lens.yaml", tmp_path / "config/lens.yaml")
    base = tmp_path / "projects" / "demo"
    shutil.copytree(REPO_ROOT / "projects" / "demo25", base)
    brief = yaml.safe_load((base / "brief.yaml").read_text())
    brief.update(project="demo", cut_s=None)
    (base / "brief.yaml").write_text(yaml.safe_dump(brief, sort_keys=False))
    tl = json.loads((base / "timeline.json").read_text())
    tl.update(
        project="demo",
        total_s=3.0,
        scenes=[{**tl["scenes"][0], "start_s": 0.0, "end_s": 3.0, "voice_start_s": 0.2, "voice_end_s": 1.5}],
        words=[{**tl["words"][0], "start_s": 0.2, "end_s": 0.5}],
    )
    (base / "timeline.json").write_text(json.dumps(tl))
    data = tmp_path / "data" / "create" / "demo"
    for d in ("timing", "music", "motion/render/assets/sfx"):
        (data / d).mkdir(parents=True)
    _tone(data / "timing" / "narration.mp3", "sine=f=220", 3.0)
    _tone(data / "music" / "bed.mp3", "anoisesrc=a=0.3:c=pink", 3.0)
    _tone(data / "motion/render/assets/sfx/pop.mp3", "sine=f=1200", 0.15)
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=white:s=1920x1080:r=30:d=3",
            "-pix_fmt",
            "yuv420p",
            str(data / "motion/render/video.mp4"),
        ],
        check=True,
    )
    (base / "motion").mkdir(exist_ok=True)
    (base / "motion" / "sfx.json").write_text(json.dumps([{"t": 1.0, "sfx": "pop", "gain_db": -6}]))
    return tmp_path


def _loudness(path: Path) -> tuple[float, float]:
    err = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True,
        text=True,
    ).stderr
    lufs = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", err)[-1])
    peak = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", err)[-1])
    return lufs, peak


def test_mix_hits_the_destination_and_the_film_length(project: Path):
    cfg = load_config(project / "config" / "lens.yaml")
    out, notes = run_mix(project, "demo", cfg)
    target = cfg.targets.loudness["linkedin"]
    lufs, peak = _loudness(out)
    assert target.min_lufs <= lufs <= target.max_lufs
    assert peak <= target.max_true_peak_dbtp
    dur = float(
        subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out)],
            capture_output=True,
            text=True,
        ).stdout
    )
    assert dur == pytest.approx(3.0, abs=0.05)
    assert notes == []


def test_mix_without_a_bed_says_so(project: Path):
    (project / "data/create/demo/music/bed.mp3").unlink()
    _, notes = run_mix(project, "demo", load_config(project / "config" / "lens.yaml"))
    assert any("no music bed" in n for n in notes)


def test_music_is_cached_by_its_plan(project: Path):
    (project / "data/create/demo/music/bed.mp3").unlink()
    calls = []

    def fake_post(body: dict, music) -> bytes:
        calls.append(body)
        return (project / "data/create/demo/timing/narration.mp3").read_bytes()

    cfg = load_config(project / "config" / "lens.yaml")
    path, _ = run_music(project, "demo", cfg, post=fake_post)
    assert path.exists() and len(calls) == 1
    assert calls[0]["model_id"] == cfg.create.music.model_id and "composition_plan" in calls[0]
    run_music(project, "demo", cfg, post=fake_post)
    assert len(calls) == 1  # same plan: no new credits


def test_pan_follows_the_reveal_across_the_frame():
    assert pan(0.0, 0.6) == -0.6 and pan(0.5, 0.6) == 0.0 and pan(1.0, 0.6) == 0.6


def test_a_cue_with_x_is_panned_toward_its_reveal(project: Path):
    sfx = project / "projects/demo/motion/sfx.json"
    sfx.write_text(json.dumps([{"t": 1.0, "sfx": "pop", "gain_db": -6, "x": 1.0}]))
    out, _ = run_mix(project, "demo", load_config(project / "config" / "lens.yaml"))
    err = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-ss",
            "1.0",
            "-t",
            "0.15",
            "-i",
            str(out),
            "-af",
            "highpass=f=900,astats=measure_overall=none:measure_perchannel=RMS_level",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
    ).stderr
    left, right = (float(v) for v in re.findall(r"RMS level dB:\s+(-?[\d.]+)", err)[:2])
    assert right > left + 3
