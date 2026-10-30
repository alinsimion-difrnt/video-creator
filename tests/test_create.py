"""P0: Phase 2 stages in the registry, project schemas, the write guard and the `create` CLI."""

import importlib.util
import json
import shutil
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from create.project import phase2_stages, status
from lens.config import REPO_ROOT
from lens.stages import STAGES, check_dag, is_write_allowed
from lens.validate import validate_file

FIXTURE = REPO_ROOT / "tests" / "fixtures" / "create" / "demo"
HOOK = REPO_ROOT / ".claude" / "hooks" / "guard_paths.py"


@pytest.fixture
def root(tmp_path: Path) -> Path:
    """A minimal repo with the shared config and taxonomy, plus the demo project."""
    for rel in ("config/lens.yaml", "taxonomy/v1.yaml", "exports/archetypes.json"):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO_ROOT / rel, tmp_path / rel)
    shutil.copytree(FIXTURE, tmp_path / "projects" / "demo")
    (tmp_path / "brands" / "demo").mkdir(parents=True)
    return tmp_path


def _edit(root: Path, name: str, change) -> Path:
    path = root / "projects" / "demo" / name
    is_yaml = path.suffix == ".yaml"
    data = yaml.safe_load(path.read_text()) if is_yaml else json.loads(path.read_text())
    change(data)
    path.write_text(yaml.safe_dump(data) if is_yaml else json.dumps(data))
    return path


def _errors(root: Path, name: str) -> tuple[str, ...]:
    return validate_file(root / "projects" / "demo" / name, root).errors


def test_registry_has_all_phase2_stages():
    assert check_dag(STAGES) == []
    ids = [s.id for s in phase2_stages()]
    assert ids[0] == "c1_brief" and ids[-1] == "c13_qa"
    # C1-C13 (C8: templated, free-form, audit; motion route: direction, motion, grade, mix; music) + F1-F7
    assert len(ids) == 27


def test_phase2_writes_stay_in_project_or_local_data():
    for s in phase2_stages():
        for w in s.writes:
            assert w.startswith(("projects/{project}/", "data/create/{project}/")), (s.id, w)
            assert not w.startswith("brands/"), (s.id, w)  # the shared hand-off is read-only


def test_write_guard_scopes_claude_stages():
    assert is_write_allowed("projects/acme-v2/script.yaml", ["c2_script"])
    assert not is_write_allowed("projects/acme-v2/brief.yaml", ["c2_script"])
    assert not is_write_allowed("brands/acme/tokens.json", ["c1_brief"])
    assert is_write_allowed("projects/acme-v2/freeform/s07.html", ["c8_build_freeform"])
    assert not is_write_allowed("projects/acme-v2/scenes/s07.html", ["c8_build_freeform"])

    spec = importlib.util.spec_from_file_location("guard_paths", HOOK)
    assert spec and spec.loader
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    payload = {"tool_name": "Write", "tool_input": {"file_path": "brands/acme/DESIGN.md"}}
    ok, message = guard.decide({**payload, "cwd": str(REPO_ROOT)}, {"LENS_STAGE": "c1_brief"}, REPO_ROOT)
    assert not ok and "not declared" in message


def test_fixture_project_validates(root: Path):
    for name in ("brief.yaml", "script.yaml", "voice.json", "timeline.json"):
        result = validate_file(root / "projects" / "demo" / name, root)
        assert result.ok, (name, result.errors)


def test_brief_checks_taxonomy_and_destination(root: Path):
    def change(d):
        d["format"] = "webinar"
        d["destination"] = "myspace"

    _edit(root, "brief.yaml", change)
    errors = _errors(root, "brief.yaml")
    assert any("taxonomy.format" in e for e in errors)
    assert any("loudness target" in e for e in errors)
    assert any("destination_frames" in e for e in errors)


def test_script_facts_must_exist_in_brief(root: Path):
    _edit(root, "script.yaml", lambda d: d["scenes"][1]["facts"].append("made_up"))
    assert any("made_up" in e and "not in the brief" in e for e in _errors(root, "script.yaml"))


def test_script_audio_tags_come_from_config(root: Path):
    def change(d):
        d["scenes"][0]["spoken"] = "[screams] People ask AI about everything now."

    _edit(root, "script.yaml", change)
    assert any("[screams]" in e for e in _errors(root, "script.yaml"))


