# BUILD_PLAN.md: `explainer-video-creator` (v2.2, Claude Code native, research → understand → create)

**Owner:** Robert Vîja (Acme.ai / difrnt.)
**Builder and annotator:** Claude Code. It builds this repo, and it also performs the visual annotation, running on Robert's Claude subscription.
**Scope (v2.2):** one repo that **researches** (builds the corpus), **understands** (measures and names patterns: the `lens` CLI) and later **creates** videos (the `create` phase, which consumes `lens` exports). Phase 1 (this plan, M0–M10) is `lens`. Phase 2 (Create) is outlined in section 12b and planned in detail at gate G5.
**Use:** internal only. Robert accepts that annotation shares his Claude plan's usage limits.
**Constraint (v2):** no pay-per-use APIs. **One exception (v2.2):** ElevenLabs on a fixed monthly subscription, with Pay As You Go / Auto Top Up left off (usage then simply pauses when credits run out), for voice in Phase 2. Robert uses the ElevenLabs MCP for interactive voice work. The pipeline's voice stage calls the REST API, because neither ElevenLabs MCP returns timestamps (see section 12b and `docs/external-facts.md` §10).
- All visual understanding is done by Claude Code reading prepared images.
- All audio analysis is done by free local tools and models.
- Infrastructure stays on free tiers: GitHub Actions minutes and Cloudflare R2's free tier.
**Status:** v2.2 plan, October 2026. Replaces v2.1 (`docs/plan-audit.md` lists every change and why) and the Gemini-based v1 plan.

**v2.2 changes** (from `docs/plan-audit.md`):
- One repo for research, understanding and creation. `lens` is Phase 1; `create` is Phase 2.
- ElevenLabs (subscription, via MCP) is the voice for Phase 2. `voice-spec.json` is shaped to brief it.
- Fixes to mechanisms that would not work as written: workflow chaining (one nightly workflow with reusable jobs), write limits enforced by a `PreToolUse` hook instead of per-subagent paths, the spring fit reparameterised (ζ, ω₀), and packet storage made consistent.
- Measurement fixes: SFX candidates keep on-beat hits, caption timing at native fps on the caption band, gradual-transition detection, filmstrips cropped to the event with 6–8 frames, set-of-marks capped.
- Earlier value: **M4.5 Baseline audit** of Acme v1 against absolute targets, before any annotation quota is spent.
- The Acme v1 HyperFrames project becomes a ground-truth fixture when its text files are uploaded.
- Annotate runs survive usage-limit kills, with code-side event triage to save quota.

**v2.1 changes** come from `HANDOFF.md`, the field notes from building Acme explainer MVP v1, now at `docs/handoff-v1.md`. It matters in four ways:

1. **v1 was built with HyperFrames** (HTML + GSAP, Apache-2.0), not Remotion. So every motion output must be **renderer-agnostic**: a cubic-bezier, the nearest GSAP ease, a fitted spring, and a Remotion spring config.
2. **v1's measured weaknesses become compare metrics:**
   - dead holds on empty placeholders;
   - uniform pacing;
   - choppy 2–3 word caption chunks;
   - SFX placed at scene start (offset 0) instead of on reveals;
   - no beat alignment;
   - −20.9 LUFS against a −16 to −14 target for social feeds;
   - motion judged only from stills.
3. **The pattern catalog must also be grouped into scene archetypes** (handoff recommendation 3), so the future factory fills archetypes instead of hand-building every scene.
4. **Pipeline hygiene lessons apply here too:** a strict DAG, declared writes, artifact-on-disk completion, resumable jobs, case-insensitive-safe file names.

---

## 0. How to use this document (Claude Code, read first)

1. Read this whole file before writing any code.
2. Create `CLAUDE.md` from **Appendix A**, `PROGRESS.md` (a milestone checklist), and `docs/decisions/` (ADRs).
3. Work **one milestone at a time** (section 12), with one branch and one PR per milestone. Prove the acceptance criteria in the PR description with commands, tests or artifacts.
4. At every **HUMAN GATE**, open a GitHub issue labelled `needs-robert` and stop.
5. Re-verify these facts against official docs before relying on them, and log URL and date in `docs/external-facts.md`:
   - `anthropics/claude-code-action` inputs: `claude_code_oauth_token`, `prompt` running skills, `claude_args` with `--allowedTools`, `--max-turns`, `--model`;
   - scheduled runs;
   - subagent support in headless runs;
   - Claude image input size guidance;
   - GitHub Actions minutes for private repos;
   - Cloudflare R2 free-tier limits;
   - the licenses and weights of the local audio models;
   - (v2.2) whether `GITHUB_TOKEN`-created events trigger workflows; subagent `tools:` scoping vs `settings.json` path rules vs `PreToolUse` hooks; GHCR private storage limits; GSAP and Remotion licences;
   - (v2.2) the ElevenLabs MCP tools, whether TTS returns timestamps through the MCP, the with-timestamps API, v3 audio tags, pronunciation dictionaries, and whether overage can be disabled.
  - ✅ Verified on 2026-10-03; see `docs/external-facts.md`.
6. When this plan is underspecified, choose the simplest option, write an ADR, and continue. Ask only when a choice changes scope, quota usage or legal exposure.

---

## 1. Mission

Build a tool that **turns premium SaaS explainer and launch videos into measured, reusable production knowledge**, and **grades our own videos against it**.

It targets three concrete problems in the current Acme explainer:

| Problem | What the tool measures | Surfaced in |
|---|---|---|
| Voice sounds AI, flat | WPM, pause distribution, pitch variability (expressiveness), energy variability, wording tone | `voice-spec`, compare report |
| Sound is basic, "elevator music" | SFX density and types, SFX-to-motion offset, cuts on beat, ducking depth, music dynamics, loudness | `sound-spec`, compare report |
| Animations are bland | Easing class mix, fitted Remotion springs, overshoot, stagger, durations by element role, transitions, depth cues | `motion-tokens`, pattern library, compare report |

### Definition of done

1. A corpus of about 50 analyzed reference videos, scalable to 500.
2. A pattern library: named patterns, each with measured numbers, references and renderer-agnostic build recipes (HyperFrames/GSAP primary, Remotion secondary), grouped into scene archetypes.
3. Exports for Phase 2 (`create`, same repo; see `docs/handoff-v1.md` §7):
   - `motion-tokens.json`, `sound-spec.json`, `pacing.json`, `voice-spec.json`, `archetypes.json`;
   - JSON Schemas;
   - a Claude Code skill pack, `premium-explainer-patterns`.

   Motion values are renderer-agnostic, with HyperFrames/GSAP as the primary target and Remotion as the secondary.
4. `lens compare <video>`: places any video (first, the Acme v1 explainer) against the corpus and lists the top 10 fixes.

### Non-goals (Phase 1)

- Generating videos. That is Phase 2 (`create`) in this same repo, which consumes the Phase 1 exports.
- Choosing or building TTS inside `lens`. `lens` only *measures* voice; `voice-spec.json` briefs the Phase 2 voice (ElevenLabs).
- Fine-tuning models.
- Any public hosting of third-party media.
- Any pay-per-use API. The ElevenLabs subscription is a Phase 2 exception and is not used by `lens`.

---

## 2. Core principles (non-negotiable)

1. **Code measures, Claude names.**
   - Times, durations, easing, springs, colours, BPM, loudness, word timings and SFX onsets are computed by code.
   - Claude Code provides semantics: what the element is, its role, the pattern, why it works, and a rebuild hint.
   - Measured values always win. Claude's estimates are kept only as a fallback, flagged `source: "model_estimate"`.
2. **Claude never sees raw video. It reads prepared annotation packets.** Each packet holds:
   - contact sheets and filmstrips with timestamps stamped on them;
   - end frames with **numbered candidate boxes drawn on them** ("set-of-marks"), so Claude picks box IDs instead of guessing coordinates;
   - spectrogram images with numbered SFX markers;
   - a `facts.json` of measured anchors.
3. **Anchoring.** Shots, events, words and SFX candidates come from code with IDs. Claude only annotates the given IDs and never invents timestamps.
4. **The file interface is the contract.**
   - Claude writes JSON to a known path, then runs `uv run lens validate <path>` (pydantic).
   - It fixes and repeats until the output is valid.
   - A non-validating output is never committed.
