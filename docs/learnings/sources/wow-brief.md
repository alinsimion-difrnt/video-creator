<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/wow/BRIEF.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# Shared brief: Acme "wow" motion tests

You build ONE short motion test as a HyperFrames composition (HTML + one paused GSAP timeline), render it, review
it in motion, and iterate until it is genuinely good. Work only inside your own folder
`wow/<test>/` (scratchpad). Never touch the git repo, never commit, never call paid APIs.

Scratchpad root: /tmp/claude-0/-home-user-explainer-video-creator/d8546e8e-2ef6-5546-bc1d-4c1a0ec27017/scratchpad
(below: `$S`).

## Product and brand
Acme (spoken "Ack-me") tracks which brands AI assistants (ChatGPT, Gemini, Perplexity) recommend, every day,
against competitors you pick; it reads how the AI talks about you topic by topic (sentiment), and which sources
the AI cites (Reddit, Facebook groups, forums, YouTube; far broader than SEO). Agencies send prospects a real
report as a link and only pay if the prospect signs.
- Canvas #F5F7FA (marketing) or #FFFFFF; cards white, 1px hairline #E5E7EB, radius 28-32px, shadow
  `0 1px 2px rgba(62,8,99,.05), 0 24px 60px -24px rgba(62,8,99,.22)`.
- Ink navy #3E0863 (headings), #111827 (UI text), muted #6B7280, secondary navy-70 #50697F.
- ONE accent: orange #00AA90 (orange text on light: #028C77 large only; tint bg #EBF8F6). Orange = "your brand"
  / the focal thing. One accent moment per frame. Status colours only for sentiment: green #16A34A, red #DC2626.
- Type: Space Grotesk 700 for headings and numbers, Inter 400-600 for UI/body. Bundled locally in
  `comp/assets/fonts.css` (families "Space Grotesk", "Inter"). Min text 24px; prefer 32px+.
- No gradients as decoration, no glow, no glassmorphism, no emoji, no dark filled buttons.
- Acme logo SVGs: /home/user/explainer-video-creator/brands/acme/logo/ (was projects/acme-v2/brand/logo/) (read only;
  `acme-primary.svg` is orange; strip the `<metadata>...</metadata>` block when inlining).
- Example brands are allowed but must be marked by a small "Example data" tag somewhere in the frame when data
  (ranks, numbers, brand names) appears.

