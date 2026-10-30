<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/ten/i08-orbits/LEARNINGS.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# i08 Orbits: learnings for the next builder

## Architecture (src/engine.js, src/index.tpl, src/build.py → comp/)
- One canvas drawn from t, using the i06 pattern: a GSAP proxy tween calls `draw(t)`, the engine lives in
  engine.js, and only the timeline registration is inline. Lint 0/0, check ok on the first try.
- **Orbit camera rig**: the keys are (target xyz, distance, pitch, yaw), with monotone cubic per channel. The basis
  is forward = (cos p sin y, sin p, cos p cos y), right = (cos y, 0, −sin y), up = forward × right. It has no
  singularity at pitch −90°, so a top-down move is just a key. To put a world point at a chosen screen pixel
  (the sun under the logo's G), offset the target along right/up by `px·dist/FOC`.
- **Kepler orbits analytic in t**: mean anomaly M = M0 + 2π·τ(t)/P. τ is an integrated clock (480 Hz table) so
  "every day" speed-ups are just a rate curve. Newton solve E (6 iters), sun at a focus, small inclination per ring.
  Equal-mean-anomaly tick dots on each ring make a subtle Kepler 2nd-law detail that avoids the school-diagram
  look.
- **Depth without 3D**: split every ring segment and planet by depth against the sun (back pass → sun → front
  pass). Planet highlight offset toward the projected sun direction. Pearl sun = radial gradient plus a soft navy
  shadow (shadowBlur ≈ R) and a hairline rim, with a rotating tick-dial corona.
- **Trails** = a ribbon polygon from samples at M − L·k/n, tapered (pow 1.4) with a linear gradient alpha. L grows
  with orbital speed, so the time-lapse star-trail look happens automatically.
- **Hero question comets live in screen space**: trail = head(t − k·dt) + (0, rise·k·dt). That is cheap and
  seek-safe, and the bubble stays readable. The fall into the sun is a bezier toward the sun's projected position
  at t.
- **Label relaxation**: sort labels by y and push apart pairs closer than a gap (6 passes). Put each label on the
  outward side of its planet (left if the planet is left of the sun) so it never covers the engine logo.
- **Logo match cut**: rings lerp (outer first) to the G-ring radius `AG = 214·dist/FOC` at a static top-down
  framing. A 61 px orange canvas ring sits exactly under the HTML logo's G, then crossfades in 0.2 s. Logo paths are
  tagged with classes in build.py so the arrow and letters animate per path (`transform-box: fill-box`).

## Gotchas
- Wide contrail ribbons on white read as grey needles or stalactites. Keep them thin (≤0.35 of the bubble size),
  with alpha ≤0.25 and a white core, and always keep a visible bubble head.
- A question bubble parked at the frame centre collides with the sun that ignites there. Drift it up first.
- Shock rings that are too big (≥1900 world) look like stray orbits in the wide shot. Use ≤1150 with a squared fade.
- Orange dashed ring 5 must stop being orange after the logo, or it pops back dashed when the orbits re-expand.

## Render times (4 shared cores, -w 2)
Snapshot of 5–13 frames: about 9 s. Draft at 15 fps (`-q draft -f 15`): 33 s. Full 30 fps: 1 min 55 s. freezedetect
was clean on every round (orbits and camera never stop). Rounds: r1 and r2 draft, r3 full, r4 = sketch.mp4.