5. **CLI-first; MCP is optional.**
   - Everything works through the repo's CLI and files.
   - MCP servers are used only as conveniences (section 10.5). No Phase 1 stage may depend on one, because custom MCPs may not load in cloud sessions or Actions.
   - Phase 2 voice also follows this rule: the ElevenLabs MCP is for interactive voice browsing and auditioning, and the voice **stage** calls the REST `with-timestamps` endpoint directly. The MCP returns no alignment data, and it may not load headless.
6. **Zero paid APIs; manage quota.**
   - Annotation uses the Claude subscription via `claude-code-action` with `CLAUDE_CODE_OAUTH_TOKEN`.
   - Quota is the scarce resource. Pace work in small nightly batches, keep images small, and cache everything.
7. **Reproducible.**
   - Every output carries provenance: schema and tool versions, prompt (skill) ID and hash, annotator (`claude-code`), model if known, input hash, timestamp.
   - Stages are idempotent and cached.
8. **Private by default.** Media lives in a private R2 bucket. Git holds code, configs, skills, taxonomy and compact JSON only.
9. **Strict DAG with declared writes** (lessons from the v1 handoff):
   - every stage declares its inputs and the exact paths it writes in a stage registry;
   - a stage may not write elsewhere or rewrite another stage's output;
   - `lens dag --check` verifies this in CI;
   - downstream stages refuse to run on stale upstream hashes;
   - completion is signalled only by validated artifacts on disk, never by an agent saying it is done;
   - file names are lowercase slugs, to avoid collisions on case-insensitive file systems; `lens dag --check` also fails if two declared outputs collide case-insensitively;
   - write limits are **enforced**, not trusted: a `PreToolUse` hook (`.claude/hooks/guard_paths.py`) allows Claude's `Write`/`Edit` only on the paths the stage registry declares for the active task.
10. **Verifiable.**
   - Measurement is tested on synthetic videos with known answers.
   - Annotation quality is evaluated against a gold set Robert corrects.
   - A skill change must not lower gold scores.

---

## 3. Architecture

```
sources.yaml ─► S1 ingest ─► S2 normalize + base frames (2 fps) + palette
                                   │
                                   ▼
            S3 deterministic signals: cuts → shots, motion energy → events,
               camera flow; AUDIO (local): stems, words, prosody, beats,
               onsets → SFX candidates + local CLAP labels, ducking, loudness
                                   │
                                   ▼
            S4 bursts (native fps) + filmstrips + candidate boxes (diff
               contours + OCR) + set-of-marks end frames + spectrograms
                                   │
                                   ▼
            S5 PACKETS  (packets/<video>/pass1/, packets/<video>/events/<eid>/)
                                   │          ── GitHub Actions (free) above ──
                                   ▼
            A1/A2 CLAUDE CODE ANNOTATION (claude-code-action, subscription)
               A1 video-annotator subagent: structure, beats, scores
               A2 event-annotator subagents: elements (by box id), pattern
               → writes JSON → `lens validate` → fix until valid
                                   │          ── GitHub Actions (free) below ──
                                   ▼
            S7 measurement (track chosen boxes, fit bezier/spring, opacity,
               text stagger, SFX offset)  →  S8 reconcile → record.json
                                   ▼
            S9 synthesis (stats, clustering)  →  A3 Claude writes pattern cards
                                   ▼                         ⛔ GATE G4
            S10 exports (tokens, specs, schemas, skill pack)
                                   ▼
            S11 compare (any video vs corpus)  →  A4 Claude writes fix list
```

The deterministic stages (S1–S5, S7–S10) run in normal GitHub Actions jobs. The annotation stages (A1–A4) run as Claude Code in Actions via `claude-code-action`. The same commands also work locally, in an interactive Claude Code session on Robert's machine.

---

## 4. Tech stack

| Concern | Choice | Notes |
|---|---|---|
| Language/tooling | Python 3.12 + `uv`, `typer` CLI (`lens`) | |
| Schemas | `pydantic` v2 → JSON Schema export | Also used by `lens validate` |
| Video/CV | `ffmpeg`, `opencv-python-headless`, `numpy`, `scipy` | Own cut/transition detector instead of PySceneDetect (ADR 0007) |
| OCR (text boxes) | `rapidocr` 3.x (local, free, Apache-2.0; `rapidocr-onnxruntime` is frozen at 1.4.4) | Text candidate boxes for set-of-marks; spike plus ADR |
| Colour | k-means palette in code | Hex values come from code, not from Claude |
| Audio | `librosa`, `pyloudnorm`, `faster-whisper` (word timestamps), `demucs` (optional stems) | All local |
| Audio labels | **Local CLAP zero-shot** (`laion_clap` or Microsoft `msclap`, ADR after a license and weights check) plus acoustic-feature rules | Labels SFX (whoosh, click, riser, impact…) and music mood/genre. No API |
| Annotation | **Claude Code** via `anthropics/claude-code-action@v1` (Actions) or a local interactive session | Auth: `CLAUDE_CODE_OAUTH_TOKEN` from `claude setup-token` |
| Agent assets | `.claude/skills/*`, `.claude/agents/*` (subagents with restricted tools) | Versioned; hashes go into provenance |
| Text clustering | `sentence-transformers` (small local model) | For merging pattern names; free |
| Corpus queries | `duckdb` over JSON records | Rebuilt, not committed |
| Reports | `jinja2` + `matplotlib` → static HTML/MD | |
| Storage | Cloudflare R2 private bucket (free tier) via `boto3` | Keep media lean (section 6.3) |
| Orchestration | GitHub Actions (private repo) | Free minutes; verify plan limits |
| Container | Dockerfile with ffmpeg + deps + model weights, pushed to GHCR | Fast, reproducible jobs |
| Tests | `pytest`, `ruff`, `mypy` strict for `lens/measure` and `lens/schemas` | |

---

## 5. Repository layout

```
explainer-video-creator/
├─ BUILD_PLAN.md  CLAUDE.md  PROGRESS.md  README.md
├─ pyproject.toml  uv.lock  Dockerfile  Makefile
├─ .claude/
│  ├─ skills/
│  │  ├─ annotate-batch/SKILL.md      # orchestrator: pick pending videos, dispatch subagents, validate
│  │  ├─ annotate-video/SKILL.md      # A1 instructions (Appendix B.1)
│  │  ├─ annotate-event/SKILL.md      # A2 instructions (Appendix B.2)
│  │  ├─ write-pattern-cards/SKILL.md # A3 (Appendix B.3)
│  │  └─ compare-fixes/SKILL.md       # A4 (Appendix B.4)
│  ├─ agents/
│  │  ├─ video-annotator.md           # tools: Read, Write, Bash (tool names only; paths enforced by the hook)
│  │  ├─ event-annotator.md           # same restricted tools
│  │  └─ annotation-reviewer.md       # fresh-context spot checker
│  ├─ hooks/guard_paths.py            # PreToolUse: allow writes only to the active task's declared paths
│  └─ settings.json                   # permissions allowlist + hook registration
├─ config/lens.yaml                   # fps, thresholds, image sizes, batch sizes, quotas
├─ sources/sources.yaml  sources/README.md
├─ taxonomy/v1.yaml  taxonomy/proposals.yaml
├─ lens/
│  ├─ cli.py config.py stages.py     # stages.py = stage registry (inputs, declared writes)
│  ├─ schemas/      ingest/   frames/   signals/   audio/ (incl. clap.py)
│  ├─ packets/      # builds annotation packets, set-of-marks overlays, spectrograms
│  ├─ validate/     # `lens validate`, `lens status` (what's pending)
│  ├─ measure/  reconcile/  corpus/  synth/  compare/  report/  storage/
├─ packets/<id>/manifest.json         # COMMITTED: task list, status, input hashes (text packets live in data/ + R2)
├─ videos/<id>/  meta.json signals.summary.json a1.json events/<eid>.a2.json record.json
├─ corpus/patterns/  corpus/archetypes/  corpus/stats/
├─ exports/ motion-tokens.json sound-spec.json pacing.json voice-spec.json archetypes.json schemas/ skill/
├─ reports/compare/<id>/
├─ gold/<id>/  runs/<run_id>/         # runs/ holds summary.md, progress/, cost.json
├─ create/                            # Phase 2 (empty placeholder until G5)
├─ docs/decisions/  docs/external-facts.md  docs/operating-guide.md
├─ scripts/make_fixtures.py  scripts/local_fetch.sh
├─ tests/  tests/fixtures/synth/  tests/fixtures/acme-v1/ (v1 HyperFrames text files = answer key)
├─ data/                              # GITIGNORED local mirror of R2 (media, images)
└─ .github/workflows/ ci.yml image.yml prepare.yml annotate.yml finalize.yml nightly.yml
```

