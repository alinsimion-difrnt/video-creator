<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/ten/i09-hologram/LEARNINGS.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# i09 learnings (for the next builder)

## Architecture that worked
- **CSS-3D world + canvas, one view matrix.** `setCam(t)` builds a look-at basis (y-down, right-handed: back = -fwd,
  right = (0,1,0) x back, down = back x right) and writes `matrix3d(R.x,D.x,B.x,0, R.y,D.y,B.y,0, R.z,D.z,B.z,0,
  tx,ty,tz+P,1)` on `#world` (left 960, top 540, size 0, transform-origin 0 0) inside a stage with `perspective:P` and
  origin at the frame centre. The canvas projects with `s = P/depth` from the same basis. They match exactly; no
  calibration was needed. Each entity: `translate3d(x,y,z) rotateY rotateX scale translate(-w/2,-h/2)` with fixed px
  sizes (no offsetWidth) and `transform-origin:0 0`.
- **Text in CSS 3D stays crisp** in the HyperFrames render (checked at full res at scale 0.6–1.9).
- **Glass panels** (rgba white .84, inset highlight, hairline, long soft navy shadow) read as Vision Pro on a white
  world without backdrop-filter (which I avoided: it is unreliable inside preserve-3d).
- **Holographic city on canvas**: ~330 painter-sorted boxes rendered to an offscreen canvas, then `destination-out`
  1.6 px lines every 5 px at 0.16 alpha for scanlines, then composited. Buildings are `min(h, scanPlaneHeight)`, so a
  rising plane "prints" them. Starting the build at t0 = -0.3 s gives a busy frame 0.
- **Flip reveal**: preserve-3d container, two `backface-visibility:hidden` faces, plus opacity switched at 90°.

## Gotchas
- `check` `text_occluded` false positives in 3D: the audit exempts only elements whose NEAREST preserve-3d ancestor is
  shared. A card in `#world` vs a face inside a preserve-3d panel are different contexts, so it flags. The fix is
  `data-layout-allow-occlusion` on the TEXT element itself (the span), not on the container or the occluder.
- `tl.seek(t)` suppresses onUpdate; use `tl.seek(t, false)` in your own puppeteer probes (src/probe.mjs prints DOM
  rects at given times; src/errs.mjs prints page errors). A `-x ** 2` syntax error gave a silent blank snapshot: run
  `node --check` on the engine first.
- Any per-frame shared state must be computed from t in the same frame (I first fed link lines from the previous frame's
  tag positions: not seek-safe). Use pure helpers like `tagPos(i,t)`.
- With a moving camera, windows you leave behind come back into frame later when the camera pulls back. Kill them with
  an explicit time fade, not only a depth fade.
- Snapshot thumbnails mislead about vertical placement; measure with the probe.

## Render numbers (4 shared cores, -w 2)
Snapshot of 6–11 frames: ~6 s. Draft 15 fps: 55 s. Draft 30 fps: 58 s. Final looks 30 fps: 2 min 35 s.
Rounds: r1 draft 15 fps, r2 draft 30 fps, final. freezedetect clean on r2 and final; lint 0/0; check ok (0 errors,
0 warnings, 3 info for rows passing each other during the daily re-rank).
