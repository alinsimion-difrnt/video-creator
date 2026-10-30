<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/ten/i05-liquid-data/LEARNINGS.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# i05 Liquid Data: learnings for the next builder

## Architecture that worked (seek-safe particles)
- **Closed-form phases, no simulation.** Each phase is (start T, duration, particle ids, targets, tone, orange,
  per-particle delay, curl amplitude). Position at time t composes all phases in order:
  `p = lerp(p, target_k(t), ease(u_k))`. Overlapping phases stay continuous, and any frame can be rendered alone.
  GSAP only drives a `clock.t` proxy, and `onUpdate` redraws. Look at src/engine.js `particles()`.
- **Dynamic targets** are functions of t: the spiral at t=0, the ChatGPT spin and dock, the void's perimeter flow,
  the globe and rings, and the "every day" stream that steps one day every 0.42 s. Setting `OUT[3]` lets a dynamic
  target override tone, which gives the globe a lighter back side.
- **Curl noise for the in-flight swirl only.** The displacement is `curl(ψ) · Σ amp·sin(πu)`, so it is zero at rest.
  That respects "no idle wobble" for free.
- **Sampling targets.** `Path2D` from the inlined SVG `d` attributes goes into an offscreen canvas, and a seeded
  pick takes points from it. Points come from two pools, a stroked pass (`sf`) and the fill. With interior points
  drawn lighter (`lift`), bubbles and rows read as outlines and the crisp text stays legible. For marks with no
  stroke, an edge band (filled pixels within 3 px of empty) does the same job.
- **Coherent assignment.** Sort both the particles (by their previous target) and the new targets by the same
  projection, plus jitter. This gives sweeping morphs instead of chaos.
- **CPU splatting into one ImageData.** Points get a bilinear 2×2 splat, or a soft disc when out of focus
  (circle of confusion from |z − focus|). Far points fade toward the background colour. 40k points cost about
  0.1 s/frame with 2 workers.

## Render numbers (4 shared cores, 2 workers)
- Snapshot of 12 frames: about 10 s. Draft render at 15 fps: about 40 s. Draft at 30 fps: about 90 s.
  Final at "looks" quality: about 150 s for 927 frames.

## Gotchas
- `lint` requires `window.__timelines` to be registered in an inline script. Externalising all the JS (to get past
  the 500-line warning) fails lint, so keep the timeline lines inline and put the engine in assets/engine.js.
- Small points lose almost all their alpha if alpha scales with r²: the first opening frame went nearly invisible.
  Use a floor (`0.4 + r²`).
- The focus distance must be in world z, not camera-relative. My first version blurred the whole opening.
- freezedetect is stricter on the final "looks" render than on draft: a 1.7 s near-still at 16.2 s only showed up
  in the final. Any hold over about 1 s needs a camera drift or other motion.
- Inlined Lobe gemini-color SVG has gradient ids. Remove the hidden source copies after cloning so the ids are
  not duplicated.
- Crisp overlays use the same projection as the particles (world x,y,z → screen), so camera pushes keep the labels
  locked to their particle shapes. A label near the frame edge gets clipped during a push, so fade it before the
  push.
