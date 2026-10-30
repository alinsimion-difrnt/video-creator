# Handoff: how the Acme explainer video (MVP v1) was made, what worked, what did not

Status: **first MVP. Not a good enough solution yet.** It produced a watchable 2:25 brand explainer from a brief in one working session, with every automated gate green, but the narration is a synthetic stand-in, the motion has only been judged from stills, sound design is minimal, and the process needed a lot of manual glue and three rounds of after-the-fact fixes. Treat everything below as field notes for building a proper `video-explainer-creator`, not as a finished architecture.

Written 2026-10-03 for an AI that will design that repo. Paths are absolute on the machine where this was built. The project folder is `/Users/acme/Code/Github/Untitled/geo-platform/explainer-output/` (git-excluded from the product repo on purpose).

---

## 1. The task

Input from the owner: "build a video like this one, but for Acme", with a LinkedIn link to a 2:56 narrated research explainer (light pastel frames, bold sans headline with one serif-italic gold accent word, tiny uppercase corner chrome with step counters, big simple data visuals, numbered takeaways, calm voiceover). Over the conversation the owner added hard constraints:

- Explain how the tool works and what it provides, without showing the dashboard.
- Use the Acme brand (colours, fonts) everywhere; the logo is always orange.
- Plain, human script. The first draft was rejected as "robotic, AI-written" (lines like "That's a count, not an opinion"). Second draft was rewritten in the register of the reference's own narration: describe what happens, concretely, no slogans or rhetorical pairs.
- Specific content: five rapid-fire everyday questions as the hook; "close to a million answers analyzed" as the only research figure; personas shown as Bob the CEO, Maria the mom with two kids, Andrew the full-time student; a visual argument for why the API is not what customers see; pitch reports for agencies (pick ten companies, free report, pay only if they convert).
- Motion: "animated, interactive, fun, fast".
- Voice: a US woman, playful, smart, sassy, chill and conversational, with pauses, breaths and giggles controllable from the script text. Brand pronounced GEO (as in geographic) plus flux (as in flux capacitor).
- House rules from memory: no fabricated numbers, stand-in brands only, engines identified by colour plus label and never a logo, no em dashes anywhere.

Output delivered: `renders/acme-explainer-v1.mp4`, 1920x1080, 30 fps, H.264 + AAC, 144.6 s, 26.8 MB, plus a 720p preview.

---

## 2. Toolchain

- **HyperFrames** (`npx hyperframes@0.8.111`): renders video from HTML. A composition is a DOM with `data-start` / `data-duration` timing attributes, one paused GSAP timeline per composition registered on `window.__timelines[id]`, media playback owned by the framework, and a deterministic seek-based renderer (headless Chrome capture plus ffmpeg encode). Scenes are sub-compositions: one HTML `<template>` fragment each, mounted by an `index.html` orchestrator.
- **HyperFrames skills** (markdown playbooks plus Node scripts installed under `~/.claude/skills/`): `hyperframes` (intent interview, brief contract, review loop), `general-video` (companion workflow), `faceless-explainer` (whose scripts I borrowed: `audio.mjs`, `frame-packets.mjs`, `captions.mjs`, `assemble-index.mjs`, `transitions.mjs`), `hyperframes-core`, `hyperframes-animation` (blueprints and motion rules), `hyperframes-creative` (design spec, typography, storyboard recipe), `hyperframes-audio` (`carve.mjs`), `media-use` (TTS, SFX library, transcription), `hyperframes-registry` (installable components).
- **Voice**: Kokoro-82M, local, through `npx hyperframes tts`, which needs a Python with `kokoro-onnx` (installed with `uv` into `~/.venvs/kokoro`, Python 3.12; the system Python 3.9 is too old). Word timings came from whisper.cpp (`npx hyperframes transcribe --engine whisper --model small.en`).
- **ffmpeg 9**, **headless Google Chrome** for screenshots of HTML sheets, **Python 3** for glue scripts.
- Fonts: the repo's own `Inter-variable.woff2` (48 KB) and `SpaceGrotesk-variable.woff2` (22 KB), both Latin subsets. Logo: `website/public/logos/logo.svg` (currentColor paths).
- Music: a CC BY 4.0 track from ende.app that ships with a `/brag` plugin. SFX: media-use's bundled 19-file CC0 library.

