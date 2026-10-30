import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".claude" / "hooks" / "guard_paths.py"

spec = importlib.util.spec_from_file_location("guard_paths", HOOK)
assert spec and spec.loader
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def _payload(path: str, tool: str = "Write") -> dict:
    return {"tool_name": tool, "tool_input": {"file_path": path}, "cwd": str(ROOT)}


def test_allows_everything_without_active_stage():
    ok, _ = guard.decide(_payload("lens/cli.py"), {}, ROOT)
    assert ok


def test_ignores_non_write_tools():
    ok, _ = guard.decide(
        {"tool_name": "Read", "tool_input": {"file_path": "/etc/passwd"}},
        {"LENS_STAGE": "a1_annotate_video"},
        ROOT,
    )
    assert ok


def test_allows_declared_path():
    env = {"LENS_STAGE": "a0_annotate_batch,a1_annotate_video,a2_annotate_event"}
    assert guard.decide(_payload("videos/acme-explainer-v1/a1.json"), env, ROOT)[0]
    assert guard.decide(
        _payload(str(ROOT / "videos/acme-explainer-v1/events/e001.a2.json"), "Edit"), env, ROOT
    )[0]


def test_blocks_undeclared_path():
    env = {"LENS_STAGE": "a2_annotate_event"}
    ok, msg = guard.decide(_payload("videos/acme-explainer-v1/record.json"), env, ROOT)
    assert not ok and "not declared" in msg


def test_blocks_traversal_and_outside_repo():
    env = {"LENS_STAGE": "a2_annotate_event"}
    assert not guard.decide(_payload("videos/x/events/../../../lens/cli.py"), env, ROOT)[0]
    assert not guard.decide(_payload("/tmp/evil.json"), env, ROOT)[0]


def test_blocks_unknown_stage():
    ok, msg = guard.decide(_payload("videos/x/a1.json"), {"LENS_STAGE": "nope"}, ROOT)
    assert not ok and "unknown stage" in msg


def test_cli_exit_code_2_on_block():
    env = {"LENS_STAGE": "a2_annotate_event", "CLAUDE_PROJECT_DIR": str(ROOT), "PATH": "/usr/bin:/bin"}
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(_payload("lens/cli.py")),
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode == 2 and "write blocked" in proc.stderr
