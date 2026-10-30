<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/research/web-workflows.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# Web research: what good AI-agent motion-graphics workflows do (2026-10-06)

## Sources and findings
1. HyperFrames repo (heygen-com/hyperframes, ~57.7k stars) https://github.com/heygen-com/hyperframes
   - 21 skills: /hyperframes, -core, -animation, -keyframes, -creative, -cli, -audio, -registry, media-use,
     faceless-explainer, product-launch-video, motion-graphics, pr-to-video, figma, ... install `npx skills add heygen-com/hyperframes`.
2. hyperframes-cli lint-validate-inspect reference
   https://raw.githubusercontent.com/heygen-com/hyperframes/main/skills/hyperframes-cli/references/lint-validate-inspect.md
   - `npx hyperframes check` = lint + one browser seek pass: runtime errors, failed requests, LAYOUT, *.motion.json, WCAG contrast.
   - Layout audit: text overflow/clip, held-text overlap + occlusion (coverage fractions), container escape, coord misalignment.
   - Samples 9 timestamps by default; `--samples 15`, `--at 1.5,4,7.25`; transient = info, persistent gates exit code.
   - Escape hatches: data-layout-allow-overflow|overlap|occlusion|caption-zone.
   - *.motion.json: {duration, assertions:[appearsBy{selector,bySec}, before{a,b}, staysInFrame, keepsMoving{withinSelector}]}.
   - `npx hyperframes snapshot --at <midpoints>` contact sheet; detects tiny unstyled content, canvas-sized icons, missing hero.
3. faceless-explainer SKILL https://raw.githubusercontent.com/heygen-com/hyperframes/main/skills/faceless-explainer/SKILL.md
   - BRIEF -> frame preset/design system (frame.md) -> STORYBOARD.md+SCRIPT.md approval loop -> audio durations sync ->
     visual design per frame (time-coded shots, "## Video direction") -> parallel frame workers -> lint/check -> snapshot contact sheet -> approval -> render.
   - "sketches-first recommendation"; motion vocab only from rules-index names.
4. Claude Design -> HyperFrames guide https://github.com/heygen-com/hyperframes/blob/main/docs/guides/claude-design-hyperframes.md
   - Banned fonts Inter/Roboto/Poppins/Playfair; 60px+ headlines, weight contrast 300 vs 900.
   - Entrance tl.from offset 0.1-0.3s; 3+ eases; every element keeps moving (2+ mid-scene patterns: counter, SVG draw, stagger, float, bar fill, zoom, highlight sweep).
   - Duration by words: 1-3w 2-3s, 4-10w 3-4s, 11-20w 4-6s, 21-35w 6-8s; hard cuts ~95%, 2-3 shader transitions for hero moments.
5. hyperframes-creative house-style + video-composition
   https://raw.githubusercontent.com/heygen-com/hyperframes/main/skills/hyperframes-creative/references/house-style.md
   https://raw.githubusercontent.com/heygen-com/hyperframes/main/skills/hyperframes-creative/references/video-composition.md
   - "Generic, web-page-looking output" = single biggest failure cause. Lazy defaults: gradient text, left stripes, neon/cyan-on-dark, pure black/white, identical card grids, centered stacks.
   - One accent hue; same bg all scenes; tinted neutrals; 2-5 ambient decoratives/scene with ONE shared loop; decorative opacity 12-25%.
   - Video scale: headlines 64-120px, body 28-42, labels 18-24, padding 60-140; justify <24px. Hero text 60-80% frame width;
     pin to edges, zone/split layouts; two focal points; 6-10 visual roles across bg/mid/fg.
   - Motion 0.3-0.6s, overlapping entries.
6. hyperframes-animation rules-index https://raw.githubusercontent.com/heygen-com/hyperframes/main/skills/hyperframes-animation/rules-index.md
   - ~50 named atomic rules (spring-pop-entrance, waterfall-entry, coordinate-target-zoom, viewport-change, cursor-click-ripple, svg-path-draw, svg-icon-enrichment, chart-scrub-readout...). Compose 2-4 per scene.
   - Transform/paint props only; stagger cap items x stagger <= ~0.5s; DOM measure at build time only; animation-map.mjs audits dead zones/stagger.
7. motion-graphics skill: asset-first (resolve real material BEFORE designing the shot); proof snapshots = opening state, signature move, final hold.
8. charlie947/motion-graphics-skills (77 stars) https://github.com/charlie947/motion-graphics-skills
   - 7 house rules: verified facts list; brand files only; banned: typewriter, glow, bounce, gradient text, purple-blue bg;
     motion on twos; empty first frame is cut; mid-shot frame QA for clipping/overlap/facts; real logos/screenshots never redrawn.
9. Grow with AI guide (Claude Design animations) https://growwithaiguide.substack.com/p/claude-makes-the-best-motion-graphics
   - Stages: style guide+shot list -> stills per shot (one HTML storyboard page at production size) -> rough -> polish.
   - Critique prompt: score 1-10 hook<2s, readability at phone size, motion quality, variety (new thing every 2-4s), brand; fix 3 biggest; loop until >=8. Best piece = 163 rounds.
   - Attach reference frames; animate real product screenshots.
10. claude-remotion-skill (haidrrrry) https://github.com/haidrrrry/claude-remotion-skill
   - no linear motion; 2-3 props per entrance; stagger 3-6 frames; exits faster than entrances; 5-layer stack; idle breathing; theme file; render->ffmpeg frames->inspect->fix loop.
11. Agent Architect (Chris Tyson) https://theagentarchitect.substack.com/p/claude-code-remotion-video-rendering
   - narration measured to frames; contact sheets of whole film reveal hierarchy/clipping/repeated compositions; consecutive frames for motion; "when a metric contradicts the evidence, inspect the evidence".
12. Remotion agent skills https://www.remotion.dev/docs/ai/skills (`npx skills add remotion-dev/skills`; best-practices, studio preview, docs lookup).
13. GSAP official skills https://github.com/greensock/gsap-skills (core, timeline, perf, plugins incl. SplitText/Flip).
14. LottieFiles motion-design-skill (MIT, 1.9k stars) https://github.com/LottieFiles/motion-design-skill — Disney 12 principles, duration/easing lookup by element size, choreography, quality eval. Lottie Creator MCP.
15. Manim: 3brown1blue https://github.com/AmitSubhash/3brown1blue (audit_video.sh frame extraction; container lifecycle anti-overlap), 3b1b-video-skill. Motion Canvas/Revideo: no official agent skill (pkgpulse comparison).
16. Anthropic frontend-design https://www.skills.sh/anthropics/skills/frontend-design — commit to bold direction; one orchestrated moment beats scattered effects; ban AI-slop fonts/palettes.

## Icons (verified via CDN 2026-10-06)
- Lobe Icons @lobehub/icons-static-svg 1.95.1, MIT (code licence; logos remain trademarks): openai, claude-color, gemini-color, perplexity-color, copilot-color, grok all 200. 700+ AI brands. https://github.com/lobehub/lobe-icons
- simple-icons 16.34.0 CC0: anthropic, claude, googlegemini, perplexity, githubcopilot present; openai 404 (removed; jsdelivr @latest cache may still serve 15.x). Monochrome only. Disclaimer: get permission from brands.
- svgl (MIT, ~400+) API api.svgl.app?search=: OpenAI (light/dark + wordmark), Claude AI, Perplexity, Gemini, GitHub/Microsoft Copilot, Grok all present.
