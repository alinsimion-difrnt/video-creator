# Phase 2 — Create: detailed plan (for G5)

Status: **draft for G5; scope, music and plan tier settled by Robert on 2026-10-06** (see §7). Expands BUILD_PLAN §12b. Robert approves or edits it at G5; nothing in `create/`
is built before that. Voice is already decided (ADR 0018).

## 1. Goal and first target
Turn a brief into a premium SaaS explainer, reusing what Phase 1 measured. Every stage writes validated
artifacts on disk; the same DAG, guard hook, provenance and caching rules as `lens` apply.

**First target: Acme v2**, a rebuild of v1 from the same facts. Acceptance is measured by `lens compare`
against the corpus, not by opinion alone:
- v1 has 12 measures outside the premium range. **v2 must have at most 4**, and none in Voice.
- Loudness inside the LinkedIn house target (-16 to -14 LUFS, true peak <= -1 dBTP).
- SFX at scene starts / reveals >= 80% (v1: 57%).
- Robert approves the sketch sheet, the motion previews and the final cut.

## 2. What Phase 2 reads from Phase 1
Only `exports/` and the skill pack (ADR 0017), never the corpus:
- `voice-spec.json`: pace, pause and pitch ranges (voice take selection, script length).
- `pacing.json`: scene length per archetype, cut-on-beat share, caption words per group.
- `motion-tokens.json`: durations by role, eases (GSAP + cubic-bezier), springs, word stagger.
- `sound-spec.json`: SFX density and mix, offset to reveal per SFX type, ducking, loudness targets.
- `archetypes.json` + `patterns.json`: 17 scene archetypes with slots, steps and build recipes.

## 3. Project layout
```
projects/<slug>/            committed: small text artifacts only
  brief.yaml                C1
  script.yaml               C2  (scenes, spoken lines with tags, on-screen copy, claim sources)
  tokens.json               C3  (colours by role, type ramp, contrast table, glyph inventory)
  voice.json                C4  (chosen take per scene, word timings, prosody, credits used)
  timeline.json             C5  (scene bounds, tails, global word timings)
  storyboard.json           C6  (archetype + filled slots per scene)
  sketches.html             C7  (never committed if it embeds brand fonts; regenerated)
  scenes/<scene>.html       C8
  audio_plan.json           C10 (SFX cues, music carve, loudness target)
  index.html                C11
  qa/                       C13 (lens compare of the render)
data/create/<slug>/         never committed: voice takes, music, SFX, previews, renders (R2 for keeps)
```

## 4. Stages
Each stage is added to the registry (`lens/stages.py`, `Stage(..., milestone="P*")`) with its reads and
exact writes, so `lens dag --check` and `guard_paths.py` cover Phase 2 too. `C` = Claude skill or
subagent, `code` = deterministic.

| Stage | Runner | Does | Gate / check |
|---|---|---|---|
| C1 brief | C | Short interview: product, audience, destination, length band, facts sources, tone | schema |
| C2 script | C + reviewer | One spoken line per scene, warm tag level, `Ack-me` respelling, every claim cites a source | style lint (no slogans, antithesis pairs, triplets; tag density); words fit the length band at 158 wpm |
| C3 tokens | code + C | Tokens from the brand's design files; WCAG contrast for every text/bg pair; glyph check vs fonts | fails on AA misses or missing glyphs |
| C4 voice | code | ElevenLabs REST with-timestamps per scene, Zara / `eleven_v4`; 2 takes, keep the one closest to `voice-spec`; cache by text+voice+model hash | whisper round trip: no spoken tags, brand heard right |
| C5 timing | code | Scene length = voice + tail (from `pacing.json`), real silence between scenes (the short-pause fix, ADR 0018) | total within the length band |
| C6 storyboard | C | Pick an archetype per scene, fill its slots; free-form only with a reason | slot schema per archetype |
| C7 sketches | code | After C8: the settled final frame of each built scene (HyperFrames snapshot) on one sheet | **Robert locks layout + copy** |
| C8 build (templates route; the default is now the motion route, ADR 0032: c6_direction, c8_motion, c8_grade, c10_music, c12_mix) | code; `c8_build_freeform` (C) for uncovered scenes | Fill HyperFrames archetype templates with tokens, motion tokens and word-cued reveals; free-form builder subagent only for uncovered scenes | per-scene contract lint (letter-led ids, one paused timeline, keep-out, no exits) |
| C9 previews | code | Low-res motion preview per scene | **Robert locks motion** |
| C10 audio | code | Music **built for the video**: an Eleven Music `composition_plan` with one chunk per story section, durations from `timeline.json` (pre-roll and tail included), tempo from the corpus (120 BPM median), style from the project (Acme: playful funk-pop, §7), no lead melody, a level check for dropouts; SFX cue map at measured offsets to reveals; carve under voice, ducking; loudness to destination | bed BPM measured; LUFS / true peak |
| C11 assemble | code | Frames, captions from TTS word timings (brand dictionary), voice, music, SFX | HyperFrames lint + check |
| C12 render | code | HyperFrames render; MP4 to R2 | ffprobe |
| C13 QA | code + C | `lens compare` + A4 fixes on the render; loop back to the owning stage | §1 acceptance |

