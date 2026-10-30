<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/ten/i02-swarm/LEARNINGS.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# i02 learnings (for the next builder)

## Worked
- **Bake the boids, play back by t.** `src/build.py` (numpy via `uv run --no-project --with numpy python -I src/build.py`;
  system pip had no numpy and pip install hung) simulates 420 boids at 60 Hz in ~10 s and writes a 15 fps int table
  (x, y, size) of 2.2 MB to `comp/data.js`. The page Catmull-Rom interpolates by t, which is 100% seek-safe.
- **Screen-space flock over a world-space city, with one shared camera.** `src/cam.py` holds the camera keys
  (monotone cubic) and a hand-written projection. The page gets the per-frame camera table and uses the SAME
  formula (no DOMMatrix), so world anchors (street launches, tower plaques, rival buildings) match the flock targets
  exactly. A small Newton solve places a world point at a wanted screen position when picking keys.
- **Lock blending.** In a formation, pos += (target - pos) * f(lock) inside the sim (fed back into the state). Shapes
  become exact (logo, bars, rings) and release never jumps.
- **Logo to points without a rasterizer.** Parse the SVG path (M/L/H/V/C/Z), flatten curves, then run an even-odd
  point-in-polygon test on a hex grid. Search the spacing until the count >= N, then subsample to exactly N.
- **Sprite bubbles on canvas.** Four pre-rendered sprites (white, far-grey, ink, orange) are drawn with drawImage and
  crossfaded per bubble. 420 a frame is cheap. Tilt each bubble by its velocity for life.
- **Formation contrast on white:** white bubbles vanish into a white UI card, so they switch to ink #50697F when they
  lock into bars and markers. Draw the card in the canvas (under the bubbles); the DOM keeps only the text.
- **Lint:** a 300+ line inline script triggers `composition_file_too_large`. Put the data and the engine in
  `data.js`/`swarm.js` and keep only the timeline registration inline, which lint requires. Do not use `offsetWidth`
  in the draw path; use `translateX(-50%)` instead.

## Gotchas
- Sort key vs size: I sorted by a priority key and then drew with that key as the width, which made giant bubbles.
  Keep the two separate.
- An obstacle repulsion (keeping the swarm off the cards) also repels the bubbles that must land INSIDE the card, so
  mask them out.
- Sizes must be continuous across phase handovers (bar size -> logo size), or the bubbles balloon for a few frames.
- 384 px strips are useless for a white-on-white piece. Review at 640 px, 4x3, 5 fps, plus full-res stills.

## Render times (4 shared cores, load around 10)
- Draft, 15 fps, `-q draft -w 2`: 1 min 35 s. Final, 30 fps, looks quality, `-w 2`: 4 min 27 s. Snapshot of 14 frames: 27 s.
