<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/ten/i06-radar/LEARNINGS.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# i06 Visibility Radar: learnings for the next builder

## Worked
- **Sweep angle as a precomputed integral.** θ(t) = Σ ω(t)/480 Hz, from a smooth piecewise ω (fast spin-up at t=0,
  1 rev/s for the logo, 0.82 s/rev for "every day"). `invTheta` (binary search) gives the exact time the beam crosses
  any bearing. Births, last-pass ages and per-pass growth all come from that, so every frame is seek-safe with no
  accumulation.
- **Placing story objects at θ(word time).** The question anchors and the Acme blip sit at the bearing the beam has
  on the word, so the beam hits them on cue for free.
- **The orthographic tilt as one 2×3 matrix.** `ctx.setTransform(a,b,c,d,e,f)` puts the world on the canvas:
  circles, `roundRect`, `createConicGradient` and river strokes all transform natively. Trick: build the path under the
  world transform, then reset to identity BEFORE `stroke()`. That gives uniform hairlines on squashed ellipses.
  Height is just `f - z*s*sinT`. Buildings are convex hull(base + top) for the sides plus the top quad, painter-sorted
  by `b*x + d*y`.
- **The beam-revealed lit layer.** Steel-blue block outlines go to an offscreen canvas, then `destination-in` with
  the same conic gradient, then drawImage. The beam visibly "reads" the terrain. It costs about 1 extra batched
  stroke.
- **Sweep-drawn logo.** Map the world beam angle to a screen direction (`[a*cos + c*sin, b*cos + d*sin]`), build a
  wedge polygon by sampling it, and clip twice: the outline at θ and the fill at θ − 0.7 rad.
- **Batching.** One path for all ~1300 blocks and one for all shadows keeps frames cheap. Culling is done by projected
  centre.
- **HTML for all text,** positioned from the same matrix each frame. A bubble's x is clamped by an estimated width
  (chars × 21.5 px) so it never clips; no offsetWidth in the draw path.

## Gotchas
- `check` flags world-anchored HTML that leaves the frame (`escaped_container`). Set opacity 0 when off-screen AND
  declare `data-layout-allow-overflow` on the plaques.
- Interpolating a flying bubble in screen space toward an off-screen target pins it to the frame edge. Lerp in world
  space (it then travels with the camera).
- Docked corner logo vs world plaques: fade the plaques that enter the logo's corner box.
- `snapshot` runs Gemini if GEMINI_API_KEY is set. Always use `env -u GEMINI_API_KEY ... --describe false`.

## Render times (4 shared cores, -w 2)
Snapshot of 7–11 frames: about 8 s. Draft at 15 fps: 32 s. Draft at 30 fps: 62 s. Final at looks quality, 30 fps:
2 min 30 s. freezedetect was clean on the first try, because the sweep, HUD readout and camera never stop.
