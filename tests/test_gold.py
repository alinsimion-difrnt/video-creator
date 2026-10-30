"""G2 gold set: even event sampling, merging reviews into the gold file, and its validation."""

from __future__ import annotations

from lens.gold import apply_reviews, review_key, sample_evenly
from lens.schemas.gold import GoldFile

GOLD = {
    "provenance": {
        "tool_version": "t",
        "stage": "g2_gold",
        "annotator": "human",
        "input_hash": "0" * 64,
        "created_at": "2026-01-01T00:00:00Z",
    },
    "video": "v",
    "watch_url": None,
    "shots": [
        {
            "shot": "s001",
            "start_s": 0.0,
            "end_s": 2.0,
            "shot_type": "kinetic_type",
            "composition": "centered",
            "transition_in": "hard_cut",
            "depth_cues": ["none"],
        }
    ],
    "events": [
        {
            "event": "e001",
            "shot": "s001",
            "start_s": 0.5,
            "end_s": 1.0,
            "elements": [{"id": "b02", "label": "Title", "role": "headline", "change_types": ["fade"]}],
            "pattern": "kinetic_word_reveal",
            "sfx": [{"id": "x001", "sync_s": 0.6, "label": "whoosh"}],
        }
    ],
}


def test_sample_evenly_keeps_ends_and_order():
    items = [f"e{i:03d}" for i in range(1, 61)]
    got = sample_evenly(items, 12)
    assert len(got) == 12 and got[0] == "e001" and got[-1] == "e060" and got == sorted(got)
    assert sample_evenly(items[:4], 12) == items[:4]
    assert sample_evenly([], 3) == [] and sample_evenly(items, 1) == ["e031"]


def test_reviews_merge_only_named_reviewed_items():
    gold = GoldFile.model_validate(GOLD)
    reviews = {
        review_key("v", "s001"): {"status": "corrected", "composition": "split", "unknown": 1},
        review_key("v", "e001"): {
            "status": "corrected",
            "elements": [
                {"id": "b02", "label": "Title", "role": "headline", "change_types": ["fade"], "moves": False}
            ],
            "missed": ["b05"],
            "sfx": [{"id": "x001", "sync_s": 0.6, "label": "click"}],
        },
        review_key("other", "s001"): {"status": "confirmed"},
        review_key("v", "s009"): {"status": "pending"},
    }
    new, n = apply_reviews(gold, reviews)
    assert n == 2
    assert new.shots[0].composition == "split" and new.shots[0].status == "corrected"
    assert new.shots[0].shot_type == "kinetic_type"
    ev = new.events[0]
    assert not ev.elements[0].moves and ev.missed == ["b05"] and ev.sfx[0].label == "click"
    assert ev.pattern == "kinetic_word_reveal"
    # pending bodies change nothing
    same, n0 = apply_reviews(gold, {review_key("v", "s001"): {"status": "pending", "composition": "grid"}})
    assert n0 == 0 and same.shots[0].composition == "centered"


def test_gold_file_validates_against_the_taxonomy(tmp_path):
    import shutil

    import yaml

    from lens.config import REPO_ROOT
    from lens.validate import validate_file

    (tmp_path / "taxonomy").mkdir()
    shutil.copy(REPO_ROOT / "taxonomy" / "v1.yaml", tmp_path / "taxonomy" / "v1.yaml")
    path = tmp_path / "gold" / "v" / "gold.yaml"
    path.parent.mkdir(parents=True)
    path.write_text(yaml.safe_dump(GOLD), "utf-8")
    assert validate_file(path, tmp_path).ok
    bad = {**GOLD, "shots": [{**GOLD["shots"][0], "shot_type": "selfie"}]}
    path.write_text(yaml.safe_dump(bad), "utf-8")
    result = validate_file(path, tmp_path)
    assert not result.ok and "shot_type" in " ".join(result.errors)