def test_script_beats_come_from_taxonomy(root: Path):
    _edit(root, "script.yaml", lambda d: d["scenes"][0].update(beat="intro"))
    assert any("s01.beat" in e for e in _errors(root, "script.yaml"))


def test_project_must_match_path(root: Path):
    _edit(root, "brief.yaml", lambda d: d.update(project="other"))
    assert any("does not match the path" in e for e in _errors(root, "brief.yaml"))


def test_voice_scenes_follow_the_script(root: Path):
    _edit(root, "voice.json", lambda d: d["scenes"].reverse())
    assert any("script's scenes in order" in e for e in _errors(root, "voice.json"))


def test_voice_audio_path_is_declared(root: Path):
    _edit(root, "voice.json", lambda d: d["scenes"][0].update(audio="voice/s01.mp3"))
    assert any("audio must be data/create/demo/voice/s01-t2.mp3" in e for e in _errors(root, "voice.json"))


def test_voice_take_and_word_order(root: Path):
    _edit(root, "voice.json", lambda d: d["scenes"][0].update(take=3))
    assert _errors(root, "voice.json")
    shutil.copy(FIXTURE / "voice.json", root / "projects" / "demo" / "voice.json")
    _edit(root, "voice.json", lambda d: d["scenes"][0]["words"].reverse())
    assert any("time order" in e for e in _errors(root, "voice.json"))


def test_timeline_scenes_are_contiguous(root: Path):
    _edit(root, "timeline.json", lambda d: d["scenes"][1].update(start_s=3.5))
    assert any("must start where" in e for e in _errors(root, "timeline.json"))


def test_timeline_words_sit_inside_their_scene(root: Path):
    _edit(root, "timeline.json", lambda d: d["words"][0].update(start_s=0.2))
    assert any("outside s01" in e for e in _errors(root, "timeline.json"))


def test_timeline_needs_the_script(root: Path):
    (root / "projects" / "demo" / "script.yaml").unlink()
    assert any("script.yaml is missing" in e for e in _errors(root, "timeline.json"))


def test_status_reports_progress(root: Path):
    rows = {r.stage: r for r in status(root, "demo")}
    assert rows["c1_brief"].state == "done"
    assert rows["c2_script"].state == "done"
    assert rows["c3_tokens"].state == "ready"
    assert rows["c4_voice"].state == "done"  # voice.json is committed; the audio is local media
    assert "local media missing" in rows["c4_voice"].detail
    assert rows["c5_timing"].state == "done"
    assert rows["c6_storyboard"].state == "done"  # the demo storyboard is present and valid
    assert rows["c7_sketches"].state == "waiting"  # after c6, which waits on c3 tokens upstream
    assert rows["c8_build_freeform"].state == "optional"


def test_status_follows_the_build_route(root: Path):
    _edit(root, "brief.yaml", lambda d: d.pop("build"))  # motion is the default route (ADR 0032)
    rows = {r.stage: r for r in status(root, "demo")}
    for sid in ("c6_storyboard", "c8_build", "c8_build_freeform", "c8_audit", "c7_sketches", "c12_render"):
        assert rows[sid].state == "unused", sid
    assert rows["c6_direction"].state == "waiting"  # after c3 tokens
    assert rows["c8_motion"].state == "waiting"
    assert rows["c10_music"].state == "ready"  # both routes use the bed


def test_write_guard_scopes_the_motion_builder():
    assert is_write_allowed("projects/demo25/motion/index.html", ["c8_motion"])
    assert is_write_allowed("projects/demo25/motion/sfx.json", ["c8_motion"])
    assert not is_write_allowed("projects/demo25/motion/grade.json", ["c8_motion"])  # code grades
    assert not is_write_allowed("projects/demo25/direction.md", ["c8_motion"])


def test_status_flags_invalid_files(root: Path):
    _edit(root, "script.yaml", lambda d: d["scenes"][0].update(beat="intro"))
    assert {r.stage: r.state for r in status(root, "demo")}["c2_script"] == "invalid"


def test_cli_init_and_status(tmp_path: Path, monkeypatch):
    import create.cli as cli

    monkeypatch.setattr(cli, "REPO_ROOT", tmp_path)
    runner = CliRunner()
    result = runner.invoke(cli.app, ["init", "Bad Name"])
    assert result.exit_code != 0
    result = runner.invoke(cli.app, ["init", "demo", "--brand", "acme"])
    assert result.exit_code == 0, result.output
    assert "brand hand-off missing in brands/acme/" in result.output
    assert (tmp_path / "brands" / "acme").is_dir()
    assert (tmp_path / "projects" / "demo").is_dir()
    assert (tmp_path / "data" / "create" / "demo").is_dir()
    result = runner.invoke(cli.app, ["status", "nope"])
    assert result.exit_code == 1


