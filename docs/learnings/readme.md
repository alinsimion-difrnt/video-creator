# Premium explainer playbook (learned on Acme v2)

Presenter TikToks from Robert's own footage have their own playbook: [`presenter-reels.md`](presenter-reels.md).
What we took from outside kits (and what we rejected, with the reason): [`launch-video-kit.md`](launch-video-kit.md).
Building or fixing a video inside DaVinci Resolve (API quirks, colour, audio, render): [`resolve.md`](resolve.md).

Read this first when you start a new explainer, for any client. It condenses everything learned making the
Acme v2 explainer (105 s, finished 2026-10-09): the process, the client gates, the creative rules with numbers,
the HyperFrames technique, audio, QA, multi-agent orchestration, and the 19 visual directions we tried.

- Raw source documents (briefs, reviews, segment notes, research, per-test learnings) are copied into
  [`sources/`](sources/). Section k lists them.
- Scratchpad paths in this file and in `sources/` (`$S/...`) are **ephemeral**: they lived in one cloud session.
  The media and source trees are archived in R2 (section k).
- Repo context: `CLAUDE.md` (hard rules), `docs/motion-quality-research.md` (why the first Phase 2 attempt was
  rejected), `docs/external-facts.md` §10 (ElevenLabs), §14–16 (HyperFrames, check tooling, logos).

Contents: a. process · b. client taste · c. creative rules · d. HyperFrames playbook · e. audio and captions ·
f. assembly and QA · g. orchestration · h. directions catalogue · i. competitor and trend research ·
j. open items · k. index

---

## The deliverable in one table

| Item | Value |
|---|---|
| Film | `acme-v2` light-UI explainer, 7 segments (A–G) concatenated frame-exactly |
| Length | 105.133 s, 3154 frames, 30 fps, 1920x1080 |
| Content framing | All foreground scaled 0.92 about (960,540) for title safe; floor and dot grid stay full bleed |
| Voice | ElevenLabs, voice "Hope (corporate)", ~211 wpm articulation, word timings from `with-timestamps` |
| Music | ElevenLabs Music instrumental bed, funk-pop, ~120 BPM, built to the voice timeline |
| SFX | 67 cues (38/min) from a 19-sound palette generated with ElevenLabs sound effects |
| Loudness | −15.2 LUFS integrated, −1.7 dBTP true peak, LRA 2.6 LU |
| Captions | 65 groups of 2–6 words, burned in as a white pill with a per-word reveal; `.srt` also exported |
| Versions | clean 1080p, captioned 1080p, `.srt` |
| Client verdict | Cut 3: "I like this version." Final notes (zoom out, captions, full HD) applied |

---

## a. How to run a premium explainer project, end to end

### The order that worked

| # | Step | Output | Gate |
|---|---|---|---|
| 0 | Intake: product, audience, claims, brand tokens, logo SVGs, fictional data universe | `projects/<p>/brief.yaml`, `brand/`, data cast list | — |
| 1 | Reference research **before** designing: premium filmstrips per scene, competitor films, corpus numbers | filmstrips, `FILMS.md`-style notes | — |
| 2 | Script, then voice audition and voice (timing locks to the audio) | `voice.json` with word times | **Client: voice** |
| 3 | Music bed built to the voice timeline | bed + master audio | (with voice) |
| 4 | Storyboard (32 shots for 105 s), one frame per shot, VO line, transition notes | storyboard page | **Client: storyboard decisions** |
| 5 | "Wow" motion tests of the hardest beats (8–27 s each), judged by a fresh-eyes reviewer | renders + strips | **Client: first look at motion** |
| 6 | Key frames (style frames) for every beat, settled 1920x1080 stills, real components | 10 key frames + sheet | **Client: look** |
| 7 | Segment build in parallel, glued by exact **seam contracts** | cut 1 | **Client: cut 1 notes** |
| 8 | Revision rounds as global rules + per-segment notes | cut 2, cut 3 | **Client after each cut** |
| 9 | (Only if asked) direction exploration: short 30 s tests in new worlds | test pages | **Client: pick / react** |
| 10 | Sound pass (SFX locked to events), captions, title-safe pass, final export | final files | **Client: final notes** |
| 11 | Archive to R2, write the knowledge base | R2 keys, `docs/learnings/` | — |

What the Acme timeline looked like (2026-10-06 → 10-09): research and storyboard on day 1, wow tests and key
frames day 2, cut 1 and cut 2 by day 3, round-0/1/2 direction tests days 3–4 in parallel with the film, cut 3,
sound, captions and final on day 4.

### Gates with the client: what to send and when

| Moment | Send | Ask |
|---|---|---|
| Voice | 2–6 auditions of the same two scenes, plus measured wpm / pitch variation | "Which voice? Too slow / too serious?" |
| Storyboard | A page: one frame per shot, VO line, hook options A/B, open decisions at the bottom | Named decisions (hook, which product UI, real vs fictional data, cut a section?) |
| Wow tests | A page with each test's video, poster, 1-line idea | "Which moments feel premium? Where does it go empty?" |
| Key frames | Contact sheet + each frame large | "Is this the look?" |
| Each cut | Full film page (video, poster), a change list against his last notes | Timecoded notes. Use a page where he can pin notes to timecodes (the film page used the artifact `db` capability so notes persist and Claude can read them back) |
| Direction tests | One grid image + each 30 s test, ranked by an independent review | "Which world?" Do not tell him which one we like before he reacts |
| Final | Clean + captioned + `.srt`, loudness/frames spec | Sign-off |

Rules for gates:
- Always send **motion**, not stills, once motion exists. Stills hide "empty" and "slow", which are his most
  common complaints.
- Ask for **timecoded** notes. Every useful note we got had a timestamp ("8 to 20 s is slow").
- Keep his words **verbatim** in a revision brief (`sources/revision-1.md` style) and translate each into a
  measurable global rule (freezedetect threshold, px sizes, % of frame).
- After each cut, re-render the same paths and keep the previous cut as `render-cutN.mp4` + source copy. Cheap
  rollbacks matter: two directions (A→B seam, F→G seam) changed mid-cut.

---

## b. Client-taste lessons

### General (true for most SaaS founders)
1. **"Slow" and "empty" are the top complaints.** Founders feel the film's pace in the first 10 s and any
   moment where nothing new lands. Plan density from the start: something new every 1.0–1.5 s.
2. **They dislike seeing their own report.** Showing the product's dashboard reads as "too simple" and
   "elements from our report". Show **one** product component, big and physical, only where the line promises
   product. Idea lines must be expressive.
3. **"Futuristic" means precision and physics, not glow.** Tech founders reject paper/hand-made looks and dark
   "AI glow" worlds that look like competitors.
4. **They react to worlds, not polish.** When asked "what would you do if you went crazy", they pick a grammar
   (one take, bubbles over a city) and a palette, then reject everything else in a sentence.
5. **They remember one moment.** Each round, he named at most one or two things he liked. Build films around a
   few memorable signature moves, not uniform quality.
6. **Shared briefs create convergence.** If the brief says "he liked X", every builder builds X. For exploration,
   give builders a clean slate: no prior looks, no "he liked", only the hard rules and the beats.
7. **Fix framing last but do fix it.** Edge-tight compositions look fine to builders at full res, but the client
   watches on a laptop or phone: "some elements too close to screen border".

