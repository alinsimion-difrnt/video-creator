# 0014 — S7 from A2 and the S8 record

- **Status:** accepted
- **Date:** 2026-10-05
- **Milestone:** M5

## Context
All 55 videos are annotated (runs/m5-full-20261005). S7 could only measure hand-picked candidate boxes,
and S8 was a stub, so nothing turned the annotations and the code measurements into one usable record.
S7 needs the proxy and the S4 evidence, which only exist in R2; sessions without R2 credentials cannot
run it.

## Decisions
- **S7 measures what A2 chose.** `lens measure --video <id>` (no `--event`) reads every
  `events/<eid>.a2.json` and measures each element's box, decoding the proxy once per video. Candidate
  boxes keep their id (`b03`). Manual boxes (`[ymin, xmin, ymax, xmax]` per mille of the full end frame)
  are converted to proxy pixels and keyed `m<1-based element index>`, so S8 can match them without an id
  in A2. The measured box is stored (`xyxy`), and boxes that cannot be measured are listed in `failed`
  with a reason instead of stopping the event. A measure file is skipped when its inputs hash is
  unchanged.
- **One record per video, a source on every value.** `videos/<id>/record.json` holds code facts (shots,
  events, camera, palette, SFX timing), Claude's labels (A1 shots and summary, A2 patterns and elements),
  and element timing. Element timing is `measured` when S7's best channel fit reaches
  `measure.min_fit_quality`, otherwise the annotator's estimate (`model_estimate`), otherwise absent. It is
  never mixed within one element.
- **Event status.** `annotated` (an A2 exists), `propagated` (a `duplicate` of an annotated event takes
  its pattern), `skipped` (triage reason; `overlap` keeps `of` but nothing is propagated, per ADR 0013),
  `pending` (a task without output). Events S4 built no burst for are `skipped` with `no_evidence`.
- **Final SFX labels.** The earliest confirm/override review across events decides (`label_source:
  claude`); unsure reviews, or none, keep the S3 label (`code`).
- **Checks** (written into the record; the command fails when one fails): A1 covers exactly the S3 shots
  and one part wrote the summary; A2 events and reviewed SFX ids exist; events lie inside their shot within
  `reconcile.shot_tolerance_frames`; every SFX has a final label; measured boxes belong to their event's
  A2 elements.
- **finalize.yml** runs S7 per annotated video in Actions (proxy and evidence pulled from R2), returns
  the measurements as artifacts, runs S8 for all videos and opens one data PR (measure + record JSON only).

## Consequences
- Records exist for every video, including A1-only ones (their events are `skipped: tier`).
- S9 synthesis can read one file per video and filter by `source`.
- Re-running finalize after new annotations re-measures only the events whose inputs changed.
