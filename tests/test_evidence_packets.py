"""M3: S4 evidence and S5 packets — geometry and triage units, then S1-S5 on the synthetic explainer."""

import json
import shutil

import numpy as np
import pytest
import yaml
from PIL import Image

from lens.config import REPO_ROOT, load_config
from lens.evidence import run_evidence
from lens.evidence.boxes import crop_box, diff_components, iou, quantile_frames, rank_and_suppress
from lens.evidence.draw import place_labels
from lens.frames import normalize_one
from lens.ingest import ingest_one
from lens.packets import EventInfo, build_packets, pack_pass1, status, triage
from lens.schemas import PacketManifest, SourcesFile
from lens.signals import run_signals
from lens.validate import validate_all
from tests.fixtures.scenes import explainer_with_sound

CFG = load_config()


# --- units -------------------------------------------------------------------------------------


def test_quantile_frames_follow_motion_not_time():
    energy = [0, 0, 0, 0, 5, 5, 0, 0, 0, 0]
    frames = quantile_frames(energy, [0, 0.25, 0.5, 0.75, 1])
    assert frames[0] == 0 and frames[-1] == 9
    assert all(4 <= f <= 5 for f in frames[1:4])  # bunched where things move
    assert quantile_frames([0] * 9, [0, 0.5, 1]) == [0, 4, 8]  # no motion: even in time


def test_crop_box_grows_and_stays_inside():
    assert crop_box((10, 10, 20, 20), 640, 360, 0.15, 160) == (0, 0, 160, 160)
    x0, y0, x1, y1 = crop_box((600, 300, 640, 360), 640, 360, 0.15, 100)
    assert x1 == 640 and y1 == 360 and x1 - x0 >= 100 and y1 - y0 >= 60


def test_candidates_rank_nms_and_union_fallback():
    mask = np.zeros((100, 200), bool)
    mask[10:30, 10:50] = True  # element A
    mask[60:90, 120:190] = True  # element B (bigger)
    comps = diff_components(mask, merge_px=2, min_area=0.001)
    assert len(comps) == 2
    boxes = [(b, "diff", None) for b in comps]
    boxes.append(((11, 11, 49, 29), "ocr", "A"))  # near-duplicate of A
    boxes.append(((5, 5, 195, 95), "union", None))
    kept = rank_and_suppress(boxes, mask, iou_max=0.6, cap=20)
    specific = [c for c in kept if c.source != "union"]
    assert [c.box for c in specific] == [(120, 60, 190, 90), (10, 10, 50, 30)]  # B (more change), then A
    assert sum(c.source == "union" for c in kept) == 1  # union kept: no specific box duplicates it
    assert len(specific) == 2  # the OCR near-duplicate of A is suppressed
    assert len(rank_and_suppress(boxes, mask, iou_max=0.6, cap=1)) == 1


def test_union_never_suppresses_a_specific_box():
    mask = np.zeros((100, 100), bool)
    mask[10:90, 10:90] = True
    kept = rank_and_suppress(
        [((10, 10, 90, 90), "union", None), ((12, 12, 88, 88), "diff", None)], mask, 0.6, 20
    )
    assert [c.source for c in kept] == ["diff"]


def test_labels_stay_in_frame_and_do_not_overlap():
    boxes = [(10, 30, 60, 60), (70, 30, 120, 60), (10, 70, 60, 100)]
    labels = place_labels(boxes, [(24, 14)] * 3, 200, 120)
    for lab in labels:
        assert lab[0] >= 0 and lab[1] >= 0 and lab[2] <= 200 and lab[3] <= 120
    for i in range(3):
        for j in range(i + 1, 3):
            assert iou(labels[i], labels[j]) == 0


def _ev(eid, shot="s001", f0=10, f1=20, energy=0.01, bbox=(0.1, 0.1, 0.3, 0.3), h="0" * 16):
    return EventInfo(eid, shot, f0, f1, energy, bbox, h)


def test_triage_reasons_and_dedupe():
    events = [
        _ev("e001"),
        _ev("e002", f0=30, f1=40, bbox=(0.4, 0.1, 0.6, 0.3)),  # same look and size: duplicate of e001
        _ev("e003", energy=1e-6),
        _ev("e004", bbox=(0.1, 0.1, 0.11, 0.11)),
        _ev("e005", bbox=(0.3, 0.85, 0.7, 0.95)),  # entirely in the caption band
        _ev("e006", shot="s002"),  # same look, other shot: not a duplicate
        _ev("e007", h="f" * 16),  # different look
    ]
    kept, skipped = triage(events, CFG, "reference")
    assert [k.id for k in kept] == ["e001", "e006", "e007"]
    assert kept[0].siblings == ["e002"]
    reasons = {s.event: (s.reason, s.of) for s in skipped}
    assert reasons == {
        "e002": ("duplicate", "e001"),
        "e003": ("low_energy", None),
        "e004": ("small", None),
        "e005": ("caption_band", None),
    }
    kept, skipped = triage(events[:1], CFG, "average")  # average tier: A1 only
    assert kept == [] and skipped[0].reason == "tier"


