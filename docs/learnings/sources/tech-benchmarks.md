<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/research2/tech/TECH.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# TECH: premium-on-white techniques measured in the HyperFrames renderer

HyperFrames 0.8.137, chrome-headless-shell 152, `--use-angle=swiftshader` (software WebGL; the probe reports "WebGL
unavailable"), on a 4-core box. Everything here is in `research2/tech/` (scratchpad). Nothing touches the repo.

## How it was measured

- Each test is a 3 s comp at 1920x1080 built from `lib/tpl.html`: one `<canvas id="cv">`, one paused GSAP proxy
  tween calling `window.__apply(t)`. The engine is an ES module bundled to an IIFE with esbuild (`lib/build.sh`),
  so three.js addons load from `file://` and lint passes (0 errors, 0 warnings).
- **bench** (`lib/bench.sh`) runs the same chrome binary and GL flags as the renderer, calls `__apply(t)` at 6 times,
  then forces a GPU sync (`readPixels` of 1 px), and reports ms per frame. It predicts the real renderer well:
  t1a bench 585 ms vs render 614 ms/frame; r1 bench 583 ms vs render ~655 ms/frame.
- **render** (`lib/render.sh`) times `hyperframes render -w 1`. Fixed overhead is about 8 s per render. A canvas comp
  adds about 47 ms/frame for capture and encode. Pure DOM/SVG comps cost about 0 to 10 ms/frame on top of the
  startup.
- **stills** (`lib/shot.sh`) take a chrome `--screenshot` after `__apply(t)`, using the same GL path. Some stills
  were also pulled from the real renders.
- **Seek safety**: the t1c render with `-w 1` and with `-w 2` matched per frame (PSNR min 48 dB, which is
  encoder noise only). The video plate matched its source frame for frame (best PSNR at offset 0 every time).
- **Workers**: `-w 2` gave **no speedup** for WebGL (100.7 s vs 99.1 s). SwiftShader already uses every core, so
  render WebGL with `-w 1`. Run only one WebGL render on the box at a time.

## Results table (in-page ms/frame at 1080p unless noted; add ~50 ms for capture)

| # | Technique | Works | ms/frame | Verdict |
|---|---|---|---|---|
| 1a | three.js, 40 rounded boxes + spheres, MeshPhysicalMaterial (clearcoat), RoomEnvironment PMREM + key light, MSAA | yes | 585 (render 614); no AA 371; standard mat 264; half-res 122 | Looks clean and expensive, but objects float without shadows |
| 1b | + PCF soft shadows (2048, radius 6) + contact shadow (drei-style port) | yes | 808 | Grounded. Contact shadow is the most important single add on white |
| 1c-i | + GTAO (three GTAOPass, half res) + VSM | yes | **3534** | Grainy halos, 4x the cost. **Reject** |
| 1c-ii | + N8AO (npm `n8ao`, half res, 8 spp) | yes, after a fix | 1397 | Blotchy denoise. Uses `performance.now()` (not seek-safe unless frozen). **Reject** |
| 1c-iii | + **analytic AO** (ground term + 16 nearest sphere proxies per object, IQ sphere occlusion) | yes | **942** (+130) | Noise-free, soft, reads as "real 3D". **Adopt** |
| 1d | + glossy white floor (Reflector at half res, 9-tap blur, Fresnel mix) + contact | yes | 1216 (838 at 0.667 scale) | Premium, but costs a second scene render. Use on hero shots only |
| 1s | Render scale 0.667 (1280x720, MSAA, CSS-upscaled) for the 1c-iii scene | yes | **577** (vs 942) | Slightly soft, fine for soft white 3D with HTML text on top. **Adopt** |
| 2a | Transmission glass (MeshPhysical transmission 1, dispersion, 3 pills) | yes | 1892 | Real refraction with dispersion; looks like glass |
| 2b | Same, `renderer.transmissionResolutionScale = 0.5` | yes | **1372** (render 1440) | Same look as 2a. Always use 0.5 |
| 2c | FBO fake glass (i03 Prism, 2D quads + refraction shader) | yes (i03) | ~100 total (i03) | Cheapest way to get glass, but it's 2D |
| 3a | Canvas2D motion blur, N sub-samples, full redraw with shadowBlur | yes | N1 123, N2 209, N4 378, N8 679, N16 1247 | Linear in N. Too slow if each sample redraws `shadowBlur` |
| 3a' | Same with **pre-rendered sprites** (shadow baked into each card) | yes | N1 38, **N8 175** (render +65 ms/frame) | Smooth at N8 to N16. **Adopt** for 2D |
| 3b | three.js motion blur, accumulate N renders into a HalfFloat RT (0.667 scale) | yes | N1 337, N4 1499, N8 2899 | Works. N4 shows steps, N8 is smooth. Use adaptive N only on fast moves |
| 4a | DOF: three BokehPass | yes | 1248 (RT path base 602) | Real disc bokeh, but it re-renders the scene for depth (+650) |
| 4b | DOF: **layered** (2 quarter-res blur levels mixed by CoC from the depth texture) | yes | **709** (+107) | Soft, dreamy. Fg edges do not spread (gather limit). **Adopt** |
| 5a | Matcap (procedural canvas matcap) + contact | yes | 213 | Cheap but plasticky. The procedural matcap needs art |
| 5b | **Clay** (MeshStandard rough 0.95) + PCF + contact + analytic AO | yes | 767 (486 at 0.667) | Best "premium matte" look. **Adopt** |
| 5c | **Baked matcap** (render a lit clay sphere into a 256 RT once at init and use it as the matcap) + contact | yes | **178** | 80 % of the clay look at 1/4 the cost. No cast shadows; light is locked to the camera |
| 6a | SDF raymarch, 7 smooth-min blobs + floor, soft shadow + AO, 48 steps | yes | **quarter res 119**; half 480; full 1815 | Affordable at quarter res. Edges slightly stair-stepped, so use for soft shapes |
| 6b | SVG morph (GSAP 3.15 MorphSVGPlugin, now free), 22 tiles + hero | yes | ~0 extra (render 8.4 s / 90 fr) | Free. Watch the point mapping (twist) |
| 6c | Lottie (lottie-web 5.13 SVG, hand-written JSON), `goToAndStop(t*fps, true)` | yes | ~0 extra (render 6.8 s / 90 fr) | Free and seek-safe when driven by t |
| 7 | Pre-baked plate: expensive pass rendered to MP4, then `<video>` in the comp | yes | render 121 ms/frame total | Frame-exact. **The way to make heavy 3D affordable** |
| 8 | GPU particles (THREE.Points, closed-form motion in the vertex shader) | yes | 50k 20, **200k 65**, 1M 307 | Beats CPU splatting (i05: 40k points). **Adopt** |

Stills (all 1920x1080 unless cropped): `tech-1a-physical.png`, `tech-1b-pcf-contact.png`, `tech-1c-gtao.png`,
`tech-1c-n8ao.png`, `tech-1c-analytic-ao.png`, `tech-1d-glossy.png`, `tech-1-scale-compare.png` (left 1.0, right 0.667),
`tech-2a-transmission.png`, `tech-3a-mblur2d-n1-n4-n8-n16.png`, `tech-3a-mblur2d-strip-n1-vs-n8.png` (real render),
`tech-3b-mblur3d-n1-n4-n8.png`, `tech-4a-bokehpass.png`, `tech-4b-layered-dof.png`, `tech-5a-matcap.png`,
`tech-5b-clay.png`, `tech-5c-baked-matcap.png`, `tech-6a-sdf-quarter.png`, `tech-6a-sdf-half.png`,
`tech-6b-svg-morph.png`, `tech-6c-lottie.png`, `tech-7-video-plate.png`, `tech-8-gpu-points-200k.png`,
`tech-9-recipe-render.png` (real render of the recipe), `tech-9-recipe-glossy-067.png`.

Where the cost goes (bench at 0.667 scale with PCF, contact and analytic AO = 583 ms): MSAA costs ~200, the
shadow map ~105, the contact shadow ~80. Shadow map 1024 instead of 2048 saves only ~20. Frame cost grows as more
objects come on screen. Pixel shading dominates: full-screen lit floors are expensive, so use an unlit floor plus a
`ShadowMaterial` overlay.

---

## 1. three.js on white (the source is `lib/scene3d.js`; options select the variants)

Setup (vendor locally: `npm i three` (0.186), bundle with esbuild `--format=iife`):

```js
const renderer = new THREE.WebGLRenderer({ canvas: cv, antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1); renderer.setSize(1280, 720, false);        // 0.667 scale; CSS keeps the canvas at 1920x1080
renderer.toneMapping = THREE.NeutralToneMapping;
scene.background = new THREE.Color('#F5F7FA'); scene.fog = new THREE.Fog('#F5F7FA', 28, 60); // hides the floor edge
scene.environment = new THREE.PMREMGenerator(renderer).fromScene(new RoomEnvironment(), 0.04).texture;
scene.environmentIntensity = 0.5;                                      // 0.75 washes white out; keep the key light dominant
const key = new THREE.DirectionalLight(0xffffff, 2.8); key.position.set(-6, 12, 7);
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFShadowMap; // PCFSoftShadowMap was removed in r18x
key.castShadow = true; key.shadow.mapSize.set(2048, 2048); key.shadow.radius = 6; key.shadow.bias = -0.0005; key.shadow.normalBias = 0.02;
const white = new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: 0.42, clearcoat: 0.8, clearcoatRoughness: 0.18, specularIntensity: 0.6 });
// floor: unlit + shadow catcher (a lit floor costs a full-screen PBR shade)
floor = new THREE.Mesh(new THREE.PlaneGeometry(400, 400), new THREE.MeshBasicMaterial({ color: 0xeef1f5 }));
catcher = new THREE.Mesh(new THREE.PlaneGeometry(30, 30), new THREE.ShadowMaterial({ color: 0x0a2a4a, opacity: 0.16 }));
window.__flush = () => gl.readPixels(0,0,1,1,gl.RGBA,gl.UNSIGNED_BYTE,px);   // for benching only
window.__apply = (t) => { setState(t); renderer.render(scene, camera); };     // setState derives everything from t
```

**Contact shadow** (port of three's `webgl_shadow_contact` example): an orthographic camera looks up from the
floor. It renders the scene with a depth material that writes `vec4(0,0,0,(1-fragCoordZ)*darkness)` into a 512 RT,
blurs it twice (Horizontal/VerticalBlurShader), and shows it on a navy-tinted plane at opacity 0.55. It is
recomputed every frame (~80 ms), so it stays seek-safe for moving objects.

**Analytic AO** (cheap "baked" AO; no screen-space noise, no temporal state). Inject it into the lit materials:

```glsl
// fragment, after #include <aomap_fragment>; vWP = world position varying; uOcc[16] = vec4(center, radius)
vec3 Nw = normalize((vec4(normal,0.)*viewMatrix).xyz); float occ = 0.;
for (int i=0;i<16;i++){ vec3 d=uOcc[i].xyz-vWP; float l=length(d), r=uOcc[i].w;
  if (l>r*1.02) occ += clamp(dot(Nw,d/l),0.,1.)*(r*r)/(l*l); }
float g = mix(smoothstep(-.05,1.1,vWP.y)*.45+.55, 1., clamp(Nw.y,0.,1.)); // ground term
float ao = clamp(1.-occ*.75,.45,1.)*g;
reflectedLight.indirectDiffuse*=ao; reflectedLight.indirectSpecular*=ao; reflectedLight.directDiffuse*=mix(1.,ao,.35);
```

In JS, each frame: approximate every object with sphere proxies (a box becomes a stack of `round(h/w)` spheres of
radius 0.62w). Each object gets a cloned material (`customProgramCacheKey` keeps one program) holding its 16
nearest proxies, excluding its own. Looping over all 96 proxies per pixel cost +700 ms; the 16 nearest cost
+130 ms.

**Glossy floor**: use `Reflector` (textureWidth/Height = half the canvas) with a custom `shader` that takes 9 taps
around the projected uv. Mix it as `mix(tint, reflection, 0.18 + 0.5*pow(1-V.y,4))`, then add
`<tonemapping_fragment>` and `<colorspace_fragment>`. Keep the contact-shadow plane above it, because Reflector
does not receive shadows.

Gotchas
- GTAO costs 3.5 s/frame and is grainy. N8AO costs 1.4 s, looks blotchy, and seeds its noise from
  `performance.now()`. If you use it anyway, wrap its render as `performance.now = () => 0`.
- The direct canvas path and the RT + OutputPass path do not match. Transparent layers (ShadowMaterial, contact
  plane) blend in linear space inside a HalfFloat RT and look lighter than on the canvas. Pick one pipeline per film
  and tune shadow opacity in that pipeline.
- `FullScreenQuad.render` clears the target when `renderer.autoClear` is true. Set `autoClear = false` while
  accumulating, or each pass silently replaces the previous one.
- Boxes need a bevel to read as premium: use `RoundedBoxGeometry(1,1,1,4,0.12)`. Hard cubes look like CAD.
- The PCF radius gives faint speckle on faces at a grazing light angle. Raise `normalBias` (0.02 to 0.04) if you see it.
- The camera must never show the floor edge: use a 400-unit floor and fog from 28 to 60.

## 2. Liquid glass

- Transmission (`MeshPhysicalMaterial({ transmission:1, thickness:0.9, ior:1.45, dispersion:4, roughness:0.04,
  clearcoat:1, attenuationColor:'#dfe9f5', attenuationDistance:3 })`) plus
  **`renderer.transmissionResolutionScale = 0.5`** (r17x+). The cost is about +0.55 s/frame at full res for 3
  pills; it scales with glass screen area. Glass only reads on white when there is structure behind it: refracted
  cubes, the orange accent, or text. Over empty white it vanishes.
- Cheap fake (2D or 2.5D scenes): i03's FBO refraction (`ten/i03-prism/src/engine.js`, FS_PRISM). Render the scene
  into an FBO, then draw the glass shape as one quad that samples the FBO with per-channel offsets
  `rf.r=S(cc+mg*.94+off).r; rf.g=S(cc+mg*.91+off*1.22).g; rf.b=S(cc+mg*.88+off*1.45).b;`. Add a dark 1 px
  outline, a bevel band, a Fresnel rim, and one specular streak. This costs about 0.1 s/frame for the whole frame.

## 3. Motion blur (sub-frame accumulation; works because every frame is a pure function of t)

```js
// canvas2D: equal-weight running average. Sample k is composited with alpha 1/(k+1)
for (let k = 0; k < N; k++) {
  const tk = t + (shutter / fps) * ((k + 0.5) / N - 0.5);   // shutter 0.5 = 180 degrees
  const c = k === 0 ? ctx : accCtx; c.drawImage(bg, 0, 0); draw(c, tk);
  if (k) { ctx.globalAlpha = 1 / (k + 1); ctx.drawImage(acc, 0, 0); ctx.globalAlpha = 1; }
}
// three.js: render each sub-sample into rtSub, add it into rtA with a quad (CustomBlending One/One, opacity 1/N,
// autoClear=false), then OutputPass to the screen. Call setState(t) again at the end.
```

- The cost is linear in N. Use sprites (bake each card with its `shadowBlur` once) so one sample is a blit:
  canvas2D N8 costs +65 ms/frame in the real render. In three.js one sample is a full scene render (N4 = 4.4x).
- How to choose N: steps show when the per-sample displacement is over ~4 px. Set
  `N = clamp(ceil(maxScreenPx_per_frame * shutter / 4), 1, 16)`, computed from the same closed-form motion, so
  static frames pay nothing. N=4 visibly strobes on 100 px/frame moves; N=8 is fine with 3D at shutter 0.5; 2D
  cards with text want N=12 to 16.
- Text smeared at 180 degrees becomes unreadable (see the strip), which goes against the doctrine of 10 px peak
  text blur. Cap the shutter per element: `shutter_el = min(0.5, 10 / speedPx)`, or draw text layers with N=1.
- The canvas accumulator is 8-bit. Above N=16 the 1/(k+1) alpha quantises, so use WebGL float accumulation instead.

## 4. Depth of field

- BokehPass (`{focus, aperture:0.004, maxblur:0.012}`) gives proper disc bokeh. It costs +650 ms because it
  re-renders the scene with MeshDepthMaterial. Use it only on static beauty shots.
- **Layered DOF** (`makeLayeredDOF` in scene3d.js) costs +107 ms. Give the scene RT a `DepthTexture`. Copy to
  quarter res and blur (9-tap separable), then go down to eighth res and blur again. Composite with
  `coc = clamp(abs(linZ - focus)/range, 0, 1)` and `mix(sharp, b1, 2coc)` / `mix(b1, b2, 2coc-1)`.
  Gotcha: blurred foreground objects do not spill over in-focus edges, because this is a gather. Keep the
  foreground blur small, or put foreground objects on their own pre-blurred layer.
- For 2D/HTML: CSS `filter: blur()` on a few large layers is fine. Never `ctx.filter` at full res per frame (i07).

## 5. Matte looks

- **Clay** (`MeshStandardMaterial({ roughness: 0.95 })`, env 0.7, PCF, contact, analytic AO) is the best matte
  premium look we measured: 767 ms at 1.0 scale, 486 ms at 0.667.
- **Baked matcap** at 178 ms. At init, render a `SphereGeometry` with the clay material under the same environment
  and a key light into a 256x256 RT with an ortho camera. Read it back with `readRenderTargetPixels`, make a
  `DataTexture`, and use it in `MeshMatcapMaterial`. Keep the bake lights low (key 1.5, env 0.32, hemi 0.35):
  the RT is linear and not tone-mapped, so brighter values clip to flat white (first attempt). Add the contact
  shadow for grounding. Limits: no cast shadows, and the light turns with the camera.
- A hand-drawn procedural matcap looks plasticky and grey. Bake it from the real lighting instead.

## 6. SVG morph, Lottie, SDF

- MorphSVGPlugin ships free in `gsap@3.15` (`node_modules/gsap/dist/MorphSVGPlugin.min.js`). It costs nothing in
  the renderer. For circle-to-square morphs give both shapes the same point count, or set `shapeIndex`, to avoid a
  mid-morph twist.
- Lottie: load `lottie_svg.min.js` locally with `autoplay:false`. In the proxy tween call
  `anim.goToAndStop(Math.min(t*fps, op-0.001), true)`. It costs nothing in the renderer and is seek-safe. It is
  good for AE-authored icons; avoid image layers and expressions, since they are not verified.
- SDF raymarch: a full-screen pass costs 1.8 s at 1080p, 480 ms at half res, and **119 ms at quarter res**
  (480x270, CSS bilinear upscale). Blob centres are closed-form in t. Use smooth-min k=0.6, 48 steps, 20-step soft
  shadows, a 4-tap AO and a floor that fades into the background. Anti-alias the silhouette with the ray's minimum
  distance: `cov = 1 - smoothstep(0, pixelWorld, minDist)`. Edges at quarter res still step a little. It suits
  soft liquid blobs, not crisp edges.

## 7. Pre-baking

- Render the expensive 3D pass as its own comp (`hyperframes render` to mp4, or `--format webm/mov` for alpha). Put
  it in the main comp as `<video src="plate.mp4" muted data-start data-duration data-track-index>`. It was
  frame-exact in our test. The main comp then renders at DOM speed (121 ms/frame here), and overlays, text and
  timing can be iterated without re-rendering 3D.
- Lint warns about sparse keyframes. Re-encode plates with
  `ffmpeg -i in.mp4 -c:v libx264 -r 30 -g 30 -keyint_min 30 -crf 14 -movflags +faststart plate.mp4`.
- Image sequences as stacked `<img>` would cost ~8 MB decoded per 1080p frame. Video plates are the better choice.
- Pre-bake anything iterative (sims, boids, matcaps, contact maps of static layouts) at init or in node, then index
  it by t (as i02 and i06 did).

## 8. GPU particles

`THREE.Points` with a `seed` vec4 attribute. The vertex shader computes the position from (seed, t) in closed
form, and the fragment shader draws a soft disc (`discard` outside, alpha 0.55, depthWrite off). Cost: 200k points
in 65 ms and 1M in 307 ms, at 1080p with 3 px points. The cost is fill-bound, so smaller points are cheaper. This
is the answer to i05's "wants 200k+": port its phase formulas to GLSL.

---

## Premium-on-white recipe (30 s at 1080p, 30 fps = 900 frames)

**Stack**
1. **3D world in three.js at render scale 0.667 with MSAA.** Use MeshPhysical clearcoat white, or Clay for matte
   scenes. Add RoomEnvironment at 0.5, a key light at 2.8 with PCF 2048 r6, the contact shadow, analytic AO (K=16),
   rounded-box bevels, an unlit floor with a ShadowMaterial catcher, fog into #F5F7FA, and Neutral tone mapping.
   This measured **~0.65 s/frame** in the real renderer (r1: 67 s for 90 frames, including 8 s startup).
2. **Hero-only extras**, switched on per shot from t:
   - glossy floor: +0.25 s at 0.667 scale;
   - transmission glass at `transmissionResolutionScale 0.5`: about +0.5 s;
   - layered DOF: +0.18 s.
3. **Adaptive motion blur**, only on fast moves (N from screen speed, max 8 in 3D). Text layers stay unblurred.
4. **All text, UI cards and logos in HTML/SVG** over the canvas, positioned with the same camera projection (crisp
   at any scale). Use MorphSVG or Lottie for icon morphs, which are free. Use GPU points for any particle field.
5. **Pre-bake the 3D into plates.** Render each 3D shot once as a 1080p mp4 with `-w 1`, one render at a time.
   Then iterate the full comp (HTML + plates) at ~0.12 s/frame.

**Expected render minutes (4 shared cores, `-w 1`; `-w 2` does not help WebGL)**

| Scenario | Per frame | 30 s total |
|---|---|---|
| Full 3D every frame, base stack | 0.65 s | **~10 min** |
| + glossy/glass/DOF on ~30 % of frames | +0.3 s avg on those | ~11.5 min |
| + motion blur N=4 on ~15 % of frames | +3 renders on those | ~+4 min, so **~15 min worst case** |
| Same, but as plates: bake once (~10 to 15 min), then every overlay iteration | 0.12 s | **~2 min per iteration** |
| Clay or baked-matcap variant (no physical) | 0.49 / 0.18 s | ~7.5 / ~3.5 min |
| Reference: i10 2D (cheapest of the ten) | | ~1 min |

For drafts, use `shot.sh`/`snapshot` stills and a 0.5-scale MSAA-off build (276 ms measured, ~0.33 s/frame with
capture, ~5 min for 30 s; drop shadows and AO for ~0.15 s).
Switch to 0.667 with MSAA and the hero extras only for the final render.
