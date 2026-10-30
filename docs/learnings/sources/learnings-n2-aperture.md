<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/six/n2-aperture/LEARNINGS.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# n2-aperture: learnings

1. **A transparent WebGL canvas between two CSS3D layers is a strong hybrid.**
   - Stack: back HTML layer, then the three.js canvas (`alpha:true`), then the front HTML layer. All three share one camera through `CSS3DRenderer`.
   - The 3D object provides real shadows and parallax, and every word stays crisp DOM text.
   - A `ShadowMaterial` plane at the depth of the back layer casts WebGL shadows onto HTML.
   - Do not set `style.transform` on the element you hand to `CSS3DObject`, because it overwrites the renderer's `matrix3d`. Wrap it, and animate the child.
2. **SVG text inside a CSS3D object scaled 0.01 collapses in Chrome.**
   - Symptom: `getComputedTextLength() = 0` and all the glyphs stacked on one spot. A world-unit viewBox does not help either.
   - Fix: curved type as HTML glyph spans with `transform-origin:0 0; rotate(θ) translate(-w/2, -R)`. Measure each width with `offsetWidth` once `document.fonts.status === 'loaded'`.
   - The CSS3D elements must be attached before you measure: call the CSS3D render once at init.
3. **The iris maths is clean.**
   - A blade's inner edge is an arc of radius R_i. When the blade turns by β about a pivot at radius R_p, the arc's centre moves by 2R_p·sin(β/2). The opening's inradius is therefore exactly r = R_i − 2R_p·sin(β/2).
   - Invert that to drive every blade from one aperture track, r(t).
   - To stack the blades without z-fighting, give each one a helical rise along its arc plus a radial dish. The rise must exceed the blade thickness for each blade pitch. The dish also gives every blade its own shading.
4. **White on white needs value steps from geometry, not paint.** Flat blades parallel to the plate disappeared completely. Tilting them (rise and dish) and using a more grazing key light (env 0.38) made the blades read.
5. **The back plane parallax magnifies what you see through the opening.** What shows through is about r·(1 + gap/D). Any "cut by the blade edge" composition (the orange sliver) has to be tuned for that factor at the camera distance of that beat, or hidden by opacity until its word.
6. **Swap content while the iris is shut.** Closed blades are a free, motivated cut: hub logo to short list to Acme logo to answer text to engine card. The mechanism is the transition.
7. **Ring text is only readable at a mid distance.** At d below ~19 the top arc leaves the frame, so beats that need a label in a close-up should put it inside the opening, as in the final "Competitors you pick".
8. **Cost.** On a box shared with three other builders, a 0.5-scale draft took about 42 min for 927 frames, against an estimated 5 min on an idle box. Budget renders before iterating, and do most of the review on stills (`shot.sh`, which calls `__apply(t)` after `document.fonts.ready`).