def test_triage_merges_overlapping_bursts():
    """Overlapping bursts show one build (trial: Acme e009-e011); the first event's task covers it."""
    ev = [
        EventInfo("e009", "s004", 300, 330, 0.01, (0.1, 0.1, 0.5, 0.5), "0" * 16, burst=(290, 340)),
        EventInfo("e010", "s004", 335, 345, 0.01, (0.1, 0.5, 0.5, 0.9), "f" * 16, burst=(325, 351)),
        EventInfo("e011", "s005", 335, 345, 0.01, (0.1, 0.5, 0.5, 0.9), "f" * 16, burst=(325, 351)),
        EventInfo("e012", "s004", 352, 380, 0.01, (0.6, 0.1, 0.9, 0.5), "a" * 16, burst=(341, 390)),
    ]
    kept, skipped = triage(ev, CFG, "reference")
    # e010: 16 of its 27 burst frames lie in e009's burst; e011 is in another shot; e012 shares 10 of 50
    assert CFG.packets.overlap_merge_min <= 16 / 27
    assert CFG.packets.overlap_merge_min > 10 / 50
    assert [k.id for k in kept] == ["e009", "e011", "e012"]
    assert [(s.event, s.reason, s.of) for s in skipped] == [("e010", "overlap", "e009")]
    assert kept[0].siblings == []  # not a duplicate: nothing is propagated to e010


def test_pass1_packing_respects_the_budget():
    shots = [("s1", ["a", "b"]), ("s2", ["c"] * 5), ("s3", ["d"] * 30), ("s4", ["e"])]
    tasks = pack_pass1(shots, 12)
    assert all(len(imgs) <= 12 for _, imgs in tasks)
    assert sum(len(imgs) for _, imgs in tasks) == 38
    assert tasks[0][0] == ["s1", "s2"]
    assert [s for t in tasks for s in t[0]].count("s3") == 3  # a long shot spans several tasks


def test_manifest_rejects_an_over_budget_task():
    with pytest.raises(ValueError, match="over the budget"):
        PacketManifest.model_validate(
            {
                "provenance": {
                    "tool_version": "0",
                    "stage": "s5-packets",
                    "annotator": "code",
                    "input_hash": "0" * 64,
                    "created_at": "2026-01-01T00:00:00Z",
                },
                "video": "v",
                "tier": "own",
                "max_images_per_task": 12,
                "event_images": 4,
                "tasks": [
                    {
                        "id": "a2-e001",
                        "kind": "a2",
                        "images": ["a", "b", "c", "d", "e"],
                        "files": [],
                        "output": "videos/v/events/e001.a2.json",
                        "input_hash": "x",
                    }
                ],
                "skipped": [],
            }
        )


# --- S1-S5 on the synthetic explainer ------------------------------------------------------------


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    if shutil.which("ffmpeg") is None:
        pytest.skip("needs ffmpeg")
    root = tmp_path_factory.mktemp("repo")
    for d in ("config", "taxonomy", "sources", "media"):
        (root / d).mkdir()
    cfg_data = yaml.safe_load((REPO_ROOT / "config" / "lens.yaml").read_text())
    for part in ("stems", "clap"):  # not needed here; keeps the test fast
        cfg_data["signals"][part]["enabled"] = False
    (root / "config" / "lens.yaml").write_text(yaml.safe_dump(cfg_data))
    shutil.copy(REPO_ROOT / "taxonomy" / "v1.yaml", root / "taxonomy" / "v1.yaml")
    mp4, truth = explainer_with_sound(root / "media", voice=False)
    entry = {
        "id": "synth",
        "url": f"file://{mp4}",
        "brand": "Synth",
        "title": "synth",
        "format": "narrated_explainer",
        "tier": "own",
        "why": "m3",
    }
    (root / "sources" / "sources.yaml").write_text(yaml.safe_dump([entry]))
    (src,) = SourcesFile.model_validate([entry]).root
    cfg = load_config(root / "config" / "lens.yaml")
    ingest_one(src, root)
    normalize_one(src, root, cfg)
    run_signals(src, root, cfg)
    s4 = run_evidence(src, root, cfg)
    s5 = build_packets(src, root, cfg)
    return root, src, cfg, truth, s4, s5


