<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/ten/i07-lab/LEARNINGS.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# i07 The Lab: learnings for the next builder

## Architecture that worked
- Same skeleton as i01: one `<canvas>` redrawn from t (`apply(t)` driven by one GSAP proxy tween). The engine is in `comp/assets/lab.js`, built from `src/lab.js` by `src/build.py`, which inlines the real SVG path data. Only the timeline registration stays inline (lint needs it).
- **Long-lens perspective camera**, keyed per channel `[t, tx, ty, tz, yaw, pitch, zoom]` with monotone cubic tangents (zero velocity at the ends). dist = 4400/sqrt(zoom) and F = zoom*dist, so zoom pushes also gain a little parallax. The near plane is never an issue.
- **Painter's algorithm per object** (an `add(depth, drawFn)` list sorted far to near). Boxes cull back faces by normal and stroke every face with a 7.5%-navy hairline. That hairline is what makes white-on-white geometry readable.
- **Crisp HTML in the world**: billboards for tags and questions (`translate + scale(F/zc)`), and an affine `matrix()` from 3 projected corners for text lying on a 3D plane. Clip with `clip-path: inset()` in local units where geometry should occlude it.
- **Arms** use closed-form 2-link IK. A target function of t (approach, carry, return) keeps them seek-safe. Moving the base along a "floor track" is a natural way to clear arms out of a shot.
- Typing with a fixed bubble width: the untyped remainder sits in a `visibility:hidden` span. Do NOT use `color:transparent`, because `check` flags it as `text_not_painted` (error). Three grey dots stand in while the bubble flies in, so it never shows an empty bubble.

## Render times (4 shared cores, -w 2)
- With `ctx.filter = blur()` applied to full-res drawImage calls (shadow layers and a blurred wall), a **draft at 15 fps took 6 min**.
- Blurring at quarter resolution into a small canvas and then upscaling with smoothing gave a **full 30 fps render in 2–2.5 min**. Never use canvas filter blur at full resolution per frame.
- Snapshot of 12 frames: about 30 s.

## Gotchas
- A ground object (plinth, conveyor) drawn before the shadow layers gets darkened by its own cast shadow. Keep a separate "pre-shadow" layer composited before the ground pass.
- Arms whose rest target is far from the base straighten into horizontal bars that cross the frame. Rest targets must sit close above the base (folded pose).
- Tags travelling sheet → rack directly crossed the scanner and the sheet. A hand-off point (the tag lifts off to a point beside the scanner, where the arm takes it) gave clean paths. Space the hand-off points like the slots, or the tags stack on top of each other.
- HTML always paints above the canvas. Any arm or object passing "in front" of HTML text must be avoided, or the text must fade first (the sheet text fades at 17.6 s before the arms slide past).
- `p3io` starts very slowly. A sheet "emerging" with p3io stays hidden for about 0.3 s, so start it earlier than the word.
