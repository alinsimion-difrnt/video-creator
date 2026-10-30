"""M5: A1/A2 annotation files validate against the packet they answer (BUILD_PLAN 7.4, CLAUDE.md:
annotators only use ids given in packets, never invent them)."""

import copy
import json
import shutil
from pathlib import Path

import pytest

from lens.config import REPO_ROOT
from lens.validate import validate_file

H1, H2, H3 = "1" * 64, "2" * 64, "3" * 64


def _prov(stage: str, input_hash: str) -> dict:
    return {
        "schema_version": 1,
        "tool_version": "0.1.0",
        "stage": stage,
        "annotator": "claude-code",
        "skill": "annotate-video@0123abcd",
        "model": None,
        "input_hash": input_hash,
        "created_at": "2026-10-04T21:00:00Z",
    }


def _task(tid: str, kind: str, output: str, h: str, shots=(), event=None) -> dict:
    return {
        "id": tid,
        "kind": kind,
        "images": ["x.jpg"],
        "files": [],
        "shots": list(shots),
        "event": event,
        "siblings": [],
        "output": output,
        "input_hash": h,
    }


@pytest.fixture
def root(tmp_path: Path) -> Path:
    (tmp_path / "taxonomy").mkdir()
    shutil.copy(REPO_ROOT / "taxonomy" / "v1.yaml", tmp_path / "taxonomy" / "v1.yaml")
    code = _prov("s5_packets", H1) | {"annotator": "code", "skill": None}
    manifest = {
        "provenance": code,
        "video": "v",
        "tier": "reference",
        "max_images_per_task": 12,
        "event_images": 4,
        "tasks": [
            _task("a1-p1", "a1", "videos/v/a1.p1.json", H1, ("s001", "s002")),
            _task("a1-p2", "a1", "videos/v/a1.p2.json", H2, ("s003",)),
            _task("a2-e001", "a2", "videos/v/events/e001.a2.json", H3, event="e001"),
        ],
        "skipped": [],
    }
    _write(tmp_path / "packets/v/manifest.json", manifest)
    words = [{"i": i, "text": f"w{i}", "start_s": i * 0.3, "end_s": i * 0.3 + 0.2} for i in range(10)]
    shots = [
        {"id": f"s00{n}", "start_s": n - 1.0, "end_s": float(n), "transition_in": None, "events": 0}
        for n in (1, 2, 3)
    ]
    anchors = {
        "provenance": code,
        "video": "v",
        "duration_s": 3.0,
        "fps": 30,
        "shots": shots,
        "words": words,
        "bpm": None,
        "beats_s": [],
        "integrated_lufs": None,
        "palette": [],
        "sfx": [],
    }
    _write(tmp_path / "data/packets/v/pass1/anchors.json", anchors)
    box = {"source": "diff", "xyxy": [10, 10, 50, 50], "norm": [0.1, 0.1, 0.5, 0.5], "changed_share": 0.9}
    _write(
        tmp_path / "data/packets/v/events/e001/candidates.json",
        {
            "provenance": code,
            "video": "v",
            "event": "e001",
            "frame_size": [100, 100],
            "start_frame": 0,
            "end_frame": 10,
            "boxes": [box | {"id": "b01"}, box | {"id": "b02"}],
        },
    )
    sfx = {"id": "x001", "sync_s": 1.0, "label": "whoosh", "clap_label": "whoosh", "clap_score": 0.7}
    _write(
        tmp_path / "data/packets/v/events/e001/facts.json",
        {
            "provenance": code,
            "video": "v",
            "event": "e001",
            "shot": "s002",
            "start_s": 1.0,
            "end_s": 1.5,
            "burst_frames": [30, 45],
            "filmstrip_frames": [30, 35, 40, 45],
            "energy": [0.1, 0.2],
            "camera": {"move": "none", "pan_x": 0, "pan_y": 0, "scale": 1},
            "sfx": [sfx],
            "words": [],
        },
    )
    return tmp_path


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def _shot(sid: str) -> dict:
    return {
        "shot": sid,
        "shot_type": "ui_closeup",
        "composition": "centered",
        "focal_element": "the search bar",
        "transition_in": "hard_cut",
        "on_screen_text": ["Find anything"],
        "text_word_count": 2,
        "typography": "bold sans, sentence case",
        "depth_cues": ["shadow"],
        "what_happens": "The search bar types a query.",
        "build_rebuild": "Type the query one character every 40 ms over a static panel.",
        "confidence": "high",
    }


