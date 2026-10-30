# 0032 — Claude directs the motion, inside our learnings

- **Status:** accepted (Robert, 2026-10-17: "let's switch to claude motion while keeping all of our learnings")
- **Date:** 2026-10-17
- **Milestone:** Phase 2, P3 (C8 build route); amends the C8 plan in docs/phase2-plan.md

## Context
The C8 plan filled HyperFrames templates (one per scene archetype) with tokens, corpus motion and word cues,
and kept a free-form builder only for scenes no archetype covers. Two comparisons on the same briefs, same
model (Sonnet subagents), same renderer (2026-10-17, evidence in the PR):

| run | build | tokens | blind review | notes |
|---|---|---|---|---|
| demo15 (15 s, silent) | A: freehand Claude | 76.5k | 7.5 / 10 | shared-surface handovers, but a glow and an underline the brand bans |
| | B: our templates + motion tokens | 97.3k | 4.5 / 10 | crossfade ghosting, clipped prompt, a 2.4 s dead hold |
| demo25 (25 s, voice + music + SFX) | A: freehand Claude | 117.1k | 4.3 / 10 | 11 grader fails (gradients, contrast, off-palette grey, dead hold) |
| | B: our templates + motion tokens | 135.7k | 3.7 / 10 | fade to blank at a handover, a stray chip over the end card |
| | C: freehand inside a direction pack + grader | 111.2k | 5.7 / 10 | 0 fails; the best handovers; overspent orange, small text |

What the numbers say: our measured motion tokens were never what separated the builds (freehand eases and
durations already sat inside the corpus ranges). Templates fix one scene at a time and have no idea of a
handover, so every templated build had to be re-assembled by hand and broke at the joins. Freehand Claude
directs layout and choreography across scenes well but drifts from the brand and from our rules. Giving it our
learnings as one compact pack (about 4k tokens instead of reading the repo) and checking it with code kept the
taste and the rules, at the lowest token cost of the three.

## Decision
A new build route, the default for tts projects (brief `build: motion`; `build: templates` keeps the old one):

- **c6_direction** (code): `projects/<p>/direction.md` assembled from the brief, the word clock, the brand
  tokens and the configured DESIGN.md sections (verbatim), the measured motion, pacing and sound ranges, the
  recipe menu (`create.motion.patterns`) and the learned rules (`create.motion.rules`, each with its source).
- **c8_motion** (Claude, `motion-builder` agent, `build-motion` skill): one composition plus SFX cues, built
  with its own taste inside the pack; it may run `create grade` within `create.motion.build` budgets.
- **c8_grade** (code): renders and checks layout, contrast, brand colours and decoration, move lengths, text
  size, accent moments, overlaps, lens pacing (hard cuts, dead holds, idle), SFX and length; writes
  `projects/<p>/motion/grade.json` (schema `MotionGrade`) and review sheets for a fresh-eyes reviewer.
- **c10_music** (code, split out of c10_audio): the bed built for the video (phase2-plan section 7) as one
  Eleven Music chunk per scene, cached by plan, checked for dropouts.
- **c12_mix** (code): narration + ducked bed + SFX at the destination's loudness.
- Brief `cut_s` may shorten the close tail (the film may not cut a word or the final hold).

Nothing learned is dropped: brand hand-offs, tokens, DESIGN.md rules, exports, patterns, pacing and sound
specs feed the pack; the lessons in docs/learnings and the two comparisons are rules in config; templates stay
for `build: templates` and as reference components.

## Consequences
- Easier: handovers are designed, not stitched; a new lesson becomes one config rule that every next build
  reads; builders cost less (no repo reading).
- Harder: quality depends on one builder's taste per run, so variance is real (the freehand winner flipped
  between demo15 and demo25). The grader and the fresh-eyes review are the guard; both must keep growing.
- Revisit after three real projects: which grade checks catch what reviewers flag, whether accent counting
  and text-size limits need tuning, and whether some recipes deserve code helpers (a shared-element morph).
