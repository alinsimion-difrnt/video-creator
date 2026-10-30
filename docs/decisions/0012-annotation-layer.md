# 0012 — Annotation layer (A1/A2): contracts, briefs, and a first in-session trial

- **Status:** accepted
- **Date:** 2026-10-04
- **Milestone:** M5 (partial: the Actions runner `annotate.yml` follows once the OAuth token secret exists)

## Context
BUILD_PLAN 7.4 and Appendix B define what Claude annotates. Robert approved a first run on 3 videos
"on your own". The Actions runner needs `CLAUDE_CODE_OAUTH_TOKEN`, which only Robert can add, so the
first trial runs in a Claude Code session with the same skills and subagents.

## Decisions
- **Ids come only from the packet, and the validator enforces it.** `lens validate` checks an A1/A2 file
  against the committed manifest (task id, output path, input hash), against the taxonomy (every enum;
  "other" needs its `*_other` text), and, when the packet is on disk, against `anchors.json` (shot ids,
  word indices), `candidates.json` (box ids) and `facts.json` (the SFX review covers exactly the
  candidates). An invalid file never counts as done: `lens status` only counts outputs that validate.
- **A1 parts and the summary.** Long videos are split into A1 parts by shot range (S5). The per-video
  summary (beats, hook, CTA, tone, signature moments, scores, localization) is written by the last part,
  which reads the earlier parts' JSON. Each part stays within the image budget and the summary still
  sees the whole video, as text for earlier shots.
- **Briefs instead of computation.** Annotators may only run `lens validate` and `lens status`.
  `lens status --task <video>/<task>` prints the brief: image and file paths, shots or event, the output
  path and an exact provenance object (`skill` = `<skill>@<sha256 of SKILL.md, 12 hex>`, the task's
  input hash, a timestamp). Annotators copy it; they never hash or timestamp anything themselves.
- **Packets for sessions without R2.** `lens storage pull-packets` and `packets.yml` (a private
  artifact kept for one day; nothing is committed) bring the packet images to an annotation session.
- **Scores may be null only where they do not apply** (e.g. `vo_script_quality` with no voice-over);
  hook, clarity, motion_polish and overall always score.

## Consequences
- The trial's outputs are ordinary A1/A2 files: the Actions runner, when it exists, resumes from them.
- Settings carry the plan's allowlist (Read on packets/taxonomy/skills, Edit on videos/runs, Bash only
  for `lens validate`/`lens status`). Write paths are enforced by the guard hook when `LENS_STAGE` is
  set (CI); in an interactive session the trial is checked afterwards with `git status`.
