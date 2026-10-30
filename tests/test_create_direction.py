"""C6 direction (ADR 0032): one compact pack a motion builder reads instead of the repo."""

import json
import re
import shutil
from pathlib import Path

import pytest
import yaml

from create.build import css_vars
from create.direction import film_s, run_direction
from lens.config import REPO_ROOT, load_config
from lens.schemas.create import Brief, Timeline, Tokens

PROJECT = REPO_ROOT / "projects" / "demo25"
EXPORTS = ("motion-tokens.json", "pacing.json", "sound-spec.json", "patterns.json")


@pytest.fixture
def root(tmp_path: Path) -> Path:
    for rel in ("config/lens.yaml", *(f"exports/{e}" for e in EXPORTS)):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO_ROOT / rel, tmp_path / rel)
    shutil.copytree(PROJECT, tmp_path / "projects" / "demo25")
    shutil.copytree(REPO_ROOT / "brands" / "acme", tmp_path / "brands" / "acme")
    return tmp_path


def _pack(root: Path) -> str:
    return run_direction(root, "demo25", load_config()).read_text()


def _brief(root: Path, **change) -> None:
    path = root / "projects" / "demo25" / "brief.yaml"
    data = yaml.safe_load(path.read_text())
    data.update(change)
    path.write_text(yaml.safe_dump(data, sort_keys=False))


def test_pack_has_every_section_in_order(root: Path):
    md = _pack(root)
    heads = re.findall(r"(?m)^## (\d+)\.", md)
    assert heads == [str(i) for i in range(1, 9)]
    assert (root / "projects" / "demo25" / "direction.md").exists()


def test_word_clock_is_the_timeline(root: Path):
    md = _pack(root)
    tl = Timeline.model_validate_json((root / "projects/demo25/timeline.json").read_text())
    for w in tl.words:
        assert f"{w.text}@{w.start_s:.2f}" in md


def test_scene_content_comes_from_the_script(root: Path):
    path = root / "projects/demo25/script.yaml"
    script = yaml.safe_load(path.read_text())
    script["scenes"][1]["on_screen"] = ["Engines light up on their names"]
    script["scenes"][1]["notes"] = "Example data label while numbers show"
    path.write_text(yaml.safe_dump(script, sort_keys=False))
    md = _pack(root)
    assert "  - on screen: Engines light up on their names" in md
    assert "  - notes: Example data label while numbers show" in md


def test_brand_is_verbatim(root: Path):
    md = _pack(root)
    tokens = Tokens.model_validate_json((root / "projects/demo25/tokens.json").read_text())
    assert css_vars(tokens) in md
    design = (root / "brands/acme/DESIGN.md").read_text()
    accent = design.split("## 2.")[1].split("\n## ")[0].strip()
    assert accent in md  # a configured section, copied word for word
    assert "## 7. Contrast table" not in md and "Contrast table" not in md  # not configured


def test_measured_numbers_come_from_the_exports(root: Path):
    md = _pack(root)
    card = json.loads((root / "exports/motion-tokens.json").read_text())["duration_ms_by_role"]["card"]
    assert f"card: {card['median'] / 1000:.2f} ({card['low'] / 1000:.2f}-{card['high'] / 1000:.2f})" in md
    sound = json.loads((root / "exports/sound-spec.json").read_text())
    dur = film_s(
        Brief.model_validate(yaml.safe_load((root / "projects/demo25/brief.yaml").read_text())),
        Timeline.model_validate_json((root / "projects/demo25/timeline.json").read_text()),
        load_config().create.motion.final_hold_s,
    )
    lo, hi = (round(sound["sfx_per_min"][k] * dur / 60) for k in ("low", "high"))
    assert f"(range {lo}-{hi})" in md
    assert "-16 to -14 LUFS" in md  # linkedin house target


def test_recipes_and_rules_come_from_config(root: Path):
    md = _pack(root)
    motion = load_config().create.motion
    patterns = {p["id"]: p for p in json.loads((root / "exports/patterns.json").read_text())["patterns"]}
    for pid in motion.patterns:
        assert f"**{pid}**: {patterns[pid]['summary']}" in md
    for r in motion.rules:
        assert " ".join(r.rule.split()) in md and r.source in md


def test_unknown_pattern_fails(root: Path):
    cfg = load_config()
    cfg.create.motion.patterns.append("no_such_pattern")
    with pytest.raises(ValueError, match="no_such_pattern"):
        run_direction(root, "demo25", cfg)


def test_cut_shortens_the_film_but_not_the_voice(root: Path):
    tl = Timeline.model_validate_json((root / "projects/demo25/timeline.json").read_text())
    last = max(w.end_s for w in tl.words)
    _brief(root, cut_s=25.0)
    assert "exactly 25 s" in _pack(root)
    _brief(root, cut_s=round(last, 1))  # no room for the final hold
    with pytest.raises(ValueError, match="cut_s"):
        _pack(root)
    _brief(root, cut_s=tl.total_s + 1)
    with pytest.raises(ValueError, match="cut_s"):
        _pack(root)


def test_pack_is_deterministic(root: Path):
    assert _pack(root) == _pack(root)
