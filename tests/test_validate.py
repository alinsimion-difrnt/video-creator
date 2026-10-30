from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from lens.config import REPO_ROOT, load_config
from lens.schemas import Provenance, SourcesFile
from lens.validate import validate_all, validate_file


def test_committed_files_validate():
    results = validate_all()
    assert results, "expected committed files with schemas"
    assert all(r.ok for r in results), [r for r in results if not r.ok]


def test_config_loads_baseline():
    cfg = load_config()
    base = cfg.baselines[0]
    assert base.video == "acme-explainer-v1"
    assert base.frames == round(base.fps * base.duration_s.value)
    assert cfg.targets.loudness["linkedin"].source == "house"


def _write_sources(tmp_path: Path, entries: list[dict]) -> Path:
    (tmp_path / "sources").mkdir()
    (tmp_path / "taxonomy").mkdir()
    (tmp_path / "taxonomy" / "v1.yaml").write_text((REPO_ROOT / "taxonomy" / "v1.yaml").read_text())
    path = tmp_path / "sources" / "sources.yaml"
    path.write_text(yaml.safe_dump(entries))
    return path


BASE = {
    "id": "demo",
    "url": "https://example.com/a.mp4",
    "brand": "B",
    "title": "T",
    "format": "feature_reel",
    "tier": "reference",
    "why": "w",
}


def test_valid_source(tmp_path):
    assert validate_file(_write_sources(tmp_path, [BASE]), tmp_path).ok


@pytest.mark.parametrize(
    "override, needle",
    [
        ({"id": "Demo"}, "lowercase slug"),
        ({"format": "vlog"}, "not in taxonomy.format"),
        ({"url": None}, "needs a url"),
        ({"url": "ftp://x"}, "pattern"),
        ({"tier": "great"}, "tier"),
        ({"surprise": 1}, "surprise"),
    ],
)
def test_invalid_sources(tmp_path, override, needle):
    result = validate_file(_write_sources(tmp_path, [{**BASE, **override}]), tmp_path)
    assert not result.ok
    assert any(needle in e for e in result.errors), result.errors


def test_draft_source_may_lack_url():
    SourcesFile.model_validate([{**BASE, "url": None, "status": "draft"}])


def test_duplicate_ids_case_insensitive():
    with pytest.raises(ValidationError):
        SourcesFile.model_validate([BASE, {**BASE, "id": "demo"}])


def test_unknown_path_has_no_schema(tmp_path):
    p = tmp_path / "x.json"
    p.write_text("{}")
    assert not validate_file(p, tmp_path).ok


def test_provenance_requires_hash_and_skill_format():
    good = {
        "tool_version": "0.1.0",
        "stage": "a1_annotate_video",
        "annotator": "claude-code",
        "skill": "annotate-video@0123abcd",
        "input_hash": "a" * 64,
        "created_at": "2026-10-03T00:00:00Z",
    }
    Provenance.model_validate(good)
    with pytest.raises(ValidationError):
        Provenance.model_validate({**good, "input_hash": "short"})
    with pytest.raises(ValidationError):
        Provenance.model_validate({**good, "skill": "annotate-video"})
