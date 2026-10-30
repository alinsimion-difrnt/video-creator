# Audit of BUILD_PLAN.md v2.1 (before implementation)

**Date:** 2026-10-03
**Audited:** `BUILD_PLAN.md` v2.1, committed unchanged.
**Method:** I read the plan in full and checked it against itself. Where I could, I also checked it against the cloud environment and how GitHub and Claude Code behave. Items tagged **[verify]** depend on outside facts that M0 must confirm (§0.5).

Overall, the core design is strong: code measures and Claude names, set-of-marks box IDs, anchored IDs, validate loops, file-derived status and synthetic fixtures. The problems are mostly about **scope order**, **a few mechanisms that won't work as written** (workflow chaining, per-subagent path limits, the spring fit) and **internal inconsistencies** that would make Claude Code stall or guess.

Severity: 🔴 a blocker, or it breaks as written · 🟠 a major flaw, causes wrong results or wasted weeks · 🟡 an inconsistency or gap · 🟢 an improvement.

---

## 0. Decisions needed from Robert first

> **Status 2026-10-03:** D1, D2, D4 and D5 are resolved and folded into BUILD_PLAN v2.2. D1: one repo that researches, understands and creates (`lens` = Phase 1, `create` = Phase 2). D4: usage limits accepted (internal use). D5: ElevenLabs subscription via MCP, with a direct-API fallback. D3 stays open; it is non-blocking until M4.

| # | Question | Why it matters | My suggestion |
|---|---|---|---|
| D1 | **Is this repo `explainer-lens`, or the factory?** The repo is `VijaRobert/explainer-video-creator` (private ✅). The plan builds `explainer-lens` and names `video-explainer-creator` as the *future factory* repo. | The names nearly collide, and the plan refers to the factory as a separate repo. | Either rename this repo to `explainer-lens`, or keep the name and replace every self-reference in the plan. Decide now; it is cheap now and annoying later. |
| D2 | ✅ **Resolved.** `HANDOFF.md` is saved as `docs/handoff-v1.md`. | Cross-checked in §4b. | — |
| D3 | **Upload the v1 HyperFrames project text files.** The handoff §8 confirms they exist locally: `index.html`, `compositions/frames/*.html`, `audio_meta.json`, `caption_groups.json`, `STORYBOARD.md`. | They are the exact ground truth for I1 (see §4b). | Copy them to `tests/fixtures/acme-v1/` (text only, a few hundred KB). Put the MP4 in `r2://inbox/`. |
| D5 | **Where does the expressive voice come from?** | The handoff calls voice "the single biggest gap", and its fix (ElevenLabs) is a paid API. `explainer-lens` can *measure* voice, but it can't fix it. | Decide this in the factory repo. Don't let `lens` scope creep into TTS (see H1). |
| D4 | **Which Claude plan are you on, and do you accept that nightly annotation shares limits with daytime building?** | Quota is the scarce resource, and the plan's own estimate is around 1,000+ subagent tasks (see M7). | Decide after the pilot gives real numbers. |

---

## 1. 🔴 Blockers: these break as written

### B1. The workflow chaining in §10.1 will not fire
`finalize.yml` runs "on merge of an annotations PR", and `nightly.yml` "chains prepare → annotate → finalize". But events created with the default `GITHUB_TOKEN`, such as pushes and PRs opened or merged by a bot, **do not trigger new workflow runs**. An annotations PR opened by `annotate.yml` and auto-merged will never start `finalize.yml`. **[verify]**
**Fix:** make `nightly.yml` one workflow that calls reusable workflows (`workflow_call`) as jobs with `needs:`. Or, if PR-triggered chaining is really needed, use a GitHub App token for the bot pushes. Note this in an ADR.