## 5. Milestones (one PR each)
- **P0 — Registry and skeleton.** `create` CLI, project schemas, Phase 2 stages in the registry, guard hook
  covers `projects/**`. *Accept:* `lens dag --check` green with C1-C13; a fixture project validates.
- **P1 — Voice and timing (C4, C5).** *Accept:* Acme script → per-scene takes with word timings;
  chosen takes inside `voice-spec` on pace and pitch; credits logged per run; rerun costs 0 credits.
- **P2 — Brief, script, tokens (C1-C3).** Script skill with the style lint and a good/bad pair.
  *Accept:* Acme v2 script passes the lint; tokens pass contrast and glyph checks.
- **P3 — Archetype templates (C6, C8).** HyperFrames templates for the archetypes Acme needs first
  (`title_card`, `kinetic_statement_card`, `prompt_input_card`, `chat_demo_panel`, `comparison_split`,
  `stat_count_up`, `tile_grid`, `cards_triptych`, `logo_close`). *Accept:* each renders from a fixture
  storyboard; `lens measure` on the render recovers the motion tokens it was built with.
- **P4 — Review surfaces (C7, C9).** *Accept:* sketch sheet and per-scene previews for Acme v2.
- **P5 — Audio and assembly (C10, C11).** *Accept:* SFX within the measured offset band; LUFS in target.
- **P6 — Render and QA (C12, C13).** *Accept:* the §1 targets on Acme v2. ⛔ Robert signs off.

## 6. Budgets
- **ElevenLabs (Starter, 30k credits/month, Pay As You Go off).** Real spend is read from
  `/v1/usage/character-stats`. This cycle: ~12.4k used (voice auditions ~11.1k, one music bed 1.25k), so
  ~17.6k remain. One Acme pass: voice ~1.4k characters x 2 takes (under 2.8k credits) + one 100 s bed
  (1.25k) is about 4k, so Starter covers the Acme v2 validation with room for regenerations.
- **Claude:** subscription only (no API keys). The free-form builder is the expensive part (v1: 190k-330k
  tokens per builder); templates should cover most scenes so builders are rare.
- **CI:** code checks only; rendering runs on Robert's machine (ADR 0019).

## 7. Decisions at G5
Settled by Robert (2026-10-06):
- **Scope:** validate on improving the first MVP (Acme v2). Build further only if that works.
- **Music:** generated with Eleven Music on the same subscription, **built for the video** (sections timed to
  the narration). A generic single-prompt bed was rejected as "elevator music", a minimal techno bed as "too
  techno". **Chosen style (2026-10-06): playful funk-pop**, from a local analysis of 4 ClickUp tracks (demucs +
  CLAP: funk/disco groove, plucks and mallets, quirky/confident, major, ~120 BPM): bouncy bass, muted funk
  guitar, marimba/mallet plucks, warm pads, claps and snaps, syncopated, no four-on-the-floor, no lead melody.
  The prototype plan is in `projects/acme-v2/reference/music-plan-prototype.json`.
- **Music QA (C10):** generated beds can fade out at a section boundary (the prototype went silent for 6 s at
  61-70 s); C10 checks the bed's level per second and patches or regenerates a dropout.
- **Plan tier:** Starter is enough for now.

- **Brand:** the Claude Design hand-off in `brands/acme/` (moved from `projects/acme-v2/brand/`, ADR 0022) (reviewed in `REVIEW.md`); the
  SVG logos are committed, fonts load from Google Fonts (ADR 0019).
- **Rendering:** on Robert's machine (ADR 0019).

G5 is closed.
