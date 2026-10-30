<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/research/hyperframes.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# HyperFrames ecosystem research (v0.8.137, 2026-10-06)

All sources are Apache-2.0 unless noted. Local copies (scratchpad/research/):
- `pkg/package/` : the npm tarball `hyperframes@0.8.137` (only bundles 3 skills: hyperframes, hyperframes-cli, media-use; plus docs/, templates/ blank|warm-grain|from-file).
- `repo/hyperframes/` : git clone of heygen-com/hyperframes at HEAD 6fe3c2c (cli version 0.8.137 == our pin).
- `repo/hyperframes-launches/` : heygen-com/hyperframes-launches (source of HeyGen's own launch films; code Apache-2.0, bundled media/fonts/brand marks NOT licensed, see NOTICE; LFS media not pulled).
- `hf-skills/` : full copy of repo `skills/` (21 published skills incl. scripts, media stripped) + `_repo-dev-skills/` (repo-internal `.claude/skills`: motion-doctrine, cut-the-curve, oversized-cursor, seam-craft, captions-overlay, changelog-video).
- `registry-list.txt` : all 410 registry items (173 blocks, 237 components, 8 examples) with tags + description.

## What our repo uses today
create/build.py hand-writes one composition per scene from create/templates; create/sketches.py calls only
`hyperframes snapshot` and `render`. NOT used: skills, registry (`catalog`/`add`), `capture`, `check`
(layout overlap/occlusion/contrast gate), `lint`, `keyframes --shot`, `animation-map.mjs`, frame presets, blueprints,
transition injector, ledger/seam-gate.

## Skills (install: `claude plugin marketplace add heygen-com/hyperframes && claude plugin install hyperframes@hyperframes`
## or `npx skills add heygen-com/hyperframes --all`; or vendor copies)
Router `hyperframes` -> workflows: product-launch-video (SaaS URL/promo; OUR route), faceless-explainer, general-video,
motion-graphics, pr-to-video, slideshow, embedded-captions, talking-head-recut, music-to-video, remotion-to-hyperframes, figma.
Domain: hyperframes-core, -animation, -keyframes, -creative, -registry, -cli, -audio, -studio, media-use.

### product-launch-video (hf-skills/product-launch-video/)
Pipeline: init -> capture -> frame.md (preset remixed onto captured brand tokens by build-frame.mjs) -> STORYBOARD.md+SCRIPT.md
(user gate) -> audio -> per-frame time-coded shot sequence (blueprint + named rule ids) -> `catalog --query` for any named look
-> pre-install blocks -> frame-packets.mjs -> ONE SUBAGENT PER FRAME (packet = frame block + blueprint body + cited rule recipes
inlined + frame-worker role) -> assemble-index -> transitions inject/verify -> lint -> check -> snapshot at midpoints and each
cut -0.1s/+0.2s -> review -> render.
Motion doctrine (references/motion-language.md), verbatim-ish:
- "Smooth beats bouncy — power3 is the default." No back/bounce/elastic as default; "Bouncy is the #1 instant turn-off".
- "Sequential reveal in the back ~50%, timed to the voiceover." Don't dump everything in first ~25%. "Less is more."
- "No lazy breathing, no bad slow pan/push in the back half." "I'd rather have NO motion than BAD motion." Only sanctioned
  aliveness = subtle low-amplitude jitter.
- Internal seams are velocity-matched cuts (zoom-through, inverse zoom-through, cut-the-curve, waterfall).
- Seek-safe: no repeat/yoyo/infinite, no Math.random/Date.now, entrances use fromTo, no CSS transition/@keyframes, no exits
  except final frame (harness transition is the exit).
Visual design (references/visual-design.md):
- Unit = time-coded shot sequence: "Scene N (a–b s)" windows, one per spoken cue; end on a held read.
- Instantiate a blueprint (Reproduce/Adapt/Compose); never drop its signature move.
- Layout inline: framing vocab (centered, thirds, split, layered-depth, asymmetric 60/40 or 70/30, triptych, full-width strip);
  density: primary visual >= 40% of canvas, >= 3 depth layers, never a lone small cluster; hierarchy: >= 2 of size (3:1),
  weight (800 vs 400), contrast, position, motion; depth via 2–3 of size/blur/opacity/overlap/shadow-stack.
- Don't show nav bars, footers, scrollbars, real cursors/browser chrome, generic decorative shapes standing in for a real asset,
  bokeh / purple-blue "AI" gradients.
- `## Video direction` block once: palette roles, motion grammar, held-frame allocation, negative list.
- Caption keep-out: all content in top ~83% (<=900px on 1080).
- Site tour: use the REAL screenshot (capture/screenshots/full-page.png) not a rebuilt page; overlay real captured assets or
  rebuild only the one moving component.
Frame worker contract (hyperframes/references/frame-worker-core.md):
- Visible text = short motion-graphics copy (hero word/stat), NEVER a narration sentence (captions already show it).
- Reveal across full duration; hero visible by t<=0.5s; every Scene = timeline phase; reproduce rule recipe, never name-guess.
- Root styled via #root (class on root breaks at render); full-bleed bg on a class="clip" layer not #root;
  no CSS transform centering on GSAP-moved elements (use xPercent/yPercent); fonts only via local @font-face files;
  prefix ids with frame_id.

### hyperframes-animation (hf-skills/hyperframes-animation/)
- 22 blueprints (blueprints-index.md, mined from 178 golden product-launch clips) with role->blueprint menu:
  kinetic-type-beats, typewriter-reveal, spatial-pan-stations, camera-journey, zoom-out-workspace-reveal, constellation-hub,
  grid-card-assemble, logo-assemble-lockup, cursor-ui-demo, device-surface-showcase, prompt-type-submit-generate,
  agent-progress-theater, panel-edit-live-sync, transcript-scroll-artifact-reveal, dataviz-countup, titlecard-reveal,
  comparison-split, overwhelm-surround, ticker-takeover, fixed-anchor-cycle, video-text-pivot, cta-morph-press.
- 48 atomic rules (rules/*.md: cursor-click-ripple, coordinate-target-zoom, multi-phase-camera, 3d-page-scroll,
  counting-dynamic-scale, svg-path-draw, svg-icon-enrichment, depth-of-field-blur, motion-blur-streak, spring-pop-entrance...).
- 13 runnable example HTMLs (examples/), transitions catalog (transitions/*.md), adapters (gsap easing incl. seek-safe
  critically damped springEase, lottie, three, html-in-canvas), scripts/animation-map.mjs (dead zones, stagger audit).

### hyperframes-creative
- motion-principles.md: vary eases (<=2 tweens with same ease per scene), vary durations (slowest 3x fastest), vary entry
  directions, don't start at t=0 (offset 0.1–0.3s), .out entering/.in leaving, stagger in importance order, total stagger
  <500ms, exits faster than entrances; 2 focal points; fill frame (hero text 60–80% width); anchor to edges; connector lines
  must name both anchors.
- video-composition.md: video scale table (headlines 64–120px, body 28–42px, labels 18–24px, borders 2–4px, padding 60–140px,
  decorative opacity 12–25%); no full-screen linear gradients on dark (banding); brand colours strict, application adapted.
- house-style.md: "AI design tells": gradient text, left-edge accent stripes, cyan-on-dark/purple-blue gradients, pure #000/#fff,
  identical card grids, everything centred.  (NB: house-style still recommends breathing decoratives; product-launch and
  motion-doctrine ban it. Product-launch/motion-doctrine win for us.)
- 13 frame presets (frame-presets/*/FRAME.md) e.g. blue-professional, cobalt-grid, code-editorial, editorial-forest.

### Repo-internal skills (HeyGen's own launch films; "supersede upstream guidance")
- motion-doctrine: Vector Law (exit determines entry: same axis, same direction, matched speed via mirrored power4.in/out, cut
  mid-motion both sides; Z: sign of scale change must match). One "current" direction per film (default LEFT); reserved
  vectors (up = conclusion, Z-forward = deeper, Z-back = arrival). Vector ledger `ledger.json` + scripts seam-stamp.mjs /
  seam-gate.mjs verify. Carriers (cursor, docking container). Causal motion (effect on the causing frame). No idle wobble —
  sustained-motion routes: staged reveals, camera with intent, sequenced UI life, animated sequences, cursor-led action.
  "Pause at any second — something meaningful must be mid-flight." Stillness before climax 0.3–0.75s. Single entry <=800ms,
  exit ~75% of entry, total stagger <=500ms, bounce/elastic forbidden, back.out(1.4–1.7) OK. 2–3 transition types per film.
  Never crossfade.
- cut-the-curve: 5 seams + waterfall entry + nudge curve; partial travel ~12% of frame; blur 10px text / 18–20px full-frame.
- oversized-cursor: macOS arrow at 7cqw (~134px @1920), enters from off-screen below (top:115%), power3.out 0.4–0.92s, tip
  targeting transformOrigin '21% 14%', click ignites next beat, never fade-in.
- seam-craft: opaque stage ground to avoid white flash at seams.

## Registry (410 items; `npx hyperframes catalog --query "<plain english>" --json`, then `npx hyperframes add <name>`)
Blocks -> compositions/<name>.html, wired with data-composition-src; components -> compositions/components/<name>.html, pasted.
SaaS-relevant: browser-device-stage, device-frame-stage, multi-device-splay, parallax-device-dive, ui-3d-reveal, vfx-iphone-device,
macos-tahoe-liquid-glass; cursors: oversized-cursor, agent-cursor, press-ripple, cursor-annotate, cursor-context-menu,
cursor-drag-drop, cursor-marquee-select, cursor-text-select, cursor-zoom-follow, cursor-glyph-trail, multiplayer-cursors,
magnetic-cursor, touch-indicator, gesture-tap; UI flows: signup-flow, settings-toggle-flow, onboarding-stepper-flow,
modal-morph, menu-morph, tabs-slide-indicator, toggle-flip, input-feedback, typed-prompt, streaming-text, typing-indicator,
skeleton-reveal, success-check, ui-focus-zoom, sticky-mock-swap, screen-flow-carousel, scroll-feed, state-chip-rail;
AI/chat: ai-answer-rank (GEO! "Is your brand in the AI answer?"), ai-chat-reveal, chat-message, chat-thread,
message-thread-reveal, chatgpt-exchange, claude-exchange; notifications: macos-notification, native-notification-pop,
notification-stack/pileup/cascade, liquid-glass-notification; data: count-up, number-wheel, number-pop-in, animated-bar-chart,
data-chart, mk-line-graph, mk-progress-stat, conic-progress-ring, chart-story, decline-chart, bar-chart-race, star-rating-fill;
logos/proof: logo-wall, trust-strip, logo-sting, logo-brand-close, logo-outro, extruded-logo, social-proof-card,
testimonial-card, cta-lockup, cta-close, store-badge-lockup; icons/grids: grid-card-assemble (thin-line icon draws on),
icon-morph-beat, icon-swap, constellation-hub, avatar-cloud, three-orbiting-cards, split-tilt-cards, comparison-split,
spotlight-card, tilt-card; text: kinetic-type-swap, kinetic-center-build, per-word-rise, per-word-crossfade, headline-slam,
text-match-cut, scramble-reveal, typewriter, marker-highlight, inline-highlight, hw-underline/hw-callout-circle;
camera/transitions: push-in, pull-back-reveal, parallax-zoom, zoom-through-transition, whip-pan-cut, match-cut, cut-the-curve,
shared-axis-y/z, focus-rack, motion-blur, transitions-* blocks (push, scale, blur, cover, 3d, grid...); background:
mesh-gradient-bg, dynamic-grid, grain-overlay, aurora-drift.

## capture
`npx hyperframes capture https://acme.example -o capture --skip-vision --json` -> AGENTS.md, CLAUDE.md, meta.json, scroll
screenshots + screenshots/full-page.png (1x plate), extracted HTML/CSS, extracted/visible-text.txt, extracted/tokens.json
(colors, fonts), font files, images, inline SVGs (cap 30), animation metadata, contact sheets, video manifest (+ `--video`
mode to download page videos), Lottie/WebGL context. Vision captioning only if GEMINI/OPENROUTER key present (pay-per-use; keep
--skip-vision). Tried here: failed `net::ERR_CERT_AUTHORITY_INVALID` (sandbox proxy CA not trusted by headless Chrome; no NSS db
/ certutil). Run on a local machine.

## Showcase / examples
- hyperframes-launches: website-to-hyperframes (61s, 4 acts, beats ~2.5s each, music hits drive cuts; STORYBOARD gives px,
  fonts, SFX per beat), HF-heygen-stripe, hyperframes-launch, spacex-launch, heygen-apple-motion (4 re-brandable templates,
  10.8–12.8s, single index.html, ONE ease family: expo.out in / expo.in out (EO/EI), frame-number timing F(n), ledger.json of
  matched-vector cuts; README tells the agent "the motion is not yours to improve", replace only brand layer via capture).
- Registry examples (init --example): product-promo, decision-tree, swiss-grid, kinetic-type, play-mode, nyt-graph, vignelli,
  warm-grain.

## Hazards vs our hard rules
- media-use icon/image/BGM/TTS resolve uses HeyGen catalog (account; OAuth free-usage tier) -> treat as optional; logos via
  theSVG/GitHub avatar/favicon are free. TTS fallback Kokoro local.
- `snapshot --describe` runs Gemini automatically when GEMINI_API_KEY is set -> always pass `--describe false`.
- `capture` vision -> `--skip-vision`. `catalog --on-device` downloads a 33MB local model (local, OK).
- `hyperframes usage`, `auth`, `cloud`, `publish`, `feedback` contact HeyGen; telemetry disabled.