### B2. Per-subagent path limits are not a native feature
§7.4 and Appendix A say subagents may `Write` only under `videos/**` and `Read` only packets and taxonomy. The subagent frontmatter `tools:` field picks tool **names**, not path scopes. Path rules (`Edit(videos/**)`, `Read(...)`) live in `settings.json` and apply to the **whole session**, orchestrator included. On top of that, A3 has to write `corpus/**` and A4 has to write `reports/**`, which a global `videos/**` rule would block. **[verify]**
**Fix:**
- Enforce writes with a `PreToolUse` hook (`.claude/hooks/guard_paths.py`) that reads the stage registry and allows only the current task's declared paths. That ties directly into the "declared writes" rule.
- Give each skill its own write allowlist in the stage registry, not one global rule.
- Keep the `settings.json` allowlist as a second layer, using the union of the paths.

### B3. The spring fit is over-parameterised
Remotion's `spring()` curve depends on `stiffness/mass` and `damping/√(stiffness·mass)`. Any `(mass, stiffness, damping)` with the same ratios produces the same normalised curve, so a three-parameter least-squares fit has no unique answer. It will drift, and clustering ("spring clusters", §8) will produce nonsense groups.
**Fix:**
- Fix `mass = 1` and fit `(stiffness, damping)`. Better still, fit `(ζ damping ratio, ω₀ natural frequency)` and convert.
- Cluster on `(ζ, settle_duration)`, which is what designers perceive.
- Add a fixture that asserts the parameters recovered from a known spring come back to within tolerance, not just that RMSE is low.

### B4. Packet storage is contradictory
- §5 says `packets/<id>/` is committed with `facts.json`, `candidates.json` and the manifest.
- §7.3 says those files live in `data/packets/<id>/` (gitignored), and only `manifest.json` is committed.
- The subagent Read rule names `data/packets/**`.

Claude Code will have to guess.
**Fix:** text packets (facts, candidates, anchors) go in R2 plus `data/` (gitignored). Only `packets/<id>/manifest.json` is committed. Update §5 to match.

---

## 2. 🟠 Major flaws: wrong results or wasted weeks

### M1. Scope order: the Acme fixes arrive last (M9)
The mission names three concrete problems in the Acme explainer. Most of the measurable ones need **no corpus and no Claude annotation**: −20.9 LUFS against an absolute target, SFX at offset 0 instead of on reveals, dead holds, uniform pacing, caption chunking and cuts on beat. Yet `lens compare` is M9, after about 6+ weeks including the full corpus.
**Fix:** add **M4.5, "Baseline audit"**: run S1–S4 plus the rhythm and audio metrics on Acme v1 against **absolute targets** from config, without percentiles. Output a fix list. This gives real value within days, proves the measurement on real footage early, and the corpus percentiles in M9 just make the targets sharper.

### M2. The SFX candidate filter throws away on-beat SFX
§7.1 keeps onsets that are "off the beat grid (±40 ms)". Premium videos *deliberately* put whooshes and hits on the beat, so this removes exactly the good examples. It also biases `sfx_density`.
**Fix:** keep every transient onset whose features fit an SFX (broadband, short attack, low harmonicity), and record `on_beat: bool` as a **feature**, not a filter. Add a fixture with an SFX that lands on a beat.

### M3. Caption metrics can't be measured from 2 fps frames
The "choppy 2–3 word caption chunks" metric needs group-change timing. At 2 fps the resolution is 500 ms, while the chunks being judged change every ~0.6–1 s. That is too coarse to measure change rate or word sync (±2 frames).
**Fix:** compute a cheap native-fps change signal on the bottom caption band (pixel diff or edge diff), and run OCR only on frames where the band changes. Word sync = band change aligned to word timestamps within ±2 frames.

