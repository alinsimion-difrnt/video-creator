#!/usr/bin/env python3
"""PreToolUse hook: Claude may write only to the paths its active stage(s) declare.

Active stages come from the LENS_STAGE environment variable (comma-separated stage ids,
e.g. "a0_annotate_batch,a1_annotate_video,a2_annotate_event"), which the annotate
workflows set. When LENS_STAGE is unset (normal building sessions), every write is allowed.

Exit code 2 blocks the tool call; stderr is shown to Claude. Standard library only.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}


def decide(payload: dict[str, object], env: dict[str, str], repo_root: Path) -> tuple[bool, str]:
    if payload.get("tool_name") not in WRITE_TOOLS:
        return True, ""
    active = [s.strip() for s in env.get("LENS_STAGE", "").split(",") if s.strip()]
    if not active:
        return True, ""

    sys.path.insert(0, str(repo_root))
    from lens.stages import allowed_writes, is_write_allowed

    tool_input = payload.get("tool_input")
    raw = ""
    if isinstance(tool_input, dict):
        raw = str(tool_input.get("file_path") or tool_input.get("notebook_path") or "")
    if not raw:
        return False, "write blocked: no file path in tool input"
    cwd = Path(str(payload.get("cwd") or repo_root))
    target = (cwd / raw).resolve() if not Path(raw).is_absolute() else Path(raw).resolve()
    try:
        rel = target.relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return False, f"write blocked: {raw} is outside the repository"
    try:
        if is_write_allowed(rel, active):
            return True, ""
        allowed = "\n  ".join(allowed_writes(active))
    except KeyError as exc:
        return False, f"write blocked: {exc}"
    return False, (
        f"write blocked: {rel} is not declared by active stage(s) {', '.join(active)}.\n"
        f"Allowed (lowercase only):\n  {allowed}"
    )


def main() -> int:
    payload = json.load(sys.stdin)
    repo_root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
    ok, message = decide(payload, dict(os.environ), repo_root)
    if not ok:
        print(message, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
