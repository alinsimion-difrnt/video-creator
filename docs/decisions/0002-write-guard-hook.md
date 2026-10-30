# 0002 — Enforce declared writes with a PreToolUse hook

- **Status:** accepted
- **Date:** 2026-10-03
- **Milestone:** M0

## Context
The plan required subagents to write only under declared paths. Verified (external-facts §2):
subagent `tools:` takes tool names only; `Write(path)` permission rules are accepted but never
checked; `Edit(...)` path rules apply session-wide; frontmatter hooks in project subagents need a
trusted folder (risky on CI). A PreToolUse hook in project `settings.json` runs for subagent calls too.

## Decision
`.claude/hooks/guard_paths.py` reads `LENS_STAGE` (comma-separated stage ids, set by the annotate
workflows) and allows Write/Edit/MultiEdit/NotebookEdit only on paths declared by those stages in
`lens/stages.py`, lowercase only, inside the repo. Blocked calls exit 2 with the allowed list.
With `LENS_STAGE` unset (building sessions) all writes are allowed.

## Consequences
One registry drives both `lens dag --check` and runtime enforcement. Stages that run together
(A0+A1+A2) share the union of their writes, so per-task progress files are separate paths
(`progress/a1-*`, `progress/a2-*`). Both files must stay standard-library only.
