<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/ten/i01-white-one-take/LEARNINGS.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# i01 learnings (for the next builder)

## Architecture that worked
- **One `<canvas>`, drawn purely from t** (`apply(t)`, driven by one GSAP proxy tween). There is no DOM per
  object, so the CSS-3D layer limit does not apply. The script lives in `comp/world.js`, with the timeline
  registration inline in `index.html`, because lint wants `window.__timelines` in the HTML and complains about
  files over about 900 lines. `src/build.py` builds both from `src/tpl.html` and inlines real SVG paths as
  `Path2D` (OpenAI, Gemini with its gradients rebuilt via `createLinearGradient`, Perplexity, Acme).
- **Camera**: the d1 Hermite engine, with explicit speeds for z and monotone tangents for x, altitude and pitch.
  Pitch (looking down at the city, then level) is hidden *inside* the bubble dive: the pitch change happens while
  the bubble fills the frame. ALWAYS check that z speed never goes negative: a key whose given speed is far from
  the segment's average speed overshoots backward (I hit this at 13.3 s). `review/cam.js` runs the camera
  in node and prints any backward frames.
- **Anchor objects to the camera path** (`pathAtZ`, `camAt(t)`), not the other way round. Questions that must be
  readable while typed ride at a fixed distance ahead of the camera (`Z = camAt(t).z + 1500`) until they are let go.

## White-on-white depth (what actually reads)
- Floor #DCE2E9 near → #EEF1F5 horizon; objects #FFFFFF; building faces cool greys (226/212/203). The white object
  is always a step brighter than its background.
- **Projected shadows in two 1/4-resolution layers** (contact: blur 1.2 px, alpha .26; soft: blur 7 px, alpha .24),
  navy-tinted. Vertical panels cast a *planar* shadow (`planeShadow`: bottom and top edges projected along the
  light). Ellipse blobs under panels looked like dirty puddles, so use planar shapes.
- Haze = alpha fade toward a background that is the fog colour, plus `mix()` toward the fog for opaque faces (an alpha
  fade on opaque boxes makes them see-through).
- Frosted glass = a downsampled copy of the frame drawn so far (480x270 + 3 px blur), clipped to the panel.
  `clip()` needs `"evenodd"` for frames with holes. Otherwise the whole rect blurs (my first gates were mush).
- Orange light pools on the floor (radial gradient under each Acme light) sell "light", even on white.

## Failures and gotchas
- The particle assembly first exploded from points near or behind the lens, giving huge random streaks. Start
  particles 1600 units ahead, inside a 160 to 580 radius ring, so they converge as a swarm.
- Per-segment strokes with round caps on translucent ribbons make beads. Stroke 4-point chunks with butt caps instead.
- Zoom-streak speed blur (redrawing the frame at scales 1.01 to 1.05) above 0.35 strength turns gates into fog.
- Stars or bubbles near the flight path become giant spheres that cover labels. Exclude a radius around the path
  and around the label areas.
- Text that the camera flies through: fade it out under ~900 units, or it becomes huge blurry letters.
- `hyperframes snapshot --at` is the fast still loop (~15 s for 8 frames). Use it before every render.

## Render times (4 cores shared, -w 2)
- Draft at 15 fps (`-q draft -f 15`): about 1 min 45 s. Full 30 fps at "looks" quality: 2 min 50 s to 4 min 45 s for
  30.9 s (927 frames). The canvas, with about 1000 buildings plus shadows plus 3 to 8 backdrop-glass copies per
  frame, is fine.
- Rounds: r1 draft, r2 draft, r3 full, then two more full renders (r4/r5 = final sketch.mp4). Strips are in
  `review/`, and `strip-final.png` is the slot → logo move.