Images (filmstrips, contact sheets, overlays, spectrograms), text packets (`anchors.json`, `facts.json`, `candidates.json`) and full per-frame signal curves live in `data/` and R2, never in git. Git holds only manifests and compact summaries.

---

## 6. Sources and ingestion (S1–S2)

### 6.1 `sources/sources.yaml`

```yaml
- id: linear-initiatives-2025
  url: https://...            # https mp4 | r2://inbox/<file> | file://...
  brand: Linear
  title: "Initiatives"
  format: feature_reel        # taxonomy.format
  tier: reference             # reference | average | own | competitor
  why: "dark UI hero, minimal VO, great stagger"
  tags: [dark-ui, no-vo]
  segment: null               # optional {start, end}
  media: full                 # full | frames_only | audio_only
  refetchable: true           # false → original is never deleted
```

- **Seed entries:**
  - the LinkedIn research explainer v1 was modelled on (`tier: reference`, `format: narrated_explainer`; its page also exposes a transcript, so store it as `transcript_hint`). v1 only captured ~20 canvas screenshots of it, so **M1 must fetch the real MP4 locally** (yt-dlp, or the `<video>` element's direct `src` from devtools). If only frames are possible, mark it `media: frames_only`; it then feeds A1 but is excluded from motion and audio stats;
  - the Acme v1 render, `acme-explainer-v1.mp4` (`tier: own`).
- About 10 `average` videos are included to calibrate scores.
- At least 15 `narrated_explainer` references (v1's own format), not only launch reels, so that `lens compare` has a like-for-like cohort.
- `own` (Acme renders) videos are compared, but never used to derive tokens.

### 6.2 Fetchers

- In the cloud: direct `https://…mp4` and `r2://inbox/`.
- YouTube, X and LinkedIn are **local-only**, via `scripts/local_fetch.sh` (yt-dlp), which uploads to `r2://inbox/`.
  - If yt-dlp fails on LinkedIn, document the fallback from the handoff: seek the page's `<video>` element and draw it onto a canvas for frame capture. That gives frames only, no audio. Mark such sources `audio: none`, and the audio metrics become `null`. Cloud IPs get bot-blocked, and there are terms-of-service considerations; record this in an ADR.

### 6.3 Normalize (lean, to fit the R2 free tier)

1. `ffprobe` → `meta.json`; sha256 plus perceptual-hash dedup.
2. Make a proxy: H.264, constant frame rate at **native fps**, max 1280 px wide. For VFR sources, "native fps" is the mode of the frame durations. Originals are not deleted immediately: an R2 lifecycle rule removes them 30 days after the proxy is verified, and never for `tier: own` or `refetchable: false`.
3. `audio.wav` at 48 kHz.
4. Base frames at 2 fps: JPEG quality around 80, 960 px wide, with timestamped names.
5. Palette: k-means on the base frames, giving the top 6 hex values per shot and per video.
6. Cap analysis at 5 min per video (or use `segment`).

---

## 7. Stages

### 7.1 S3 — Deterministic signals

- **Cuts and shots:** an AdaptiveDetector-style frame-diff spike test for hard cuts (own implementation, ADR 0007), **plus gradual-transition detection** (crossfade, push-slide, zoom-through: sustained frame-diff plateaus with a dissolve or global-motion signature). Shots carry IDs, frame-accurate bounds and `transition_in` with type and duration.
- **Motion events:**
  - compute a per-frame mean absolute difference (320 px grayscale, light blur) and smooth it;
  - apply an adaptive threshold, merge gaps of 3 frames or fewer, and drop runs shorter than 2 frames;
  - classify each event as `cut`, `motion`, `camera` or `continuous`;
  - record `bbox_union` from the diff-mask contours.
- **Camera:** Farnebäck flow → median translation and divergence → pan/zoom.
- **Audio (local only):**
  - stems via demucs `htdemucs`, two stems (**required** for ducking and SFX; if it fails, fall back to a VAD speech mask on the mix and mark the dependent metrics low-confidence);
  - word timestamps via faster-whisper (`small.en` int8 on CPU by default, `medium` in config), run on the **vocal stem** with VAD to cut hallucinations over music;
  - prosody:
    - WPM overall and per shot;
    - pause stats;
    - pitch variability in semitones (std via `librosa.pyin`);
    - energy variability;
    - speaking-rate variance;
  - music: BPM, beats, dynamics in dB, and build/drop candidates;
  - cuts on beat (±2 frames);
  - ducking (accompaniment RMS during speech vs in gaps), with attack/release;
  - loudness: integrated LUFS, short-term max, LRA and true peak;
  - **SFX candidates**: spectral-flux onsets on the accompaniment with SFX-like features (short attack, broadband, low harmonicity). Being on the beat grid (±40 ms) is recorded as an `on_beat` **feature, not a filter**, because premium videos deliberately put hits on the beat.
- **Local SFX labelling (no API):**
  - For each candidate, take a 0.6 s clip and score it with zero-shot CLAP against a fixed label prompt set (whoosh, reverse swoosh, click, tick, pop, riser, impact, chime, glitch, typing, music only, speech).
  - Combine with feature rules: a riser has a rising centroid and length over 0.5 s; a click is under 30 ms and broadband.
  - Store `label`, `score` and `agreement`.
- **Captions (visual):**
  - compute a native-fps change signal on the caption band (bottom 25%), and OCR only the frames where the band changes (2 fps is too coarse for 0.6–1 s caption groups);
  - measure words per caption group, group duration and change rate;
  - record whether captions are word-synced (group changes aligned to word timestamps).
- **Pace shape:**
  - per-shot motion energy, information density (OCR word count plus count of changed regions) and VO rate, giving a "pace curve";
  - store its variance and peaks, so a uniform pace is detectable.
- **Dead holds:** intervals of 0.8 s or more after a cut, or within a shot, where motion energy is near zero **and** the focal region is empty or unchanged (low edge density inside the event bbox), for example a placeholder waiting for its content.
- **Music mood/genre:** CLAP zero-shot on 10 s windows. Results are stored as probabilities.
- **What we deliberately do not claim:** the "emotion" in the voice. We report measurable prosody (expressiveness) and, from A1, Claude's judgement of the *wording's* tone. Perceived vocal emotion stays `null` in v1.

### 7.2 S4 — Visual evidence

- **Bursts:** frames at native fps from `start − 0.3 s` to `end + 0.3 s` for each `motion`, `camera` or `cut` event. These are used for measurement.
- **Filmstrip:** 6–8 burst frames **cropped to the event's `bbox_union` plus a margin**, chosen at quantiles of cumulative motion energy (0, 10, 25, 50, 75, 90, 100%) rather than evenly in time, each stamped with its timestamp, plus a small full-frame context thumbnail. Long edge ≤ the configured maximum (about 1500 px; verify Claude's current image guidance). Uncropped 15-frame strips give ~300×170 px per frame, which is too small for UI text.
- **Candidate boxes:**
  - connected components of the event diff mask on the settled end frame (merged and filtered by size);
  - plus OCR text boxes (**line level** by default, and only boxes that intersect the diff mask);
  - plus the `bbox_union`;
  - merged with NMS and capped at ~20 boxes, ranked by overlap with the diff mask;
  - each box gets an ID, and its coordinates go in `candidates.json`.
- **Set-of-marks end frame:** the end frame with the numbered boxes drawn as thin outlines, labels placed outside the boxes with leader lines. Make a second clean copy without marks.
- **Spectrogram image:** mel spectrogram of ±0.6 s around the event, with SFX candidates marked as `S1`, `S2`… and their CLAP labels printed. It is evidence for Claude, not the source of truth.
- **Contact sheets (Pass 1):** per shot, base frames (2 fps) tiled with timestamps and a header showing the shot ID, plus one higher-resolution mid-shot keyframe for reading typography and text. Long shots are split across several sheets.

### 7.3 S5 — Annotation packets

```
data/packets/<id>/pass1/  anchors.json  sheets/shot_<sid>_<n>.jpg  keyframes/shot_<sid>.jpg   # data/ = gitignored, synced to R2
data/packets/<id>/events/<eid>/  filmstrip.jpg  end_marked.jpg  end_clean.jpg  spectrogram.jpg
                                  facts.json  candidates.json
packets/<id>/manifest.json        # the only committed packet file: tasks, status, input hashes
```

- `anchors.json` contains the shots (IDs and times), the transcript with word indices and times, BPM and beats, loudness, the palette, and the event count per shot.
- `facts.json` contains the energy curve, the camera summary, SFX candidates (time, CLAP label and score), nearby words, and the shot ID.
- Packet size budgets, enforced in code:
  - at most N images per Pass 1 task (configurable, for example 12 sheets);
  - exactly 4 images per event task;
  - long videos are split into multiple Pass 1 tasks by shot range.
- **Event triage before A2 (in code, saves quota):** merge micro-events; skip events below the energy and area thresholds; **dedupe repeated events** (for example, a stagger of 6 identical cards is 1 task, matched by perceptual hash plus a similar motion profile, with the result propagated to the siblings). A2 runs only for `reference` and `own` tiers. `average` videos get A1 only.

### 7.4 A1/A2 — Claude Code annotation

**Runtime:** the `annotate.yml` workflow (section 10).

1. It downloads the pending packets from R2.
2. It runs `claude-code-action` with `prompt: "/annotate-batch"`, `claude_args` set to `--max-turns <cfg>` plus an allowlist, and `claude_code_oauth_token`.
3. Then `lens validate --all` and `lens status` run **with `if: always()`**. A usage-limit kill of the Claude step is an expected outcome, and it must not discard the valid JSON already on disk.
4. Only files that validate are committed to a branch, and a PR is opened or updated.

**Orchestrator skill `annotate-batch`:**

1. Run `uv run lens status --pending --limit <videos_per_run>` to get the work list.
2. For each video: dispatch `video-annotator` (A1) per Pass 1 task, then dispatch `event-annotator` (A2) subagents in groups of about 5 events. Each subagent gets a fresh context, so images don't accumulate.
3. Each subagent:
   - reads its packet images and JSON;
   - writes `videos/<id>/a1.json` or `videos/<id>/events/<eid>.a2.json`;
   - runs `uv run lens validate <file>`, and if it fails, fixes and retries (max 3).
4. Each subagent writes `runs/<run_id>/progress/<a1|a2>-<task>.json` as it finishes a task (one file per task, so no two stages share a write path), so progress is visible during the run and survives a kill. The orchestrator writes `runs/<run_id>/summary.md` (done, failed with reasons, remaining, and "stopped: usage limit" when that applies) and `runs/<run_id>/cost.json` (tasks, images, turns, wall time).
5. It stops cleanly at the turn or batch budget. The work is resumable, because `lens status` derives everything from files.

**Subagent tool restrictions:**
- Agent frontmatter `tools:` limits subagents to `Read`, `Write` and `Bash`.
- Write paths are enforced by the `PreToolUse` hook against the stage registry. Each skill has its own write allowlist: A1/A2 → `videos/**` and their own `runs/<run_id>/progress/<a1|a2>-<task>.json`; A3 → `corpus/patterns/**` and `corpus/archetypes/**`; A4 → `reports/compare/**`.
- `settings.json` allows `Read` on `data/packets/**`, `taxonomy/**` and `.claude/skills/**`, and `Bash` only for `uv run lens validate*` and `uv run lens status*`. Path rules must use `Edit(...)`, because `Write(path)` rules are accepted but never checked.
- The hook is registered in project `settings.json`, which also runs it for subagent tool calls. Hooks in subagent frontmatter are not used, because they need a trusted folder on CI.
- The `annotate-batch` skill lists its tools in `allowed-tools` frontmatter. Scheduled runs need the cron last edited by a human, or the bot listed in `allowed_bots`.

No network, no git and no other shell. The orchestrator handles git through the workflow, not through Claude.

**A1 output (`a1.json`)**, per shot ID:
- `shot_type`, composition, focal element, `transition_in`;
- on-screen text verbatim and its word count;
- typography observations;
- depth cues;
- `what_happens`;
- `build_rebuild`;
- confidence.

Per video:
- script beats mapped to shot IDs; hook text and technique; CTA;
- tone of the wording;
- `signature_moments` (max 3);
- scores 1–5 with evidence for hook, clarity, ui_showcase, motion_polish, sound_design (judged from the audio facts plus visuals, marked as such), vo_script_quality, brand_consistency, works_muted and overall;
- `localization_friendliness`.

**A2 output (`<eid>.a2.json`):**
- elements, each referencing a **candidate box ID** (or `manual_box` with coordinates and `reason`, if no candidate fits), with:
  - label, role and change types (taxonomy);
  - text and text unit;
  - fallback estimates;
- the SFX candidate review:
  - confirm or override the CLAP label from the spectrogram and visual context;
  - or `unsure`;
- the pattern: canonical ID or `other` + `proposed_name`, a description, and `why_premium`;
- `build_hint`;
- confidence and notes.

### 7.5 S7 — Measurement (precision layer)

For each element box chosen in A2:

1. **Tracking:** template-match the end-frame crop backwards through the burst with a multi-scale NCC search; use CSRT as the alternative. Record `method` and per-frame confidence.
2. **Opacity proxy:** fit alpha against a pre-event background where the box region is static; clamp to 0–1.
3. **Progress curves:** for x, y, scale and opacity, find `start_f` and `end_f` (end = within 2% of final).
4. **Fitting:**
   - `linear`;
   - CSS `cubic-bezier` (bounded least squares), classified as `ease_in`, `ease_out` or `ease_in_out`;
   - a damped-spring model, fitted **renderer-agnostically**, and exported in three forms:
     - the fit is done in **(ζ damping ratio, ω₀ natural frequency)** with mass fixed at 1, because `{mass, stiffness, damping}` is over-parameterised (scaling all three together gives the same curve). It is then converted to:
     - (a) **Remotion** `{mass: 1, stiffness, damping}`. The damped-oscillator model is implemented **from first principles**, not ported from Remotion's source. Remotion is source-available and free only for individuals and companies with ≤ 3 employees (5.0 will count contractors). A golden test checks it against the `remotion` npm package (ADR 0004: the team of 3 is within the free licence; revisit at 4 people or with Remotion 5.0). Emitting a config of numbers is not use of Remotion;
     - (b) the **nearest GSAP ease** from the built-in set (power1–4, expo, circ, sine, back with its overshoot parameter, elastic), with its RMSE;
     - (c) a `cubic-bezier` usable by GSAP `CustomEase` and by CSS.

   Model selection between bezier and spring uses AIC/BIC with a margin. Inside the margin, `class` is `ambiguous` (for example, a critically damped spring vs `ease_out`). Record `class`, all of these parameter forms, RMSE, `overshoot_pct`, `duration_ms` and `fit_quality`. Spring clusters (section 8) are built on `(ζ, settle_duration)`. The primary consumer is HyperFrames/GSAP. A golden test verifies the GSAP ease curves against values sampled from GSAP in Node.
5. **Text:** OCR word boxes inside the element → per-word reveal frames → unit and `stagger_ms`.
6. **Stagger groups:** elements of the same role entering in sequence.
7. **SFX sync:** `sfx_offset_ms = onset − visual landing frame`, where a negative value means the sound leads.

Measured values carry `source: "measured"`, `method` and `quality`. Below the quality threshold, fall back to A2 estimates with `source: "model_estimate"`.

### 7.6 S8 — Reconcile

Merge everything into `videos/<id>/record.json` with a per-field `source`. Run consistency checks: IDs exist, events fall inside shots, every SFX candidate has a final label.

---

## 8. Synthesis (S9, A3) and exports (S10)

1. **Stats in DuckDB**, weighted toward high-scoring reference videos (the rule lives in config):
   - durations by role and change type;
   - easing mix and spring clusters;
   - overshoot and stagger;
   - SFX types, density and offset;
   - ducking, LUFS, WPM, pitch variability;
   - shot length by format;
   - cuts on beat;
   - time to first UI.
2. **Pattern clustering:** canonical IDs first. For `other`, embed `proposed_name + description` with a local sentence-transformer and cluster. Proposals go to `taxonomy/proposals.yaml`.
3. **A3 pattern cards:** the `write-pattern-cards` skill, run through Claude Code, gets each pattern's stats and member descriptions and writes `corpus/patterns/<pid>.md` and `.json`. It uses only the provided numbers.
4. ⛔ **G4:** a PR with the catalog and proposals, for Robert to approve, rename or merge.
5. **Archetypes:** group the approved patterns into **scene archetypes** for explainers. Seed list (from handoff §7.3):
   - question relay
   - shortlist card
   - stat count-up
   - title with step rail
   - comparison split
   - document highlight
   - bars plus ring
   - cards triptych
   - tile grid
   - logo close

   Each archetype records its parameters, the patterns it uses, the measured timing, the SFX cue map with offsets, and reference examples. The A3 skill writes `corpus/archetypes/<aid>.md` and `.json`; Robert reviews them at G4.
6. **Exports:**
   - `motion-tokens.json`, `sound-spec.json`, `pacing.json`, `voice-spec.json`, `archetypes.json`;
   - `schemas/*.schema.json`;
   - `skill/premium-explainer-patterns/` (SKILL.md plus pattern references).

   Exports contain no third-party media.

---

## 9. Compare / QA (S11, A4)

`lens compare --video <path|id> [--against tier=reference,format=...] [--fast] [--targets-only]`

- The cohort defaults to the target's own `format` (Acme v1 → `narrated_explainer`). Voice metrics are computed only against sources that have VO.
- `--targets-only` places the video against absolute targets from config, with no corpus. This is the M4.5 mode.
- `--fast` runs S1–S3 plus the rhythm and sound metrics only, with no Claude and under a minute per scene clip. It is meant for Phase 2's motion-preview review loop.

1. Runs S1–S8 on the target.
2. Computes percentile placements in four sections:
   - **Voice:** WPM, pitch variability, pause variety, wording tone.
   - **Sound:** SFX density/types/offset, cuts on beat, ducking, music dynamics, LUFS, sample peak and true peak; SFX offset relative to the nearest reveal, flagging cues that sit at scene start with offset 0; loudness vs a **destination house target** (config: `linkedin` −16 to −14 LUFS, `youtube` about −14; these are commonly cited, not published platform specs, see `docs/external-facts.md`).
   - **Motion:** easing mix (flag linear), overshoot, stagger, duration fit per role, transitions, depth cues, time to first UI, shot length.
   - **Rhythm (added in v2.1):** dead-hold seconds and count, pace-curve variance (flag uniform pacing), caption words per group and change rate.

   This is the "judge motion in motion" check the v1 handoff lacked. It runs on the actual rendered MP4, not on stills, and can also run on low-resolution per-scene preview clips.
3. Runs the A4 `compare-fixes` skill: the top 10 fixes with evidence, a timestamp, a pattern/token reference and effort.
4. Writes `reports/compare/<id>/<date>.html` and `.md`.

The baseline is the Acme v1 explainer, `r2://inbox/acme-explainer-v1.mp4` (1920×1080, 30 fps, 4338 frames). Its known values from the handoff are sanity checks for the tool, with tolerances in `config/lens.yaml`:
- integrated loudness −20.9 LUFS (±0.5 LU); sample peak −3.2 dBFS (±0.3 dB; the handoff value is a sample peak, not a true peak);
- duration 144.6 s (±0.1 s);
- 15 scenes and 14 transitions (crossfade, push-slide left, zoom-through): ≥ 13/14 detected within ±2 frames, with the type correct;
- SFX at scene starts: ≥ 80% of cues within 2 frames of a scene start;
- WPM about 180 (Kokoro at ~3.0 words/s), ±10%;
- dead holds detected in the triptych scenes (frames 7, 13, 14).

If `lens compare` does not reproduce these, the tool is wrong. When the v1 HyperFrames text files are in `tests/fixtures/acme-v1/`, the exact values come from them instead (scene bounds and transitions from `index.html`, eases from `compositions/frames/*.html`, SFX and words from `audio_meta.json`, captions from `caption_groups.json`).

---

## 10. Running in the cloud

### 10.1 Workflows

- **`ci.yml`** on PRs: ruff, mypy, pytest; regenerate fixtures and run the measurement tests; schema export; `lens validate` on all committed JSON.
- **`image.yml`:** build the GHCR image (ffmpeg and Python deps with CPU-only torch). GHCR storage is currently free, so weights *may* be baked in, provided their licences allow redistribution: ship the MS-PL text if `msclap` is used, and confirm the htdemucs weights licence first. Private runners have **2 vCPU, 8 GB RAM and a 14 GB disk**, so keep the image well under about 6 GB, or cache weights with `actions/cache` (10 GB per repo). ADR 0003.
- **`prepare.yml`** (dispatch, or on a push to `sources.yaml`):
  - runs S1–S5 for new videos in a matrix (`max-parallel` from config) inside the image;
  - syncs media and packets to R2;
  - commits `packets/<id>/manifest.json` and `signals.summary.json` (compact; full curves go to R2) through a PR, or a bot commit to a `data` branch (ADR).
- **`annotate.yml`** (dispatch + nightly cron):
  1. checkout;
  2. pull the pending packets from R2;
  3. `anthropics/claude-code-action@v1` with:
     - `claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}`;
     - `prompt: "/annotate-batch"`;
     - `claude_args: --max-turns <cfg> --allowedTools <list>`;
  4. `lens validate --all` (`if: always()`);
  5. commit only the validated `videos/**` JSON plus `runs/<run_id>/` and open or update an "annotations" PR (`if: always()`).

  Use `concurrency` so only one annotate run happens at a time.
- **`finalize.yml`** (`workflow_call` + dispatch): runs S7–S8 for newly annotated videos, then S9 (stats only) and S10 if requested; opens a PR.
- **`nightly.yml`:** one workflow that calls `prepare`, `annotate` and `finalize` as **reusable workflows** (`workflow_call`) chained with `needs:`. Events created with the default `GITHUB_TOKEN` (bot pushes, bot-opened or bot-merged PRs) do not trigger other workflows, so chaining through "on merge" would silently never fire.
- All of `prepare`, `annotate` and `finalize` define `workflow_call` and `workflow_dispatch`, so they work standalone or chained.

### 10.2 Secrets

- `CLAUDE_CODE_OAUTH_TOKEN` (generated with `claude setup-token`; it lasts about a year, so put a renewal reminder in the README).
- `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`.

There are **no** Gemini, OpenAI or Anthropic API keys.

### 10.3 Quota and pacing (the "budget guard" for v2)

- Config:
  - `annotate.videos_per_run` (default 3);
  - `annotate.max_turns`;
  - `annotate.max_images_per_task`;
  - image long-edge maximum;
  - `annotate.events_per_subagent`.
- Before dispatching, `lens status --plan` prints the planned task and image counts, plus an estimate based on the rolling averages in `runs/*/cost.json`. The orchestrator refuses to start more than the configured batch.
- Annotation and building share Robert's Claude plan limits. Schedule nightly runs and keep building sessions in the daytime.
- About 50 videos at 3–5 per night is roughly 2–3 weeks unattended. Raise the batch size if quota allows.

### 10.4 Reliability

- Every stage writes a `.done` marker with its cache key, so reruns skip work.
- A usage-limit stop is a normal outcome: validated work is committed, and the next run resumes from `lens status`.
- Annotation completeness comes from files (`lens status`). Partial runs are safe.
- A failed task is retried in the next run up to 2 times, then marked `needs_review` and listed in the summary.

### 10.5 MCP (optional conveniences, never load-bearing)

- **GitHub:** issues, PRs and gate notifications. It is available in cloud sessions and Actions; the workflow itself also handles git.
- **Local only, optional:**
  - a browser/Playwright MCP to find direct MP4 URLs on product pages while curating `sources.yaml`;
  - a docs-lookup MCP while building (Remotion, librosa).
- Any MCP use goes through `--mcp-config` in local or interactive sessions. The Phase 1 pipeline must pass with no MCPs configured.
- **ElevenLabs MCP (Phase 2):** the hosted server (OAuth) for voice browsing, design and auditioning in interactive sessions. Pipeline TTS uses REST with-timestamps and `ELEVENLABS_API_KEY`.

### 10.6 Expected resources (estimates; the tool logs actuals)

- Actions: about 5–10 min of CPU per video for prepare (demucs and whisper dominate), plus the annotate runtime. Check this against the plan's private-repo minutes.
- R2: about 50–120 MB per video after the original is deleted (proxy plus images). 50 videos fit within a 10 GB free tier; verify the current limits.
- Claude subscription: about 1 A1 task and 15–30 A2 tasks per video, each with up to 4 images. **Max plan strongly recommended** for the full corpus.

---

## 11. Quality and evaluation

### 11.1 Synthetic fixtures (required before real data)

`scripts/make_fixtures.py` generates:

- a box moving with linear, easeOutCubic and a Remotion spring with overshoot (at 24, 25, 30 and 60 fps);
- a fade-in;
- a scale-pop;
- a 5-word per-word reveal with a 3-frame stagger;
- a hard cut, a known-length crossfade, a push-slide and a zoom-through;
- a dead hold (an empty placeholder card for 1.2 s before its content lands);
- burned-in captions in 2-word and 5-word groups, word-synced;
- a slow push-in;
- audio: a 120 BPM click track; a whoosh 60 ms before a visual landing; **an impact exactly on a beat**; a riser; a "voice" segment with ducked music; a mix normalised to a known LUFS.

Tests assert:
- boundaries, durations and stagger within ±1 frame;
- the correct easing class;
- a spring fit RMSE below the threshold **and** recovered (ζ, ω₀) within tolerance;
- transitions detected with the right type; dead hold found; caption group size and sync correct;
- BPM within ±1;
- SFX offset within ±1 frame;
- ducking within ±1.5 dB;
- the CLAP or rule label for whoosh, click and riser is correct; the on-beat impact is a candidate.

**Real-world fixtures (v2.2):**
- `tests/fixtures/acme-v1/`: the v1 HyperFrames text files (once uploaded) are an exact answer key for scenes, transitions, eases, SFX times, captions and word timings on real UI-style footage (section 9).
- **SFX calibration set:** about 100 CC0 clips from freesound.org (whoosh, click, riser, impact…) mixed over music beds at known offsets. It gives honest CLAP and rules accuracy at M2 and drives the choice between `msclap` and `laion_clap`.

### 11.2 Gold set (⛔ G2)

- After the pilot, export A1 and A2 for 3 videos to editable YAML in `gold/<id>/`. Robert corrects them (about 2 hours).
- `lens eval` reports:
  - enum accuracy;
  - box-ID choice accuracy;
  - pattern agreement;
  - the share of `measured` events;
  - SFX label accuracy (CLAP alone vs after Claude review);
  - a self-consistency sample (10 events re-annotated).
- CI blocks a skill or taxonomy change if the gold score drops. The eval itself runs only on a manual dispatch (cached packets, to save quota) and writes `runs/eval/<hash>.json`. A **required CI check** hashes `.claude/skills/**` plus `taxonomy/**` and fails when there is no passing eval for the current hash ("run eval dispatch"). That way it blocks without spending quota on every PR.

### 11.3 Spot review

On about 5% of events, the `annotation-reviewer` subagent re-checks with a fresh context. Disagreements go to `runs/<id>/review.md`.

---

## 12. Milestones

Each milestone has one PR with acceptance evidence. Robert may pre-authorize auto-merge for M0–M3.

**M0 — Bootstrap.**
- Skeleton, CLI, config, schemas, `CLAUDE.md`, `PROGRESS.md`, ADR template, Dockerfile, `ci.yml`, `image.yml`.
- Stage registry (`lens/stages.py`) and `lens dag --check`; `lens validate`; the taxonomy file; the `guard_paths.py` hook with tests.
- `docs/external-facts.md`: verify every item in §0.5.
- *Accept:* `uv run lens --help` works, CI is green, the image builds, and the facts are logged.

**M1 — Ingest, normalize, base frames, palette, storage.**
- Includes the local fetch helper and getting the real MP4 of the LinkedIn reference (or marking it `frames_only`).
- *Accept:*
  - 2 synthetic fixtures plus Acme v1 (from `r2://inbox/`) process locally and in `prepare.yml`;
  - a rerun is a no-op;
  - the R2 lifecycle rule for originals is in place, and `own` / `refetchable: false` originals are kept.

**M2 — Deterministic signals and local audio.**
- Fixtures; cuts (hard and gradual)/events/camera; rhythm metrics (dead holds, pace curve, caption chunking); full audio, including the CLAP and rule SFX labelling and the SFX calibration set.
- *Accept:* the §11.1 signal and audio tests pass.

**M4.5 — Baseline audit of Acme v1 (no corpus, no Claude quota).** Runs after M2. M3 and M4 continue in parallel.
- `lens compare --video acme-explainer-v1 --targets-only`: Sound (LUFS, peaks, SFX offset to reveals, cuts on beat, ducking) and Rhythm (dead holds, pace-curve variance, caption chunking) against absolute targets from config, plus Voice prosody (WPM, pauses, pitch variability) reported raw.
- *Accept:* the report reproduces the handoff's known values within tolerance (section 9) and lists the measurable fixes with timestamps.

**M3 — Visual evidence and packets.**
- Bursts, filmstrips, candidate boxes (diff and OCR), set-of-marks overlays, spectrograms, contact sheets, packet manifests, `lens status`.
- *Accept:* a packet HTML preview artifact for Acme v1 is readable, and the image budgets are respected.

**M4 — Measurement core.**
- Includes the GSAP ease mapping. (The rhythm metrics are S3 signals and land in M2.)
- The spring port with a golden test, fitting, tracking, opacity, text stagger, SFX offset (using ground-truth boxes on fixtures).
- *Accept:* all §11.1 measurement assertions pass. If `tests/fixtures/acme-v1/` exists, the eases, durations and SFX offsets recovered from the v1 render match the answer key within tolerance.

**M5 — Claude annotation layer.**
- Schemas for `a1` and `a2`; `lens validate`; skills (`annotate-batch`, `annotate-video`, `annotate-event`); subagents with restricted tools; `.claude/settings.json`; `annotate.yml` with the OAuth token; `finalize.yml`; reconcile.
- *Accept:*
  - one real video (Acme v1) is annotated end-to-end **by `claude-code-action` in Actions**;
  - all JSON validates;
  - `record.json` is produced;
  - a rerun makes no annotation calls.

**M6 — Pilot and calibration ⛔ G1 + G2.**
- **G1:** Robert adds 5 pilot sources (3 reference, 1 average, Acme v1). Claude posts the planned task and image counts.
- Run the pilot. Then **G2:** the gold set, `lens eval` baseline, one tuning round of skills and thresholds, re-eval.
- ADR on the image budgets (for example whether the filmstrip needs 15 frames or 10).
- *Accept:*
  - the eval improves over the baseline;
  - at least 60% of motion events in reference videos are `measured`;
  - Robert signs off.

**M7 — Full corpus ⛔ G3.**
- Robert completes about 50 sources and approves the nightly pacing. Nightly runs process the corpus.
- *Accept:* at least 90% of videos complete; failures are listed.

**M8 — Synthesis and exports ⛔ G4.**
- Stats, clustering, pattern cards (A3), exports, skill pack.
- *Accept:* the catalog is approved, the exports validate, and the skill pack has no third-party media.

**M9 — Compare / QA.**
- *Accept:*
  - a Acme v1 compare report with all four sections (Voice, Sound, Motion, Rhythm), where every fix links to a pattern or archetype and a timestamp;
  - the report reproduces the handoff's known values (−20.9 LUFS, 144.6 s, 14 transitions, SFX at scene starts) within tolerance.

**M10 — Private viewer (nice to have).** A static site of the corpus in private R2 (or Cloudflare Pages behind Access). Never public.

**Order:** M0 → M1 → M2 → **M4.5** → M3 → M4 → M5 → M6 → M7 → M8 → M9 → M10 → ⛔ G5 → Phase 2.

## 12b. Phase 2 — Create (outline; detailed plan at G5)

Same repo, `create/` package and `create` CLI, built after M9. It follows the handoff's recommendations (§7), reusing the `lens` foundations (stage registry, DAG check, guard hook, provenance, resumable runs):

- **DAG:** brief → script (with a style-guard reviewer) → design tokens (precomputed contrast, glyph check) → **voice** → durations → storyboard JSON → scene build (fill archetypes first, free-form only as a fallback) → assembly → QA (`lens compare --fast` on per-scene previews, then the full compare) → render.
- **Voice = ElevenLabs** (Robert's subscription, Pay As You Go off). The hosted ElevenLabs MCP (OAuth; the local `elevenlabs-mcp` repo was archived on 2026-08-20) is used for browsing, designing and auditioning voices in interactive sessions. The **voice stage calls REST `POST /v1/text-to-speech/{voice_id}/with-timestamps`**, which returns character-level alignment that the stage aggregates into word timings. That removes the whisper pass and its caption mis-hearings. Neither MCP's TTS returns alignment.
- **Voice and model: Zara (warm) on `eleven_v4`** (ADR 0018, superseding ADR 0005's `eleven_v3`), set in config so it can change. Detailed plan: `docs/phase2-plan.md`. The facts behind the earlier choice:
  - `eleven_v4`: audio tags `[short pause]`, `[long pause]`, `[laughs]`, `[chuckles]`; **no** pronunciation dictionaries or phoneme tags, so brand names use inline IPA or respelling;
  - `eleven_v3`: tags `[laughs]`, `[sighs]`, `[whispers]`…; dictionary support not documented;
  - neither supports SSML `<break>`;
  - the docs don't say whether with-timestamps works with v3 or v4, so **test it first** (ADR 0005's spike). Pronunciation of `Acme` is checked by round-trip transcription. `voice-spec.json` from `lens` provides the brief: WPM range, pause distribution by punctuation, pitch-variability range, breath density.
- **Audio plan:** SFX cue map with per-reveal offsets from `sound-spec.json`, music carve, optional beat alignment, loudness normalisation to the destination target.
- **Reconstruction loop:** rebuild patterns in HyperFrames, run `lens measure` on the renders and compare the curves with the corpus.
- ⛔ **G5:** Robert approves the Phase 2 plan.

---

## 13. Human gates

| Gate | When | Robert does |
|---|---|---|
| G1 | Before the pilot | Add 5 sources, approve the task/image counts |
| G2 | After the pilot | Correct the gold set (~2 h), approve the tuning |
| G3 | Before the full corpus | Complete ~50 sources, approve the nightly pacing |
| G4 | After synthesis | Approve the pattern catalog and taxonomy |
| G5 | After M9 | Approve the Phase 2 (Create) plan and the ElevenLabs voice choice |

Claude opens a `needs-robert` issue covering what was done, what is needed, the quota used so far, the next step and links.

---

## 14. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Claude has no native video understanding | Filmstrips with timestamps; motion measured by code. Claude labels; it doesn't time |
| Claude's box coordinates are imprecise | Set-of-marks: Claude picks code-generated box IDs; a manual box only with a reason |
| Claude can't hear audio | All audio measured locally; SFX labelled by local CLAP and rules; Claude reviews spectrograms only as a tiebreak. Perceived vocal emotion is out of scope in v1 |
| Subscription quota exhaustion | Small nightly batches, image budgets, fresh-context subagents, caching, resumability |
| OAuth token expiry or auth issues in Actions | README renewal steps; fallback of running `/annotate-batch` in a local interactive session |
| Tracking fails on complex UI | Fall back to flagged estimates; a 60% measured target; coverage reported |
| Taxonomy doesn't fit | `other` + proposals → G4; versioned taxonomy |
| Skill edits degrade quality | Gold-set eval gate (manual dispatch) |
| YouTube blocking or ToS | Local fetch plus the R2 inbox; ADR |
| Copyright | Private repo and bucket; exports carry numbers and text only |
| Free-tier limits (R2, Actions) | Lean media, an original-deletion policy, a minutes estimate in `lens status` |
| Usage-limit kill mid-run | `if: always()` validate and commit, per-task progress files, resume from files |
| Workflow chaining silently not firing | Reusable workflows with `needs:` in one nightly workflow |
| ElevenLabs MCP has no timestamps and may not load headless (confirmed) | The voice stage uses REST with-timestamps; the MCP is for interactive work only |
| Remotion licence (free only for ≤ 3 employees) | First-principles spring model; Remotion golden test only after ADR 0004 |
| Corpus/format mismatch skews compare | Cohort defaults to the target's format; ≥ 15 narrated explainers |

---

## 15. Robert's setup checklist

1. ✅ Private repo `VijaRobert/explainer-video-creator` exists, and this file is committed.
2. A Claude subscription that can carry the load (Max recommended for the full corpus).
3. Locally, run `claude setup-token`, then add `CLAUDE_CODE_OAUTH_TOKEN` as an Actions secret (it works on Pro, Max, Team and Enterprise). Alternatively, run `/install-github-app` in Claude Code, which installs the GitHub App and sets up the secret.
4. Install the Claude GitHub App on the repo (step 3 does this if you used `/install-github-app`).
5. For building in Claude Code on the web, the cloud environment needs network access to `pypi.org`, `files.pythonhosted.org`, `github.com`, `ghcr.io`, `huggingface.co` and the R2 endpoint, plus a setup script that installs `uv` and `ffmpeg`.
6. Cloudflare R2: a private bucket `explainer-lens-data` and a token scoped to it. Add the R2 secrets.
7. Put the Acme v1 explainer (`renders/acme-explainer-v1.mp4` locally) into `r2://inbox/`. ✅ `HANDOFF.md` is in the repo as `docs/handoff-v1.md`. Upload the v1 HyperFrames text files to `tests/fixtures/acme-v1/` when convenient (`index.html`, `compositions/frames/*.html`, `audio_meta.json`, `caption_groups.json`, `STORYBOARD.md`).
7b. (Phase 2) ElevenLabs subscription with usage-based billing disabled; add `ELEVENLABS_API_KEY` as a secret, and configure the ElevenLabs MCP locally.
8. Collect the 5 pilot videos (download YouTube ones locally with the helper after M1).
9. Block about 2 hours for the gold set at M6.

---

## 16. Kickoff prompt (paste into Claude Code)

```
You are building the repo "explainer-video-creator" (Phase 1: the `lens` CLI). Read BUILD_PLAN.md (v2.2) completely first.

Constraints: no paid APIs. Visual annotation is done by Claude Code (you, via skills/subagents and
claude-code-action with CLAUDE_CODE_OAUTH_TOKEN). Audio is analyzed with local tools/models only.
MCP servers are optional conveniences; nothing in the pipeline may depend on them.

Then:
1. Read docs/handoff-v1.md (lessons from the v1 video build). Create CLAUDE.md from Appendix A,
   PROGRESS.md, docs/decisions/0001-plan-adopted.md.
2. Execute M0 only, including verifying every fact in section 0.5 and logging it in
   docs/external-facts.md with URLs and today's date.
3. Open a PR for M0 with acceptance evidence. You may auto-merge M0–M3 when CI is green; from M4 on,
   wait for my review.
4. Continue milestone by milestone. At HUMAN GATES open an issue labelled needs-robert and stop.

Never commit media or secrets. Keep annotation batches within configured limits.
```

---

## Appendix A — `CLAUDE.md`

```markdown
# CLAUDE.md — explainer-video-creator

## Mission
Research, understand and (Phase 2) create premium SaaS explainers. Phase 1 = `lens`: measure what makes
premium explainers premium; export reusable specs; grade our own videos.
Truth: BUILD_PLAN.md (v2.2). Audit: docs/plan-audit.md. Lessons: docs/handoff-v1.md. Progress: PROGRESS.md. Decisions: docs/decisions/.

## Hard rules
- No pay-per-use APIs (no Gemini/OpenAI/Anthropic API keys). Visual annotation = Claude Code skills/subagents.
  Audio analysis = local tools/models only. Only exception: ElevenLabs subscription for Phase 2 voice.
- One milestone per branch/PR; acceptance evidence in the PR. Stop at HUMAN GATES (issue `needs-robert`).
- Never commit media or images (except tiny synthetic fixtures). Never commit secrets.
- Code measures, Claude names. Numbers about timing/easing/colour/audio come from code; Claude estimates
  only as flagged fallback (source="model_estimate").
- Annotators only use IDs given in packets (shots, words, events, box ids, SFX candidates). Never invent
  timestamps. Prefer candidate box ids; manual_box only with a reason.
- Every annotation file must pass `uv run lens validate <file>` before the task is done.
- Subagents: Read packets/taxonomy; Write only to the active task's declared paths (enforced by
  .claude/hooks/guard_paths.py); Bash only `uv run lens validate*` and `uv run lens status*`.
- Respect annotate batch limits in config/lens.yaml. Never exceed images-per-task budgets.
- MCP servers are optional; the Phase 1 pipeline must pass without any. ElevenLabs MCP (Phase 2) always
  has a direct-API fallback.
- Verify external facts in official docs before relying on them; log them in docs/external-facts.md.
- Measurement code is test-first against synthetic fixtures.
- Every stage declares inputs and the exact paths it writes (stage registry); `lens dag --check` must pass.
  No stage rewrites another stage's output. Completion = validated artifacts on disk.
- Motion outputs are renderer-agnostic: GSAP ease + cubic-bezier (primary, HyperFrames) and Remotion spring.
- Lowercase slug file names only (case-insensitive filesystems).
- Every output JSON has provenance (schema_version, tool_version, skill_id@hash, annotator, input_hash,
  created_at). Stages are idempotent and cached.
- Exports and the skill pack contain no third-party media.

## Commands
make setup | make test | make fixtures | uv run lens ingest|frames|signals|audio|packets|status|validate|
measure|reconcile|synth|export|compare|eval|report

## Style
Python 3.12, type hints, ruff, mypy strict in lens/measure, lens/schemas and lens/stages.py. Small pure functions.
```

---

## Appendix B — Skills (initial content for `.claude/skills/*/SKILL.md`)

### B.1 `annotate-video` (A1)

```
You annotate the STRUCTURE of one SaaS explainer/launch video for a measured reference library.
You cannot watch video: you read contact sheets (2 fps, timestamps stamped, one header per shot id),
mid-shot keyframes, and anchors.json (shots, transcript with word indices, BPM, loudness, palette,
event counts). Treat anchors as ground truth.

Rules
1. Annotate EVERY shot id in anchors; never add/merge/split shots or invent times. Use word indices
   for anything tied to speech.
2. Use only taxonomy enums (taxonomy/v1.yaml); otherwise "other" + *_other text.
3. Quote on-screen text verbatim; count words. Describe typography (style, weight, case, tracking);
   font names only as low-confidence guesses. Do not output colours; palette comes from code.
4. build_rebuild: one concrete sentence a developer can implement.
5. Scores 1–5 with evidence (shot ids / word indices); 3 = competent, 5 = best-in-class.
   sound_design is judged from the audio facts provided (sfx density, ducking, beats) — say so.
6. works_muted: is the story understandable with sound off? localization_friendliness: baked-in text,
   VO dependence.
7. Max 3 signature_moments, each with why it elevates perceived quality.
8. Confidence per shot; "unknown" when unsure. Do not guess what you cannot see.
Write videos/<id>/a1.json, then run `uv run lens validate videos/<id>/a1.json`; fix until valid.
Context: insights inform Acme.ai (AI-visibility SaaS for SEO agencies); don't let it bias scores.
```

### B.2 `annotate-event` (A2)

```
You annotate ONE motion event. Inputs: filmstrip.jpg (frames left→right, top→bottom, timestamps
stamped), end_marked.jpg (settled end frame with numbered candidate boxes), end_clean.jpg,
spectrogram.jpg (SFX candidates marked S1..Sn with local classifier labels), facts.json, candidates.json.
Code measures all timing; you identify and label.

Tasks
1. Elements that visibly move/change (max 12): choose the best candidate box id for each. If none
   fits, give manual_box [ymin,xmin,ymax,xmax] in 0–1000 on the end frame + reason. For each: label,
   role, change_types (enums), is_text, text (verbatim), text_unit (whole|line|word|char|unknown).
   Optional fallback estimates of duration/easing (clearly estimates).
2. SFX: for each candidate S#, confirm or override the classifier label using the spectrogram shape
   and what happens visually at that moment; or "unsure". Do not add candidates.
3. Pattern: canonical id from taxonomy.patterns, or "other" + proposed_name (2–4 words, reusable),
   description, why_premium (concrete).
4. build_hint: renderer-agnostic (which properties animate, order, stagger, spring vs ease); give a
   GSAP/HyperFrames phrasing first (e.g. fromTo + ease name + stagger), Remotion second.
5. Confidence + notes on ambiguity. Never list elements that are static in all frames.
Write videos/<id>/events/<eid>.a2.json, run `uv run lens validate` on it; fix until valid.
```

### B.3 `write-pattern-cards` (A3)

```
Write one pattern card per input pattern for an AI agent building HyperFrames (GSAP) or Remotion videos. You get the pattern
definition, member event descriptions, and MEASURED stats. Use only provided numbers.
Sections: name; one-line definition; when to use / not; anatomy (elements, order); motion spec
(median durations in seconds and in frames @30/@60 fps, dominant easing, GSAP ease + cubic-bezier +
Remotion spring config, stagger); sound recipe (layers, offsets relative to the reveal in ms/frames);
variations; do/don't (≤4 each); implementation sketch for HyperFrames/GSAP (primary) and Remotion.
Then group approved patterns into scene archetypes (corpus/archetypes/<aid>.md + .json): parameters,
patterns used, measured timing, SFX cue map with offsets, reference examples. Reference examples only as video_id + time. No marketing language.
Write corpus/patterns/<pid>.md and .json; validate the json.
```

### B.4 `compare-fixes` (A4)

```
Given metric placements (value, corpus percentile, target range) for a target video in Voice, Sound,
Motion, Rhythm, plus the pattern catalog index, produce the 10 highest-impact fixes ordered by perceived-quality
gain per hour. Each: problem + evidence (metric + timestamp), target, pattern_id/token, concrete change,
effort S/M/L. No fix without metric evidence. Write reports/compare/<id>/fixes.json; validate.
```

---

## Appendix C — Taxonomy v1 (`taxonomy/v1.yaml`)

```yaml
format: [feature_reel, narrated_explainer, teaser, founder_talk, tutorial, other]
shot_type: [ui_closeup, ui_full, ui_recreated, screen_recording, kinetic_type, 3d, abstract,
            footage, presenter, logo, data_viz, other]
composition: [centered, rule_of_thirds, split, grid, stacked, full_bleed, other]
transition: [hard_cut, whip, scale_dissolve, crossfade, mask_wipe, match_cut, morph, slide,
             zoom_through, blur, push, other]
element_role: [headline, body_text, label, card, button, chart, metric, icon, cursor, ui_panel,
               list_item, logo, background, avatar, notification, other]
change_type: [fade, slide_up, slide_down, slide_left, slide_right, scale_up, scale_down, pop, rotate,
              mask_reveal, draw_on, blur_in, blur_out, typewriter, count_up, color_shift, weight_shift,
              morph, highlight, other]
easing_class: [linear, ease_in, ease_out, ease_in_out, spring_no_overshoot, spring_overshoot,
               bounce, step]
camera_move: [none, push_in, pull_out, pan_left, pan_right, tilt_up, tilt_down, orbit, parallax, other]
sfx: [whoosh, swoosh_reverse, click, tick, pop, riser, impact, chime, glitch, typing, none, music,
      speech, unsure, other]
music_event: [none, build, drop, stop, swell, beat_cut]
depth_cue: [shadow, blur, parallax, glow, grain, perspective_tilt, none]
hook_technique: [question, stat, bold_claim, pain, demo_first, other]
beat: [hook, problem, agitate, mechanism, demo, proof, outcome, cta]
patterns:
  - stagger_list_reveal
  - card_wall_stagger
  - ui_camera_push_in
  - spotlight_focus
  - kinetic_word_reveal
  - metric_count_up
  - chart_draw_on
  - match_cut_element
  - scale_dissolve_transition
  - whip_transition
  - notification_pop
  - cursor_guided_demo
  - logo_resolve
  - parallax_layers
# v2.2: aliases to the v1 HyperFrames animation blueprints, so the catalog uses the factory's vocabulary
pattern_aliases:
  kinetic_word_reveal: [kinetic-type-beats]
  card_wall_stagger: [grid-card-assemble]
  metric_count_up: [dataviz-countup]
  logo_resolve: [logo-assemble-lockup]
```
