# PROGRESS

Plan: BUILD_PLAN.md v2.2. Order: M0 → M1 → M2 → M4.5 → M3 → M4 → M5 → M6 → M7 → M8 → M9 → M10 → G5 → Phase 2.

M0 + M1 merged (VijaRobert/explainer-video-creator#1). M2 + M4.5 on `claude/gifted-mayer-7839e3`.

## M0 — Bootstrap ✅
- [x] Skeleton: `pyproject.toml` (uv, Python 3.12), `lens` package, typer CLI with planned-command stubs
- [x] `config/lens.yaml` + schema (thresholds, budgets, house loudness targets, Acme v1 baseline)
- [x] Schemas: provenance, config, sources, taxonomy; `lens schemas export [--check]` → `exports/schemas/`
- [x] `lens validate <path>|--all` (fails on zero files)
- [x] Stage registry `lens/stages.py` (17 stages) + `lens dag --check` (cycles, unknown deps, overlapping
      and case-colliding writes, undeclared reads, lowercase paths)
- [x] `.claude/hooks/guard_paths.py` PreToolUse write guard + tests; `.claude/settings.json`
- [x] `taxonomy/v1.yaml` (+ `ambiguous` easing class, v1 blueprint aliases), `taxonomy/proposals.yaml`
- [x] `sources/sources.yaml` seeds: Acme v1 (own), LinkedIn reference (draft, URL needed)
- [x] `CLAUDE.md`, ADRs 0000–0004, `docs/operating-guide.md`
- [x] `Dockerfile` (built and smoke-tested: 964 MB), `ci.yml`, `image.yml`
- [x] `docs/external-facts.md`: all §0.5 facts verified 2026-10-03
- [x] CI green on GitHub (PR #1 and main)

## Open items for Robert
- LinkedIn reference URL for `sources/sources.yaml` (`linkedin-research-explainer`).
- Upload Acme v1 HyperFrames text files to `tests/fixtures/acme-v1/` (needed by M4).

## M1 — Ingest, normalize, base frames, palette, storage ✅
- [x] `lens ingest` (S1): https, `r2://inbox/`, `file://`; sha256; drafts skipped; cached reruns
- [x] `lens frames` (S2): ffprobe meta, native fps from packet timing (VFR → mode, snapped to the nearest
      common rate), CFR H.264 proxy ≤ 1280 px with exact frame count, verified before anything else;
      48 kHz `audio.wav`; 2 fps base frames `t<ms>.jpg` at 960 px; k-means palette; dHash duplicates;
      segment and `max_minutes` window
- [x] Schemas `video-meta`, `palette`; `lens validate` covers `videos/*/meta.json|palette.json`
- [x] Storage: R2 (S3 API) + local backend; `lens storage push|pull-state|put-inbox|lifecycle`;
      originals uploaded only after proxy verification, to `originals/keep/` (own, refetchable: false)
      or `originals/expiring/` (30-day lifecycle rule, tested against a mocked S3 API)
- [x] Stage markers persisted to `state/` so a fresh CI runner's rerun is a no-op (tested)
- [x] Synthetic fixtures (`make fixtures`): 1080p30 + stereo, VFR from 30, two-colour 25 fps
- [x] `scripts/local_fetch.sh` (yt-dlp / direct MP4 → `r2://inbox/`), `prepare.yml`, ADR 0006
- [x] Verified locally and inside the Docker image (ffmpeg 5.1): 3 fixtures, rerun = all `cached`
- [x] Acme v1 from `r2://inbox/` locally and in `prepare.yml` (R2 bucket + secrets in place)
- [~] `lens storage lifecycle --apply` on the real bucket — deferred (Robert, 2026-10-06): the bucket is
      ~7.8 GB, the rule would free only `originals/expiring/` (~1.2 GB) while `inbox/` keeps the same
      uploads; kept so ingest can be re-run without refetching. Revisit if the bucket grows (and expire
      `inbox/` too)

Bugs caught by the M1 tests (fixed): 30 fps was read as 29.97 (duration rounding + first-match snap);
a 2.0 s segment at 25 fps produced 51 frames (fps filter boundary flush; now capped exactly).

## M2 — Deterministic signals and local audio 🟡 (all but CLAP labels; tested on synthetic ground truth)
- [x] Video (S3): hard cuts; gradual transitions classified crossfade / push (with direction) / zoom-through /
      whip; shots; motion events with change boxes; camera moves (only for full-frame change); holds and
      **dead holds** (empty focal region); pace curve and its variation. Exact on fixtures at 24/25/30/60 fps.
- [x] Audio: BS.1770 loudness (integrated, short-term max, LRA, sample + true peak; matches ffmpeg ebur128);
      BPM and beats (kick-phase correction, sample-accurate); SFX candidates from a beat-period REPET
      foreground on the accompaniment stem, sample-accurate onsets, `on_beat` as a feature, rule labels
      (whoosh, riser, impact, click); groove and voice do not leak in
- [x] Stems: demucs htdemucs on CPU-only torch (vocals vs accompaniment); ducking depth
- [x] Speech: local faster-whisper words, boundaries tightened to voice energy; WPM, articulation rate,
      pauses and their variety, phrase-rate variation, pitch variability (semitones), energy variability;
      perceived emotion deliberately null
- [x] Captions: caption-band switches at native fps (ignoring scene changes), two-pass OCR (rapidocr 3.x,
      offline); words per group, durations, coverage, word sync
- [x] `lens signals` → `videos/<id>/signals.summary.json` (validated) + `data/signals/<id>/` (curves, stems,
      detail), cached by proxy hash; SFX offsets to reveals and scene starts; cuts on beat; WPM per shot
- [x] `prepare.yml` runs S3 with cached models; image 3.9 GB, verified S1–S3 + compare inside it
- [x] CLAP labels (local `laion/clap-htsat-unfused`, Apache-2.0) recorded next to rule labels, with agreement
      (ADR 0008); rules stand where they decide, CLAP fills `unsure`
- [ ] CC0 SFX calibration set (freesound.org needs an account/API key) and the msclap vs laion choice (G2)
- [x] Real footage: Acme v1 found 0/14 transitions (slow fades/pushes on a light canvas); added a
      long-baseline dissolve detector (ADR 0009) → exactly 14 (7 crossfade, 5 push, 2 zoom-through).
      SFX-at-scene-start now measured against the whole transition span, not one frame

## M4.5 — Baseline audit ✅ code (waits on the Acme v1 file)
- [x] `lens compare --video <id> --targets-only [--destination linkedin|youtube]` → `reports/compare/<id>/`
      `metrics.json` (validated), `<date>.md`, `<date>.html`; house targets in `config/lens.yaml` with sources
- [x] Ranked top fixes with timestamped evidence; voice/beat/caption metrics n/a when absent
- [x] Tool check against Acme v1's known values (duration, frames, LUFS, sample peak, transitions,
      SFX at scene starts, WPM) — runs automatically for `acme-explainer-v1`
- [x] On the synthetic explainer the planted problems come back: dead hold at 0:04.50, flat intonation,
      no ducking, 1/4 cuts on beat, loudness under target
- [x] Run on Acme v1 (see M9)

Fixed: an intermittent end-to-end failure (an extra SFX candidate) came from demucs' default random
time shift per run; stems are now deterministic (`shifts=0`, seeded), with a regression test.

## Corpus batch 1 🟡 (waits on local fetch)
- [x] 61 vetted candidates (≤ 3 min reported, or unknown length; possible re-uploads excluded) in
      sources.yaml as `r2://inbox/<id>.mp4` + `page_url`
- [x] `scripts/fetch_batch.py` (local: length check, download, upload), `lens queue`, batched `prepare.yml`
      (matrix, self-continuing, failed videos marked and skipped), ingest `waiting` state
- [ ] Robert runs the fetch on his machine; batches analyse in CI

## M3 — Visual evidence and packets ✅ (code; PR pending)
- [x] S4 `lens evidence`: bursts (frame ranges), filmstrips at motion-energy quantiles cropped to the event
      box + context thumbnail, candidate boxes (diff components, changed OCR lines, union; NMS, ≤ 20),
      set-of-marks + clean end frames, mel spectrograms (accompaniment stem) with SFX ids, 2 fps contact
      sheets per shot + keyframes; every image ≤ 1500 px
- [x] S5 `lens packets`: anchors.json, facts.json, candidates.json; Pass 1 parts within 12 images; event
      tasks of 4 images; triage (low energy, small, caption band, tier, duplicates); committed manifest
- [x] `lens status [--pending --limit --json]`, `lens preview` (HTML), prepare.yml runs S1-S5
- [x] Acme v1: 5 A1 parts + 60 event tasks, 286 images, 11 events skipped; preview published
- [x] Tests: geometry, NMS, label placement, triage, packing, budgets; S1-S5 on the synthetic explainer
      finds the moving box (IoU ≥ 0.7)

## M4 — Measurement core ✅ (code; PR pending, needs Robert's merge)
- [x] Curves: GSAP eases + damped spring + cubic-bezier from first principles; golden-tested against GSAP
      3.14.2 and Remotion 4.0.532 samples (5e-9); Remotion draws overdamped springs as critical
- [x] Fits: linear / bezier / spring with free start and duration, AIC + margin, nearest GSAP ease,
      Remotion config, CSS bezier; joint timing across channels; free amplitude for unseen starts
- [x] Tracking: NCC (ring, scale steps + refinement, padded frames, held faint frames); opacity proxy;
      per-word stagger; SFX offset; `lens measure --video --event --box` -> videos/<id>/measure/<eid>.json
- [x] Fixtures (tests/fixtures/motion.py): slides, spring, fade, scale-pop, fade-and-rise at 24/25/30/60 fps
      within 1 frame; stagger exact
- [x] Acme v1 answer key from its HyperFrames source (642 tweens, 14 transitions, 14 SFX);
      evaluation: start < 1 frame, duration ~2 frames, direction 51/62, exact ease 12/62 (ADR 0011)
- [ ] Ease *names* on short UI moves are not identifiable; Phase 2 should use curve + duration

## Batch 1 — S1-S5 on 55 sources ✅
- [x] 55/55 ready sources analysed (PR #8 data); fixes on the way: 1-frame shots, outputs kept in R2,
      chain not stopped by the PR step, analysis window ends with the picture (PRs #7, #9, #10)

## M5 — Claude annotation layer (in progress)
- [x] A1/A2 schemas; `lens validate` checks ids against the manifest, taxonomy and packet (ADR 0012)
- [x] `lens status --task` briefs with exact provenance; status counts only valid outputs
- [x] Skills annotate-batch / annotate-video / annotate-event; video-annotator / event-annotator agents
- [x] `lens storage pull-packets` + packets.yml for sessions without R2
- [x] Trial (in-session, approved by Robert): Acme v1, Loom AI, Linear Releases — 73/73 tasks valid on
      the first validate; findings in runs/m5-trial-20261004/summary.md
- [x] Trial tuning (ADR 0013): overlap triage (-23% Acme tasks), 8 UI-demo patterns, camera note,
      annotated videos never repacked, repack.yml
- [x] Repack the 25 A2-tier videos (PR #13), then annotate the remaining 52 — all 55 videos complete,
      2221/2221 files valid; findings in runs/m5-full-20261005/summary.md
- [ ] annotate.yml with claude-code-action (needs CLAUDE_CODE_OAUTH_TOKEN secret from Robert)
- [x] S7 from A2 (candidate + manual boxes, one decode per video) and S8 reconcile -> record.json with a
      source per value and consistency checks; finalize.yml (ADR 0014)
- [x] Run finalize.yml: run 37287200544 measured 25/28 videos (S7). Its S8 job could not start (Actions
      minutes used up), so S8 ran in-session on the run's artifacts: 55 records, all checks ok;
      1888 elements, 1039 measured, 691 estimated, 158 without timing (83% measured outside the 3 below)
- [ ] datadog, atlassian, elevenlabs-conversational hit the 60-min job limit (estimates only). Tracking is
      now coarse to fine and pads only the search area (same positions, ~10-20x faster). Re-run finalize
      for those three after the Actions minutes reset (Nov 1; 2,000 free min/month, private repo)

## M6 — Pilot and calibration (in progress)
- [x] G1 is covered by the 55-video run (reference, average and Acme v1 sources)
- [x] Gold set seeded: `gold/<id>/gold.yaml` for Acme v1, Loom AI, Notion AI Connectors (config
      `gold`): 29 shots, 28 events (even sample, at most 12 per video), every item `pending`
- [x] Review page (`lens gold page`) and `lens gold import`; not used (see the G2 decision below)
- [x] G2 decision (Robert): machine checks only, no human gold (ADR 0015). The gold-set code stays, unused
- [x] `lens eval` (S13): answer key (Acme v1 HyperFrames truth), blind re-annotation of 10 events
      (`--rerun`), measured share -> runs/eval/<hash>.json; results in docs/evals/m6-eval.md
- [x] Tuning round (S8): measured change directions in records; easing class from the joint fit.
      Change types 64% -> 85% with measured; measured easing class 32% -> 58%
- [x] Measured share of annotated reference events: 64.4% (target 60%)
- [ ] Robert signs off M6

## M8 — Synthesis and exports (in progress)
- [x] S9 `lens synth`: weighted corpus stats (numpy, bootstrap intervals) -> corpus/stats/{motion,sound,
      pacing,patterns}.json; 45 weighted videos, 837 measured elements (ADR 0016)
- [x] `other` clustering (local MiniLM) -> taxonomy/proposals.yaml: 10 proposals (2 suggested merges)
- [x] A3 pattern cards: 21 cards (`lens status --card`, write-pattern-cards skill, numbers checked verbatim
      against the stats, own videos excluded from briefs) -> corpus/patterns/<pid>.json + .md (`lens cards`)
- [x] Proposals carry a plain description and Claude's recommendation; 6 from at least 2 brands
- [x] G4 (Robert, 2026-10-05, all 8 agreed): 4 patterns added to the taxonomy (avatar_hero_expand,
      chat_bubble_append, diagonal_ui_wipe_in, footage_with_ui_overlay); ui_camera_pan merged into
      ui_camera_push_in; documentary_handheld_drift rejected; metric_count_up held out of the recipe book;
      20 + 4 cards approved. Decided proposals stay in proposals.yaml and their events count in the stats
- [x] Scene types: 1,138 corpus shots sorted (A3, text only, `lens status --scenes`, 19 batches) ->
      corpus/scenes/; `lens scenes` -> corpus/stats/scenes.json + taxonomy/scene_proposals.yaml
      (18 candidates from 2+ brands, grouped by name)
- [x] G4 part 2 (Robert, 2026-10-05): 10 corpus scene types added (presenter_to_camera kept, hero_product_render
      rejected on his call); 3 seed archetypes held back; 7 seed archetypes kept (ADR 0017)
- [x] 17 archetype cards (write-archetype-cards skill, `lens status --archetype`) -> corpus/archetypes/
- [x] S10 `lens export`: motion-tokens, sound-spec, pacing, voice-spec, patterns, archetypes (validated) and
      the premium-explainer-patterns skill pack; leak check for corpus brands, ids and on-screen text

## M9 — Compare / QA (in progress)
- [x] `lens compare --video <id>` (corpus mode, default): 22 measures in Voice, Sound, Motion and Rhythm,
      placed among the weighted premium videos of the same format (percentile, 25-75% band, gap in band
      widths, capped); loudness also against the destination house target; baseline tool check
- [x] A4 compare-fixes skill (`lens status --fixes <video>`): top 10 fixes, each with metric, timestamps
      from the video's own timeline and recipe-book references (pattern, archetype, token) that must exist
- [x] Report (md + html) with the fixes, four sections, tool check and cohort
- [x] Acme v1: 12 measures outside the premium range; duration, LUFS, sample peak, 14 transitions and
      WPM reproduced; SFX-at-scene-start 57% (handoff expected >= 80%)

## Phase 2 prep — voice
- [x] Voice chosen: Zara (warm), `eleven_v4`, default settings (ADR 0018); account on Starter
- [x] ADR 0005 spike done (timestamps on v3/v2/v4, tags not spoken, brand respelling); ADR 0005 superseded
- [x] Detailed Phase 2 plan drafted: `docs/phase2-plan.md`
- [x] G5 partly settled: scope = Acme v2 (improve the MVP), music = Eleven Music, Starter is enough
- [x] Music: single-prompt bed rejected ("elevator music"); built-for-the-video plan (7 sections timed to Zara
      warm) prototyped and mixed under the voice at -15.6 LUFS
- [x] Acme brand hand-off received and reviewed: now `brands/acme/` (REVIEW.md; moved by ADR 0022)
- [x] G5 closed: logos in git, fonts from Google Fonts, rendering on Robert's machine (ADR 0019)

## P0 — Create: registry and skeleton
- [x] Stages C1-C13 in `lens/stages.py` (C8 split into templated `c8_build` and Claude `c8_build_freeform`);
      writes only under `projects/{project}/` and `data/create/{project}/`; the brand hand-off is an input
- [x] Schemas: brief, script, voice, timeline (`lens/schemas/create.py`), with cross-file checks in
      `lens validate` (facts in the brief, audio tags from config, scenes follow the script, contiguous timeline)
- [x] `config/lens.yaml` `create:` voice (ADR 0018) and timing defaults
- [x] `create init|status`; synthetic fixture project `tests/fixtures/create/demo/` validates

## P1 — Create: voice and timing (in progress)
- [x] C4 `create voice`: ElevenLabs with-timestamps per scene, takes cached by text+voice+model hash (rerun
      = 0 credits), words from the character alignment (tags skipped), take chosen by lens prosody against
      `exports/voice-spec.json`; `--dry-run` counts characters first
- [x] C5 `create timing`: scene = voice + tail, pre-roll and close tail from config, one word clock,
      narration preview in data/create/<project>/timing/
- [x] Acme v2 brief (13 facts with sources; topic sentiment from Robert, not yet on the site) and
      9-scene script (~105 s; Zara warm tags; sentiment by topic, sources, agency pay-on-sign);
      v1's "pay only for clients" claim dropped (not on the site)
- [x] Robert approved the script; `create voice acme-v2`: 18 takes, 306 credits (v4 ~0.11/char);
      `create timing`: 9 scenes, 108.6 s; whole narration 6/7 voice-spec measures in band (energy
      variation 8.2 dB high, for the mix); pauses now in band (628 ms) thanks to scene tails
- [x] Take choice: distance from the bands on `select_on` (config), brand round-trip check (a take whose
      transcript misses the brand ranks last); fixed a flat pick in s03 and a "Ackma" take in s09
- [x] Robert: Zara read "too slow and bored". Audition of 6 voices (228 credits); **Hope (corporate)** chosen,
      serious delivery, 0.5 s scene tail (ADR 0020). Narration 105.1 s, 298 credits, 6/7 in band
- [x] Preview: music built to Hope's timeline (9 chunks, 124 BPM), mixed at -15.4 LUFS
- [x] Robert approved Hope + the funk-pop bed (style from a local analysis of 4 ClickUp tracks; plan in
      projects/acme-v2/reference/); a 6 s dropout in the generated bed was patched (C10 must check)

## P2 — Create: brief, script, tokens
- [x] C3 `create tokens`: brand hand-off + hand-written `brand/video.yaml` -> `projects/<p>/tokens.json`:
      colours by role, WCAG 2.1 contrast computed (exact, not rounded; a failing pair needs a written
      exception), type at 1920x1080 with overrides (label 22 -> 24 px), glyph coverage measured on the Google
      Fonts files (Space Grotesk lacks ✓ -> Inter), layout in px with the 184 px caption keep-out
- [x] Acme v2 tokens: 11 pairs pass; orange accent on the marketing canvas is 2.74:1 (2.94 on white),
      allowed for display accent word and hero stat only (brand rule)
- [x] C2 style guard in `lens validate` (config `create.script`): em dash, antithesis, punchline pairs,
      slogan words, tag density, and the script's planned length against the brief's band
- [x] R2 in the cloud environment (read & write); Acme v2 media uploaded to r2://create/acme-v2/ (voice takes, narration, funk bed prototype and preview; 40 files, sizes verified)

## P3 — Create: storyboard and scene templates (in progress)
- [x] C6 storyboard schema + checks (scenes follow the timeline; archetypes from exports with required slots;
      cues on words spoken in that scene, in order; no em dash on screen; numbers need `example_data`)
- [x] Acme v2 storyboard: 9 scenes on 9 corpus archetypes (kinetic statement, chat demo, icon orbit, prompt
      input, AI working loader, document highlight, tile grid, cards triptych, logo close), 45 word cues
- [x] `create status`: "ready" needs every upstream Phase 2 stage done, not only the direct one
- [x] 9 HyperFrames templates in `create/templates/` (one per archetype the Acme storyboard uses) on a
      shared base (`_base.css` from tokens, `_kit.js`); no project copy inside templates
- [x] `create build` (C8): one standalone composition per scene; cue times = word times; motion from the
      corpus tokens (card 0.717 s, text 0.485 s, word stagger 0.084 s, circ.out / back.out(3)); render bundle
      with local GSAP 3.14.2 and fonts (no CDN at render time)
- [x] `create sketches` (C7, now after C8): HyperFrames snapshots of every scene's final frame + sheet;
      uploaded to r2://create/acme-v2/sketches/. HyperFrames check: lint/runtime/layout/motion clean;
      contrast flags only the orange accent word (2.74:1, brand exception; it suggests #F36100)
- [x] Superseded: the template sketches were replaced by the hand-built film below (Robert approved the new
      storyboard, key frames and cuts directly)

## Acme v2 film — delivered ✅ (built outside the pipeline, in session scratch; sources in R2)
The template route (C8) was not premium enough, so the film was hand-built as 7 HyperFrames segments by
parallel agents, with seam contracts between segments and independent fresh-eyes reviews. Full write-up:
**`docs/learnings/readme.md`** (read it first for any new video) and `docs/learnings/sources/`.
- [x] Research: why v1/v2 visuals failed + motion-quality method (`docs/motion-quality-research.md`)
- [x] Storyboard v2 + 10 key frames on fictional data (Acme CRM; no real client data), approved by Robert
- [x] Cuts 1→3 on Robert's notes; final = cut 3 zoomed to 0.92 (title-safe) + burned-in captions
- [x] 19 alternative directions tested in 30 s (round 0: 3, round 1: 10, round 2: 6), independently scored;
      catalogue and what to reuse in `docs/learnings/readme.md` §h
- [x] Sound: 67 SFX (ElevenLabs sound generation, Robert-approved), mixed ≥6 dB under the voice, −15.2 LUFS
- [x] Final: 1920x1080, 30 fps, 105.133 s, 3154 frames; clean + captioned + SRT
- [x] R2: `create/acme-v2/renders/` (final exports), `create/acme-v2/source/` (film source zip),
      `create/acme-v2/archive/2026-10-09/` (full session archive, 2.7 GB), `knowledge/explainer-video/`
      (the learnings tree)

## Open items for Robert (Phase 2)
- ADR 0035 (Claude usage per video) is `proposed`: accept or change it. It edited two CLAUDE.md lines, your
  call to keep: the subagent-Bash hard rule now lets builder agents (motion-builder, reel-planner) run the
  commands their agent file lists, and "Claude usage" gained the measured cost rules.
- `.claude/settings.json` now denies the tools video work never uses (session admin, Workflow, onboarding,
  and the ClickUp, Figma, Gmail, Calendar, Sheets, Planable, Semrush, SEOmonitor, Spotify and Claude Docs
  connectors): a fresh session starts at 68.9k tokens instead of 90.5k (measured). A session on this repo that
  needs one of them: delete its line from `permissions.deny`. The probe branch `claude/baseline-probe` can be
  deleted (the cloud proxy refused).
- CLAUDE.md hard rule still says ElevenLabs is voice-only; Robert approved it for SFX too. Edit that line
  (an agent may not edit CLAUDE.md), then record an ADR and the sound-generation API facts in
  `docs/external-facts.md` (facts already verified: `docs/learnings/sources/elevenlabs-facts.md`).
- Optionally add a pointer to `docs/learnings/readme.md` in CLAUDE.md so every new session reads it.
- The film's code lives in R2 (not git, media rule); bring the reusable kit (camera rig, captions, edge audit,
  assemble script) into `create/` as a proper milestone before the next video.
- Research for the next phase (vertical TikTok/Reels/Shorts with measured safe zones, presenter footage, more
  brands): `docs/research/vertical-footage-brands.md` (roadmap M-A..M-G and Robert's decisions in §5–6).

## Brands and own footage (ADR 0022)
- [x] Robert's answers recorded (ADR 0022): code changes approved, ElevenLabs speech-to-text approved, own voice,
      any language, phone with or without a mic, edits only in the pipeline, palette for acme.example later
- [x] `brands/<brand>/` is the shared hand-off: Acme moved to `brands/acme/`; `Brief.brand` (validated);
      `create init <project> --brand <brand>`; C1/C3/C8 read `brands/{brand}/**`
- [ ] Robert: apply the CLAUDE.md lines written out in ADR 0022 (the agent's edit was blocked)
- [x] M-B part 2: C3 for any brand (validated `video.yaml`, font families by role with weights, named size
      set, semantic logos, `extra_glyphs`, brand accent tint, template UI `strings`, brief `language`); format in
      `brands/README.md`; Acme tokens and scenes regenerated (CSS unchanged)
- [x] acme.example intake from the Claude Design hand-off (2026-10-12): `brands/acme/` (tokens with
      1920x1080 and 1080x1920 size sets, video.yaml, DESIGN.md, FONTS.md, REVIEW.md, 10 logos with outlined
      wordmarks); `create tokens` clean on both frames (✓ in Inter; C3 now checks and loads fallback families);
      Acme v2 scenes rebuilt with the brand: audit 0 issues
- [x] Robert's answers (2026-10-12, REVIEW.md): prism is the main logo, English only, accent fills -> ink
      (`accent_fill` role read by every solid accent fill in templates and the motion kit); vertical captions
      light the spoken word in cobalt on a near-solid pill; scene CSS takes weight and family from the brand
- [x] M-C frame profiles (ADR 0023): `create.design.frames` (landscape, vertical with the measured TikTok/Reels/
      Shorts safe area and caption band), destination -> frame, tiktok/instagram_reels/youtube_shorts destinations,
      brand `frames.<frame>` sizes, templates declare frames, `create audit` (c8_audit) measures text/logo boxes
      in Chromium; Acme v2: "Example data" was in the caption band in 3 scenes, fixed, audit clean
- [x] M-D part 1, caption kit (ADR 0024): `create captions` (grouping per frame; Acme v2: 67 groups vs 65
      hand-made), brand `captions.<frame>` styles (pill, karaoke) checked in C3, `create burn` (HyperFrames,
      frame-exact); landscape and vertical burns verified in the sandbox
- [x] M-F presenter footage (ADR 0025): `voice: presenter` briefs; `create ingest` (CFR SDR masters, HDR tone
      map), `transcribe` (ElevenLabs Scribe, verbatim, keyterms; whisper fallback), `cuts` (fillers, cue words,
      false starts, long pauses) + `cuts-approved.yaml` human gate, `edl`, `timing` (presenter mode), `edit`;
      sandbox run: 20.8 s of takes -> 15.3 s, captioned 1080x1920. Filming guide: `docs/filming-guide.md`
- [x] F5 `create reframe` (YuNet face crops, alternating punch-ins) + `create pip` (per-scene layouts from
      `layout.yaml`: full / corner bubble / off, one continuous move between them; safe-area and caption aware);
      tested on a real presenter clip from the corpus (local only)
- [x] TikTok finish (ADR 0025 addendum, Robert's first take): punch-in splits on long stretches and a short first
      shot, voice finishing to the destination loudness with a true-peak limiter, captions below the face and
      above the seam in split scenes, `layout.yaml` split (product on top) and `create overlay` cards, `create qa`
- [x] Presenter reels (ADR 0026): `create reel` renders layout, script-timed widgets (create/kit/motion.js),
      captions above the head / above the seam and a grade in one pass; `--preview` contact sheets; QA
      `captions_clear_body`; synthesised UI sounds; 6 variants audited, 2 finals
- [x] Reel tooling (ADR 0026 addendum, 2026-10-11): `create prep`, `create words`, `create reel --check` (plan +
      Chromium layout checks; renders refuse plans with errors), `--draft`, `create review` (+ crops), skills
      draft-reel-plan / review-reel, agents reel-planner / reel-reviewer (smaller model); JPEG frames make a reel
      render ~6 min instead of ~14; tests run in parallel (~2 min); audit fixes (cut approval by id, faststart loop,
      crop edge, faces in short segments)
- [x] Reel props and effects (ADR 0027, 2026-10-11): `props:` characters in room space (Robert's PNG or drawn:
      fish, pixel cat) with styles photo / illustrated / pixel / toon3d, accessories, moves, tags, carries;
      `fx:` anime, blocky, grade, caption font, shake, flash, glitch, fade to black; widgets shredder, code,
      bucket, agents; `create matte` (F7, HyperFrames remove-background, spans only); prop sounds. Checked on a
      synthetic take (contact sheets and a full render with the matte). Filming notes: `docs/filming-fred-and-pixie.md`
- [x] Pixel art from shapes (ADR 0028): create/pixel renderer (hue-shifted ramps, one light, sel-out, contact
      shadows, cleanup), kitten and pixel-Fred sprites with keyed cycles, `create pixel` previews, skill
      pixel-art; reels use the sprites (Python schedules every frame)
- [x] Animation lab (ADR 0029, 2026-10-12):
      - `create lab`: a stand-in reel from a stock photo and an ElevenLabs voice, with motion-study strips
        and a green-edge scan;
      - 20 lab reels reviewed and logged in docs/learnings/animation-lab.md;
      - motion and timing rules in props.py and the kit (gait speeds, jumps, a pounce, stop-short carries,
        exits that wait or stay, peeks behind the matte, accent recolour);
      - real 3D Fred (create/render3d, a numpy SDF ray marcher; turntable, idle, hop, wave);
      - a better Pixie (a three-quarter face with big eyes, soft fur, pounce, jump) and pixel Fred (fins
        off the face);
      - skill character-animation;
      - a fresh-eyes code audit with every confirmed bug fixed and tested.

      Final demo plan: docs/lab/v20.yaml.
- [x] Fred and Pixie take 1 (2026-10-12/13): cuts, carp redesign, hand tracking, 10 iterations, a variants
      tournament and a 9/10 push (r12-r26, best fresh-eyes score 7.6, r25). Logged in
      docs/learnings/fred-and-pixie-take1.md and fred-and-pixie-tournament.md. Robert: "the animations are
      overused; Fred should go in and out of the scene", which led to the two studies below
- [x] Studies (2026-10-13, studies/README.md), kept independent and combinable:
      - TikTok: 200 listed, 194 measured and annotated (AI, marketing, Claude, GEO, SEO), findings and
        stats.json, skill tiktok-edit;
      - pixel art: 79 sources (33 games, 7 styles, 7 artists, 10 creators, 21 tutorials, 1 talk), 125 notes,
        39 GIFs and 57 TikTok clips measured, findings with 15 rules for Fred, skills pixel-art and
        character-animation updated;
      - studies/combining.md: where the two meet.

      YouTube (tutorial channels, Kyle Bunk's GDC talk, trailers) is deferred: the cloud is blocked, and
      scripts/study_youtube_fetch.py runs on Robert's laptop if a later re-cut shows a craft gap
- [x] acme creative latitude (ADR 0031, Robert 2026-10-17): DESIGN.md splits fixed anchors (logo, end
      card, lower third, captions, brand type, voice, legibility) from per-video variables (animation colours,
      style and motion that fit the topic, reason in a `# look:` comment); topic palette starting points with
      measured contrast in colour-roles.md; draft-reel-plan and review-reel read it
- [ ] Next: re-cut Fred and Pixie with tiktok-edit + pixel-art (fewer moves, exits and returns, small Fred in
      the back, one effect, hook at 0 s, comment-keyword CTA)
- [x] Phone flow (2026-10-11): `create cuts --page` (tap to keep/cut, send back one line), `create cover` (hook
      below the chin, cover-safe rect), write-post skill (TikTok), process-take skill (a full video Robert sends
      to finished versions). Robert films on his own (no teleprompter), sends the video himself (no Drive
      watching), and other formats are built only when he asks;
      the SessionStart hook installs media tools, exports CHROMIUM and warms the GSAP cache
- [x] Motion kit craft (2026-10-11): entrance styles per widget (rise, pop, slide, flip, focus, pixel), code-drawn
      pixel art (14 fill-only sprites, outline and edge shading from code, 3x5 pixel font, frame-exact builds,
      shine, burst), livelier landings; tests/test_motion_kit.py proves every widget seek-safe (found 5 bugs)
- [x] Reel flow (ADR 0033, Robert 2026-10-17: "lackluster, repeating from one video to another, no flowing
      animation from one cut to the other"): `motion: {style}` per plan (config presets paper, editorial, playful,
      terminal; classic = before), hand-overs between product cards (morph carrier, push, stack; never a swap or a
      crossfade), one step label per run of cards, the push-in alternating across cuts, the product background
      and cards reacting to cuts, cards entering on the cut, wipe and unfold entrances, a drifting background;
      review rubric line "flow". Seek-safe in the kit tests; e2e on the synthetic take. Not yet rendered on
      Robert's footage (no take in the cloud): the first real render tunes the config numbers
- [ ] Next: presenter archetypes in the storyboard, assemble step, vertical template layouts,
      M-G vertical corpus, a phone-friendly cut approval page; Robert's first real take to tune the cut rules

## P3b — Claude motion with our learnings (ADR 0032)
- [x] Comparisons (2026-10-17): demo15 (15 s silent) and demo25 (25 s, Hope voice, funk-pop bed, SFX): freehand
      Claude vs our templates vs freehand inside a direction pack + grader; the hybrid won demo25 (blind 5.7 vs
      4.3 vs 3.7, 0 grader fails, fewest tokens). Robert: switch to Claude motion, keep the learnings
- [x] Route: brief `build: motion` (default) | `templates`; `cut_s` shortens the close tail; status marks the
      other route's stages unused
- [x] `create direction` (c6_direction): direction.md from brief, word clock, tokens, DESIGN.md sections,
      exports and config `create.motion` (11 recipes, 12 learned rules with sources)
- [x] `create grade` (c8_grade): bundle (GSAP, fonts, logos, HyperFrames' Pixabay SFX from the pinned npm
      package), hyperframes check, brand colours (light tints only) and decoration, move lengths, DOM samples
      (text size, accent moments, overlaps; persisting only), lens pacing, SFX, length -> motion/grade.json
      (`MotionGrade`) + review sheets; `--lint-only`, `--snapshot`
- [x] `create music` (c10_music, split from c10_audio): one Eleven Music chunk per scene, cached by plan,
      dropout check; `create mix` (c12_mix): voice + ducked bed + SFX at the destination's loudness
- [x] `motion-builder` agent (Sonnet) and `build-motion` skill; settings allow its two files and `create grade`
- [x] From launch-video-kit (docs/learnings/launch-video-kit.md): grade checks the ease mix (families,
      overshoot share, overshoot only on small elements) and the frame at rest inside a handover window; 3
      new motion rules; SFX cues pan with their reveal (`x`); reviewer asks the logo-swap and stock-move
      questions
- [ ] Next: tune accent counting and text-size limits on real projects; c13_qa on the motion final; a
      shared-element morph helper if builders keep re-inventing it; test the kit's pacing claims on the
      corpus (docs/learnings/launch-video-kit.md)

## Claude usage per video (ADR 0035)
- [x] Measured five video sessions (2026-10-17): $3.4-25 of Opus each, 47-64% of cache reads from the ~83k
      start context; requests one call at a time, polling, page writing and reference reading in the main session
- [x] Beat sheet then page in the main session from a 7 KB starter (a Sonnet panel-builder agent was tried and
      dropped: ~135k output tokens a page); `create panel --init`, stamped
      stills sheet, `create words --times`, `create cover --split --onto`, `void seek` (render hang)
- [x] process-take, build-panel, write-post, lab-reviewer, motion-builder and CLAUDE.md: fewer and smaller
      requests; SessionStart silences uv's UV_NATIVE_TLS warning
- [x] Five loops with an independent auditor (2026-10-23): `create take`, quieter status, the handover in one
      call, two fresh-eyes reviews kept, seek-safe starter, missing assets and covered captions refused, the
      split cover inside the grid-crop safe area, `--assets`, agent-only skills and CLAUDE.md out of agents;
      two builder-agent trials (blind 7 vs 6 against v2, but ~$2.2 a page: the page stays with Opus);
      estimate about -15% (a lean session like x-ads) to -35% (one like facebook-algorithm), to be measured
- [x] Cuts in the message with the take: `create take --approve [--keep 0:41]` (8 of 11 projects approved
      every cut); `permissions.deny` on the tools video work never uses (fresh session 90.5k -> 68.9k tokens)
- [ ] Next: cost per video and Robert's verdict on the next three panel videos; Sonnet for video sessions and
      a device library for panels (the two levers left, Robert's call)
