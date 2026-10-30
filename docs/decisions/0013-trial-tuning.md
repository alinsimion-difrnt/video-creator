# 0013 — Tuning after the M5 trial: overlap triage, UI-demo patterns, camera note, repack

- **Status:** accepted (the new pattern names need Robert's approval: merging the PR is that approval)
- **Date:** 2026-10-05
- **Milestone:** M5

## Context
The 3-video trial (runs/m5-trial-20261004/summary.md) produced valid files everywhere, but showed waste
and gaps before the 52 remaining videos (about 770 tasks): overlapping events annotated two or three times,
27 of Acme's 60 events labelled "other" with recurring names, and annotators confused by camera facts.

## Decisions
- **Overlap triage.** An event whose S4 burst (the frames the annotator sees) lies at least
  `packets.overlap_merge_min` (0.3, as a share of the shorter burst) inside an already kept event's burst
  in the same shot is skipped as `overlap` with `of` = that event. On Acme's packets this merges exactly
  the pairs the annotators flagged (e009–e011, e019/e020, e055/e056, e059–e061) plus similar builds:
  14 of 60 tasks. At 0.5 it merged only 7 and missed flagged pairs. Unlike `duplicate`, nothing is
  propagated to the skipped event: it is the same build, not a repeat.
- **Eight UI-demo patterns** added to `taxonomy/v1.yaml`: prompt_type_on, ai_answer_stream,
  input_text_cycle, chip_append, skeleton_resolve, masked_scroll, blur_crossfade, layout_reframe. They
  cover about 21 of the trial's 27 "other" events. This is an early, narrow G4 decision; the full
  catalogue review stays at G4 after synthesis. Existing "other" annotations stay valid.
- **Camera facts are explained, not changed.** `camera.move` is "none" by design when the change covers
  less than `signals.video.camera_min_area` of the frame. The raw whole-frame sums (`pan_x`, `pan_y`,
  `scale`) then describe content moving inside the frame. The annotate-event skill now says so.
- **Annotated videos are never repacked.** `build_packets` refuses when any task output exists: new task
  ids and input hashes would orphan the annotations. `repack.yml` rebuilds packets for A2-tier videos
  without annotations from the S3/S4 data in R2 (`lens storage pull-media`).

## Consequences
- The trial videos keep their packets and annotations; the other A2-tier videos get fewer, cleaner tasks.
- Old event folders of merged events stay in R2 (unused; not in any manifest).