### M4. Filmstrip frames are too small to read
15 frames tiled into a ~1500 px long edge works out to about **300×170 px per frame**. Claude also downsizes big images (roughly 1.15 MP / ~1568 px long edge **[verify]**). UI text and small elements can't be read at that size, and A2 depends on reading them.
**Fixes:**
- **Crop the filmstrip to the event's `bbox_union` plus a margin** (with a thumbnail of the full frame for context). This is the biggest legibility gain.
- Use 6–8 frames, not 10–15, picked at progress milestones (0, 10, 25, 50, 75, 90, 100% of the motion-energy integral) rather than evenly spaced in time.
- Start the M6 image-budget ADR from this default.

### M5. Set-of-marks gets cluttered on dense UI
Word-level OCR boxes plus diff components plus `bbox_union` can easily mean 40+ numbered boxes on a dashboard frame. Overlapping labels lower box-ID accuracy.
**Fix:**
- Default to line-level OCR boxes, and only those that intersect the diff mask.
- Apply NMS/merge, and cap at about 20 boxes, ranked by overlap with the diff mask.
- Place labels outside the boxes using leader lines.
- Track box-ID accuracy at G2.

### M6. The annotation PR path conflicts with the DAG rule
§7.4 has subagents write `videos/<id>/events/<eid>.a2.json`. §5 lists `events/<eid>.json`. S8 then writes `videos/<id>/record.json` into the same tree. That is fine in itself, but the names have to be fixed in the stage registry. And `signals.json` is committed per video (§10.1). Per-frame energy curves for 5-minute 60 fps videos come to MBs per video, which bloats git over 500 videos.
**Fix:**
- Commit only compact summaries: `signals.summary.json`. Full curves go to R2.
- Standardise on `events/<eid>.a2.json` everywhere.

### M7. The quota estimate is optimistic, and there is no triage
50 videos × 15–30 A2 tasks × 4 images is about **750–1,500 subagent tasks and 3,000–6,000 images**, on top of the A1 tasks. Max-plan usage limits, including any weekly caps **[verify]**, are shared with daytime building.
**Fixes (cheap, large savings):**
- **Event triage in code before A2:**
  - merge micro-events;
  - skip events with low energy or tiny area;
  - **dedupe repeated events**: a stagger of 6 identical cards is 1 task, not 6. Use perceptual hash plus a similar motion profile.
- Run A2 only on `reference` tier videos, plus `own` for compare. For `average` videos, A1 alone is enough to calibrate scores.
- `lens status --plan` prints an estimated task and image count **and** the measured average cost per task from earlier runs (logged in `runs/`).

### M8. "Sanity values" for Acme v1 need defined tolerances and definitions
"15 scenes, 14 transitions": HyperFrames crossfades or morphs may not register as cuts, and "peak −3.2 dBFS" is sample peak, not true peak. Without tolerances, M9's acceptance can't be decided.
**Fix:** define it in config. Example: duration ±0.1 s, integrated loudness ±0.5 LU, transitions detected ≥ 13/14 within ±2 frames, and "SFX at scene start" means |offset to the scene start| ≤ 2 frames for ≥ 80% of cues. Report sample peak and true peak separately. The plan's rule ("if `lens compare` doesn't reproduce these, the tool is wrong") then becomes testable.

### M9. The gold-score gate can't block CI automatically
§11.2 says CI blocks skill changes if the gold score drops, but the eval runs only on manual dispatch. As written, nothing blocks.
**Fix:** use a required CI check that compares the hash of `.claude/skills/**` plus `taxonomy/**` against the latest `runs/eval/<hash>.json`. If there is no eval for the current hash, the check fails with "run eval dispatch". That costs no quota and still blocks.

### M10. Container size and GHCR storage [verified: GHCR container storage is currently free; runner disk is 14 GB. See ADR 0003]
Baking faster-whisper, CLAP and demucs weights plus torch into the image comes to **roughly 4–8 GB**. Private GHCR storage counts against the account's Packages quota, which is small on Free/Pro. Pulling it every job also costs minutes.
**Fixes:**
- Use a CPU-only torch wheel.
- Keep weights *out* of the image and cache them with `actions/cache`, keyed by model version, or pull them from R2.
- Or skip GHCR and use `uv` with an `actions/cache` for the venv, plus `apt-get install ffmpeg`. Decide in an ADR at M0 with measured sizes.

