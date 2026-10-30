# 0015 — G2 by machine checks: `lens eval`

- **Status:** accepted
- **Date:** 2026-10-05
- **Milestone:** M6

## Context
BUILD_PLAN 11.2 plans a human gold set: Robert corrects A1 and A2 for 3 videos (about 2 hours). The review
page (`lens gold page`) asked expert questions: shot types, compositions, change types, motion patterns.
Robert could not answer them and chose **machine checks only** (G2 decision, 2026-10-05).

## Decisions
- **`lens eval` (S13) scores the annotation layer three ways**, with no human labels:
  - **Answer key.** Acme v1 is our own render, and its HyperFrames source gives exact truth for every
    GSAP tween: its target's box, its properties, its ease and its SFX clips. This scores Claude's element
    boxes (precision and recall at `eval.answer_key.min_iou`), change labels, easing guesses and SFX
    labels. It also scores the S3 classifier alone, so "CLAP alone vs after Claude review" is measured.
    Elements where the key animates nothing (text swaps, the caption pill) are counted as unjudged,
    not as wrong.
  - **Consistency.** A blind second annotation of an even sample of 10 events
    (`lens status --task … --rerun <run>`, written to `runs/<run>/videos/…`, never over the canonical
    answer) is compared with the first.
  - **Measured share.** Annotated reference events with at least one S7-measured element; M6 accepts at
    `eval.min_measured_share` (0.6).
- **The result is `runs/eval/<hash>.json`.** The hash covers `.claude/skills/**` and `taxonomy/**`, so a
  skill or taxonomy change needs a new eval (the CI gate in plan-audit M9 can read it).
- **The gold-set code stays but is unused.** That covers `gold/`, `lens gold seed|page|import` and the
  review page, in case a simpler human check is wanted later. Nothing in the eval reads it.
- **The tuning round is code, not prompts.** The eval found two code-side gaps, and both are fixed in S8:
  - **Measured changes.** Each measured element's record now carries `timing.changes`: the directions S7's
    channels show (`slide_up`, `fade`, `scale_up`…). Annotators often see a fade but miss a 10–50 px rise.
    Code measures it, so code names it.
  - **Easing class from the joint fit.** `timing.easing_class` now comes from the joint-fit GSAP ease (one
    ease for all channels, ADR 0011). One channel's fit alone often read "spring" or "ambiguous" for a
    plain ease-out.

## Results
Baseline, then after the tuning round (same annotations): docs/evals/m6-eval.md.

## Consequences
- Annotation quality is tracked without human time. What the machine checks cannot see (beats, hooks,
  scores, shot-level labels) has no score yet; the consistency check is the only signal there.
- Skill edits that would fix box choice need a re-annotation to score. Later tuning can re-run the
  10-event sample with `--rerun` and compare.
