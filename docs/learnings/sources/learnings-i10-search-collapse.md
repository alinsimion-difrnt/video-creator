<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/ten/i10-search-collapse/LEARNINGS.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# i10 Search Collapses: learnings for the next builder

## Architecture (src/engine.js + src/index.tpl + src/build.py → comp/)
- I used the i08 pattern: one canvas plus DOM overlays, all set inside `apply(t)`, which is driven by one GSAP
  proxy tween. Lint was 0/0. Check passed once overlaps were declared. freezedetect was clean on every round.
- **Orbit camera rig with monotone cubic keys** (target, dist, pitch, yaw), with the projection shared by the city,
  the stack and the shards. I reused it unchanged from i08/i04, and it worked first time.
- **Textured triangles in 2D canvas (the new technique).** Each result card is pre-rendered to an offscreen canvas
  (1200x236). It is cut into a seeded jittered 8x3 grid (48 triangles), and each triangle is drawn with
  `clip()` + `setTransform(affine uv→xy)` + `drawImage`. Expand the clip by about 0.9 px around the centroid or
  hairline seams show. 10 cards × 48 triangles plus up to 432 shards per frame is cheap. The final 30 fps render
  at looks quality took about 60 s with `-w 2`.
- **3D card flip with the same mesh.** Rotate the card's local y/z by θ. Past π/2, draw the next texture with θ−π,
  and darken by (1−|cos θ|). The three result sets (shoes, restaurants, CRM) flip in a cascade on their words.
- **Closed-form shatter.** Impact time `HIT(k)` is fixed. A shard is `c0 + v·τ + ½gτ²` plus a Rodrigues rotation
  of its vertices about a seeded axis. The facet shade comes from the world normal, with a navy hairline edge so
  white shards read on white. It is fully seek-safe.
- **Shards → logo.** Rasterise the inlined logo paths (`Path2D` from the `<path d>`) into an offscreen canvas and
  rejection-sample points inside. Sort shards and targets by x, then fly each shard on a quadratic bezier with
  expo.out, shrink it to 0.21, and tint it orange (fill overlay alpha). The crisp SVG logo fades in over the mosaic.
- **DOM rect from projection.** The answer card's start rect is `frontRect(10.45)`, the projection of result #1.
  The card grows from it, which makes a seamless canvas→DOM hand-off.

## Gotchas
- Canvas text needs the fonts. Build the textures lazily in `apply()` and rebuild once when
  `document.fonts.status === "loaded"`. Kick off `document.fonts.load(...)` at script start.
- Put the title FIRST in a stacked card: in a staircase stack only the top ~90 px of each back card shows.
- Rank swaps that slide names through each other read as overlapping text. A refresh (old name slides out left and
  fades, new name slides in from the right, staggered by slot) is clean.
- `check` flags clones sliding out from behind their source card (content_overlap on every name). Declare
  `data-layout-allow-overlap` on the name elements themselves, not only on the card. Two identical "5" labels
  stacked (slot plus dashed overlay) is an error; keep one.
- Python `str.replace` on engine.js: the file holds a literal "›", not `›`.
- Foreground bubbles tied to random buildings land off-screen. Place the opening hero bubbles at explicit world x/z
  near the camera path so something big pops by 0.3 s.

## Render times (4 shared cores, -w 2)
Snapshot of 3–16 frames: about 9 s. Draft at 15 fps: 28 s. Draft at 30 fps: 55 s. Final at looks quality, 30 fps:
about 60 s. Rounds: r1 draft at 15 fps, r2 draft at 30 fps, r3 final, r4 final (sketch.mp4).
