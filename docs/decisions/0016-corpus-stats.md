# 0016 — S9 corpus statistics and pattern proposals

- **Status:** accepted
- **Date:** 2026-10-05
- **Milestone:** M8

## Context
BUILD_PLAN 8 asks for weighted statistics over the corpus (stats in DuckDB) and for clusters of the
annotators' `other` patterns. Plan-audit I6 asks for confidence-weighted medians with bootstrap
intervals. 55 records exist: 27 reference, 18 average, 9 competitor and 1 own video.

## Decisions
- **numpy, not DuckDB.** The corpus is a few thousand rows read from 55 JSON files. Weighted quantiles
  and a bootstrap are a few lines of numpy, and DuckDB would be a new dependency doing nothing more. If
  the corpus grows past what fits comfortably in memory, revisit.
- **Weights** (config `synth.weights`):
  - **Tier:** reference 1, average 0.5, competitor 0.5, own 0. Our own videos are what `lens compare`
    places against the corpus, so they are never averaged into it.
  - **Score:** overall score / 5.
  - **Fit quality:** for measured motion values only.
- **Every number is a `Stat`.** It carries the weighted median, the quartiles, a bootstrap interval of
  the median (from `synth.min_n` observations), n and the number of videos.
- **Only code-measured motion feeds the motion stats.** Annotator estimates never do. Change types are
  the union of Claude's labels and the measured directions (ADR 0015).
- **Outputs** go to `corpus/stats/`:
  - `motion.json`: durations by role and change type, easing and ease mix, overshoot, three spring
    clusters on (zeta, settle) with a Remotion config, stagger;
  - `sound.json`: SFX density, label mix, reveal offsets per label, loudness and ducking;
  - `pacing.json`: shot length by format, pace variation, cuts on beat, time to the first UI shot, WPM,
    pitch variation, caption density;
  - `patterns.json`: per taxonomy pattern, its events, videos, measured duration, mixes and the
    best-weighted examples (ids only, no media).
- **Pattern proposals.** Each `other` event's "proposed name: description" is embedded with
  all-MiniLM-L6-v2 (Apache-2.0, local CPU, pinned revision; external-facts 13) and clustered by
  average-link at cosine >= `synth.cluster.threshold`.
  - A cluster becomes a proposal only with `min_members` events from `min_videos` (2) videos, because
    one brand's habit is not a corpus pattern.
  - A proposal close to an existing pattern (>= `merge_similarity`) is suggested as a merge.
  - Robert's verdicts (`status`) survive re-runs when the proposal keeps its id.

## Results (2026-10-05)
- 45 weighted videos and 837 measured elements.
- 21 taxonomy patterns with stats.
- 158 `other` events gave 10 proposals: 8 new and 2 suggested merges (`prompt_field_type_on` into
  `prompt_type_on`, `ui_camera_pan` into `ui_camera_push_in`). The other 153 events are one-offs.

## Consequences
- A3 pattern cards and archetypes read only these files and the records' ids; the numbers on a card
  come from `Stat`s.
- G4 decides on the 10 proposals.