---

## 3. What I actually did, stage by stage

### 3.1 Understand the reference
The LinkedIn page renders without login but its video frames do not paint in the browser pane's screenshots (poster only). Working trick: inject a `<canvas>` over the page, seek the `<video>` element with JS, `drawImage(video)` onto the canvas, screenshot. Tainted canvases still display, they just cannot be read back. I captured about 20 frames into 2x2 grids and derived the visual grammar (see section 1). The page also exposes a full transcript, which gave the narrative structure.

### 3.2 Brief, through a structured interview
One field per question, native UI: story direction (five pitched concepts, owner picked "the methods section"), destination (LinkedIn, 16:9), length (150 s, later accepted at about 3:00, actual 2:25), review mode (storyboard sketches first), voice route, build mode (companion). Everything landed in `BRIEF.md` with the owner's wording preserved. Preference-backed answers were recorded to a small prefs store so the next run can propose them.

### 3.3 Script
`SCRIPT.md`: 15 spoken lines, one per scene, 419 words in v3, with per-line delivery notes. Iterated three times on register. Lesson that matters for the repo: a good explainer script reads like a person describing what the product does, with specifics and no punchlines. Every claim was traced to the website's own published copy. The brand is spelled `Ack-me` only in the spoken lines so the TTS pronounces it; on screen it is always `Acme`.

### 3.4 Design spec
`frame.md`: YAML tokens (colours by role, type ramp, radii, components) plus prose rules, derived from the repo's `website/DESIGN.md` and `platform/DESIGN.md`. The reference supplies layout bones only; the brand supplies everything else. Key decisions: canvas `#F5F7FA`, white hairline cards, navy ink `#1E2A3B`, one orange element per frame, orange as text uses `#01775C` (AA), the gold italic accent word becomes an orange marker-highlighted word, corner chrome is texture only, caption keep-out is the bottom 17%, the logo is always orange. Section 6 carries the motion grammar (rewritten to "lively, fast, fun" after the owner's note).

