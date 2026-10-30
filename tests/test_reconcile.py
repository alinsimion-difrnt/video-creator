"""S8 reconcile pieces that need no video: element ids, manual boxes, final SFX labels, checks."""

from __future__ import annotations

from lens.reconcile import element_ids, events_in_shots, manual_box_px, resolve_sfx
from lens.schemas.annotation import A2File


def _a2(elements: list[dict], sfx: list[dict] | None = None, event: str = "e001") -> A2File:
    return A2File.model_validate(
        {
            "provenance": {
                "tool_version": "t",
                "stage": "a2_annotate_event",
                "annotator": "claude-code",
                "input_hash": "0" * 64,
                "created_at": "2026-01-01T00:00:00Z",
            },
            "video": "v",
            "event": event,
            "task": f"a2-{event}",
            "elements": elements,
            "sfx_review": sfx or [],
            "pattern": {"id": "logo_resolve", "description": "d", "why_premium": "w"},
            "build_hint": {"gsap": "g", "remotion": "r"},
            "confidence": "medium",
        }
    )


def _el(box: str | None = None, manual: list[int] | None = None) -> dict:
    return {
        "box": box,
        "manual_box": manual,
        "manual_reason": "no candidate" if manual else None,
        "label": "x",
        "role": "card",
        "change_types": ["fade"],
        "is_text": False,
    }


def test_element_ids_keep_candidates_and_number_manual_boxes_by_position():
    a2 = _a2([_el(box="b03"), _el(manual=[0, 0, 500, 500]), _el(box="b01"), _el(manual=[1, 1, 2, 2])])
    assert element_ids(a2) == ["b03", "m02", "b01", "m04"]


def test_manual_box_is_ymin_xmin_ymax_xmax_per_mille_of_the_full_frame():
    assert manual_box_px((100, 250, 500, 750), 1280, 720) == (320, 72, 960, 360)
    assert manual_box_px((0, 0, 1000, 1000), 1280, 720) == (0, 0, 1280, 720)


def test_final_sfx_label_prefers_a_confident_review_over_unsure_and_falls_back_to_code():
    reviews = {
        "x001": [("e002", "unsure", "unsure"), ("e003", "override", "music")],
        "x002": [("e004", "unsure", "unsure")],
        "x003": [("e005", "confirm", "whoosh"), ("e006", "override", "impact")],
    }
    got = {
        sid: resolve_sfx(classifier, reviews.get(sid, []))
        for sid, classifier in [("x001", "chime"), ("x002", "click"), ("x003", "whoosh"), ("x004", "pop")]
    }
    assert got["x001"] == ("music", "claude", "override")
    assert got["x002"] == ("click", "code", "unsure")
    assert got["x003"] == ("whoosh", "claude", "confirm")  # earliest confident review wins
    assert got["x004"] == ("pop", "code", None)


def test_events_must_lie_inside_their_shot_within_a_tolerance():
    shots = {"s001": (0.0, 2.0), "s002": (2.0, 5.0)}
    events = [("e001", "s001", 0.5, 1.9), ("e002", "s002", 1.99, 3.0), ("e003", "s002", 4.0, 5.5)]
    assert events_in_shots(events, shots, tolerance_s=1 / 30) == ["e003"]


def test_candidates_fall_back_to_the_packet_copy(tmp_path):
    from lens.config import REPO_ROOT
    from lens.reconcile import _candidates

    src = REPO_ROOT / "data" / "packets" / "acme-explainer-v1" / "events" / "e001" / "candidates.json"
    if not src.exists():
        import pytest

        pytest.skip("packets not pulled in this checkout")
    assert _candidates(tmp_path, "v", "e001") is None
    dst = tmp_path / "data" / "packets" / "v" / "events" / "e001" / "candidates.json"
    dst.parent.mkdir(parents=True)
    dst.write_text(src.read_text("utf-8"), "utf-8")
    got = _candidates(tmp_path, "v", "e001")
    assert got is not None and got.event == "e001"
