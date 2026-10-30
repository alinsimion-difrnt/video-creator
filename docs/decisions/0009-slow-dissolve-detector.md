# 0009 — Slow transitions on real footage: long-baseline dissolve detector

- **Status:** accepted
- **Date:** 2026-10-03
- **Milestone:** M2 (real footage) / M4.5

## Context
The first real run on Acme v1 found 0 of its 14 transitions. Its fades and pushes run over ~0.5–1 s on a
light canvas, so the frame-to-frame change stays under the 0.03 noise-floor-relative thresholds the
synthetic fixtures were tuned with. The whole video became one shot, which also broke "SFX at scene
starts". Frame-to-frame tests cannot see a slow change; a change over a longer baseline can.

## Decision
After the existing per-frame detectors, `detect_dissolves` looks for peaks of change across a
`dissolve_baseline_s` baseline (caption band `ignore_bottom_fraction` excluded) above
`dissolve_min_change`, away from known transitions (`min_shot_s`). Each candidate span is grown over
frames above the noise floor (≤ `dissolve_max_s`) and must pass two tests:
- **Layout replaced:** edge retention (old edges still present in the new frame) ≤ `dissolve_max_retention`.
  An in-card text scroll keeps its frame (0.45 on v1) and is rejected; an old frame with almost no edges
  counts as retained (a fade-in onto an empty canvas is an entrance, not a transition).
- **Kind:** summed phase-correlation shift ≥ `push_min_total` → push (with direction); enough frames with a
  scale step → zoom-through; otherwise crossfade, which must also fit an alpha blend of the end frames
  plus the canvas (relative NNLS residual ≤ `dissolve_max_residual`). A box moving alone does not.

All thresholds live in `signals.video` in config/lens.yaml.

## Consequences
Acme v1 now gives exactly 14 transitions (7 crossfade, 5 push left, 2 zoom-through), matching the
known count, and all synthetic video/caption tests still pass. The thresholds are tuned on one real video;
the pilot corpus (dark UI, 60 fps, busy launch reels) will re-test them, with failures added as fixtures.
