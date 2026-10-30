# 0026 — Presenter reels: one render, widgets on the words, captions off the body

- **Status:** accepted (Robert's feedback, 2026-10-09; built and audited 2026-10-10)
- **Date:** 2026-10-10
- **Milestone:** Phase 2, presenter footage (follows ADR 0025)

## Context
Robert on the first two TikTok versions of his Budapest take:
- the layout version's animations "are not related to this tiktok in any way" (it reused the Acme film);
- the overlay version was boring: graphics with no relevant animation;
- captions sat on his chest or face;
- the cuts were fine.
He asked for three variants of each type (layout: product on top, him below; overlay: animations on his own
video), an audit, then one finished version of each.

## Decision
- **`create reel`** renders the presenter video, the product area, overlays and captions in one HyperFrames
  composition (`create/kit/reel.html`, `create/footage/reel.py`). It replaces three renders (pip, overlay, burn)
  with one: about 14 minutes for 81 s on the cloud sandbox instead of about 25 (PNG frames); about 6 minutes
  since reels extract frames as JPEG, 4 for a half-size `--draft` (2026-10-11).
- **The plan names, code times.** `projects/<p>/reel.yaml` (`ReelPlan`) lists layouts from a word on and widgets
  between two words, with `marks` for their beats (when to type, when a source lights up, when the button is
  clicked). Every time comes from the timeline's word times; every position from the frame's safe areas and the
  face (F5 framing).
- **Widgets are the script.** `create/kit/motion.js` draws them from the brand tokens: an AI chat whose question
  types as it is said, a search, a sources list that lights up row by row, a review whose stars fill and whose
  context phrases get a marker, a rolling counter, a map with pins, a chart that draws up, call-to-action click,
  stickers, vague vs specific queries, tiles, the brand logo. There are no third-party logos or media: names
  appear as text with generic icons. Restaurant names in examples are made up.
- **Captions never sit on the presenter.**
  - In full shots they go above the head, in `frames.vertical.caption_top` (y 300–500, under TikTok's top tabs),
    moved up when the head is high.
  - In split shots they end `caption_seam_gap_px` above the product area's bottom edge.
  - In product-only shots they use the caption band.
  - `create qa` checks this as `captions_clear_body`: in a full shot a caption must end above the top of the head
    (the face box raised by `hair_above_face`).
- **Overlays** go where the widget's shape fits best: on the chest, or left of the face under the captions
  (`overlay_aspect`). They are checked against the face and against the captions on screen.
- **Motion.** Every card enters with a spring and drifts slowly while on screen. Rows and tiles are visible
  (dimmed) at once and light up on their word, so no card waits empty. Product widgets hold until the next one
  or the layout move, so the product area is never blank. Widgets wait for a layout move to finish.
- **Look.**
  - A slow push-in per shot (1.05).
  - Punch-ins on key words (1.1, full shots only).
  - A light CSS grade (contrast, saturation, a touch of warmth) on the presenter only.
  - A dark brand product area (`product_bg: ink`) for the layout version.
- **Sound.** `create/footage/sfx.py` synthesises a pop, a whoosh and a click with ffmpeg formulas (no samples,
  no API). They are placed from the reel's sidecar, mixed 20 dB under the voice and limited to the voice's
  true-peak ceiling. Loudness does not change (-14.1 LUFS, -1.7 dBTP).

## Evidence (sandbox, Robert's take, 81.3 s)
- Six variants: L1 light split, L2 light split only during widgets, L3 dark split, O1 chest UI cards, O2 stickers,
  O3 cutaways.
  - All six pass `create qa`: format, loudness, hook, pacing, captions clear of the body, overlay placement.
    O3 failed one overlay check at a cutaway edge; that is fixed.
  - An independent review (fresh context, frames only) scored them L3 7.5, L1 6.5, O2 6, O3 5.5, L2 5, O1 4.5.
  - Its main findings were tiny card text, empty or dead product moments, fade-only entrances, stickers that
    only repeat the speech, the counter showing "00", and captions hitting cards during moves. All of these are
    fixed in code above, except the stickers, which are a plan choice.
- The finals combine L3 with the fixes (layout) and O2's stickers with three short cutaways and widgets
  (overlay). They went through five render-and-review rounds; each review came from a fresh reviewer that saw
  only frames.
  - Layout scores: 6.5, 6.5, 6.5, 7, 7. Overlay scores: 5.5, 5.5, 5.5, 5.5, 6.
  - Fixes from those rounds: the presenter vanishing mid-move (a GSAP clip-path string bug, see
    test_layout_kits_never_tween_clip_path_strings), the counter glitch, crossfading cards, white cards on a
    white shirt, a city mismatch (Bucharest), a missing URL, and the face sitting under TikTok's description.
  - Both finals pass `create qa` 17/17 with sound at -14.1 LUFS and -1.4 / -1.6 dBTP.
  - Plans: docs/examples/reel-layout.yaml, docs/examples/reel-overlay.yaml.
- Still open, for Robert's eye:
  - In split, his face sits at about y 1130–1370, partly under TikTok's description text. Moving it higher
    means a smaller product area or more of his head cut by the seam.
  - Overlay cards sit on the chest, where they have room to be read; beside the face they become too small.
  - Overlays have a few beats with no new graphic.

## Addendum: the process as tools (2026-10-11)
- `create words <p>`: the words with indexes, per scene, and the cuts.
- `.claude/skills/draft-reel-plan`: drafts `reel.yaml` from them, by the rules the reviews produced.
- `create reel --check` (create/footage/reel_check.py, config `create.footage.reel.check`): plan checks on the
  built data and layout checks measured in Chromium (no render). On the first take's plans it caught, in about
  2 s each, the Bucharest mismatch, small text, a static stretch, overlays touching the face, and two bugs the
  reviewers had missed:
  - an overlay that spans a cut was placed clear of the face in only one of its shots (fixed: `face_span`);
  - product cards reached past the safe rects (fixed: boxes inside them, with room for the spring).
- `create review` + `.claude/skills/review-reel`: the fresh-eyes round as one command and one skill.

## CLAUDE.md lines (Robert applies; an agent may not edit CLAUDE.md)
In "Commands", after the `uv run create sketches` line, add:
```
uv run create ingest|transcribe|cuts [--approve ids|all]|prep <project> (presenter footage, ADR 0025) |
uv run create words <project> | uv run create reel <project> [--plan f] [--check|--preview s,s|--draft] |
uv run create qa|review <project> --video f.mp4 (presenter reels, ADR 0026; skills draft-reel-plan, review-reel;
agents reel-planner, reel-reviewer) | LENS_ROOT=<dir> runs any command on a project outside the repo |
```
Optionally, under "Mission":
```
Presenter TikToks: docs/learnings/presenter-reels.md first.
```

## Consequences
- A new presenter video is one plan file per type; three variants of one take cost about 18 minutes of render (12 as drafts).
- `create pip`, `create overlay` and `create burn` stay for landscape and non-presenter work. `create burn`'s
  chest band fails `captions_clear_body` on presenter videos by design.
- The widget set is Acme-shaped (AI answers, sources, reviews). Other topics need new widget kinds in
  `motion.js`; each is a function of its spec and the word marks.
- The sounds are formula-made and were checked by level and spectrum only (no listening in the sandbox).
  Robert should judge them by ear.