### M11. Deleting the original is irreversible for sources you can't fetch again
LinkedIn and canvas-captured sources may not be fetchable again. If S2 has a bug found later (colour range, VFR handling), those inputs are lost.
**Fix:** keep originals for `own` sources and any `refetchable: false` source. For the others, use an R2 lifecycle rule (delete originals 30 days after the proxy is verified) instead of deleting immediately.

---

## 3. 🟡 Inconsistencies and gaps (each will make Claude Code guess)

1. **Rhythm metrics' stage:** §7.1 puts dead holds, pace curve and captions in **S3**, while M4 says they belong to measurement. Pick S3, since they are deterministic signals, and fix M4's text.
2. **The §5 layout is missing directories used elsewhere:** `corpus/archetypes/`, `reports/compare/`, `exports/archetypes.json`, `.claude/hooks/`, a stage registry file (e.g. `lens/stages.py` or `config/stages.yaml`), and `renders/` (see the next item).
3. **`renders/acme-explainer-v1.mp4`** (§9) contradicts "never commit media". Use `r2://inbox/acme-explainer-v1.mp4` everywhere.
4. **§9 says "three sections"** but lists Voice, Sound, Sound (v2.1), Motion and Rhythm. Merge the two Sound entries; that leaves four sections.
5. **`lens dag --check`** is required (§2.9, Appendix A), but no milestone builds it. Add it to M0, with the stage registry as an M0 deliverable.
6. **Easing class ambiguity:** a critically damped spring and an `ease_out` cubic-bezier can fit equally well. Define model selection by AIC/BIC with a margin, and report `ambiguous` when inside the margin.
7. **Frame rate:** VFR sources and 23.976/25/29.97 rates aren't covered. "Native fps" for a VFR source needs a rule: take the mode of the frame durations and resample to CFR. Fixtures at 24 and 25 fps should be added to the 30 and 60 ones.
8. **The faster-whisper model is not specified.** Pick one, e.g. `small.en` int8 on CPU, with `medium` as an option. Run it on the **vocal stem** with VAD, to cut hallucinations over music.
9. **The demucs dependency is optional, but ducking and SFX candidates depend on it.** Either make it required, or define the degraded algorithms (e.g. ducking from a speech/no-speech VAD mask on the mix).
10. **Destination loudness targets** (LinkedIn −16 to −14 LUFS) are **not published platform targets [verify]**. Label them house targets in config, cite the sources found in M0, and accept that LinkedIn autoplays muted, which makes `works_muted` more important.
11. **Copyright of committed text:** verbatim on-screen text and transcripts of third-party videos end up in git (`a1.json`, anchors). The private repo makes that acceptable, but **exports and pattern cards should not quote third-party copy**. Add an export lint for that: no string over N words that matches the corpus's transcripts or OCR text.
12. **`claude_code_oauth_token` in Actions for unattended nightly batches:** confirm that it is supported, and check the usage-policy wording for automated subscription use at M0 **[verify]**. Keep the local-interactive fallback (already in the plan).
13. **The R2 endpoint** is `<account_id>.r2.cloudflarestorage.com`. The cloud environment's network policy has to allow that exact host (see the environment check below).

---

## 4. 🟢 Improvements (ranked by value ÷ effort)

### I1. Use the Acme v1 HyperFrames source as a **real-world ground-truth fixture** ⭐
v1 was built from code, so every scene boundary, transition type, element ease, duration, stagger and SFX timestamp is **known exactly**. Render it (or use the existing MP4) and assert that `lens` recovers them. This validates tracking, fitting, SFX offsets and dead holds on real UI-style footage. The synthetic fixtures can't do that, and it costs almost nothing. Add it to the M4 acceptance criteria.

