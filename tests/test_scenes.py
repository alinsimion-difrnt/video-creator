"""Scene archetypes: assignments need a name for `other`; a batch must cover its shots exactly."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from lens.config import load_config
from lens.schemas.scenes import SceneAssignment, SceneBatch
from lens.synth import scenes

PROV = {
    "tool_version": "t",
    "stage": "a3_scene_types",
    "annotator": "claude-code",
    "input_hash": "0" * 64,
    "created_at": "2026-01-01T00:00:00Z",
}


def test_other_needs_a_short_name():
    SceneAssignment(
        video="v", shot="s001", archetype="other", proposed_name="product ui tour", confidence="high"
    )
    with pytest.raises(ValidationError):
        SceneAssignment(video="v", shot="s001", archetype="other", confidence="high")


def test_batch_must_cover_its_shots(monkeypatch, tmp_path):
    monkeypatch.setattr(scenes, "batches", lambda root, cfg: {"b01": [("v", "s001"), ("v", "s002")]})
    cfg = load_config()
    item = {"video": "v", "archetype": "logo_close", "confidence": "high"}
    ok = SceneBatch.model_validate(
        {"provenance": PROV, "batch": "b01", "items": [{**item, "shot": "s001"}, {**item, "shot": "s002"}]}
    )
    assert scenes.batch_errors(tmp_path, cfg, ok, ["logo_close"]) == []
    short = ok.model_copy(update={"items": ok.items[:1]})
    assert "exactly" in scenes.batch_errors(tmp_path, cfg, short, ["logo_close"])[0]
    unknown = ok.model_copy(update={"items": [i.model_copy(update={"archetype": "nope"}) for i in ok.items]})
    assert any(
        "not a scene_archetype" in e for e in scenes.batch_errors(tmp_path, cfg, unknown, ["logo_close"])
    )
    other = ok.model_copy(update={"batch": "b09"})
    assert "not a scene batch" in scenes.batch_errors(tmp_path, cfg, other, ["logo_close"])[0]
