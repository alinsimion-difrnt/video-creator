"""C13 create qa: the helpers that read the file and the pipeline's sidecars."""

import subprocess
from pathlib import Path

import pytest

from create.qa import moov_first, visual_events
from lens.config import load_config
from lens.schemas.create import Edl


def _mp4(path: Path, faststart: bool) -> Path:
    args = ["-movflags", "+faststart"] if faststart else []
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=black:s=64x64:d=0.5", "-c:v",
                    "libx264", *args, str(path)], check=True)  # fmt: skip
    return path


@pytest.mark.skipif(
    subprocess.run(["which", "ffmpeg"], capture_output=True).returncode != 0, reason="needs ffmpeg"
)
def test_faststart_is_detected(tmp_path):
    assert moov_first(_mp4(tmp_path / "a.mp4", True))
    assert not moov_first(_mp4(tmp_path / "b.mp4", False))


def test_visual_events_come_from_cuts_layouts_and_graphics():
    prov = {"schema_version": 1, "tool_version": "0", "stage": "f4_edl", "annotator": "code"}
    prov |= {"input_hash": "0" * 64, "created_at": "2026-10-09T00:00:00Z"}
    segs = [
        {"take": "t", "src_in": 0, "src_out": 60, "rec_in": 0},
        {"take": "t", "src_in": 90, "src_out": 150, "rec_in": 60},
    ]
    edl = Edl.model_validate(
        {
            "provenance": prov,
            "project": "p",
            "fps": 30,
            "applied": [],
            "duration_frames": 120,
            "segments": segs,
        }
    )
    meta = {
        "layout": {
            "scenes": [
                {"start_s": 0, "end_s": 3, "layout": "full"},
                {"start_s": 3, "end_s": 4, "layout": "pip"},
            ]
        },
        "overlays": {"items": [{"t0": 0.5, "t1": 1.5, "zone": [0, 0, 1, 1], "title": "x"}]},
    }
    assert visual_events(meta, edl) == [0.5, 1.5, 2.0, 3]


def test_captions_belong_in_the_band_or_on_a_split_seam():
    from create.qa import caption_placed

    frame = load_config().create.design.frames["vertical"]
    band = frame.caption_band
    mid = (band.y0 + band.y1) / 2
    assert caption_placed(mid, 40, frame, None)
    assert not caption_placed(band.y0 - 100, 40, frame, None)
    seam = 900.0  # above the band, inside the safe area: fine in a split scene, if it ends above the seam
    assert caption_placed(seam - 50, 40, frame, seam)
    assert not caption_placed(seam, 40, frame, seam)  # it would cover the presenter's head
    assert not caption_placed(seam - 50, 40, frame, None)
    assert not caption_placed(200.0, 40, frame, 260.0)  # a seam caption still stays out of the top UI


def test_mux_copies_audio_that_covers_the_video(tmp_path):
    from create.burn import audio_seconds, mux

    v = tmp_path / "v.mp4"
    a = tmp_path / "a.mp4"
    run = ["ffmpeg", "-y", "-v", "error"]
    subprocess.run([*run, "-f", "lavfi", "-i", "color=c=black:s=64x64:r=30:d=1", "-c:v", "libx264", str(v)],
                   check=True)  # fmt: skip
    subprocess.run([*run, "-f", "lavfi", "-i", "sine=f=440:d=2", "-c:a", "aac", str(a)], check=True)
    out = tmp_path / "o.mp4"
    mux(v, a, 1.0, out)
    codec = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_name",
         "-of", "csv=p=0", str(out)], capture_output=True, text=True, check=True,
    ).stdout.strip()  # fmt: skip
    assert codec == "aac"
    assert audio_seconds(out) == pytest.approx(1.0, abs=0.05)


def test_a_box_that_runs_to_the_end_is_not_faststart(tmp_path):
    import struct

    p = tmp_path / "zero.mp4"
    p.write_bytes(struct.pack(">I4s", 0, b"free") + b"\0" * 16)
    assert moov_first(p) is False  # it used to seek back and forth forever
