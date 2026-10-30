<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/ten/i04-inside-model/LEARNINGS.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# i04 Inside the Model: learnings for the next builder

## Architecture (seek-safe 3D in a 2D canvas, no WebGL)
- `src/engine.js` holds the whole world. GSAP tweens only a `clock.t` proxy, and `apply(t)` redraws the canvas and
  places every DOM overlay. Everything is a pure function of t, and the PRNG is mulberry32 with fixed seeds.
- **Camera.** It is a look-at camera from time keys `[t, pos, target, fov, roll]`, interpolated with cubic Hermite.
  Use **monotone Fritsch–Carlson tangents**. Catmull-style tangents overshot badly at uneven key spacing (the camera
  drifted the wrong way for 2 s before a fast move). Ride keys are generated from the pulse's node route
  (position = node + offset, target = a point ahead), which keeps the pulse centred.
- **Near-plane clipping** of every edge (cz > 40) is essential once the camera flies through layers. Without it,
  lines invert through the lens.
- **Alpha bucketing.** About 2000 edges are put into 12 opacity `Path2D` buckets, giving 12 strokes per frame.
  Render cost: 15 fps draft for 30.9 s in about 22 s, and the final 30 fps "looks" in about 95 s (2 workers).
- **Bokeh sprite pyramid.** Each node style is pre-rendered at 8 blur levels with `ctx.filter = blur()` (this works
  in headless Chrome), and the level is picked from the circle of confusion. Cap the blur for coloured (lit)
  sprites. A blurred orange node became a big orange blob that read as a stain.
- **Logo from lit paths.** Use `getTotalLength / getPointAtLength` on a temporary in-DOM SVG path, split at jumps
  over 25 units (subpaths such as the O's counter), halve each subpath, and resample everything to 60 points. Each
  strand is lerped from its projected network route (resampled by arc length every frame) with a per-point
  stagger, so it reads as "drawing".
- **DOM labels pinned to 3D** use the same projection. Clamp their scale (0.95–1.2) or text drops under 30 px.

## Gotchas
- A **stale per-frame variable** (`q.dot`, set only while a bubble was flying) persisted across frames after the
  flight. Sequential rendering drew three frozen orange dots for 3 s. Reset per-frame state on *every* branch. A
  bug like this is also a seek-safety bug.
- Distant objects need a different fog during the opening (`FOGN`/`FOGR` lerped by t), or the network over the
  city is invisible. A tighter FOV (40°) at the start made the sphere loom without moving the camera closer.
- The sideways three-net view looked off-centre because the camera target was beyond the net plane. Aim the
  target *at* the plane that holds the content.
- Snapshot (`--at`) takes about 7 s for 10 frames. Use it for framing, then 15 fps draft renders for motion.
- freezedetect was clean on the first full render. The logo hold (20.9–21.7 s) survives only because the logo
  scales 0.94→1.0 and the strands fade behind it.