### Acme-specific timeline (Robert, founder; verbatim)
1. First wow tests: "From second 17 onwards it seems a little empty (focus not there, things in focus appear too
   late or slow)".
2. Storyboard decisions:
   - no HubSpot or real client data;
   - hook A;
   - phones;
   - leave out buyer journey;
   - "some things okay presented using our dashboard, maybe more expressive animated ways".
3. Cut 1 notes:
   - "the questions at the start are too slow, maybe add more faster? try an animation with many chats typing
     questions and zooming in to 1 conversation when you ask 'where to buy running shoes'";
   - "8 to 20 s is slow, simple and doesn't keep you interested";
   - "24–30 too simple, use something more nice in design, not elements from our report";
   - "0:50–1:15 feels slow", "same for 1:30–1:37";
   - "I don't want static slides that sit more than 2–3 seconds".
4. He liked cut 2.
5. Directions round 0, three tests (one-take navy, paper, answer city):
   - "One take is great, but white and orange, not navy";
   - "I like the chat bubbles over city but that's it";
   - "I don't like paper";
   - "we are tech based, it needs to be futuristic".
6. After the ten tests: "I think you overused the city. Clear the cache, try other ideas, do more research, then
   improve our most recent complete variant". Cause: our shared brief told every builder he liked the city, so all
   ten converged on it. Lesson: shared briefs create convergence; give builders a clean slate and no prior looks.
7. Cut 3: "I like this version."
8. Final notes: "zoom out a little, some elements too close to screen border"; captions yes; full HD export.
9. He approved ElevenLabs for sound effects. The CLAUDE.md hard-rule line still says ElevenLabs is for voice only,
   because editing it was blocked in-session; that is a pending item for him (section j).