@pytest.mark.parametrize(
    ("spoken", "reason"),
    [
        ("Demo-flow checks three assistants — every day.", "em dash"),
        ("It isn't just a tracker. It is a plan.", "'isn't just'"),
        ("Not only does it track, but it also explains.", "'not X, but Y'"),
        ("A seamless way to see where you show up.", "slogan word"),
        ("That's a count, not an opinion.", "punchline pair"),
        ("[curious] [happy] [excited] Demo-flow checks.", "audio tags"),
    ],
)
def test_script_style_guard(root: Path, spoken: str, reason: str):
    _edit(root, "script.yaml", lambda d: d["scenes"][1].update(spoken=spoken))
    assert any(reason in e for e in _errors(root, "script.yaml")), _errors(root, "script.yaml")


def test_script_must_fit_the_brief_length(root: Path):
    _edit(root, "brief.yaml", lambda d: d["length"].update(min_s=60, max_s=90))
    assert any("the brief asks 60-90 s" in e for e in _errors(root, "script.yaml"))


def _storyboard_root(root: Path) -> Path:
    (root / "exports").mkdir(exist_ok=True)
    shutil.copy(REPO_ROOT / "exports" / "archetypes.json", root / "exports" / "archetypes.json")
    return root


def test_storyboard_validates(root: Path):
    _storyboard_root(root)
    result = validate_file(root / "projects/demo/storyboard.json", root)
    assert result.ok, result.errors


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda d: d["scenes"].reverse(), "timeline's scenes in order"),
        (lambda d: d["scenes"][0].update(archetype="hologram"), "not in exports/archetypes.json"),
        (lambda d: d["scenes"][0]["slots"].pop("headline"), "needs slot 'headline'"),
        (lambda d: d["scenes"][0]["slots"].update(sparkles="yes"), "'sparkles' is not a slot"),
        (lambda d: d["scenes"][0]["cues"][1].update(word=8), "cue word 8 is not spoken in this scene"),
        (lambda d: d["scenes"][0]["cues"][0].update(target="emphasis"), "'emphasis' is not a filled slot"),
        (lambda d: d["scenes"][0]["slots"].update(headline="People ask AI — everything."), "em dash"),
        (lambda d: d["scenes"][1]["slots"].update(icons=["ChatGPT 72%"]), "example_data"),
    ],
)
def test_storyboard_checks(root: Path, change, message):
    _storyboard_root(root)
    _edit(root, "storyboard.json", change)
    errors = _errors(root, "storyboard.json")
    assert any(message in e for e in errors), errors


def test_storyboard_cues_follow_the_narration(root: Path):
    _storyboard_root(root)
    _edit(root, "storyboard.json", lambda d: d["scenes"][0]["cues"].reverse())
    assert any("in order" in e for e in _errors(root, "storyboard.json"))


def test_brief_brand_must_have_a_folder(root: Path):
    assert validate_file(root / "projects" / "demo" / "brief.yaml", root).ok
    path = _edit(root, "brief.yaml", lambda d: d.update(brand="nobody"))
    assert any("brands/nobody/" in e for e in validate_file(path, root).errors)


def test_brand_dir_comes_from_the_brief(root: Path):
    from create.project import BrandError, brand_dir, brand_missing

    assert brand_dir(root, "demo") == root / "brands" / "demo"
    assert brand_missing(root, "demo") == ["tokens.json", "video.yaml", "DESIGN.md", "logo"]
    _edit(root, "brief.yaml", lambda d: d.pop("brand"))
    with pytest.raises(BrandError, match="does not name a brand"):
        brand_dir(root, "demo")


def test_frame_profiles_are_checked():
    from lens.schemas.config import CreateFrame, Rect

    rect = {"x0": 0, "y0": 0, "x1": 10, "y1": 10}
    with pytest.raises(ValueError, match="outside"):
        CreateFrame(
            width=5, height=5, min_text_px=1, safe=[Rect(**rect)], caption_band=Rect(**rect), source="t"
        )
    with pytest.raises(ValueError, match="x0 < x1"):
        Rect(x0=5, y0=0, x1=5, y1=1)
