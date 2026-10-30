---
name: annotate-batch
description: A0 orchestrator — pick videos with pending annotation tasks, dispatch video-annotator (A1) and event-annotator (A2) subagents with fresh contexts, and write the run summary. Resumable; everything is derived from files.
allowed-tools: Read, Write, Bash(uv run lens status:*), Bash(uv run lens validate:*), Agent
---

# annotate-batch (A0)

Inputs: a run id (`<run_id>`, e.g. the workflow run id or a date-stamped id) and optionally video ids.

1. Work list: `uv run lens status --pending --limit <annotate.videos_per_run>` (config/lens.yaml), or the
   given video ids. `uv run lens status --json` shows each video's pending task ids.
2. For each video, in order:
   - A1: dispatch one `video-annotator` per pending `a1-p*` task, **in part order**: the last part writes
     the video summary and reads the earlier parts, so it runs after them.
   - A2: dispatch `event-annotator` subagents with groups of `annotate.events_per_subagent` pending
     `a2-*` tasks of the same video. A2 groups may run in parallel; they share no files.
   Each subagent gets a fresh context, so images never accumulate here. Do not read packet images yourself.
3. After each subagent: `uv run lens validate <output>` for each of its tasks. A task that still fails is
   retried once (`annotate.task_retries`) with the validator errors in the prompt, then recorded as failed.
4. Write `runs/<run_id>/summary.md`: per video, tasks done / failed (with the validator reason) / remaining,
   and "stopped: usage limit" or "stopped: turn budget" when that applies. Write `runs/<run_id>/cost.json`:
   {"tasks": n, "images": n, "subagents": n, "wall_time_s": n}.
5. Stop cleanly at the batch or turn budget; a rerun continues from `lens status`.

Never run git or any other shell; never edit packet files; never write another stage's outputs.
