"""P3: C8 build (scene compositions from storyboard + templates) and the render bundle, without a browser."""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from create.build import TEMPLATES, blend, clean_svg, motion_values, run_build, template_path
from create.sketches import scene_duration
from lens.config import REPO_ROOT
from lens.schemas.create import Storyboard, Timeline

PROJECT = REPO_ROOT / "projects" / "acme-v2"


@pytest.fixture
def root(tmp_path: Path) -> Path:
    for rel in ("config/lens.yaml", "exports/motion-tokens.json", "exports/archetypes.json"):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO_ROOT / rel, tmp_path / rel)
    dest = tmp_path / "projects" / "acme-v2"
    dest.mkdir(parents=True)
    for name in ("storyboard.json", "timeline.json", "tokens.json", "brief.yaml"):
        shutil.copy(PROJECT / name, dest / name)
    shutil.copytree(REPO_ROOT / "brands" / "acme", tmp_path / "brands" / "acme")
    return tmp_path


def _data(html: str) -> dict:
    m = re.search(r'<script type="application/json" id="scene-data">(.*?)</script>', html, re.DOTALL)
    assert m
    return json.loads(m.group(1).replace("<\\/", "</"))


def test_every_storyboard_archetype_has_a_template():
    board = Storyboard.model_validate(json.loads((PROJECT / "storyboard.json").read_text()))
    assert all(template_path(s.archetype).exists() for s in board.scenes)


def test_build_writes_one_composition_per_scene(root: Path):
    paths = run_build(root, "acme-v2")
    board = Storyboard.model_validate(json.loads((PROJECT / "storyboard.json").read_text()))
    timeline = Timeline.model_validate(json.loads((PROJECT / "timeline.json").read_text()))
    assert [p.stem for p in paths] == [s.scene for s in board.scenes]
    words = {w.i: w for w in timeline.words}
    for path, sc, ts in zip(paths, board.scenes, timeline.scenes, strict=True):
        html = path.read_text()
        assert f'data-composition-id="{sc.scene}"' in html
        assert scene_duration(html) == pytest.approx(ts.end_s - ts.start_s, abs=1e-3)
        assert 'src="assets/gsap.min.js"' in html and "cdn." not in html  # no CDN at render time
        data = _data(html)
        assert [c["t"] for c in data["cues"]] == [
            round(words[c.word].start_s - ts.start_s, 3) for c in sc.cues
        ]
        assert "<metadata>" not in data["logo"]["primary"]  # the hand-off's C2PA block is stripped
        tpl = (TEMPLATES / f"{sc.archetype}.js").read_text()
        assert "Acme" not in tpl  # templates stay project-free
        assert not any(f'"{v}"' in tpl for v in data["strings"].values())  # UI copy comes from the brand


def test_css_and_motion_come_from_tokens(root: Path):
    html = run_build(root, "acme-v2")[0].read_text()
    tokens = json.loads((PROJECT / "tokens.json").read_text())
    assert f"--accent:{tokens['colors']['accent']}" in html
    assert f"--keepout:{tokens['layout']['caption_keepout_px']}px" in html
    motion = json.loads((REPO_ROOT / "exports" / "motion-tokens.json").read_text())
    m = motion_values(motion)
    assert m["card"] == round(motion["duration_ms_by_role"]["card"]["median"] / 1000, 3)
    assert m["ease_out"] == motion["easing"]["ease_out"]["gsap"]
    assert _data(html)["motion"] == m


def test_freeform_scenes_are_left_to_the_builder_subagent(root: Path):
    path = root / "projects/acme-v2/storyboard.json"
    board = json.loads(path.read_text())
    board["scenes"][0].update(archetype="freeform", freeform_reason="test")
    path.write_text(json.dumps(board))
    assert "s01" not in [p.stem for p in run_build(root, "acme-v2")]


def test_missing_template_is_an_error(root: Path):
    path = root / "projects/acme-v2/storyboard.json"
    board = json.loads(path.read_text())
    board["scenes"][0]["archetype"] = "bars_ring"  # a corpus archetype without a template yet
    path.write_text(json.dumps(board))
    with pytest.raises(FileNotFoundError, match="bars_ring"):
        run_build(root, "acme-v2")