def _score(n: int | None = 4) -> dict:
    return {"score": n, "evidence": "clear", "refs": ["s001", "w3"]}


SUMMARY = {
    "beats": [{"beat": "hook", "shots": ["s001"], "words": [0, 3]}, {"beat": "cta", "shots": ["s003"]}],
    "hook": {"text": "Find anything", "technique": "demo_first", "shots": ["s001"], "words": [0, 2]},
    "cta": {"text": "Try it", "shots": ["s003"]},
    "tone": "confident, plain",
    "signature_moments": [{"shots": ["s002"], "description": "push-in", "why_premium": "smooth"}],
    "scores": {
        k: _score(None if k == "vo_script_quality" else 4)
        for k in (
            "hook",
            "clarity",
            "ui_showcase",
            "motion_polish",
            "sound_design",
            "vo_script_quality",
            "brand_consistency",
            "works_muted",
            "overall",
        )
    },
    "localization_friendliness": {"score": 3, "baked_in_text": True, "vo_dependent": False, "notes": "-"},
}

A1_P1 = {
    "provenance": _prov("a1_annotate_video", H1),
    "video": "v",
    "task": "a1-p1",
    "shots": [_shot("s001"), _shot("s002")],
}
A1_P2 = {
    "provenance": _prov("a1_annotate_video", H2),
    "video": "v",
    "task": "a1-p2",
    "shots": [_shot("s003")],
    "summary": SUMMARY,
}
A2 = {
    "provenance": _prov("a2_annotate_event", H3) | {"skill": "annotate-event@0123abcd"},
    "video": "v",
    "event": "e001",
    "task": "a2-e001",
    "elements": [
        {
            "box": "b01",
            "label": "Headline",
            "role": "headline",
            "change_types": ["fade", "slide_up"],
            "is_text": True,
            "text": "Find anything",
            "text_unit": "word",
            "estimates": {"duration_ms": 450, "easing_class": "ease_out"},
        },
        {
            "manual_box": [100, 200, 300, 400],
            "manual_reason": "no candidate covers the icon",
            "label": "Icon",
            "role": "icon",
            "change_types": ["pop"],
            "is_text": False,
        },
    ],
    "sfx_review": [{"id": "x001", "verdict": "confirm", "label": "whoosh"}],
    "pattern": {"id": "kinetic_word_reveal", "description": "words rise in", "why_premium": "rhythm"},
    "build_hint": {"gsap": "fromTo words y:26 opacity:0, expo.out 0.45, stagger 0.1", "remotion": "spring"},
    "confidence": "high",
}


def _check(root: Path, rel: str, data: dict):
    _write(root / rel, data)
    return validate_file(root / rel, root)


def test_valid_annotations_pass(root):
    for rel, data in (
        ("videos/v/a1.p1.json", A1_P1),
        ("videos/v/a1.p2.json", A1_P2),
        ("videos/v/events/e001.a2.json", A2),
    ):
        r = _check(root, rel, data)
        assert r.ok, r.errors


def _bad(root: Path, rel: str, data: dict, needle: str) -> None:
    r = _check(root, rel, data)
    assert not r.ok
    assert any(needle in e for e in r.errors), r.errors


def test_a1_shots_must_be_exactly_the_tasks(root):
    d = copy.deepcopy(A1_P1)
    d["shots"] = [_shot("s001")]
    _bad(root, "videos/v/a1.p1.json", d, "exactly the task's shots")
    d["shots"] = [_shot("s001"), _shot("s002"), _shot("s009")]
    _bad(root, "videos/v/a1.p1.json", d, "exactly the task's shots")