### Acme taste profile (use as a starting hypothesis for similar B2B SaaS clients)
- White + orange. Cool white world (#FFFFFF–#EEF1F5), navy #3E0863 only for text, orange #00AA90 only for
  "your brand".
- Loves: one-take camera feel, chat bubbles, fast questions, real engine logos, physical cause and effect.
- Rejects: navy/dark worlds, paper/hand-made, report UI slides, static frames >2–3 s, a calm middle.
- Data: fictional brands only (Acme CRM = "you"; rivals Northwind, Contoso, Fabrikam, Tailspin), "Example data"
  tag whenever names or numbers show, never imply the product makes you #1.

---

## c. Creative rules (checklist with numbers)

Tick every box per segment before the client sees a cut.

### Pace and stillness
- [ ] **Hook by 0.3 s**: something striking on screen, the camera moving from frame 1. Frame 0 is never empty and
      never a fade-up.
- [ ] **Something new every 1.0–1.5 s** (a word-synced reveal, a camera move, a cut or a data change).
- [ ] **No composition still for more than 1.5 s** (finals: none > 1.2 s, checked with freezedetect `d=1.2`).
      The only exception is a designed final settle of ≤ 1.0 s at the very end.
- [ ] If a frame must be read for ≥ 2 s, the camera keeps a **purposeful** move: ≥ 3 %/s scale or ≥ 40 px/s
      toward the next focus. Never idle wobble, breathing or drift loops.
- [ ] More, shorter shots: corpus median shot 2.31 s (narrated explainers 2.74 s). Prefer cutting to a close-up
      over sitting on a wide. A long take is premium only if something moves at every moment.
- [ ] Stillness is allowed only as a **dramatic comma before a climax**: 0.3–0.75 s.

### Frame use
- [ ] **Hero object ≥ 40 % of the frame.**
- [ ] **No frame > 30 % empty for > 0.5 s**, including during transitions and whips. Drive carriers from camera
      progress so the outgoing object stays big until the incoming one lands.
- [ ] One focal element per beat; everything else dimmed (navy-70 or 40–60 % opacity) or blurred (2–3 px).
- [ ] Max 3 moving labels or cards at once; nothing flies across text; no chip covers another's text.
- [ ] A 2x2 cluster beats a row of four (a readable row of four pills does not fit the frame).

### Type
- [ ] **Questions ≥ 44 px, meaningful labels ≥ 32 px, nothing important < 28 px** at 1080p (phone-first).
      Headlines 64–120 px. Kinetic hero numbers 96–250 px.
- [ ] Words on screen are short labels: median ≤ 6 words visible, ≤ 1 text block per shot, never the narration
      sentence (captions carry the narration). Premium corpus median: 3 on-screen words per shot (v1 had 36).
- [ ] Typed questions match the voice **word for word** and type in sync with it.
- [ ] Type: Space Grotesk 700 for headings and numbers, Inter 400–600 for UI. Fonts bundled locally.

### Title safe and captions
- [ ] **Content scale 0.92** about (960,540) on all foreground; background layers stay full bleed so no frame
      edge shows. Seam geometry maps through x' = 960 + 0.92(x − 960), y' = 540 + 0.92(y − 540).
- [ ] Nothing meant to be read within **5 % of an edge** (96 px left/right, 54 px top/bottom). Exempt: motion
      entries/exits (whips, cut-the-curve), things flying past the lens, out-of-focus foreground depth layers.
- [ ] Keep important content above **y = 930**: the bottom 150 px carry captions.

### Colour and brand
- [ ] **Orange means "you" (or Acme), nothing else.** No orange send buttons, outlines, arrows or decorations;
      buttons are navy. One orange accent moment per frame.
- [ ] Orange text on white: #028C77 (large only). Tint fill #EBF8F6.
- [ ] Status green/red only for sentiment and "Signed" (Signed text #15803D for AA contrast).
- [ ] **Depth on white**: #FFFFFF cards on a #EEF1F5 floor, layered contact shadows (contact + mid + ambient), a
      1–3 px DOF blur on background planes, slight perspective/parallax. White must never read flat or milky.
- [ ] Value steps, not tint. Ban steel-blue "white" (#C9D6E6 family); it reads grey and clinical.
- [ ] No gradients as decoration, no glow, no glassmorphism, no emoji, no purple-blue "AI" gradients.
- [ ] Real logos for AI engines and sources (Lobe Icons MIT, simple-icons CC0); never typed names alone, never
      recoloured or stretched. Fictional brands for everything tracked.

### Story and timing
- [ ] **Every reveal lands on its spoken word**: motion starts 0.05–0.15 s before the stressed word and settles
      by its end. Hold a result ≥ 0.5–1 s after the voice leaves it.
- [ ] **No empty or placeholder state on any spoken line**: no blank card waiting for content, no 00.0 %, no
      skeleton bars on "ChatGPT", no logo before its word, no machine waiting for its trigger. Answer text
      streams the moment the engine appears. (Eight of ten builders broke this even though it was in the brief.)
- [ ] **Every line has an image.** The beat everyone left empty was "It tracks which brands AI recommends":
      show answers being read and brands detected (a feed with boxed brands and an "N brands found" counter).
- [ ] **Logo on the word**: the Acme logo is complete *on* "Ack-me", not 0.8 s after.
- [ ] **"Every day" gets a 1.5–2 s readable time-lapse** (we used "Every day · Day N", Day 1 → 30 at 96 px,
      with an odometer). A date flashing past in 0.8 s does not count.
- [ ] The empty fifth place is always labelled **"Your brand?"**; "Acme" appears only after the logo, as
      example data.
- [ ] Product UI only where the line promises product: one component, zoomed, physical (shadow, depth). Never
      a full dashboard, never a screen of small widgets.
- [ ] Endings never sit: the end card keeps a slow push (~2.9 %/s) and resolves on beats; only the last
      ≤ 1 s is still.

### Motion grammar
- [ ] Eases: `power3.out` / `expo.out` entrances, `power3.inOut` moves, `power3.in` / `power4.in` exits. No
      back, bounce or elastic. Entrances ≤ 800 ms; exits ~75 % of the entrance; total stagger ≤ 500 ms.
- [ ] **The current is LEFT**: content travels left across seams; reserved vectors: Z-forward = deeper,
      Z-back = arrival, up = conclusion.
- [ ] Seams are velocity-matched cuts, never crossfades:
  - **cut-the-curve LEFT**: exit x 0 → −640 px, `power4.in`, blur 0 → 16 px, opacity 1 until the last 2 frames,
    last 0.30 s; entry from +640 px, blur 16 → 0, `power4.out` over 0.45 s;
  - **zoom-through forward**: last 0.24 s scale 1 → 1.3 (`power3.in`), blur 0 → 12 px, opacity 1 → 0.4; the
    next segment starts at scale 0.75, blur 12, opacity 0.4 and grows over 0.5 s (`expo.out`);
  - **match cut**: identical component, identical rect, the push continues at the same scale velocity across
    the cut (+6–8 %/s);
  - peak blur 10 px for text, 16–20 px for full-frame surfaces.
- [ ] **Motion blur on fast moves** (whips, dives); cap text blur so it stays readable.
- [ ] Cause and effect: the thing that causes a change moves first (a press, a scan line, a drop).

### Signature moves that worked (reuse the grammar, not the Acme content)
| Move | Where in Acme | Why it works |
|---|---|---|
| Wall of 15 chat windows in CSS 3D typing questions, dive into one | A 0–4.8 s | Answers "too slow" opening; huge scale contrast |
| Question pills that grow per keystroke and stack | A 3.9–9.3 s | Typing becomes a physical event; big type |
| Log-space dive through the "o" of "should" into the ChatGPT answer | A 9.4–11.4 s | One-take question → answer transition, pure DOM |
| Empty orange slot curls into the G of the logo | A→B seam | Slot → brand with no cut |
| Live answer feed, brands boxed as read, "N brands found" counter | B 1.6–4.45 s | The honest "tracks" image |
| Full-frame engine moments: real logo disc out of depth, answer cards arc into your mark, odometer | B 4.75–7.4 s | Engines on their words with real content |
| Day 1 → 30 time-lapse | B 7.4–8.9 s | "Every day" readable |
| Three phones from one bubble ripple, fan, whip, push into Perplexity → answer card | D | "We open the actual apps" made literal |
| Sentiment X-ray: scan line, phrases tear loose and fly into signed bars | E | Sentiment as physical evidence |
| Card shatters past the lens; its source pills release a 3D cloud of sources | E (chain-36) | "Far beyond search results" as space |
| Cast orbits, spirals into the arrow tip as the logo forms | G (t5-close) | Every character of the film converges on the brand |

---

## d. HyperFrames technical playbook

### Setup and hazards (HyperFrames 0.8.137, Apache-2.0)
- Pin `npx --yes hyperframes@0.8.137`; run `telemetry disable` once (telemetry is on by default).
- **Never** pass `--describe` to `snapshot` (it sends frames to Gemini when `GEMINI_API_KEY` is set). Run
  `env -u GEMINI_API_KEY npx hyperframes@0.8.137 snapshot ... --describe false`.
- **Never** use `capture` in the cloud sandbox (proxy CA not trusted by headless Chrome); run it locally with
  `--skip-vision`.
- Bundle GSAP and fonts locally (CDNs and Google Fonts fail in the sandbox; this also makes renders
  reproducible). Asset paths root-relative (`assets/...`); `../` fails lint.

### Composition contract
- `comp/index.html` is the only HTML with `data-composition-id`. Root:
  `<div id="root" data-composition-id="<id>" data-width="1920" data-height="1080" data-start="0" data-duration="<s>">`.
  Style the root via `#root`; full-bleed background on a layer, not on `#root`.
- One **paused** GSAP timeline registered **inline** in `index.html`:
  `window.__timelines["<id>"] = tl;` and end with `tl.set({}, {}, <duration>)`. Moving the registration to an
  external file fails lint (`missing_timeline_registry`).
- Lint warns on large composition files (`composition_file_too_large`): keep `index.html` small. Put CSS in
  `assets/<id>.css`, the engine in `assets/<id>.js`; build from `src/` with a `build.py` that inlines SVGs and
  strips comments/blank lines.
- Audio in previews: `<audio id="vo" src="audio.m4a" data-start="0" data-duration="<len>" data-track-index="0">`.
- The renderer emits one extra frame at t = duration: trim to the exact frame count in assembly.

### Seek safety (every frame must be a pure function of t)
- Initial hidden states with `gsap.set(...)` **outside** the timeline.
- A `fromTo` that starts after t = 0 on an already-styled element needs `immediateRender: false`.
- No CSS transitions or `@keyframes`, no `repeat: -1` / `yoyo`, no `Math.random` / `Date.now` /
  `performance.now`. Seeded PRNG (`mulberry32(seed)`).
- Reset per-frame state on every branch (a stale variable froze three dots for 3 s in i04). Never feed one
  frame's positions into the next.
- Precompute anything iterative (boids, sweep-angle integrals, orbit clocks, glyph counters) offline or at init,
  then index it by t.
- In your own probes use `tl.seek(t, false)`; plain `seek` suppresses `onUpdate`.

### Architecture that works (all builders converged on it)
- **One proxy tween drives `apply(t)`**, which derives the camera, geometry, overlays and typed text from t.
- **Canvas from t** for heavy scenes: one `<canvas>` redrawn per frame. More than ~1000 CSS-3D layers time out the
  renderer.
- **HTML for all text**, positioned with the same projection as the canvas/WebGL, so text is crisp at any scale:
  - billboards: `translate + scale(F/z)`;
  - text on a 3D face: project the 4 corners, solve the square-to-quad homography, write `matrix3d` with
    `transform-origin: 0 0`; lay labels out at ~400 px per world unit so they are scaled down, never up;
  - or a CSS3D / WebGL (`alpha: true`) / CSS3D sandwich sharing one camera; a `ShadowMaterial` plane casts WebGL
    shadows onto HTML;
  - HTML always paints over the canvas: occlude with `clip-path: polygon(evenodd, frame, hulls…)` or fade text
    before anything passes in front;
  - clamp label scale (0.95–1.2) so text never drops under 30 px.
- **Camera**: monotone cubic (Fritsch–Carlson) keys per channel. Catmull-Rom / naive Hermite overshoot on uneven
  key spacing and reverse the camera. Check in node that z-speed never goes negative. An orbit rig (target,
  distance, pitch, yaw) has no singularity at top-down. For recursive zooms keep the camera in **log space**,
  relative to the deepest level (absolute coordinates lose sub-pixel precision by level 6).
- **Carriers**: objects that travel across a whip follow the camera's own progress (or put camera keys on the
  carrier path), or the frame goes 60 % empty.
- **Pre-bake heavy 3D as video plates**: render the expensive pass once, include it as
  `<video src="plate.mp4" muted data-start data-duration data-track-index>` (frame-exact in tests), then iterate
  overlays at DOM speed (~0.12 s/frame). Re-encode plates with
  `ffmpeg -i in.mp4 -c:v libx264 -r 30 -g 30 -keyint_min 30 -crf 14 -movflags +faststart plate.mp4`.
- Pure DOM (CSS 3D, SVG, blur filters) is the cheapest way to premium: the n5 Droste dive and all seven film
  segments were pure DOM.

### three.js on white (measured; full detail in `sources/tech-benchmarks.md`)
WebGL renders through **SwiftShader** (software). Vendor three.js locally and bundle the engine with esbuild
`--format=iife`. Render WebGL with `-w 1` (`-w 2` gives no speedup) and only one WebGL render on the box at a time.

| Technique | ms/frame (1080p) | Verdict |
|---|---|---|
| Base: MeshPhysical clearcoat white, RoomEnvironment 0.5, key 2.8, PCF 2048 r6, contact shadow, analytic AO, render scale 0.667 + MSAA | ~650 in the renderer | **The recipe** |
| GTAO / N8AO | 3534 / 1397 | Reject (grainy / blotchy, N8AO not seek-safe) |
| Analytic AO (16 nearest sphere proxies) | +130 | Adopt |
| Glossy floor (Reflector half res) | +250 at 0.667 | Hero shots only |
| Transmission glass, `transmissionResolutionScale = 0.5` | +500 | Needs structure behind it or reads as acrylic |
| Layered DOF (2 blur levels by CoC) | +107–180 | Adopt; premultiply by CoC to avoid halos |
| BokehPass | +650 | Static beauty shots only |
| Clay (MeshStandard rough 0.95) | 486 at 0.667 | Best matte look |
| Baked matcap | 178 | 80 % of clay at 1/4 cost |
| SDF raymarch, quarter res | 119 | Soft blobs only |
| GPU points (closed form in vertex shader) | 200k = 65 | Adopt for particles |
| MorphSVG (free in gsap 3.15), Lottie `goToAndStop(t*fps, true)` | ~0 | Free and seek-safe |

Recipe notes: unlit floor + `ShadowMaterial` catcher (a lit full-screen floor is expensive); 400-unit floor and fog
28–60 so the floor edge never shows; `RoundedBoxGeometry(...,0.12)` bevels (hard cubes look like CAD); NeutralToneMapping.

### Motion blur
- Sub-frame accumulation works because every frame is a function of t. Choose N from on-screen speed:
  `N = clamp(ceil(px_per_frame * shutter / 4), 1, 16)`; static frames pay nothing.
- Canvas 2D: pre-render sprites with baked shadows so a sample is a blit (N8 = +65 ms/frame).
- DOM: stack N clones of the world, each with an opaque background and opacity `1/(j+1)`, each at its own
  sub-time; `N = ceil(d * 0.5 / 2.5)` from the corners' screen displacement; clones use classes, never ids.
- three.js: accumulate N renders into a HalfFloat target (N8 smooth; N4 strobes on 100 px/frame).
- Cap shutter on text: `shutter_el = min(0.5, 10 / speedPx)`, or draw text unblurred.
- Cheap alternative used in the film segments: CSS `filter: blur()` on the moving layer at peak speed.

### Depth of field
- 2D/HTML: CSS `blur()` on a few large layers. `blur()` acts before the transform, so divide the screen blur by
  the element's screen scale.
- Never `ctx.filter = blur()` at full res per frame (6 min → 2 min draft once moved to quarter res + upscale).
- Mip-bias DOF on tiny type fades to blank; raise ink with distance.

### Colour gotchas
- three.js `new THREE.Color('#hex')` is already linear; converting again crushed orange to red.
- NeutralToneMapping greys white: use background #FFFFFF at exposure 1.2 to land near #F4F6F8.
- Lit orange turns salmon under tone mapping: darken the albedo in linear (`multiplyScalar(0.62)`), lower env
  and specular.
- White type on a white floor reads only with the key light behind the type.
- Blurred orange sprites read as stains; orange passing near the lens becomes a smear. Keep orange crisp.
- White bubbles vanish into white cards: switch them to ink when they lock into a shape.
- Wide contrails on white read as grey needles: thin (≤ 0.35 of bubble size), alpha ≤ 0.25, white core.

### `lint` / `check` gotchas
- Gate per render round: `lint` 0 errors / 0 warnings; `check --at-transitions --json` ok, layout 0 errors /
  0 warnings, contrast 0 errors.
- Declare deliberate layering **on the text element itself**: `data-layout-allow-overlap|occlusion|overflow="<reason>"`
  (declaring it on the container does not cover the span; 3D contexts flag `text_occluded` otherwise).
- Untyped text: `visibility: hidden`, never `color: transparent` (`text_not_painted` error). Never
  `display: none` on things you measure (`offsetWidth` = 0).
- World-anchored HTML that leaves the frame flags `escaped_container`: opacity 0 off-screen and declare overflow.
- Two identical stacked labels are an error; keep one. An svg id like `flow` is read as a connector.
- `check` times out on heavy WebGL: run it on a 0.25-scale, no-MSAA, no-blur build (same DOM layout).
- Load fonts before measuring or drawing canvas text: `document.fonts.status === "loaded"` (rebuild textures
  once when loaded). Decompose composite glyphs for extruded type (fontTools `DecomposingRecordingPen`).
- `CSS3DRenderer` owns `style.display` (toggle `object.visible`) and overwrites `style.transform` on the element
  you hand it (wrap it).
- `toShapes(true)` not `createShapes` (deprecated warnings show up in `check`).
- Run `node --check` on engines: a syntax error gives a silent blank snapshot.

### Render times and the CPU budget (4-core box, shared)
| What | Time |
|---|---|
| `snapshot --at` 5–15 stills | 6–30 s: the fast iteration loop |
| Puppeteer stills via `__apply(t)` (WebGL) | 0.4–5 s each: the real loop for three.js tests |
| 2D canvas 30 s draft (15 fps, `-q draft`) | 30 s–1 min 45 s |
| 2D canvas 30 s final | 1–5 min |
| Pure DOM 30 s with motion-blur clones (n5) | ~17 min under contention |
| three.js 30 s draft at 0.5 scale | 7–55 min under contention |
| three.js 30 s final | ~1.5–2 h under contention (~10–15 min estimated on an idle box) |
| Film segment (DOM, 8–31 s) | minutes each |
| Caption burn over the 105 s plate | 463 s |

Rules: up to 4 builders on 4 cores; one render at a time per builder; WebGL `-w 1`; drafts at reduced quality
first; most review on stills; at most two drafts then one final. Long renders: start detached with
`setsid nohup <cmd> > log 2>&1 &` (the tool's background limit is ~2 h; a render started with plain `&` inside a
tool call dies with `render_cancelled_parent_exited`). Watch the output file, not `pgrep` (it matches its own loop).

---

## e. Audio

### Voice
- ElevenLabs REST `POST /v1/text-to-speech/{voice_id}/with-timestamps` gives **character** alignment; aggregate to
  words in code. The MCP gives no timestamps (use it only for interactive voice work).
- Audition the same two scenes across 4–6 voices; measure articulation wpm and pitch variation (lens prosody).
  The client wanted "a cool 30 year old female salesman, with interest in tech and marketing": serious, fast.
  Chosen: Hope (corporate), v4 model, default settings, ~211 wpm articulation, pitch std ~3.9 st.
- Delivery: no playful audio tags (a chuckle read as weak); full stops instead of `...`; scene tail 0.5 s.
- v4: no pronunciation dictionaries, no SSML breaks; audio tags appear in alignment but are not spoken.
- Cost: v4 ≈ 0.11 credits/character (18 takes, 2,798 chars = 306 credits); the 105 s read ≈ 298 credits.
- Short lines run fast (247–265 wpm); watch them in review.

### Music bed
- ElevenLabs Music `POST /v1/music` with a `composition_plan` (chunks with `[Section]` and `{directions}`,
  `duration_ms` per chunk, positive/negative styles) built to the voice timeline. `force_instrumental` is refused
  with a plan; a plan without lyrics came back instrumental. ~12.5 credits/s.
- Style that worked: playful funk-pop, ~120 BPM, bouncy bass, mallets, claps, **no lead melody**, "sits under a
  fast voiceover"; negatives: four-on-the-floor, EDM drops, corporate stock, ukulele.
- Master (voice + bed) measured −15.5 LUFS, −1.7 dBTP before SFX.

### SFX method (the pass that worked; `sources/sfx-notes.md` has every cue)
1. **Event list first.** Every cue starts from a beat in the segment NOTES (latest cut), with its global time.
2. **Palette, not one-offs.** 19 sounds, each generated once and reused with pitch shifts (±4 semitones) and
   per-cue gain: swoosh-soft, whip-fast, swoosh-reverse, dive-whoosh, click-ui, key-ticks, count-ticks,
   tick-roll, chime-warm, chime-rise, glass-tick, pop-soft, card-land, pill-drop, impact-low, stamp-felt,
   send-swish, riser-air, logo-hit. Generations are cached by a hash of the request body, so nothing regenerates.
3. **Snap to the picture.** Per-frame max block difference (12x9 grid on 192x108 grey). A cue snaps to the motion
   peak (appearances, swooshes) or to the settle frame (landings, ≤ +6 frames) within ±0.2 s. Without a clear
   spike, check a 10 fps strip and set it by hand.
4. **Per-type offsets** (corpus medians): chime −31 ms, impact +16 ms, swoosh −27 ms, click −89 ms, pop +23 ms,
   typing 0. Placement: start = reveal + offset − the sound's anchor (onset for transients, RMS peak for swooshes).
5. **Pan swooshes right → left** (±0.35) to follow the leftward current.
6. **Voice masking rule.** Estimate the voice from the narration stem (least-squares gain into the master). For
   every 400 ms window (50 ms hop) where the voice is active, SFX bus RMS ≤ voice RMS − 6 dB. Lower the worst
   contributor until no window fails; cues pushed below ~−27 dBFS are dropped or moved.
7. **Logo exception**: the riser and logo hit under "Ack-me" sit 3 dB under the voice, band-limited to
   < 300 Hz and > 6 kHz so they stay out of the voice's mids.
8. **Density**: target ≤ 40/min (corpus median 38/min, range 13–57; premium-calm films are near 0–5). Final:
   67 cues, 38.2/min; impact 33 %, swoosh 22 %, chime 15 %, pop 12 %, click 9 %, typing 9 %.
9. **Not on cuts**: ≤ 30 % of cues at scene starts (±2 frames) (we had 1 %, or 21 % counting pushes/whips).
   ≥ 60 % of cues near a local motion peak (93 %).
10. **Mix**: master + SFX bus → 4x-oversampled limiter at −2.5 dBFS → two-pass `loudnorm` (I −15.2, TP −1.2,
    LRA 11), second pass in **linear** mode → 48 kHz → AAC 192k. The video stream is copied untouched.
11. **Listen proxies**: waveform + cue markers + voice/SFX RMS + spectrogram for the full film and the 3 busiest
    10 s windows. No human listening was done on Acme; do one next time.

Lessons: two short generations came back silent (−63 dB); re-prompt with plainer wording ("Mouse click sound
effect, a single crisp clicky computer mouse button press"). Generated whooshes carry more low end than asked:
high-pass at 120 Hz. Typing and count ticks mixed under −16 dBFS read as texture. With near-continuous VO most
cues must land between words.

### ElevenLabs facts (verified 2026-10-08; `sources/elevenlabs-facts.md`)
- `POST https://api.elevenlabs.io/v1/sound-generation`, header `xi-api-key`, query `output_format=mp3_44100_128`.
  Body: `text`, `duration_seconds` 0.5–30 (null = inferred), `prompt_influence` 0–1 (default 0.3; we used
  0.5–0.6), `loop` (false), model id `eleven_text_to_sound_v2`.
- The docs say 40 credits/s when duration is specified; the `character-cost` response header showed ~10/s
  (21 generations, 208 total). Which one bills is unverified.
- Our scoped key lacks `user_read`, so the balance (`GET /v1/user/subscription`) is unreadable with it.
- Prompts that worked are short and physical, with audio words: "Soft paper card landing on a table, gentle muted
  tap, dry"; "Felt rubber stamp pressed firmly on paper, soft dull thud, satisfying, dry".

### Captions
- 65 groups of 2–6 words, split on phrase boundaries from the word timings (`captions.json`: `start`, `end`,
  `words[{w, t}]`); also exported as `.srt`.
- Look: Inter 600, 44 px, navy #3E0863 on a white pill (rgba 255,255,255,0.92), pill bottom 66 px above the frame
  edge (baseline ~y 990), two-line groups get a 40 px radius.
- Motion: group text fades in 0.12 s with a 6 px rise; each word goes from 0.35 to 1.0 opacity on its spoken time
  (0.06 s); adjacent groups crossfade the pill surface while the words swap (no blink, no ghosted text).
- Burn: a HyperFrames comp with the finished film as a `<video>` plate (`sources/burn-captions.sh`): build, lint,
  render (`--video-frame-format png`), mux the final audio, assert the output frame count equals the plate's.
- Design the film for captions from the start: keep y > 930 free.

---

## f. Assembly and QA

### Segments and the frame clock
| Seg | Global frames | Seconds | Content |
|---|---|---|---|
| A | 0–590 | 0.000–19.667 | chat wall, questions, dive into ChatGPT answer, short list, empty slot 5 |
| B | 590–927 | 19.667–30.900 | slot curls into logo, live feed, engine moments, Day 1→30, rivals, competitor table |
| C | 927–1379 | 30.900–45.967 | how it works: your questions, suggestions, personas |
| D | 1379–1643 | 45.967–54.767 | real browser runs: three phones |
| E | 1643–2585 | 54.767–86.167 | answer read, sentiment X-ray, sources cloud, places to win |
| F | 2585–2906 | 86.167–96.867 | agencies pitch with a report link, Signed |
| G | 2906–3154 | 96.867–105.133 | orbit collapse into the logo, end card |

Segment boundaries sit on voice pauses; each segment gets its own words file (local times) and preview audio.

### `assemble.sh` (`sources/assemble.sh`)
For each segment: count frames (`ffprobe -count_frames`), re-encode video only with
`fps=30,scale=1920:1080,setsar=1,trim=end_frame=<N>,setpts=PTS-STARTPTS`, libx264 crf 16, yuv420p; concat with
`-c copy`; mux the master audio (AAC 192k, `-shortest`). It prints each segment's frame count against the
contract, so a missing or extra frame shows at once.

### QA checks (run all on every cut)
| Check | Command / tool | Pass |
|---|---|---|
| Lint | `npx hyperframes@0.8.137 lint .` | 0 errors, 0 warnings |
| Layout/contrast | `check . --at-transitions --json` | ok; layout 0/0; contrast 0 errors |
| Stillness | `ffmpeg -i x.mp4 -vf freezedetect=n=0.002:d=1.2 -map 0:v -f null - 2>&1 \| grep freeze_` | no freezes (also try d=0.8 to find near-holds) |
| Seams | `strip-start.png` / `strip-end.png` (30 fps, first/last 0.6 s); compare last frame of N with frame 0 of N+1 (PSNR ≥ 30 dB, diff = edge antialias only); a join test of the last 1 s + first 2 s | contract geometry within 1 px; motion continuous |
| Seam ledger | `ledger.json` + seam gate (exit/entry vector, speed ratio, zero overlap, z-sign scan) | PASSED 0 fail 0 warn |
| Edge audit | `sources/edge-audit.py.txt film.mp4` (5 fps, 480x270, 4 % margin, flags dark ink or saturated orange in the margin) + a DOM audit per segment at 0.2 s steps | only exempt items (motion entries, depth layers) |
| Motion review | 10 fps strips across every move, full-res stills of every settled beat, a 480 px legibility still | nothing empty, late, colliding or cheap |
| Loudness | `ffmpeg -i film.mp4 -af ebur128=peak=true -f null -` | I −15 ±0.5 LUFS, TP ≤ −1 dBTP |
| Frames | `ffprobe -count_packets` on every output | 3154 |

Notes:
- freezedetect is stricter on final "looks" renders than drafts; a slow push under the noise threshold can read
  as a freeze (G's end card: push at ≥ 2.9 %/s).
- Seam contracts must be numeric: rect in px, radius, stroke, colours, font sizes, scale velocity (e.g. "slot
  640x120 at (960,540), still growing at 8 %/s"). Measure them on the rendered frame, not the source.
- When a seam changes mid-project (the A→B slot became 1240x200; the F→G zoom-through changed blur/opacity;
  C's send button became navy), relay the change to both neighbours in the same message.

### Export spec
- Video: H.264 High, yuv420p, 1920x1080, 30 fps CFR, 3154 frames, `+faststart`.
- Video bitrate came out ~2.5 Mbps (clean) and ~4.1 Mbps (captioned, PNG-frame render).
- Audio: AAC-LC, 48 kHz stereo (~200–290 kbps), −15.2 LUFS, −1.7 dBTP.
- Files: `acme-v2-1080p.mp4` (clean), `acme-v2-captioned.mp4`, `acme-v2.srt`.
- Platforms publish no official LUFS target (LinkedIn, YouTube); −14 to −16 LUFS with TP ≈ −1 dBTP is a convention.

---

## g. Multi-agent orchestration lessons

1. **Parallel builders: up to 4 on a 4-core box.** Each builder renders one thing at a time; WebGL with `-w 1`.
   Under contention three.js finals took ~2 h against ~17 min for pure DOM. Prefer DOM unless 3D is the idea.
2. **Detach long renders** with `setsid nohup ... &` and poll the output file; the background limit is ~2 h.
3. **Subagents can hit session rate limits mid-task.** Keep every task resumable from files: NOTES.md with a
   rounds log, renders kept per round (`render-cutN.mp4`), sources versioned (`src/x-cutN.tpl`), cue lists in JSON.
   A new agent should be able to pick up from the folder alone.
4. **Independent fresh-eyes reviewers beat self-critique.** Builders' own CRITIQUE.md files were kinder than the
   independent review every time. The reviewer forms a view from strips and stills first, then reads the
   builders' notes. Use a fixed rubric (Hook, Clarity, Brand, Motion, Craft, Scale, /10 each) and a "moments worth
   stealing" table.
5. **Seam contracts between segments, with exact geometry**, in the shared film brief. Each builder proves its
   seams with 30 fps start/end strips. Relay seam changes between neighbour agents immediately.
6. **Shared briefs create convergence.** For exploration rounds give a clean slate: no prior looks, no "he liked",
   ban the overused element explicitly ("no city, no buildings, no skyline, no map").
7. **Hard-won rules go into the next brief as numbers** (≥ 44 px questions, ≥ 40 % hero, ≤ 30 % empty for
   ≤ 0.5 s). Eight of ten builders still broke the placeholder rule, so add an automatic check where possible.
8. **Require deliverables that make review cheap**: render.mp4, kf stills, poster, strips, check.json, NOTES with
   beats in local and global time, CRITIQUE (3 good / 3 bad with timestamps), LEARNINGS for the next builder.
9. **A coordinator owns cross-segment fixes** (the A hook rebuild, F's Sent flip timing, the orbit pre-roll) and
   writes one global revision brief per cut, plus short per-segment messages.
10. **Builders rewrote the same camera/projection/typing helpers ten times.** Extract a shared kit before the
    next project (section j).

---

## h. Directions catalogue (19 concepts tried)

Scores are the independent reviewer's /60 (Hook, Clarity, Brand, Motion, Craft, Scale). Round 0 directions were
judged by the client directly. Detail: `sources/round1-review.md`, `sources/round2-review.md`,
`sources/direction-*.md`, `sources/learnings-*.md`.

### Round 0: three "go crazy" directions (9.4 s sketches + 3 key frames each)
| Concept | Pitch | Client verdict | Best moment | Steal |
|---|---|---|---|---|
| d1 One Take (navy) | One unbroken camera flight through the AI's mind; glass answers; Acme is the only warm light | "One take is great, but white and orange, not navy" | Prompts bloom in depth and fire streams; dive through "running shoes" | The one-take grammar; Hermite camera with matched speeds |
| d2 Paper Studio | Everything is a real object on a desk: typed, printed, cut, pinned, stamped | "I don't like paper" | Orange as a material (tape, stamp ink) | Orange as the only coloured material; the stamp |
| d3 Answer City | Brands are buildings, height = share of answers; questions rise as light | "I like the chat bubbles over city but that's it" | Bubbles rising over a dusk city, drone dive | Canvas engine drawn from t (CSS 3D with > 1000 layers timed out) |

### Round 1: ten futuristic 30 s directions (white + orange)
| Rank | Concept | Score | Verdict | Best moment | Steal |
|---|---|---|---|---|---|
| 1 | i01 White One Take | **46** | yes | 0–3.9 s white city with planar shadows, haze, camera flying; 17.9–20.3 s push through the glowing empty slot, orange particles assemble the logo | White depth via value steps + planar shadows; frosted glass from a downsampled frame |
| 2 | i08 Orbits | **46** | yes | 17.9–19.3 s dashed orange 5th orbit + "Is yours one of them?"; 19.3–21.5 s orbits contract into the G ring | Logo match cut; Kepler orbits analytic in t; label relaxation |
| 3 | i06 Visibility Radar | 45 | maybe → yes | Beam finds each question bubble; sweep draws the logo; Day chip per revolution | Placing objects at the beam's bearing at word time; sweep as precomputed integral |
| 4 | i09 Hologram | 44 | maybe | 27.7–30.9 s three glass engine panels re-ranking as the date ticks | Look-at `matrix3d` CSS-3D world matching canvas exactly; flip reveal |
| 5 | i10 Search Collapses | 41 | maybe | 9.2–10.4 s ten-result staircase rams into result #1 and shatters | Textured triangles in 2D canvas; closed-form shatter; best "why it matters" setup |
| 6 | i07 The Lab | 40 | maybe | 14.7–17.6 s orange laser scan lifts each brand out of the answer | 7.5 % navy hairline makes white geometry readable; 2-link IK arms |
| 7 | i03 The Prism | 39 | as a moment | 16.8–19.5 s "you are the missing colour": spectrum with an orange gap | FBO refraction + chromatic dispersion at ~0.1 s/frame |
| 8 | i02 Question Swarm | 35 | no | 20.1–21.0 s swarm locks into the logo | Bake boids to a table, play back by t |
| 9 | i04 Inside the Model | 35 | no | The list as the network's output layer; 5th node "Yours?" | Bokeh sprite pyramid; near-plane clipping |
| 10 | i05 Liquid Data | 32 | no | 12.0–13.5 s particles condense into a bold ChatGPT knot | Closed-form particle phases; curl noise zero at rest (stipple looked like pencil: avoid) |

Client reaction: "I think you overused the city." Every builder was told he liked the city, so 8 of 10 used one.

### Round 2: six clean-slate 30 s directions (no city)
| Rank | Concept | Score | Verdict | Best moment | Steal |
|---|---|---|---|---|---|
| 1 | n6 Inflate | **45** | yes | 16.6–18.4 s deflated orange skin "Your brand?" beside inflated rivals; balloons grow per keystroke | Inflation as a superellipse profile driven by thickness; 2x2 cluster; Day 1 → 30 over breathing spheres |
| 2 | n1 Answer Glass | **43** | yes/maybe | 11.6–15.9 s answer built from glass word tiles; brand tiles lift onto plinths 1–4; orange rim draws the logo | HTML pinned to 3D faces by homography; clip-path occlusion |
| 3 | n5 Droste | **42** | maybe, leaning yes | 9.4–11.4 s dive into the "o" of "should" into the answer; multi-engine feed with "N brands found" | Log-space camera; DOM motion-blur clones; coverage culling; pure DOM in ~17 min |
| 4 | n3 Type Tide | 40 | maybe | 13–17.3 s four extruded names rise out of a sea of names; engine discs ripple the sea | Key light behind white type; decomposed glyphs |
| 5 | n4 Instrument | 39 | maybe | 27.5–29 s DAY 001 → 030 odometer with motion blur | Homography screens; separate focus track; dot-matrix mask |
| 6 | n2 Aperture | 38 | no | 0–1 s iris opening on frame 1; swap content while the iris is shut | Iris maths; free motivated transition |

What we did with them: cut 3 of the film took n5's dive and feed, n6's grow-per-keystroke and big orange slot,
n4's Day counter and the review's "ten improvements" (depth on white, navy buttons, animated end card).

### Earlier motion tests (round "wow", folded into the film)
| Test | Idea | Fate |
|---|---|---|
| t1 Answer Tunnel | Fly through the question into the answer; names park on the list | Superseded by the A dive |
| t2 Three Phones | One prompt, three real apps, push in on the one that names you | Became segment D |
| t3 Sentiment X-ray | Scan line lights phrases, slips fly into signed bars | Became E's X-ray |
| t4 Source Explosion | Answer card shatters into a 3D cloud of ~340 sources | Became E's sources |
| t5 Close | Cast orbits, spirals into the arrow tip, logo forms | Became segment G |
| chain-36 | t3 → t4 as one 26.8 s film with a seam ledger and gate | The base of segment E; proved the seam-gate method |

---

## i. Competitor and trend research (summary; `sources/film-research.md`, `sources/web-trends.md`)

### GEO competitors' films (Ahrefs Brand Radar, Profound, Scrunch, Conductor; plus Attio, ClickUp, Linear, Notion)
- All open on a query or a problem, never the product; engines appear as logos; brands as pills or orbs; all end
  in a tilted dashboard, three of four on dark.
- **Avoid (already theirs)**: navy/teal with a glowing horizon (Ahrefs, Conductor); orange as glow on dark;
  warm off-white + flat orange-red + black (Scrunch, closest to us: differ with cool white, brighter orange,
  light materials, no big orange slab); radar sweeps and share-of-voice donuts; logo-chip walls; stock montage
  openers; brand-vs-brand through the ChatGPT knot (Profound).
- **White space nobody uses**: a real chat answer with the brand named inside the sentence; the same question
  across three engines side by side; rank as a physical position; one continuous camera as the spine; light,
  bright futuristic materials; tracking over time as a place you travel through.

### Craft numbers (54-video corpus)
- Median shot 2.31 s (feature reels 1.96, narrated explainers 2.74), `pace_cv` 0.85: vary shot length.
- Long takes are premium only with no dead holds (Scrunch 7.0 s, Attio 6.7 s, Linear 30 s: 0 dead holds).
- Scene medians: kinetic statement 3.23 s, comparison split 1.95 s, shape metaphor 1.59 s, icon orbit 0.99 s,
  chat demo 6.18 s (keep chat beats moving), logo close 6.86 s. Time to first UI 6.4 s.
- Motion tokens: ease-out 35 %, ease-in-out 23 %, spring overshoot 14 %; camera push-in 562 ms; kinetic word
  reveal 577 ms with 84 ms stagger; chat bubble append 589 ms; AI answer stream one piece per 238 ms; layout
  reframe 624 ms (most common transition).
- Sound: median 38 SFX/min; premium-calm films (Attio, Notion, Linear) are near music-only.
- Transitions: hard cut 53 %, continuous move 30 %, crossfade 3 %. ~80 % of shots have a depth cue.

### Trends (2024–2026, light/futuristic)
- Cliché now: purple-blue gradients, sparkles, "AI glow", pulsating orb logos, neural nets, holograms, dark HUDs,
  generic floating glass cards (Liquid Glass made glass an OS default).
- Fresh if disciplined: AI as a physical instrument (Teenage Engineering, Nothing; orange belongs here); matte
  soft-body/inflated 3D (keep it engineered, not candy); kinetic typography as the actor; light as an edge event;
  low-res dot matrix on white; real physics in white space (Lusion, Igloo); restraint (OpenAI site; Anthropic's
  2026 film shows no AI visuals at all).
- Rule of thumb: frame on white, one physical metaphor with weight, type as hero, orange only for "you"; the
  future comes from precision and physics, not glow.

### Method research (`sources/craft-research.md`, `sources/hyperframes-ecosystem.md`)
- Mayer: narration is not on-screen text; signal what the VO names when it names it.
- Studio process: brief → script → VO → moodboard → style frames (incl. the busiest frame) → storyboard →
  animatic → animation → SFX/music → mix; sign-off at each stage.
- HyperFrames skills (Apache-2.0): `product-launch-video` motion doctrine ("smooth beats bouncy", power3 default,
  no lazy breathing), `pr-to-video` cut catalog (zoom-through, inverse zoom-through, cut-the-curve, waterfall),
  `hyperframes-animation` 48 rules and 22 blueprints, the registry (410 items, `catalog --query`), and the
  repo-internal motion doctrine (vector law, the current, carriers, ledger + seam gate).

---

## j. Open items and next ideas

### Open (owner: Robert unless noted)
- [ ] **CLAUDE.md hard rule**: it still says ElevenLabs is for Phase 2 voice only. Robert approved ElevenLabs
      sound effects (and the music bed uses ElevenLabs Music); the edit was blocked in-session. Update the line
      and log an ADR.
- [ ] Log the SFX endpoint facts (`sources/elevenlabs-facts.md`) into `docs/external-facts.md` §10 and confirm
      which cost (40/s documented vs ~10/s header) is billed.
- [ ] Give the ElevenLabs key `user_read` (or check the dashboard) so credit balance can be read.
- [ ] Human listening pass on the final mix (all SFX verification so far is plots and numbers).
- [ ] Commit `docs/learnings/` (this tree; no media in it).

### Known weak spots in the final film
- Logo sting is quiet (hit −28.5 dBFS, riser −22.8) because it sits under the first syllable of "Ack-me".
- B's live feed: boxes often land as a line crosses the read band; the Acme box → mark lift is small.
- A's dive middle (10.2–10.9 s) reads as a blurred navy ring with a small card; landing frame keeps ~30 % white.
- E: G→R camera leg is sparse for ~0.25 s; docked mini cards are symbolic (17 px text).
- F: phone close-up leaves ~25 % plain floor; "Billing starts on sign" readable ~1.25 s.
- G: the orbit is fully readable for only ~0.2 s before the collapse (contract-limited).

### Next ideas
1. **Extract a `world-kit`**: camera rig (monotone cubic, orbit, log-zoom), projection + HTML pinning
   (billboard, homography), `apply(t)` proxy, SVG inliner, typing helper (grow per keystroke), carrier helper,
   motion-blur clones, edge/DOM audit, seam strips. Ten builders rewrote these.
2. **Automate the placeholder rule**: a check that no card/panel is visible > 0.3 s without content, and an
   "empty frame" metric (% background pixels per frame) in QA.
3. **Wire the SFX method into the pipeline** as a create stage (event list → cue draft → snap → mask → mix),
   with thresholds in `config/lens.yaml`.
4. **Sonic logo**: a 3-note motif for "your brand appears", reused at the orange slot and the logo.
5. **Develop the n6 Inflate world + n5 dive grammar** as a full alternative film if the client wants a v3.
6. **Pre-bake 3D as plates** to get three.js looks at DOM iteration speed.
7. **Run `capture` locally** on the client site at intake for real tokens, fonts and screenshots.
8. Ship a vertical (1080x1920) and a 30 s cut-down from the same segments; plan title-safe for both at storyboard time.

---

## k. Index: where everything is

### R2 (bucket of the lens storage; keys only)
| Key prefix | Contents |
|---|---|
| `create/acme-v2/renders/` | final renders (clean 1080p, captioned) and the `.srt` |
| `create/acme-v2/archive/2026-10-09/` | archived working media: cuts, segment renders, tests, strips, pages' media |
| `create/acme-v2/source/` | source trees (segment comps and `src/`, sfx scripts and palette, captions comp, key frames) |
| `create/acme-v2/proofs/` | the earlier s03 proof renders (`docs/motion-quality-research.md`) |
| knowledge base | this `docs/learnings/` tree, uploaded from `$S/knowledge/` |

Never put presigned URLs in docs: they carry signatures.

### Artifact pages (claude.ai, private; titles only)
- Acme v2 Explainer (the film page; notes pinned to timecodes, kept with the `db` capability)
- Acme Ten Directions (round 1)
- Acme Round Two (round 2)
- Acme Three Directions (round 0)
- Acme v2 Key Frames
- Acme Wow Tests
- Acme v2 Storyboard (two versions)
- Acme v2 Visual Directions (the rejected first directions)
- Explainer Quality Research

### Scratchpad layout (ephemeral; mirrored in R2 `archive/` and `source/`)
`$S = /tmp/claude-0/-home-user-explainer-video-creator/d8546e8e-2ef6-5546-bc1d-4c1a0ec27017/scratchpad`
| Path | What |
|---|---|
| `$S/research/` | craft, HyperFrames ecosystem, agent workflows; `hf-skills/` copies of the HyperFrames skills |
| `$S/research2/{films,web,tech}/` | round 2 research; `tech/lib` = three.js test harness (bench, render, stills) |
| `$S/wow/` | wow tests t1–t5, chain-36, shared BRIEF and JUDGE |
| `$S/keyframes/` | 10 key frames (`src/` tokens.css + kfNN.html + build.py) |
| `$S/film/` | FILM_BRIEF, REVISION_1–3, segments A–G (`comp/`, `src/`, NOTES), `assemble.sh`, `sfx/` |
| `$S/dirs/`, `$S/ten/`, `$S/six/` | round 0, 1, 2 tests with reviews |
| `$S/final/` | final exports, captions comp + `burn.sh`, `edges.py` |
| `$S/acme-v2-audio/` | narration, voice takes, music plan and bed |

### Repo
- `projects/acme-v2/` (brief, script, voice.json, storyboard, tokens, brand logo SVGs)
- `docs/decisions/0018-phase2-voice.md`, `0019-brand-assets-and-rendering.md`, `0020-voice-hope.md`
- `docs/motion-quality-research.md`, `docs/external-facts.md` §10, §14–16

### `sources/` in this folder
| File | Original |
|---|---|
| `craft-research.md`, `hyperframes-ecosystem.md`, `agent-workflows-research.md` | `$S/research/*.md` |
| `wow-brief.md`, `wow-judge.md`, `wow-t1-tunnel.md` … `wow-t5-close.md`, `chain-36-notes.md`, `chain-36-seam-gate.txt`, `chain-36-ledger.json` | `$S/wow/` |
| `keyframes-notes.md` | `$S/keyframes/NOTES.md` |
| `film-brief.md`, `revision-1.md`, `revision-2.md`, `revision-3.md` | `$S/film/` |
| `segment-a.md` … `segment-g.md` | `$S/film/<X>/NOTES.md` (cut 1/2/3/Final sections) |
| `sfx-notes.md`, `elevenlabs-facts.md` | `$S/film/sfx/` |
| `assemble.sh`, `burn-captions.sh`, `caption-build.py.txt`, `caption-template.html`, `edge-audit.py.txt` | `$S/film/`, `$S/final/` |
| `directions-brief.md`, `direction-d1-one-take.md`, `direction-d2-paper.md`, `direction-d3-answer-city.md` | `$S/dirs/` |
| `round1-brief.md`, `round1-review.md` | `$S/ten/` |
| `film-research.md`, `web-trends.md`, `tech-benchmarks.md` | `$S/research2/` |
| `round2-brief.md`, `round2-review.md` | `$S/six/` |
| `learnings-i01-white-one-take.md` … `learnings-n6-inflate.md` | each test's `LEARNINGS.md` |
