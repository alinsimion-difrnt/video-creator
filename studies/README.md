# Studies: TikTok and pixel art (Robert, 2026-10-13)

Robert, after the Fred & Pixie 9/10 push: "the edits are strange, they don't deliver the right direction and
the animations are overused... Fred should have been doing stuff in and out of the animation: exit, come in,
do something, do it again, go away, maybe smaller in the back and do something there." He asked for two
studies, done like the explainer corpus, kept **independent** so they can be used alone or combined:

1. **TikTok**: 200 TikToks on AI, marketing, Claude, GEO and SEO.
2. **Pixel art**: tutorials and at least 30 pixel-art games, styles or stories, with the list of what was
   studied.

Each study has its own folder, its own source list, its own code, its own findings and its own skill. Neither
imports or reads the other. `studies/combining.md` (written last) is the only place they meet.

| | TikTok | Pixel art |
|---|---|---|
| Folder | `studies/tiktok/` | `studies/pixel-art/` |
| Source list | `studies/tiktok/sources.yaml` (200 videos) | `studies/pixel-art/sources.yaml` (30+ subjects, tutorials) |
| Code (tested) | `study/tiktok/` | `study/pixel/` |
| Media (never committed) | `data/study/tiktok/` | `data/study/pixel/` |
| Per-item notes | `studies/tiktok/notes/<id>.json` | `studies/pixel-art/notes/<id>.json` |
| Findings | `studies/tiktok/findings.md`, `stats.json` | `studies/pixel-art/findings.md`, `metrics.json` |
| Skill it feeds | `.claude/skills/tiktok-edit/` (new) | `.claude/skills/pixel-art/` (updated) |

Rules carried over from the explainer corpus (CLAUDE.md): code measures, Claude names; numbers come from code;
no third-party media or verbatim copy is committed or exported; every notes file has provenance and passes
its validator; thresholds live in config, not code.

## Track 1: TikTok (200 videos)

### Find (the list)
- **Seed: Robert's 50 accounts** (marketing and growth, SEO/GEO/AI search, AI and automation, Claude/dev).
  Each handle is checked on TikTok first; a handle that does not exist or has no videos is dropped and noted.
  From each live account: its recent videos from the creator embed (`tiktok.com/embed/@handle`).
- **Fill: topic searches** on TikTok's discover pages (server-reachable headless), e.g. "claude code",
  "ai marketing", "generative engine optimization", "seo tips 2026", "ai agents", "chatgpt seo", picking the
  most-liked videos the creators list did not cover.
- **Balance**: about 40 per topic (AI, marketing, Claude, GEO, SEO), at most 5 per creator, 15 s to 3 min.
  Each entry: id, url, creator, topic, title/caption (short), likes when shown, why it was picked.

### Fetch
TikTok's video pages and yt-dlp are blocked from the cloud, but its **embed player** serves the MP4
(576x1024, verified 2026-10-13 and logged in docs/external-facts.md). A headless Chromium opens
`tiktok.com/embed/v2/<id>` and saves the file to `data/study/tiktok/<id>.mp4`. Nothing to do on Robert's
machine.

### Measure (code, all 200)
Per video, `study/tiktok/measure.py` writes `studies/tiktok/measure/<id>.json`:
- **Shape**: duration, aspect, loop (last frame vs first).
- **Cutting**: cuts (frame-difference shot detection), cuts per minute, longest hold, first cut time.
- **Words**: faster-whisper words; words/s, time to the first word, silence share.
- **On-screen text**: OCR at 2 fps: text coverage, caption position (top/middle/bottom thirds), words on
  screen per second, the hook text in the first 2 s.
- **Face**: face size and position (share of frame height, x/y), talking-head share of the video.
- **Motion and graphics**: motion energy per second, zoom/punch-in events (scale change between frames),
  share of frames with overlays (OCR + edge density outside the face).
- **Sound**: loudness (LUFS), music under speech (spectral estimate, no demucs).
- **Hook window (0-3 s)**: first word, first text, first cut, first motion peak.

### Annotate (Claude subagents, all 200)
Each subagent gets 5 videos: a contact sheet, a 0-3 s hook strip, the transcript and the measure JSON, and
writes `studies/tiktok/notes/<id>.json`:
- **Format** archetype (talking head, green screen, screen recording, voice-over B-roll, skit, podcast clip,
  listicle, tutorial, news).
