---
name: build-motion
description: Build a narrated explainer the motion way (ADR 0032) — Claude directs one HyperFrames composition with its own taste inside projects/<p>/direction.md (brand rules, measured motion/pacing/sound, recipes, learned rules), then `create grade` checks it, `create music` and `create mix` finish it. Use for any new tts project with `build: motion` (the default) after `create timing` and `create tokens`.
---

# build-motion

Claude directs; code measures. The direction pack carries everything the studio has learned, so the builder
reads one file instead of the repo, and `create grade` checks what code can measure. Templates
(`build: templates`) stay for projects that ask for them.

## The flow (main session)
1. `uv run create status <p>`: c1-c5 and c3 done (brief with `build: motion`, optional `cut_s` to shorten the
   close tail; script with each scene's `on_screen` items and `notes`, which the pack carries; voice; timeline;
   tokens).
2. `uv run create direction <p>` -> `projects/<p>/direction.md`. Read only its first lines to check it.
3. `uv run create grade <p> --new-round`, then spawn the `motion-builder` agent with the slug. Do not build in the main session (images and long outputs
   stay out of it).
4. When it reports, run `uv run create grade <p> --on-record` yourself (the grade on record; not counted).
   Fails must be fixed: run `uv run create grade <p> --new-round`, then send the findings back to the same
   agent (SendMessage) for one more round. `create grade` itself stops a builder that has spent its round's
   full grades or snapshot frames (exit 2).
5. Fresh eyes: give a `lab-reviewer` agent `data/create/<p>/motion/render/review/overview.png` and
   `handovers.png`, the brief's beats and the rules in direction.md section 8, and ask for scores and defects by
   time, each as "at <t> s: what is wrong, why it matters, the fix". Also ask two questions: could a
   competitor put their logo on this film and change nothing else (if so, which moments are generic)? Which
   moves look like stock HyperFrames defaults rather than the brand's own? Fix what it finds that the grader
   cannot see, the same way as step 4.
6. `uv run create music <p> --dry-run`, then `uv run create music <p>` (ElevenLabs credits: ask first in team
   mode; a rerun with the same plan is free).
7. `uv run create mix <p>` -> `data/create/<p>/motion/final/<p>.mp4`. Listen; send it.
8. New lessons go into config `create.motion.rules` (with their source), so the next pack carries them.

## The build (motion-builder agent)
1. Read direction.md once, fully. Plan before writing code, briefly: per scene the layout and the reveals on
   their words (the word clock, section 2); per handover the ONE carrier element and how it changes shape; the
   pattern ids from the recipe menu (section 7) you will use; where SFX land.
2. Write `projects/<p>/motion/index.html`:
   - root `<div id="main" data-composition-id="main" data-width=".." data-height=".." data-start="0"
     data-duration="<film length from section 1>">`, sized to the frame, overflow hidden;
   - link `assets/fonts.css`, load `assets/gsap.min.js`; logo `assets/logo.svg`; the CSS variables from
     section 3, verbatim;
   - one paused GSAP timeline spanning the film, `window.__timelines = {main: tl}`; deterministic (no
     Math.random, Date, requestAnimationFrame loops or CSS animations); ids start with a letter;
   - every number and duration inside the measured ranges (section 4); a reveal on the word that names it.
3. Write `projects/<p>/motion/sfx.json`: `[{"t": seconds, "sfx": "<name>", "gain_db": <dB>, "x": 0..1}]`,
   names and gains from section 6, onsets at the measured offsets to their reveal, `x` (optional) the reveal's
   horizontal centre as a share of the frame width so the mix pans the cue there; `uv run lens validate` it.
4. `uv run create grade <p> --lint-only` until it is clean (free, no render).
5. `uv run create grade <p>` (renders, ~1-2 min). Fix every fail; fix cheap warns. Watch especially: text
   overlaps, accent moments, idle stretches (pacing), dead holds, small text.
6. Look with `uv run create grade <p> --snapshot <times>` at the handovers and the busiest moments; the frames
   land in `data/create/<p>/motion/render/snapshots/`. Spend the frame budget where the grade cannot see:
   whether the carrier reads as one element, hierarchy, polish.
7. One more full grade if the budget allows, then report.

## What the grade checks (create/grade.py)
HyperFrames lint, runtime, layout and contrast; colours outside the brand tokens (light tints of accent and
status colours are fine); gradients, glows, glass, underlines; moves past `max_move_s`; the ease mix (at least
`min_ease_families`, overshoot within the corpus share and only on small elements); the frame at rest inside a
handover window (last word of one scene to just after the next scene's first word); text under the frame's
minimum size, accent moments per frame, text running into text or the logo (each only when it lasts
`persist_s`); hard cuts, dead holds and idle stretches from lens signals; SFX names, times and count; the
film's length. It also writes the two review sheets. It cannot judge taste: that is the builder's frames and the
fresh-eyes review.