### I2. Reorder milestones for earlier value
M0 → M1 → M2 → **M4.5 baseline audit of Acme v1 (absolute targets)** → M3 → M4 → M5 … The audit already answers "why does v1 feel cheap?" before any quota is spent.

### I3. A real SFX calibration set, not only synthetic
Collect about 100 CC0 SFX clips from freesound.org (whoosh, click, riser, impact…), and mix them over music beds at known offsets. That gives honest CLAP-plus-rules accuracy numbers at M2 and drives the ADR choosing `msclap` vs `laion_clap` on measured accuracy, not on licence alone.

### I4. Progress-based frame sampling everywhere
Pick filmstrip frames at quantiles of the cumulative motion energy, not evenly in time. Ease-out motions then get frames where the change actually happens.

### I5. A `lens preview` HTML for every packet (M3), made permanent
The M3 "packet HTML preview" should be a standing debug tool: what Claude saw, plus what it answered, side by side. That speeds up gold-set correction at G2 a lot. Robert can correct in the browser and export YAML.

### I6. Confidence-weighted corpus stats
Weight each measured value by `fit_quality` × video score × tier, and report medians with bootstrap CIs. A pattern card should say "median 420 ms (CI 380–470, n=37)", not just "420 ms".

### I7. Cost log as a first-class output
Each annotate run logs tasks, images, turns, wall time and failures to `runs/<run_id>/cost.json`. `lens status --plan` uses the rolling averages. That turns M7's "approve the nightly pacing" (G3) into a decision made on data.

### I8. Keep the schemas as the single source of truth for the factory
Publish `exports/schemas/*.schema.json` with a semver `schema_version`, and add a CI check that compares against the last released schema and fails on breaking changes without a major version bump. The factory repo can pin a version.

---

## 4b. Cross-check against `docs/handoff-v1.md`

The handoff confirms several audit items and adds new ones.

### H1. 🟠 The plan's effort doesn't match where the handoff says the gap is
The handoff ranks **voice** as the biggest gap (§5.1, §6). The plan gives voice one export (`voice-spec.json`) and spends most of its milestones on motion. That's fine *if* everyone accepts that `lens` will only *diagnose* the voice: a corpus percentile on pitch variability won't make Kokoro expressive. The real fix is a TTS choice under the "no paid APIs" constraint, which is a factory decision (D5). **Action:** add a non-goal line, "choosing or building TTS", and make `voice-spec.json` concrete enough to brief whichever TTS gets chosen: WPM range, pause-length distribution by punctuation, pitch-variability range and breath density.

### H2. 🟠 The seed reference video may be frames-only, so no motion can be measured
The handoff got the LinkedIn reference only as **about 20 canvas screenshots** (§3.1). A tainted canvas can't be read back, so there was no native-fps video and no audio. S4 bursts, S7 tracking and every audio metric need the real MP4. **Fix:**
- In M1, fetch the reference locally. Try yt-dlp first. Otherwise find the `<video>` element's `src` (usually a direct progressive MP4 from LinkedIn's CDN) in devtools and download it.
- If it stays frames-only, mark it `media: frames_only` and **exclude it from motion and audio stats**. It can still feed A1 (structure, typography, beats).

### H3. 🟠 The compare cohort has to match the format
v1 is a calm, **narrated** research explainer (light pastel, voiceover-led). The plan's example sources are dark-UI `feature_reel`s with no voiceover (Linear). Comparing v1's voice and pacing against a no-voiceover cohort gives meaningless percentiles. **Fix:**
- Make `lens compare` pick its cohort by `format` by default (`narrated_explainer` for v1).
- Only compute voice metrics against sources that have voiceover.
- Make sure G1/G3 sourcing includes at least 15 `narrated_explainer` references, not only launch reels.