def test_helpers():
    assert blend("#00AA90", 0.08, "#FFFFFF") == "#EBF8F6"  # 102*0.08 + 255*0.92 = 242.8
    assert clean_svg('<?xml version="1.0"?><svg><metadata>x</metadata><path/></svg>') == "<svg><path/></svg>"


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
@pytest.mark.parametrize("template", sorted(p.name for p in TEMPLATES.glob("[!_]*.js")))
def test_templates_are_valid_javascript(template: str, tmp_path: Path):
    src = tmp_path / "scene.js"
    src.write_text((TEMPLATES / "_kit.js").read_text() + "\n" + (TEMPLATES / template).read_text())
    res = subprocess.run(["node", "--check", str(src)], capture_output=True, text=True)
    assert res.returncode == 0, res.stderr


def test_brand_families_and_language_reach_the_scene(root: Path):
    path = root / "projects/acme-v2/tokens.json"
    tokens = json.loads(path.read_text())
    tokens["families"]["mono"] = {"family": "Geist Mono", "weights": "400", "fallback": "monospace"}
    tokens["accent_tint_alpha"] = 0.5
    path.write_text(json.dumps(tokens))
    brief = root / "projects/acme-v2/brief.yaml"
    brief.write_text(brief.read_text().replace("brand: acme\n", "brand: acme\nlanguage: ro\n"))
    html = run_build(root, "acme-v2")[0].read_text()
    assert '--font-mono:"Geist Mono", monospace' in html
    assert '<html lang="ro">' in html
    assert f"--accent-tint:{blend(tokens['colors']['accent'], 0.5, tokens['colors']['surface'])}" in html


def test_accent_fill_defaults_to_the_accent_and_a_brand_can_change_it(root: Path):
    """Solid accent fills read --accent-fill (acme: cobalt is never a fill, so fills are ink)."""
    path = root / "projects/acme-v2/tokens.json"
    tokens = json.loads(path.read_text())
    html = run_build(root, "acme-v2")[0].read_text()
    assert f"--accent-fill:{tokens['colors']['accent']}" in html
    tokens["colors"]["accent_fill"] = tokens["colors"]["ink"]
    path.write_text(json.dumps(tokens))
    html = run_build(root, "acme-v2")[0].read_text()
    assert f"--accent-fill:{tokens['colors']['ink']}" in html


def test_type_weight_and_family_come_from_the_brand(root: Path):
    path = root / "projects/acme-v2/tokens.json"
    tokens = json.loads(path.read_text())
    tokens["type"]["headline"]["weight"] = 500
    path.write_text(json.dumps(tokens))
    html = run_build(root, "acme-v2")[0].read_text()
    assert "--headline-wt:500" in html
    assert '--label-font:"Inter"' in html  # Acme labels are Inter
    css = (TEMPLATES / "_base.css").read_text()
    for name in ("display", "headline", "stat", "body", "caption", "label"):
        assert f"var(--{name}-wt)" in css and f"var(--{name}-font)" in css


def test_no_template_fills_with_the_raw_accent():
    for f in [*TEMPLATES.glob("*.js"), *(TEMPLATES.parent / "kit").glob("motion.*")]:
        text = f.read_text()
        assert not re.search(r"background(?:Color)?:\s*[\"']?var\(--accent\)", text), f.name


def test_a_landscape_template_is_not_built_into_a_vertical_frame(root: Path):
    path = root / "projects/acme-v2/tokens.json"
    tokens = json.loads(path.read_text())
    tokens.update(frame="vertical")
    path.write_text(json.dumps(tokens))
    with pytest.raises(ValueError, match="has no vertical layout"):
        run_build(root, "acme-v2")


def test_frame_geometry_reaches_the_css(root: Path):
    html = run_build(root, "acme-v2")[0].read_text()
    assert "--frame-w:1920px;--frame-h:1080px" in html and "--safe-x0:77px" in html
    assert "width: var(--frame-w)" in html