def test_s4_s5_outputs_valid_and_cached(run):
    root, src, cfg, _, s4, s5 = run
    assert (s4, s5) == ("built", "built")
    results = validate_all(root)
    assert all(r.ok for r in results), [r for r in results if not r.ok]
    assert any("candidates.json" in r.path for r in results)
    assert run_evidence(src, root, cfg) == "cached"
    assert build_packets(src, root, cfg) == "cached"


def test_annotated_video_is_never_repacked(run):
    """Rebuilding packets would change task ids and hashes and orphan the annotations already made."""
    from lens.packets import PacketError

    root, src, cfg, *_ = run
    m = PacketManifest.model_validate_json((root / "packets" / "synth" / "manifest.json").read_text())
    out = root / m.tasks[0].output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("{}")
    try:
        with pytest.raises(PacketError, match="annotat"):
            build_packets(src, root, cfg, force=True)
    finally:
        out.unlink()


def test_images_within_budget(run):
    root, _, cfg, *_ = run
    images = list((root / "data" / "packets" / "synth").rglob("*.jpg"))
    assert images
    for p in images:
        assert max(Image.open(p).size) <= cfg.evidence.image_long_edge_px
    m = PacketManifest.model_validate_json((root / "packets" / "synth" / "manifest.json").read_text())
    for t in m.tasks:
        assert len(t.images) <= (
            cfg.annotate.event_images if t.kind == "a2" else cfg.annotate.max_images_per_task
        )
        for rel in t.images + t.files:
            assert (root / "data" / "packets" / "synth" / rel).exists()
    a2 = [t for t in m.tasks if t.kind == "a2"]
    assert a2 and all(len(t.images) == cfg.annotate.event_images for t in a2)  # audio: 4 images each


def test_candidates_find_the_moving_box(run):
    """Scene 0: a 120x80 box slides in and lands at (260, 140). A candidate must cover it."""
    root, _, _, truth, *_ = run
    m0 = truth["motions"][0]
    ev = json.loads((root / "data" / "evidence" / "synth" / "evidence.json").read_text())
    eid = next(k for k, v in ev["events"].items() if v["start_f"] <= m0["f1"] and v["end_f"] >= m0["f0"])
    cands = json.loads(
        (root / "data" / "evidence" / "synth" / "events" / eid / "candidates.json").read_text()
    )
    best = max(iou(tuple(b["xyxy"]), (260, 140, 380, 220)) for b in cands["boxes"])
    assert best >= 0.7
    # filmstrip frames lie in the burst, ordered, first/last at its ends
    fr, (b0, b1) = ev["events"][eid]["filmstrip_frames"], ev["events"][eid]["burst"]
    assert fr == sorted(fr) and fr[0] == b0 and fr[-1] == b1


def test_status_lists_pending_tasks(run):
    root, *_ = run
    (row,) = status(root)
    assert row["video"] == "synth" and row["done"] == 0 and row["pending"]
    m = PacketManifest.model_validate_json((root / "packets" / "synth" / "manifest.json").read_text())
    out = root / m.tasks[0].output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("{}")
    try:
        assert status(root)[0]["done"] == 0  # only outputs that validate count (tests/test_annotation.py)
    finally:
        out.unlink()


def _measure_motion(run, k: int, end_box: tuple[int, int, int, int]):
    from lens.measure.run import measure_event
    from lens.schemas import MeasureFile

    root, src, cfg, truth, *_ = run
    m = truth["motions"][k]
    ev = json.loads((root / "data" / "evidence" / "synth" / "evidence.json").read_text())
    eid = next(e for e, v in ev["events"].items() if v["start_f"] <= m["f1"] and v["end_f"] >= m["f0"])
    cands = json.loads(
        (root / "data" / "evidence" / "synth" / "events" / eid / "candidates.json").read_text()
    )
    best = max(cands["boxes"], key=lambda b: iou(tuple(b["xyxy"]), end_box))
    out = MeasureFile.model_validate_json(measure_event(src, root, cfg, eid, [best["id"]]).read_text())
    return out, out.elements[0], m


def test_measure_event_on_pipeline_output(run):
    """S7 on S1-S4 output (H.264 proxy): scene 1's white bar moves linearly, fully on screen."""
    root = run[0]
    out, el, m = _measure_motion(run, 2, (480, 280, 560, 320))
    fps = out.fps
    assert el.timing is not None and el.timing.ease == "none"
    assert {c.cls for c in el.channels if c.name == "x"} == {"linear"}
    assert abs(el.timing.start_s - m["f0"] / fps) * fps <= 1
    assert abs(el.timing.duration_ms / 1000 - (m["f1"] - m["f0"]) / fps) * fps <= 1
    assert el.source.value == "measured"
    assert all(r.ok for r in validate_all(root) if "measure" in r.path)