- **Hook** type and hook line.
- **Story** shape (beats with times from the measure file only).
- **Graphics** used (captions style, stickers, arrows, screenshots, zooms, memes) and how often.
- **Characters or mascots**, if any: how they enter, act, exit and come back.
- **CTA**, and why it works or does not.

Validated against a schema (`uv run python -m study.tiktok validate`).

### Synthesise
`studies/tiktok/findings.md` and `stats.json`:
- Medians and spreads per topic and per format; the top-liked quartile against the rest.
- Hook patterns that recur.
- How much graphics the best ones use. Robert's note: ours were "overused", so this gets a number.
- A list of all 200 studied.

This feeds a new **tiktok-edit** skill: rules with numbers, used when planning a reel.

## Track 2: Pixel art (30+ subjects, plus tutorials)

### Find (the list)
`studies/pixel-art/sources.yaml`, at least 30 subjects across kinds:
- **Games** (Celeste, Owlboy, Hyper Light Drifter, Stardew Valley, Shovel Knight, Dead Cells, Eastward,
  Sea of Stars, Octopath Traveler, Blasphemous, Katana ZERO, Undertale, Terraria, Metal Slug, Street Fighter
  III, Chrono Trigger, Final Fantasy VI, Castlevania SotN, Mother 3, Pokemon, Hotline Miami, Kingdom,
  Loop Hero, Minit, Downwell, Sword & Sworcery, Noita...).
- **Styles** (1-bit, Game Boy 4-colour, NES, isometric, HD-2D, pixel cinemagraphs, colour cycling).
- **Artists and stories** (Mark Ferrari, Paul Robertson, waneella, Kirokaze, eBoy, Slynyrd).
- **Tutorials** (Pedro Medeiros/saint11, Slynyrd Pixelblog, Lospec, Pixel Logic, Derek Yu, AdamCYounis,
  Brandon James Greer, MortMort...): text and image tutorials, since YouTube is blocked from the cloud.

Each entry: id, kind, title, maker, year, what it is known for, the reference URLs used.

### Gather
Public reference images per subject (sprite sheets, animated GIFs, screenshots) downloaded to
`data/study/pixel/<id>/` for measuring only; never committed.

### Measure (code)
`study/pixel/measure.py` writes `studies/pixel-art/metrics/<id>.json`:
- **Native resolution** (the pixel scale of a screenshot) and sprite size.
- **Palette**: colour count, ramps and the hue shift along them, darkest and lightest values, saturation.
- **Outline** style (none, dark, coloured, selective), measured on sprite edges.
- **Dithering** share.
- **Animation**: frame counts, frame durations and cycle lengths from GIFs; squash and stretch from
  bounding boxes.

### Annotate (Claude subagents)
Per subject, `studies/pixel-art/notes/<id>.json`:
- What makes it read: silhouette, light, palette, animation, staging.
- The techniques, named.
- How a character acts in the scene: entrances, exits, depth, idle loops.
- What to steal for Fred and Pixie. Tutorials become technique rules with their source.

### Synthesise
`studies/pixel-art/findings.md` and `metrics.json`:
- The list of everything studied.
- A style atlas (which look for which job).
- Animation timing tables.
- Rules for character acting in and out of a scene.

These update the **pixel-art** skill and the character-animation skill, including Robert's choreography
note.

## Order
The two tracks run in parallel: listing, then fetch/gather, then measure, then annotate, then findings. Each
finished step is committed and pushed (lists, code, tests, JSON notes, findings; never media).

## Status (2026-10-13)
- **TikTok: done.** 194 of 200 measured and annotated (6 could not be fetched). See `studies/tiktok/findings.md`
  and `studied.md`, and the skill `tiktok-edit`.
- **Pixel art: done.** 79 sources, 125 notes. See `studies/pixel-art/findings.md` (with the list of
  everything studied) and the skills `pixel-art` and `character-animation`.
- **Combined:** `studies/combining.md`.
- **YouTube: deferred** (Robert, 2026-10-13). The rules don't depend on it. Run `studies/youtube-fetch.md` on
  the laptop only if a re-cut shows a craft gap (for example, stiff moves) that the tutorials would fix.
