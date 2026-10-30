"""F1/F2 helpers: probing decisions (rotation, HDR, VFR, master size) and the Scribe response mapping."""

import pytest

from create.footage.media import display_size, is_hdr, is_vfr, master_size, rotation
from create.footage.run import approved_ids, take_id
from create.footage.transcribe import keyterms_for, words_from_scribe
from lens.schemas.create import CutApprovals, Cuts


def test_phone_rotation_and_hdr_and_vfr_are_detected():
    portrait = {
        "width": 3840,
        "height": 2160,
        "side_data_list": [{"rotation": -90}],
        "color_transfer": "arib-std-b67",
        "r_frame_rate": "30/1",
        "avg_frame_rate": "29.91/1",
    }
    assert rotation(portrait) == 270 and display_size(portrait) == (2160, 3840)
    assert is_hdr(portrait) and is_vfr(portrait)
    assert not is_hdr({"color_transfer": "bt709"})


def test_masters_keep_4k_and_scale_larger_sources():
    assert master_size(3840, 2160, 2160) == (3840, 2160)
    assert master_size(2160, 3840, 2160) == (2160, 3840)
    assert master_size(5760, 3240, 2160) == (3840, 2160)


def test_scribe_words_keep_fillers_and_events_and_drop_spacing():
    data = {"words": [
        {"text": "So", "type": "word", "start": 0.1, "end": 0.3, "logprob": -0.1},
        {"text": " ", "type": "spacing", "start": 0.3, "end": 0.4},
        {"text": "um,", "type": "word", "start": 0.4, "end": 0.6},
        {"text": "(laughs)", "type": "audio_event", "start": 0.7, "end": 1.0},
        {"text": "late", "type": "word", "start": None, "end": None},
    ]}  # fmt: skip
    words = words_from_scribe(data, "t1", 10)
    assert [(w.i, w.text, w.kind) for w in words] == [
        (10, "So", "word"),
        (11, "um,", "word"),
        (12, "(laughs)", "event"),
    ]


def test_keyterms_respect_the_api_limits():
    terms = keyterms_for("Acme", "Ack-me", ["ChatGPT", "a" * 60, "one two three four five six", "x<y"])
    assert terms == ["Acme", "ChatGPT"]


def test_take_ids_are_slugs():
    assert take_id("IMG_0042 Final.MOV") == "img-0042-final"


def test_approvals_reject_wins_and_unknown_ids_fail():
    cuts = Cuts.model_validate({
        "provenance": {"schema_version": 1, "tool_version": "0", "stage": "f3_cuts", "annotator": "code",
                       "input_hash": "0" * 64, "created_at": "2026-10-09T00:00:00Z"},
        "project": "demo",
        "proposals": [{"id": f"c00{i}", "kind": "silence", "take": "t1", "start_s": i, "end_s": i + 0.5,
                       "reason": "pause"} for i in (1, 2, 3)],
    })  # fmt: skip
    assert approved_ids(cuts, CutApprovals(approve="all", reject=["c002"])) == ["c001", "c003"]
    with pytest.raises(ValueError, match="c009"):
        approved_ids(cuts, CutApprovals(approve=["c009"]))


def test_cut_approval_rejects_unknown_ids_on_approve_too(tmp_path, monkeypatch):
    import json

    from typer.testing import CliRunner

    import create.cli as cli

    base = tmp_path / "projects" / "demo"
    base.mkdir(parents=True)
    prov = json.loads((cli.REPO_ROOT / "projects/acme-v2/tokens.json").read_text())["provenance"]
    (base / "cuts.json").write_text(
        json.dumps(
            {
                "provenance": prov,
                "project": "demo",
                "proposals": [
                    {
                        "id": "c001",
                        "take": "t",
                        "kind": "silence",
                        "start_s": 1.0,
                        "end_s": 2.0,
                        "reason": "pause",
                    }
                ],
            }
        )
    )
    monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
    res = CliRunner().invoke(cli.app, ["cuts", "demo", "--approve", "c001,c999"])
    assert res.exit_code != 0 and "c999" in res.output
    ok = CliRunner().invoke(
        cli.app, ["cuts", "demo", "--approve", "c001"]
    )  # failed before: every id "unknown"
    assert ok.exit_code == 0, ok.output
    assert (base / "cuts-approved.yaml").exists()


def test_the_edit_is_frame_exact_with_one_seeked_input_per_segment(tmp_path):
    """render_edit seeks each segment's input (memory: one decoded 4K master split 40 ways was killed);
    the kept frames must still be exactly src_in..src_out-1 of each segment."""
    import subprocess

    import numpy as np

    from create.footage.media import render_edit
    from lens.schemas.create import EdlSegment

    src = tmp_path / "count.mp4"  # frame k is grey level 4k: the frame index can be read back
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=black:s=64x64:r=30:d=2",
         "-f", "lavfi", "-i", "sine=f=440:d=2", "-vf", "geq=lum='4*N':cb=128:cr=128",
         "-c:v", "libx264", "-qp", "0", "-g", "30", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest",
         str(src)],
        check=True,
    )  # fmt: skip
    segs = [
        EdlSegment(take="t", src_in=10, src_out=20, rec_in=0),
        EdlSegment(take="t", src_in=40, src_out=55, rec_in=10),
    ]
    out = render_edit(segs, {"t": src}, 30, 0, tmp_path / "edit.mp4", (64, 64))

    def levels(path):  # each frame's mean grey, read the same way for the source and the edit
        raw = subprocess.run(
            ["ffmpeg", "-v", "error", "-i", str(path), "-f", "rawvideo", "-pix_fmt", "gray", "-"],
            check=True, capture_output=True,
        ).stdout  # fmt: skip
        return [float(f[20:44, 20:44].mean()) for f in np.frombuffer(raw, np.uint8).reshape(-1, 64, 64)]

    src_levels, got = levels(src), levels(out)
    # each edited frame is the source frame of that index (nearest level; levels are 4 grey steps apart)
    idx = [min(range(len(src_levels)), key=lambda k: abs(src_levels[k] - g)) for g in got]
    assert idx == list(range(10, 20)) + list(range(40, 55))