### 3.5 Storyboard
`STORYBOARD.md`: frontmatter (format, duration, message, arc, audience, music) + decision sections (message, audience and arc, format, the spine, brand, bans, held frames, truthfulness, changes-from-vN with the owner's notes verbatim) + `## Video direction` + one `## Frame N - Title` block per scene with fields `scene`, `voiceover`, `duration`, `poster`, `transition_in`, `status`, `src`, `type`, `persuasion`, `beat`, `blueprint`, `focal`, `roles`, `sfx`, then `narrativeRole`, `keyMessage` and a time-coded shot sequence (`Scene 1 (0.0–2.2s): …`). Each frame cites a motion blueprint from the animation skill (kinetic-type-beats, grid-card-assemble, dataviz-countup, titlecard-reveal, comparison-split, fixed-anchor-cycle, transcript-scroll-artifact-reveal, logo-assemble-lockup). Frame headings must not use an em dash; the parser accepts `## Frame N - Title`.

### 3.6 Sketch sheet (the review surface that earned its keep)
`tools/build-storyboard-sheet.py` generates `storyboard.html`: fifteen 16:9 cells drawn in the real fonts and colours at their key moment, with container-query units (`cqw`) so the sheet matches the 1920 canvas, plus a seam map and a tokens cell. Fonts inlined as base64 so it opens from `file://`. The same generator emits one standalone sketch per frame into `.hyperframes/sketches/frame-NN.html` for the scene builders. The owner locked the sheet in one pass. Verified by headless Chrome screenshots, cropped per cell with ffmpeg for inspection.

### 3.7 Audio
`faceless-explainer/scripts/audio.mjs` with `--voice af_sky`: parsed SCRIPT.md, synthesized 15 wavs with Kokoro, transcribed each with whisper for word timings, wrote `audio_meta.json`. One line failed (exit 190, transient) and was regenerated by hand. Caption words were normalised by `tools/patch-audio-meta.py` (Acme, ChatGPT, "share of voice", sentence-initial capitals). The music bed was added to the metadata by hand (`bgm.path`, volume 0.14). `fetch-sfx` resolved the storyboard's `sfx:` cues against the bundled library.

### 3.8 Duration sync
`tools/sync-durations.py` wrote real voice length plus a per-frame tail (0.7 to 1.1 s, longer for the title card and the close) into STORYBOARD.md. Total went from a planned 177 s to 144.6 s because Kokoro speaks at about 3 words per second against the 2.7 I had assumed.

### 3.9 Scene builders (parallel subagents)
`frame-packets.mjs` wrote one packet per frame (`.hyperframes/frame-packets/NN-*.md`: the frame block, the blueprint body, every cited motion rule inlined) plus `_role.md` (the worker contract). I dispatched five general-purpose subagents, three frames each, in one wave, each prompt carrying the role path, packet paths, `frame.md`, a shared `.hyperframes/dispatch-context.md`, and the frame's sketch file. Output contract: exactly one `<template>…</template>` fragment at `compositions/frames/<frame_id>.html`, styles and scripts inside the template, root `data-composition-id` equal to the frame id, one paused timeline, background on a `class="clip"` layer, `fromTo` entrances, no exits except the final frame, no audio, no narration text, content above y = 896.

Builders took 13 to 31 minutes and 190k to 330k tokens each. A rate-limit event killed one wave mid-run: two builders had already written their files, one had written nothing. The three missing frames were re-dispatched one frame per agent after the limit reset.

### 3.10 Assembly, transitions, captions, music, checks
`tools/assemble-all.sh` runs the whole pass idempotently: `fix-ids.py` (prefix digit-leading ids), `fix-chrome-contrast.py`, `frame-precheck.py` (static contract check), `mark-animated.py`, `assemble-index.mjs` (index.html with frames on track 1, captions on track 2, voice on 10, music on 11, SFX on 20+), `post-assemble.py` (voice slots trued to media length, caption track kind), `transitions.mjs inject` and `verify` (14 transitions: crossfade, push-slide LEFT, zoom-through), `carve.mjs` (music bed carved under the voice: 7 EQ dips plus a level envelope), `hyperframes lint`, `hyperframes check` (lint, runtime, layout, motion, WCAG contrast in one browser session), `hyperframes snapshot` at frame midpoints (contact sheets). Final state: 0 lint errors (8 cosmetic warnings), 0 runtime, 0 layout, 0 contrast findings.

### 3.11 Render and verification
`npx hyperframes render --quality high`: 4338 frames captured by 4 Chrome workers in 1m45s, encoded in 21 s, total 2m19s on an Apple M4. Verified the MP4 itself: ffprobe streams, frame tiles extracted with ffmpeg at 14 times, audio windows (speech about -24 dB mean, peaks -4 dB, title gap carries music, close tail quiet), integrated loudness -20.9 LUFS, peak -3.2 dBFS.

---

## 4. What worked

- **Brand truth in one file.** `frame.md` tokens plus prose made five independent builders produce frames that read as one film. Every builder read it; none invented colours.
- **Sketch-first review.** The static sheet caught layout and copy problems for the cost of a few minutes and gave the owner something to lock before any motion existed. Builders then "dressed" approved layouts instead of inventing them.
- **Voice-first timing.** Generating narration first and cutting every scene to the real line length (plus a tail) kept picture and voice in sync without hand-timing. Builders keyed reveals to spoken cues taken from the word timings.
- **Parallel builders with a hard output contract.** Fifteen scenes landed in roughly 30 minutes of wall-clock instead of hours. The contract (template transport, id rules, clip attrs, no exits, keep-out) is what made their output assemblable.
- **Automated gates.** `lint`, `check` and the contact sheets found real defects (digit ids, contrast, text overlap, a broken lookup) before anyone watched the video.
- **Idempotent glue scripts.** Being able to rerun the whole assembly pass in one command after each fix was essential. Every patch that touched generated data had to be a script, not an edit.
- **Carved music bed.** The carve step produced a mix where the voice sits clearly in front without the bed disappearing.
- **The reference-frame capture trick and headless Chrome screenshots** for anything the in-app browser could not show.

## 5. What did not work, or not well enough

1. **Voice.** The owner wanted a playful, sassy, expressive US female voice with text-controlled pauses, breaths and giggles. Kokoro cannot do any of that, mispronounced the brand until the spelling was changed, and the four sample voices were rejected. The ElevenLabs route was chosen but no key existed, the OpenAI key in the platform env was invalid, HeyGen needed an interactive OAuth sign-in. Result: a labelled stand-in voice. This is the single biggest gap between v1 and "good enough". A real tool must have an expressive TTS with native word timestamps (ElevenLabs v3/v4 tags, or similar) wired in before anything else, and a fallback that is explicitly marked as scratch.
2. **Script register.** The first two drafts sounded like marketing slogans and were rightly rejected. The fix was a style rule, not a tool: describe what happens, concretely, in the register of the reference's own narration. The repo should encode that rule and show a good/bad pair in the prompt.
3. **Pacing estimates were wrong.** Planning assumed 2.7 words per second; the voice ran about 3.0. The 3:00 plan became 2:25 and builders had to compress planned scenes. Never plan durations from word counts; generate the voice first, then plan.
4. **Ordering bug in my own glue.** Frame packets were built once before durations were synced, so builders would have received stale timings had I not caught it. A strict DAG (voice → sync → packets → build) must be enforced by the tool, not by discipline.
5. **Subagent fragility.** A rate limit killed three builders at once; one had produced nothing, two had finished but never reported. There was no checkpointing; recovery meant watching the filesystem and re-dispatching by hand. The tool needs resumable jobs and artifact-on-disk as the completion signal.
6. **Id and CSS pitfalls.** Builders prefixed ids with the frame number (`13-what-else-level`), which CSS cannot select unescaped. My bulk rename then temporarily broke a frame whose script built ids dynamically. Rule for the repo: ids must start with a letter, stated in the contract, and the lint must run per frame before acceptance.
7. **Contrast tokens.** The design spec's muted grey (`#9AA6B3`) fails AA as text on the light canvas; 15 findings. A dimmed card (opacity 0.6) produced 72 more. Precompute contrast for every text/background token pair in the spec, and treat opacity dims as a contrast risk.
8. **Font subsets.** Neither shipped font carried U+2248 (≈) or U+2713 (✓); builders drew them as inline SVG. Ship full fonts or declare the glyph inventory.
9. **Sound design is thin.** The engine places every SFX at the frame start with offset 0; cue-level sync to reveals is impossible without hand-editing index.html. Music is not beat-aligned to cuts. Loudness is -20.9 LUFS, quiet for social feeds (-16 to -14 is typical). A real tool needs an SFX cue map with offsets, optional beat alignment, and a loudness normalisation step.
10. **Captions from ASR.** Whisper misheard "Acme", "chat GPT", "share a voice". Normalisation fixed them but this is brittle. TTS with native word timestamps removes the ASR pass entirely.
11. **Hidden side effects.** `fetch-sfx` rewrote `audio_meta.json` from an engine sidecar and silently dropped my patches; the transition injector edits the frame files to pad durations. Both are reasonable internally and both bit me. Every stage should declare what it writes.
12. **Motion has not been judged in motion.** All review was on stills: sketch sheet, contact sheets, MP4 tiles. The "fun, fast, interactive" direction cannot be verified that way. The tool needs a cheap motion preview per scene (low-res clip or GIF) before the final render.
13. **Registry components were installed but barely used.** Builders hand-built everything. Either make components first-class scene archetypes or do not install them speculatively.
14. **Environment friction.** `timeout` missing on macOS, zsh word splitting, case-insensitive filename collisions (`Acme` vs `Acme` wav files overwrote each other), the in-app browser cannot screenshot `file://` pages, the Agent harness forbids reading subagent transcripts (so progress was invisible until completion).
15. **Cost.** Roughly 1.6 million subagent tokens for the frames plus a long orchestrator context, about 5 hours of wall-clock including two owner review rounds and a rate-limit outage. Acceptable for an MVP, far too much for a product.

---

## 6. Honest quality assessment of v1

Likely weaknesses a human viewer will notice: the synthetic voice (flat, fast, slightly robotic); some scenes hold on empty placeholders for a second or two before their content lands (the triptychs in frames 7, 13, 14); the pace is uniform rather than shaped; sound effects are sparse and not tied to reveals; captions show two or three words at a time, which can feel choppy; the API-comparison scene is dense. Strengths: brand consistency, clean type and layout, honest content, correct structure.

---

## 7. Recommendations for the `video-explainer-creator` repo

1. **Pipeline as a typed DAG with checkpoints.** Stages: brief → script → design tokens → voice (with word timestamps) → durations → storyboard JSON → scene build → assembly → QA → render. Each stage writes versioned artifacts and can be resumed. No stage may silently rewrite another stage's output.
2. **Voice first, expressive by default.** Integrate an expressive TTS with native word timestamps and text tags (pauses, breaths, laughs). Keep a local fallback but flag the output as scratch in the deliverable. Build a pronunciation dictionary step (brand names) and verify it by round-trip transcription.
3. **A library of parameterised scene archetypes** for explainers (question relay, shortlist card, stat count-up, title with step rail, comparison split, document highlight, bars plus ring, cards triptych, tile grid, logo close). Fill them from the storyboard JSON instead of asking a model to hand-build each scene. Fall back to a free-form builder only for scenes no archetype covers. This is the biggest cost and quality lever.
4. **Design tokens with precomputed contrast** and a glyph check against shipped fonts.
5. **Scene contract enforced by lint before acceptance**: template transport, letter-led ids, one paused timeline, clip attributes, keep-out, no exits, no narration text, deterministic motion only.
6. **Three review surfaces**: a static sketch sheet (lock layout and copy), a motion preview per scene (lock motion), a final contact sheet plus MP4 frame tiles and audio metrics (lock delivery). Humans decide at the first two; automation decides the third unless metrics fail.
7. **Audio as a first-class track plan**: SFX cue map with per-reveal offsets, music bed with carve and optional beat alignment, loudness normalisation to a target per destination.
8. **Caption skin from tokens**, word-synced from TTS timestamps, with a brand-word dictionary.
9. **Honesty guards**: stand-in data generator with an on-screen "example data" marker, claims traced to a source list, no numbers without provenance.
10. **Script style guard**: a reviewer pass that rejects slogans, antithesis pairs and rhetorical triplets, and asks for plain declarative explanation with product specifics.

---

## 8. File inventory (project root `explainer-output/`)

- `BRIEF.md`, `STORYBOARD.md` (v5), `SCRIPT.md` (v6), `frame.md`
- `storyboard.html` (review sheet), `.hyperframes/sketches/frame-NN.html`
- `audio_meta.json`, `caption_groups.json`, `assets/voice/*.wav`, `assets/music/`, `assets/sfx/`, `assets/fonts/`, `assets/brand/logo.svg`
- `.hyperframes/frame-packets/` (per-frame build packets and the worker role), `.hyperframes/dispatch-context.md`, `.hyperframes/caption-skin.html`
- `compositions/frames/01-questions.html … 15-close.html`, `compositions/captions.html`, `compositions/components/` (installed registry items, mostly unused)
- `index.html` (assembled, with transitions and carve applied), `snapshots/contact-sheet-1.jpg`, `-2.jpg`
- `renders/acme-explainer-v1.mp4`, `renders/acme-explainer-v1-720p.mp4`
- `tools/`: `build-storyboard-sheet.py`, `patch-audio-meta.py`, `sync-durations.py`, `fix-ids.py`, `fix-chrome-contrast.py`, `frame-precheck.py`, `mark-animated.py`, `post-assemble.py`, `assemble-all.sh`, `openai-tts.mjs` (unused, key invalid), `README.md` (re-run sequence for a voice swap)