def test_measure_event_flags_an_unseen_start(run):
    """Scene 0's box slides in from off-screen: only the tail of its easeOutCubic is visible. The
    channel says so, the direction is still right, and the timing is within a few frames."""
    out, el, m = _measure_motion(run, 0, (260, 140, 380, 220))
    fps = out.fps
    (x,) = [c for c in el.channels if c.name == "x"]
    assert not x.observed_start
    assert el.timing is not None and el.timing.ease.endswith(".out")
    assert abs(el.timing.start_s - m["f0"] / fps) * fps <= 3
    assert abs(el.timing.duration_ms / 1000 - (m["f1"] - m["f0"]) / fps) * fps <= 3


def _write_a2(root, eid: str, elements: list[dict]) -> None:
    """A hand-written A2 for one event (shape only; `lens validate` would also check the hash)."""
    out = root / "videos" / "synth" / "events" / f"{eid}.a2.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "provenance": {
                    "tool_version": "t",
                    "stage": "a2_annotate_event",
                    "annotator": "claude-code",
                    "input_hash": "0" * 64,
                    "created_at": "2026-01-01T00:00:00Z",
                },
                "video": "synth",
                "event": eid,
                "task": f"a2-{eid}",
                "elements": elements,
                "sfx_review": [],
                "pattern": {"id": "layout_reframe", "description": "bar slides", "why_premium": "clean"},
                "build_hint": {"gsap": "gsap.to(bar, {x})", "remotion": "interpolate x"},
                "confidence": "high",
            }
        )
    )


def test_measure_video_from_a2_then_reconcile(run):
    """S7 measures what A2 chose (candidate and manual boxes); S8 merges it into record.json with a
    source per value, and the consistency checks pass."""
    from lens.measure.run import measure_video
    from lens.reconcile import reconcile_video
    from lens.schemas import MeasureFile
    from lens.schemas.record import RecordFile

    root, src, cfg, truth, *_ = run
    m = truth["motions"][2]  # scene 1's white bar, linear, lands at (480, 280, 560, 320)
    ev = json.loads((root / "data" / "evidence" / "synth" / "evidence.json").read_text())
    eid = next(e for e, v in ev["events"].items() if v["start_f"] <= m["f1"] and v["end_f"] >= m["f0"])
    cands = json.loads(
        (root / "data" / "evidence" / "synth" / "events" / eid / "candidates.json").read_text()
    )
    best = max(cands["boxes"], key=lambda b: iou(tuple(b["xyxy"]), (480, 280, 560, 320)))
    w, h = cands["frame_size"]
    manual = [round(280 / h * 1000), round(480 / w * 1000), round(320 / h * 1000), round(560 / w * 1000)]
    bar = {"label": "bar", "role": "card", "change_types": ["slide_right"], "is_text": False}
    _write_a2(
        root,
        eid,
        [
            {**bar, "box": best["id"]},
            {
                **bar,
                "manual_box": manual,
                "manual_reason": "same bar, drawn by hand",
                "estimates": {"duration_ms": 400, "easing_class": "ease_out"},
            },
        ],
    )
    try:
        paths = measure_video(src, root, cfg)
        assert [p.name for p in paths] == [f"{eid}.json"]
        mf = MeasureFile.model_validate_json(paths[0].read_text())
        assert [e.box for e in mf.elements] == [best["id"], "m02"]
        assert all(e.xyxy is not None for e in mf.elements)
        assert mf.elements[0].source.value == "measured"
        assert measure_video(src, root, cfg) == []  # cached

        assert reconcile_video(src, root, cfg) == "built"
        rec = RecordFile.model_validate_json((root / "videos" / "synth" / "record.json").read_text())
        assert all(c.ok for c in rec.checks), rec.checks
        (event,) = [e for e in rec.events if e.id == eid]
        assert event.status == "annotated" and event.pattern and event.pattern.id == "layout_reframe"
        cand, hand = event.elements
        assert cand.box_source == "candidate" and cand.timing and cand.timing.source.value == "measured"
        assert cand.timing.ease == "none" and "x" in cand.timing.channels
        assert hand.box_source == "manual" and hand.timing is not None
        assert rec.coverage.annotated == 1 and rec.coverage.elements == 2
        assert rec.coverage.pending == len([e for e in rec.events if e.status == "pending"])
        assert rec.shots and all(s.annotation is None for s in rec.shots)  # no A1 in this fixture
        assert all(s.label for s in rec.sfx)
        assert reconcile_video(src, root, cfg) == "cached"
        assert all(r.ok for r in validate_all(root) if r.path.endswith(("record.json", f"{eid}.json")))
    finally:
        (root / "videos" / "synth" / "events" / f"{eid}.a2.json").unlink()
