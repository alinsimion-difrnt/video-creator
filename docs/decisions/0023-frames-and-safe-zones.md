# 0023 — Frame profiles and the safe-zone audit

- **Status:** accepted (Robert approved the roadmap, 2026-10-09)
- **Date:** 2026-10-09
- **Milestone:** M-C of `docs/research/vertical-footage-brands.md` §5

## Context
- The pipeline only knew a 1920x1080 frame, with a bottom 17% caption keep-out.
- TikTok, Reels and Shorts need 1080x1920. Their app overlays (action rail, description, tabs) cover large parts of
  the frame.
- The research measured the official overlay files and proposed one safe area for all three platforms
  (`docs/research/vertical-footage-brands.md` §1.2, `docs/external-facts.md` §17).

## Decision
- **Frames live in config** (`create.design.frames`). Each frame has:
  - a size and a text minimum (vertical: 44 px; landscape: 24 px);
  - a list of safe rectangles (critical content must sit fully inside one of them);
  - a caption band.
- The two frames:
  - **Vertical:** core x 120–780, y 288–1248; upper extension x 120–888, y 288–840; captions y 900–1150.
  - **Landscape:** the 4% margin of the v2 edge audit; captions in the bottom 17% (y ≥ 896).
- **The destination decides the frame** (`create.design.destination_frames`): linkedin and youtube → landscape;
  tiktok, instagram_reels and youtube_shorts → vertical. The three vertical destinations get the house loudness
  target (no platform publishes one).
- **Brands opt into frames.**
  - A brand's `video.yaml` `type.sizes` and `layout` serve landscape. Any other frame needs
    `frames.<frame>: {sizes, overrides, layout}`.
  - C3 fails when the brand has no sizes for the brief's frame, or when text is under that frame's minimum.
- **Templates declare their frames** (`// frames: landscape` header). C8 refuses to build a template into a frame
  it is not laid out for. All current templates are landscape only; vertical layouts come with the film kit (M-D).
- **New stage `c8_audit` (`create audit <project>`).**
  - It runs every built scene in headless Chromium, seeks the timeline every 0.2 s, and records the boxes of
    visible text and logos (clipped by overflow masks, with ancestors' opacity).
  - Problems: a box outside every safe rectangle, or scene text in the caption band. Captions
    (`data-role="caption"`) and decoration (`data-safe-exempt`) are exempt.
  - Problems held under 0.4 s count as motion entering or leaving and are not issues.
  - Output: `projects/<p>/audit/safe-zones.json` (validated).
  - It uses `uv run --with playwright` like `scripts/hyperframes_answer_key.py`, so playwright is not a project
    dependency.

## Consequences
- **First run on Acme v2 (landscape, 9 scenes, 4719 boxes):** the "Example data" label sat 56 px inside the caption
  band in three scenes. It was moved above the band; the audit is now clean.
- Platform UIs change. The rectangles are config with a `source`, re-measured from the official files when they move.
- The audit checks placement only; overlaps between elements stay with `hyperframes check`.
- On a Mac, run the audit with `CHROMIUM=<path to Chrome or Chromium>`.

## Amendment (2026-10-09, after Robert's "it doesn't seem to fit")
- The vertical caption band was x 120–780, so its centre was x 450. Captions read as left of centre on a phone.
- It is now x 300–780: centred on the frame (x 540) and still inside the core's right edge, where TikTok's action
  rail sits below y 840. A test checks the band is centred and inside the core.
- `create pip --fit auto|cover|contain`:
  - Wide product videos are now contained (whole, at the frame's width, on the brand canvas, from the top of the
    safe area) instead of centre-cropped.
  - Open: a contained 16:9 product still runs under the side and rail zones at full width, and fitting it inside
    the safe area leaves no room for the corner bubble.
  - Vertical videos with landscape product footage need a split layout (product top, presenter bottom), or a
    vertical capture of the product.
