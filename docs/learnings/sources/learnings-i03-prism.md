<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/ten/i03-prism/LEARNINGS.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# i03 The Prism — learnings for the next builder

## Architecture that worked
- `src/engine.js` (state + WebGL), `src/prism.tpl` (HTML/CSS shell), `src/build.py` (inlines the real SVGs,
  writes `comp/index.html` + `comp/assets/engine.js`). Keeping the engine in an asset file keeps the HTML
  under the lint "composition_file_too_large" threshold. The `gsap.timeline` + `window.__timelines`
  registration must stay inline in index.html, or lint reports `missing_timeline_registry`.
- Seek-safety: one linear GSAP proxy tween calls `apply(t)`; `apply` derives everything (camera, beams,
  ribbons, prisms, HTML overlays, typed text) from `t` alone. Camera = monotone-cubic (Fritsch–Carlson) keys,
  so it never stops dead or overshoots. Pill traffic on beams is `mod(s - v*t - phase, D)` in the shader.
- HTML overlays (bubbles, band labels, etched engine logos, the Acme logo) are positioned with the same
  world->screen camera function the shader uses, so text stays sharp and stays locked to the light.

## The big gotcha: per-pixel loop shaders are ~60x too slow in the renderer
- HyperFrames renders WebGL with SwiftShader (`--use-angle=swiftshader`, "WebGL unavailable" -> software).
- v1 was one full-screen fragment shader looping over 16 beams + 20 ribbons + 4 prisms per pixel:
  **5–8 s per frame** (bench) -> a 30 s render would take ~2 h. The first render looked hung.
- v2 rasterises instead: beams/ribbons/shadows/caustics are quads built in JS each frame (one draw call,
  13 floats per vertex, along/across coordinates passed as varyings that are affine in position so the
  interpolation is exact even on tapered ribbons), drawn premultiplied into an FBO; the FBO is copied to
  screen; each glass prism is one quad whose shader samples the FBO with per-channel offsets
  (Maxime Heckel's FBO refraction + chromatic dispersion). **~0.1 s per frame; full 927-frame render in
  ~3 min with `-w 2`** on the shared 4-core box.
- Benchmark harness: `bench/run.sh <comp>` injects a timing loop into a copy of index.html and runs
  chrome-headless-shell with `--no-sandbox --use-angle=swiftshader --dump-dom`. Use it before any full render.

## Making light read on a white set
- White beams on a near-white sweep disappear. What made them read: a cool grey rim line, and above all a
  soft **offset drop shadow** (grey, ~13% alpha, offset down by w*1.6+12) so beams look like physical light
  rods over a studio floor; chat-bubble pills get the same shadow. The sweep itself is #F5F7FA centre to a
  #D5DDE6 vignette so pure white is the brightest thing on screen.
- Spectrum on white: saturated violet -> blue -> cyan -> green at ~0.88 alpha reads like a rainbow cast on a
  wall. The warm end is deliberately missing; the 5th band is an orange dashed gap = "your brand".
- Glass on white reads through its edges: dark 1px outline, a bevel band that refracts/disperses the FBO,
  a fresnel rim, one specular streak, an offset back-face outline for depth, and a contact shadow.

## Other gotchas
- `pgrep -f "<pattern>"` inside an `until` loop matches the loop's own bash command line, so the wait never
  ends. Watch the output file or the task notification instead.
- A render started with `&` inside a Bash call dies with `render_cancelled_parent_exited` when the call
  returns; use the tool's background mode.
- Logo "chromatic settle": three spectral copies with `mix-blend-mode:multiply` over the orange logo made
  brown/olive mud; normal blending with copies fading as they converge (main opacity = conv^1.6) reads clean.
- Wide establishing shot: scale beam width by `(0.95/zoom)^0.85` when zoomed out, or the fan vanishes.

## Render times (shared 4-core box, other builders rendering)
- v1 per-pixel shader: ~9 s/frame in the real renderer (aborted). v2 quads+FBO: 181 s for 927 frames (r1),
  similar for r2–r5. Snapshots (`snapshot --at`, 5–9 frames) ~1–1.5 min.