def test_a1_summary_only_in_the_last_part(root):
    _bad(root, "videos/v/a1.p1.json", A1_P1 | {"summary": SUMMARY}, "only the last A1 part")
    _bad(root, "videos/v/a1.p2.json", {k: v for k, v in A1_P2.items() if k != "summary"}, "video summary")


def test_a1_refs_and_enums(root):
    d = copy.deepcopy(A1_P2)
    d["summary"]["hook"]["words"] = [8, 12]  # the transcript has 10 words
    d["summary"]["beats"][0]["shots"] = ["s042"]
    d["summary"]["scores"]["overall"]["refs"] = ["w99"]
    d["shots"][0]["shot_type"] = "drone_shot"
    d["shots"][0]["composition"] = "other"  # without composition_other
    r = _check(root, "videos/v/a1.p2.json", d)
    text = "\n".join(r.errors)
    needles = ("outside the transcript", "unknown shot s042", "unknown ref 'w99'", "drone_shot", "_other")
    for needle in needles:
        assert needle in text, text


def test_a1_input_hash_and_output_path(root):
    d = copy.deepcopy(A1_P1)
    d["provenance"]["input_hash"] = H2
    _bad(root, "videos/v/a1.p1.json", d, "input_hash")
    _bad(root, "videos/v/a1.json", A1_P1, "writes videos/v/a1.p1.json")


def test_a2_boxes_and_sfx_come_from_the_packet(root):
    d = copy.deepcopy(A2)
    d["elements"][0]["box"] = "b07"
    _bad(root, "videos/v/events/e001.a2.json", d, "b07 is not a candidate")
    d = copy.deepcopy(A2)
    d["sfx_review"] = []
    _bad(root, "videos/v/events/e001.a2.json", d, "exactly the SFX candidates")
    d["sfx_review"] = [{"id": "x001", "verdict": "confirm", "label": "boing"}]
    _bad(root, "videos/v/events/e001.a2.json", d, "'boing' is not in the taxonomy")


def test_a2_element_rules(root):
    d = copy.deepcopy(A2)
    d["elements"][1]["box"] = "b02"  # both a candidate and a manual box
    _bad(root, "videos/v/events/e001.a2.json", d, "exactly one of box")
    d = copy.deepcopy(A2)
    del d["elements"][1]["manual_reason"]
    _bad(root, "videos/v/events/e001.a2.json", d, "manual_reason")
    d = copy.deepcopy(A2)
    d["pattern"] = {"id": "other", "proposed_name": "thing", "description": "x", "why_premium": "y"}
    _bad(root, "videos/v/events/e001.a2.json", d, "2-4 words")
    d["pattern"] = {"id": "made_up", "description": "x", "why_premium": "y"}
    _bad(root, "videos/v/events/e001.a2.json", d, "taxonomy.patterns")


def test_brief_gives_exact_provenance_and_status_counts_only_valid_outputs(root):
    from lens.packets import status, task_brief

    for skill in ("annotate-video", "annotate-event"):
        (root / ".claude/skills" / skill).mkdir(parents=True)
        (root / ".claude/skills" / skill / "SKILL.md").write_text(skill)
    b = task_brief(root, "v", "a1-p2")
    assert b["writes_summary"] and b["earlier_parts"] == ["videos/v/a1.p1.json"]
    assert b["provenance"]["input_hash"] == H2 and b["provenance"]["stage"] == "a1_annotate_video"
    assert b["provenance"]["skill"].startswith("annotate-video@")
    assert task_brief(root, "v", "a2-e001")["files"] == []  # paths are repo-relative under data/packets/v
    with pytest.raises(KeyError):
        task_brief(root, "v", "a2-e999")

    _check(root, "videos/v/a1.p1.json", A1_P1)
    _write(root / "videos/v/events/e001.a2.json", {"broken": True})
    (row,) = status(root)
    assert row["done"] == 1 and row["pending"] == ["a1-p2", "a2-e001"]
