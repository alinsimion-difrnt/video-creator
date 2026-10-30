# 0024 — Caption kit: grouping, brand caption styles, burn-in

- **Status:** accepted (part of the approved roadmap, 2026-10-09)
- **Date:** 2026-10-09
- **Milestone:** M-D (first part) of `docs/research/vertical-footage-brands.md` §5

## Context
- The Acme v2 film was hand-built outside the pipeline. Its source is in R2
  (`create/acme-v2/source/acme-v2-final-source-2026-10-09.zip`).
- Most of it is bespoke per segment. The "camera rig" is a few lines inside each segment (a focal point and a
  scale, tweened), not a module.
- The reusable parts are the captions (grouping, the pill composition, burn-in with a frame-count check) and the
  assemble script.
- Every future video needs captions: narrated, filmed and vertical.

## Decision
- **`create captions <p>` (C11)** groups the timeline's words into `projects/<p>/captions.json` (validated against the
  timeline).
  - Sentences end groups, and a pause always starts one.
  - A long sentence splits where it balances best, preferring a comma or a pause.
  - Rules come per frame from config `create.design.captions`:
    - landscape: at most 6 words / 32 characters;
    - vertical: at most 3 words / 16 characters.
  - On the Acme v2 words the result is 65–67 groups against the hand-made 65, and 37 of those groups are
    identical.
- **The brand's `video.yaml` has `captions.<frame>`.**
  - Two kinds:
    - `pill`: words on a soft surface, lit as spoken (the v2 look; Acme landscape uses it);
    - `karaoke`: bold words with a stroke or surface, the spoken word in an active colour (for vertical).
  - C3 copies the style for the project's frame into tokens and checks:
    - known roles;
    - at least the frame's text minimum;
    - fits the caption band;
    - WCAG AA for text and active colour on the surface or stroke.
- **`create burn <p> --plate film.mp4 [--audio mix]` (C12):**
  - builds `create/kit/captions.html` (the v2 template, made generic: frame size, band, style, language);
  - lints and renders it with HyperFrames (a hard kill after each group's exit, per the HyperFrames lint);
  - muxes the audio, and fails unless the output has exactly the plate's frame count.
- Output goes to `data/create/<p>/render/` (not committed).

## Evidence (2026-10-09, cloud sandbox)
- **Landscape:** 10 s of the v2 clean render, burned with Acme's pill style. 300 frames in 43 s, frame-exact,
  visually matching the hand-made captioned final.
- **Vertical:** a 1080x1920 crop of the same 10 s with a karaoke style. The spoken word turned orange; groups sit in
  the vertical caption band. 36 s.

## Consequences
- Captions no longer depend on the session scratch scripts.
- **Still to bring over:**
  - an `assemble` step (concatenate segment renders frame-exactly plus the master audio);
  - a small camera helper for the template kit.
  - Both are small; they come when a multi-segment build needs them.
- **For filmed footage** the same grouping runs on the transcript's words (F5 writes a timeline with the same word
  schema).