### H4. 🔴 A rate-limit kill in Actions would lose the night's work
The handoff's real failure (§3.9, §5.5) was a rate limit killing a wave of subagents mid-run. In `annotate.yml`, the same event makes the `claude-code-action` step fail, so the later `lens validate --all` and commit steps are **skipped** and the valid JSON already on disk is lost with the runner. **Fix:**
- Run the validate and commit steps with `if: always()`, and commit only files that pass validation.
- Treat an exhausted limit as an expected outcome, not an error: the summary says "stopped: usage limit".
- Have subagents append to `runs/<run_id>/progress.jsonl` as they go. That fixes the handoff's "progress was invisible until completion" (§5.14).

### H5. ✅ The v1 project is a full answer key (makes I1 concrete)
From §3 and §8 of the handoff, the uploaded v1 text files give:

| Lens metric | Ground truth in v1 files |
|---|---|
| Scene bounds, 15 scenes | `data-start` / `data-duration` in `index.html` |
| 14 transitions and their types (crossfade, push-slide left, zoom-through) | `transitions.mjs` output in `index.html` |
| Element eases, durations, staggers | GSAP `fromTo` calls in `compositions/frames/*.html` |
| SFX times (all at scene start, offset 0) | SFX track entries in `index.html` / `audio_meta.json` |
| Ducking (7 EQ dips plus a level envelope) | carve output in `index.html` |
| Caption groups (2–3 words) | `caption_groups.json` |
| Word timings, WPM (~3.0 words/s ≈ 180 WPM) | `audio_meta.json` |
| Dead holds (frames 7, 13, 14 triptychs) | handoff §6, plus scene timelines |
| 30 fps, 4338 frames, 144.6 s | handoff §1, §3.11 |

This upgrades M8's tolerances from guesses to per-metric checks against known values. Note that crossfades and zoom-throughs won't show up as hard cuts, which confirms M8: S3 needs gradual-transition detection, or "14 transitions" will fail.

### H6. 🟡 Handoff lessons the plan should state explicitly
- **The loudness target is "typical", not published** (handoff §5.9 says "-16 to -14 is typical"). Treat it as a house target (matches §3 item 10).
- **"Peak -3.2 dBFS" is a sample peak** measured by ffmpeg, so compare the sample peak, not the true peak (matches M8).
- **Judge motion in motion** (§5.12, rec 6): `lens compare` on low-res per-scene preview clips should be a supported, fast path (under 1 min per scene, no Claude), because that is how the factory will use it in its motion-review loop. Add a `--fast` mode: S1–S3 plus rhythm and sound metrics only.
- **The case-insensitive collision was real** (`Acme` vs `Acme` wav files, §5.14). Beyond lowercase slugs, `lens dag --check` should fail on any two declared outputs that collide case-insensitively.
- **Archetype names map to v1 blueprints** (§3.5: kinetic-type-beats, grid-card-assemble, dataviz-countup, titlecard-reveal, comparison-split, …). Seed `taxonomy.patterns` with aliases to those blueprint IDs, so the catalog speaks the factory's vocabulary from day one.

---

## 5. Cloud environment check (this session)

| Need (plan §15.5) | Status here |
|---|---|
| Python | 3.11.15 installed; `uv` present (it can install 3.12) |
| ffmpeg | 6.1.1 ✅ |
| Node (for the Remotion/GSAP golden tests) | v22 ✅ |
| pypi.org / huggingface.co / registry.npmjs.org | reachable ✅ |
| github.com / ghcr.io | reachable (redirect / 400 on bare root = OK) |
| R2 endpoint | untested: needs `<account_id>.r2.cloudflarestorage.com` allowed in the environment's network policy |
| CPU / RAM | 4 vCPU, 15 GB: fine for whisper `small`; demucs works but is slow |

---

## 6. Proposed next step

Once D1, D3, D4 and D5 are answered, I'll fold the accepted fixes into **BUILD_PLAN v2.2**: B1–B4, M1–M11, H1–H6 and the §3 items, with I1, I2 and I7 as additions. Then I'll start M0.
