<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/six/n5-droste/LEARNINGS.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# Learnings: n5 "Droste Answer"

1. **Pure DOM was the right tool for a recursive zoom.** Text stays vector-crisp at any scale, from 0.003x to over 300x.
   - The full 30 s render took about 17–18 min on the shared box, at 1080p with up to 10 motion-blur copies. That is about
     6x cheaper than the three.js siblings.
   - There is no WebGL anywhere.
2. **Keep the camera in log space and in the coordinates of the deepest level, never in absolute coordinates.**
   - Each level stores its offset O and scale s inside its parent. Global depth is μ = ln(w) + Σ ln s.
   - Nine levels span about e⁻³⁰. Converting the camera level by level keeps doubles exact. Absolute coordinates would
     already lose sub-pixel precision at around level 6.
3. **Fritsch–Carlson on μ(t) gives "slow at the beats, fast between" for free.**
   - Put two keys per beat, close together in μ. The whips fall between beats, and the curve never overshoots or reverses,
     so the camera only ever moves forward.
   - For position, use a fixed-point zoom per segment: f = (c_A·w_B − c_B·w_A)/(w_B − w_A). Smoothstep-blend the two
     neighbouring segment formulas over ±0.2 s around each key. This removes the pan-velocity kink.
4. **Motion blur in DOM with sub-frame copies.** Stack N clones of the world. Each clone has an opaque background and
   opacity 1/(j+1), and renders the camera at its own sub-time. The result is an exact equal-weight average.
   - Choose N from the measured screen displacement of the four corners: N = ⌈d·0.5/2.5⌉.
   - At /5 px per sample, slow pans showed doubled text. At /2.5 px per sample it is clean.
   - Clones must only use classes, never ids.
5. **Measure glyph counters offline, never at render time.**
   - A puppeteer pass draws the anchor "o" at 400 px on a canvas with the computed font and scans the counter (centre and
     half-sizes).
   - It maps the result into level coordinates with the span rect and a zero-size `vertical-align:baseline` probe.
   - The output is baked into anchors.json and the comp is rebuilt. The lens then sits exactly in the counter, with no
     dependence on font-load timing.
6. **Coverage culling makes the DOM cheap.** Hide a parent as soon as the child lens covers all four screen corners
   (circle: corner distance < R; rect: contains the screen). Hide a child while its lens is under 3 px. That leaves only
   2–3 levels live at a time.
7. **Gate each child level on its anchor.** The lens inside the "o" appears only once that "o" has been typed, and the
   lens inside the G only once the G has drawn. Otherwise the Droste hint shows up before its letter exists.
8. **Every beat's frame must keep forward-only zoom, which constrains layout.** You cannot zoom out to fit a wider
   list later. Lay each level out so that its successive frames shrink: the paragraph, then the list, then the 5th
   line. Leave about 80 px of margin, or the left edge crops the logo and the first letters.
9. **Fill rule versus narration gaps.** While the voice is between beats (11.6–14.6), the answer level needed extra real
   content (answer chips) to avoid frames that are 30–40 % empty. A placeholder state was not allowed, so plan more
   than one content group per level.
10. **CSS blur as DOF on a parent zoomed past 3–4x reads as passing through glass.** The value is in local px, so divide
    the screen blur by the level's scale. It costs nothing visible to the frame rate in the renderer, but puppeteer
    stills of whip frames take 2–6 s.