## Real assets (use these, never draw lookalikes or write a name instead of a logo)
- AI engines (MIT, Lobe Icons): `$S/icons/package/icons/` e.g. `openai.svg` (set fill to #0D0D0D),
  `gemini-color.svg`, `perplexity-color.svg`, `claude-color.svg`, `copilot-color.svg`, `google-color.svg`.
  Strip `width="1em" height="1em"`, `style`, `<title>` when inlining.
- Sources (CC0, simple-icons, single path, use each brand's hex): `$S/icons/si/package/icons/<name>.svg`
  (reddit #FF4500, youtube #FF0000, facebook #0866FF, quora #B92B27, wikipedia #000000, tiktok #000000,
  medium #000000, stackoverflow #F58025, tripadvisor #34E0A1, trustpilot #00B67A, yelp #FF1A1A, g2 #FF492C,
  discord #5865F2, substack #FF6719, pinterest #BD081C, instagram #FF0069, x #000000, googlemaps #4285F4).
- Reference for style and a working composition: `$S/proof-src/src6.tpl` (a judged 11 s test of this brand,
  with build script `$S/proof-src/build.py` that inlines SVGs into a template) and its render
  `$S/proof-src/proof-v6.mp4`. Read src6.tpl first: it shows the composition contract, the GSAP patterns that
  are seek-safe, and the brand styling.
- Premium reference filmstrips (the bar to beat): `$S/proof-src/judge/profound-motion.jpg`,
  `scrunch-motion.jpg`, `ahrefs-open.jpg`; contact sheets in `$S/refs/sheets/`.
- HyperFrames skills (Apache-2.0) with the motion doctrine and recipes: `$S/research/hf-skills/` — read
  `product-launch-video/references/motion-language.md` and `pr-to-video/references/cut-catalog.md`; the rules in
  `hyperframes-animation/rules/` are concrete recipes (e.g. orbit-3d-entry, svg-path-draw, coordinate-target-zoom,
  multi-phase-camera, avatar-cloud-network). Use them.

## Composition contract (HyperFrames 0.8.137)
- `comp/index.html` is the ONLY html file with `data-composition-id` in `comp/` (put templates/scripts elsewhere,
  e.g. `wow/<test>/src/`). Root: `<div id="root" data-composition-id="<test>" data-width="1920"
  data-height="1080" data-start="0" data-duration="<len>">`. Style the root via `#root`.
- Audio: `comp/audio.m4a` is the real narration + music for your window; include
  `<audio id="vo" src="audio.m4a" data-start="0" data-duration="<len>" data-track-index="0" data-volume="1">`.
- One paused timeline: `const tl = gsap.timeline({paused:true}); ... window.__timelines["<test>"] = tl;`
  End with `tl.set({}, {}, <len>)`.
- Load `assets/fonts.css` and `assets/gsap.min.js` (local; CDNs fail in this sandbox). Inline all SVGs.
- Seek-safe rules: initial hidden states with `gsap.set(...)` OUTSIDE the timeline; a `fromTo` that starts
  after t=0 for an element already styled needs `immediateRender:false`; no CSS transitions/animations; no
  `repeat:-1`/`yoyo` loops; no Math.random/Date.now (use a seeded PRNG, e.g. mulberry32, for particle layouts);
  canvas drawing is allowed only if driven from the timeline (e.g. a proxy object tweened with onUpdate that
  redraws deterministically from its value).
- 3D: CSS perspective + `transform-style: preserve-3d` + GSAP `z`, `rotationX/Y` works and renders. WebGL renders
  in software (slow); prefer CSS 3D or 2D canvas.

## Motion doctrine (non-negotiable)
- Every reveal lands on its spoken word (word times below, seconds from the start of your clip). Motion starts
  0.05-0.15 s before the stressed word and settles by its end.
- Eases: `power3.out` / `expo.out` entrances, `power3.inOut` moves, `power3.in`/`power4.in` exits. No back/bounce/
  elastic. No idle breathing or slow drift for "life"; a held frame is fine.
- Seams are velocity-matched cuts (zoom-through, cut-the-curve, match cut; peak blur 10px text / 16-20px
  surfaces, same on both sides). No plain cross-dissolves.
- One focal element per beat; everything else dimmed (navy-70 or 40-60% opacity) or blurred. Words on screen
  are short labels only, never the narration sentence; median <= 6 words visible.
- Nothing collides. Deliberate layering must be declared on the element with
  `data-layout-allow-overlap="<reason>"` / `data-layout-allow-occlusion="<reason>"` /
  `data-layout-allow-overflow="<reason>"`.
- This is a "wow" test: spend boldness on ONE signature move that a viewer would remember, built to premium
  craft. It must still explain the product idea of the line.

## Commands (run inside `wow/<test>/comp`)
- `npx --yes hyperframes@0.8.137 telemetry disable` (once)
- `npx --yes hyperframes@0.8.137 lint .` — must be 0 errors, 0 warnings.
- `npx --yes hyperframes@0.8.137 check . --at-transitions --json > ../check.json` — `ok` must be true and
  layout errorCount 0, warningCount 0 (info is fine). Fix or declare.
- `npx --yes hyperframes@0.8.137 render . -o ../render.mp4 --quiet` (takes ~1-3 min).
- Never pass `--describe` to snapshot; do not use `capture`.
- Motion review (mandatory, every iteration): `ffmpeg -ss <a> -t <d> -i ../render.mp4 -vf
  "fps=10,scale=384:-1,tile=8x3:padding=3" -frames:v 1 ../strip-<n>.png` around each move, plus full-res stills
  of settled beats (`-frames:v 1`). LOOK at them with the Read tool. Fix collisions, empty/dead frames, things
  appearing before their word, unreadable text, and anything that reads cheap. Iterate at least 3 render rounds;
  stop when you would show it to a top motion studio.

## Deliverables (in `wow/<test>/`)
- `render.mp4` (final, with audio), `comp/` (final source), `check.json` (final, clean),
  `strip-final.png` (10 fps strip of the signature move), `NOTES.md`: the idea in 2 lines, the beat list with
  times, what you changed across iterations, known weaknesses.
- Final message: 5-10 lines: the idea, the signature move, check result, known weaknesses.
