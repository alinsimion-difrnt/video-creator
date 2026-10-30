# Motion quality research (2026-10-06)

Why the P3 storyboard and the three direction tests were rejected ("bad animations, elements that hover into each
other, no relevant direction, overuse of text, AI names instead of their icons"), what the research found, and
how Phase 2 works from here. External facts are in `docs/external-facts.md` §15-16.

## Root causes
1. **No references while designing.** The corpus videos were in R2 and never watched for v2. The AI-visibility
   references (Profound, Scrunch, Ahrefs Brand Radar, Conductor) share one grammar: one focal object per beat,
   very little text, real engine logos, real product UI, a camera in 3D space, elements carried across cuts.
2. **Engines as text.** v1's house rule ("colour plus label, never a logo", `docs/handoff-v1.md`) carried over.
3. **Drawn UI instead of the real kit.** The brand hand-off has the real components (Competitor breakdown,
   Visibility over time, Rankings, Sentiment); the templates drew lookalikes.
4. **Slides, not shots.** Elements popped in at fixed positions, so they collided; scenes ran 9-16 s.
5. **No gate.** `hyperframes check` (layout/motion/contrast across time) and HyperFrames' motion doctrine were
   unused; all review was on stills.

## Corpus numbers (computed from `videos/*/record.json`, `exports/pacing.json`)
| Measure | Premium | Acme v1 |
|---|---|---|
| On-screen words per shot (median) | 3 | 36 |
| Shots with no text | 24% | - |
| Shot length, narrated explainers (median) | 2.74 s | 9.64 s |
| Transitions: hard cut / continuous move / crossfade | 53% / 30% / 3% | 0% / - / 47% |
| Shots with a depth cue (blur, shadow, tilt) | about 80% | - |
| Motion events with a camera move | about 25% | - |

## Sources and what each gave
- **HyperFrames skills** (Apache-2.0): `product-launch-video` motion doctrine, `pr-to-video/cut-catalog.md`
  (velocity-matched cuts), `hyperframes-animation` rules and blueprints, `hyperframes check` gate.
- **Plugin directory skills:** video-shotcraft (Apache-2.0: styleframes first, one motion per shot, hold budgets,
  clean-context final review), IMG.LY CoDesign judge (read, not copied: eight axes, every axis >= 8, judge
  mid-transition frames), animation-studio (MIT: frame QA for text overlap, contrast, pacing), Anthropic
  frontend-design (AI-tell list). The Remotion skills are API guidance, not design craft.
- **Craft:** Mayer (narration is not on-screen text), Material/Carbon easing and durations, School of Motion
  match cuts, style frames before animation.

## Proof
The s03 line was rebuilt six times as an 11 s HyperFrames composition with real engine icons (Lobe Icons) and the
kit's Competitor breakdown, gated by `hyperframes check --at-transitions` and scored by a clean-context judge
against reference filmstrips. It is clearly better than the rejected directions (text, icons and direction
fixed; no overlaps found by the checker) but is not premium: judges scored composition 6 and motion 6 and put it
"about two tiers below" the references. The flat scores after round 5 showed the missing piece is a visual
idea (a graphic metaphor and a camera world), which is decided in style frames, not by polishing code.
Renders: R2 `create/acme-v2/proofs/`.

## Working method from here
1. Pull the matching premium moments (5-10 fps filmstrips) for each scene before designing.
2. Real assets only: engine and source logos, kit components, captures of the Acme app.
3. Style frames (stills, including the busiest frame) for 2-3 concepts, critic-scored, chosen by Robert before
   any animation.
4. Re-cut the storyboard to about 30 shots of 2.5-3.5 s, median <= 6 words on screen.
5. Motion follows the HyperFrames doctrine: reveals on the spoken word, `power3`/`expo` eases, no bounce, no
   idle drift, velocity-matched cuts.
6. Two gates before Robert sees anything: `hyperframes check --at-transitions` clean (deliberate layering
   declared with `data-layout-allow-*` and a reason) and a clean-context judge with every axis >= 8 on settled
   frames and 10 fps transition strips. Thresholds go in `config/lens.yaml`.
