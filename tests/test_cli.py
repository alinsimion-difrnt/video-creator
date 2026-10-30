from typer.testing import CliRunner

from lens.cli import app
from lens.config import REPO_ROOT
from lens.schemas.export import stale

runner = CliRunner()


def test_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "validate" in result.output


def test_dag_check():
    result = runner.invoke(app, ["dag", "--check"])
    assert result.exit_code == 0, result.output


def test_validate_all():
    result = runner.invoke(app, ["validate", "--all"])
    assert result.exit_code == 0, result.output


def test_committed_schemas_up_to_date():
    assert stale(REPO_ROOT / "exports" / "schemas") == []


def test_validate_all_fails_when_nothing_found(tmp_path, monkeypatch):
    import lens.validate as v

    monkeypatch.setattr(v, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(v, "validate_all", lambda root=tmp_path: [])
    result = runner.invoke(app, ["validate", "--all"])
    assert result.exit_code == 1
    assert "nothing to validate" in result.output


def test_find_repo_root(tmp_path, monkeypatch):
    from lens.config import find_repo_root

    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "lens.yaml").write_text("x: 1")
    (tmp_path / "a" / "b").mkdir(parents=True)
    monkeypatch.delenv("LENS_ROOT", raising=False)
    assert find_repo_root(tmp_path / "a" / "b") == tmp_path.resolve()
    monkeypatch.setenv("LENS_ROOT", str(tmp_path / "a"))
    assert find_repo_root() == (tmp_path / "a").resolve()
