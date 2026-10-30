<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/six/n3-type-tide/LEARNINGS.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# n3 Type Tide: learnings

1. **three.js `Color('#hex')` is already linear** (ColorManagement is on). Calling `convertSRGBToLinear()` on it a second
   time crushed #00AA90 to pure red, so the "orange" hollow rendered salmon-red. Pass `new THREE.Color(hex)` straight
   into shader uniforms.
2. **Typeface JSON from a variable font: decompose composites.** fontTools `RecordingPen` silently drops composite
   glyphs (i, j and some accented forms), which left "Northw nd". Use `DecomposingRecordingPen(glyphSet)` after
   `instantiateVariableFont(..., {"wght": 700})`. Three's `q` command order is end point first, then control point.
3. **White type on a white floor needs the key light behind the type.** Front faces then sit in hemi/env light only,
   at a light grey, while bevels and the floor stay white, and the shadows fall toward the camera, where they read.
   A front key flattened everything to white on white.
4. **Mip-bias DOF is free, but the mip average of tiny type is nearly white.** Far type faded to blank, which made
   "empty" frames. Fix: raise the ink with distance (`1 + clamp((d-8)/20, 0, 0.9)`) and draw the atlas at a heavier
   weight (600/700). Check the far field at render scale, not only close stills.
5. **Catmull-Rom with unevenly spaced keys overshoots badly.** A 34-unit move followed by a hold flew the camera past
   the subject. Monotone tangents (zero at a reversal, capped at 3x the smaller secant) fixed every overshoot without
   retiming any key.
6. **CSS3DRenderer owns `style.display`** for its objects. Toggle `object.visible`, never the element's display.
7. **`hyperframes check` times out on heavy WebGL.** Run it on a 0.25-scale, no-MSAA, no-blur build: the DOM layout is
   the same, and it takes 6 minutes instead of more than 20.
8. **Budget on a shared box:** 4 builders made the 0.5-scale draft take 29 minutes without blur and 55 with N<=3 blur.
   A puppeteer stills script (one page, many `__apply(t)` calls, 1 to 5 s per still) was the real iteration loop. Do
   at most 2 drafts, then one final render.
9. Keep the HTML-in-3D (CSS3D) for anything that must be read: questions, the answer card, the answer page and the
   logos all stay razor sharp while the WebGL layer renders at 0.667.
