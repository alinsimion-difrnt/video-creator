<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/six/n6-inflate/LEARNINGS.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# n6 Inflate: learnings

1. **Inflation as a profile, not a scale.** I build a stadium outline and push it inward with a superellipse
   profile (p = 2.5). The normals come from the exact implicit gradient, so there are no seams. This gives a
   premium pillow, and thickness T drives the inflation from a flat skin to a puffy shape. I rebuild it on the CPU
   only when (L, R, T) change. It costs about 0 ms in practice: 40 balloons at 80x27 vertices each.
2. **Squash-and-settle without bounce:** thickness arrives first (power3.out on 1.45·u) and the width lags
   (expo.out). Add a small volume term: while thickness leads, the shape is 10 % taller and 7 % narrower. Both
   curves are monotone, so it reads as soft-body with no overshoot.
3. **A balloon that grows with typing:** the bubble's half-length is the measured DOM width of the typed prefix,
   eased per keystroke. Cache the prefix widths only after `document.fonts.status === 'loaded'`. Hide labels with
   `visibility:hidden`, never `display:none`, or `offsetWidth` returns 0 and the balloons collapse to circles.
4. **Orange on white under NeutralToneMapping turns salmon** (measured 248,97,73), because the lit orange goes
   above 1 and neutral desaturates it toward white. An emissive term made it worse. The fix is to darken the
   albedo in linear (`new Color('#FF6200').multiplyScalar(0.62)`) and lower the env and specular. That gave 242,99,37 on
   the lit face. Keep a little clearcoat for the gloss highlight.
5. **Layered DOF haloes in-focus colour into the background** (an orange glow around Acme and the logo). Premultiply
   the blur source by the far CoC (`rgb*w, alpha=w`), blur, then divide by alpha. The halo goes away, and it costs no
   extra pass.
6. **Logo from the real SVG:** `SVGLoader` paths, then `toShapes(true)` (`createShapes` is deprecated and spams
   runtime warnings in `check`). Then `ExtrudeGeometry` with bevelSize just under half the thinnest stroke and
   `bevelOffset = -bevelSize`, so the silhouette stays exact. Use `rotateX(PI)`, not a negative scale, to flip the
   SVG's y-axis; that keeps the winding and normals right.
7. **Carrier object across a whip:** when the sent question flies between zones, put camera keys on the carrier's
   own path at 3 or 4 times. Without them the monotone camera spline leads or lags the carrier, and the frame goes
   60 % empty.
8. **A 2x2 cluster beats a row** for "four names". A row of 4 pills at a readable size can't fit the frame, and
   the camera pans past the count. The cluster fills the frame and leaves room for the 5th place (the flat skin)
   to spread on "five".
9. **Budget:** under load about 12, the 0.5-scale draft took 7 to 9 min (0.45 to 0.6 s/frame). Puppeteer stills with
   `__apply(t)` took about 0.4 s each and were the real iteration loop. Two drafts and one final were enough.
