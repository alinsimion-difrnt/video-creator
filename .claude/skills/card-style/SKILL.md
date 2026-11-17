---
name: card-style
description: Make a talking-head video TikTok-ready in the "card style" — the difrnt. YouTube look (calm rounded cards that build one element at a time beside the speaker, mask-rise lines, one accent as a state change, full-frame takeover slides) translated to 9:16 in white / yellow / black with one font (Montserrat). Split screen: an animated paper panel on top, the speaker below, a caption pill at the seam, a yellow takeover on the song's drop. Use when the owner asks for "the card style", "animations like the difrnt. video", "cards that build", or white/yellow/black animated graphics over a talk or a take.
---

# card-style

Measured from the owner's reference (a difrnt. YouTube video, 16:9, 86 s; screen recording studied frame by frame
on 2026-11-17) and built once end to end on a 65 s TikTok (a GEO talk, split layout, a song with a drop). The
starter is `create/kit/card-style.html`; the tool is `scripts/card_style.py`.

## 1. The look (what the reference does)
- Content lives on **cards** that sit still in the frame: no float or parallax. White cards (pure white, soft
  shadow) and near-black cards (white text).
- A card arrives in about 0.4 s, then its parts arrive **one at a time** on the speaker's words, 1-2 s apart:
  kicker, title, chips, rows. Nothing arrives all at once.
- Text lines **mask-rise**: each line is clipped and slides up from below in about 0.3 s, ease-out. No typewriter
  and no bounce anywhere.
- **Emphasis is a state change.** One grey row flips to the accent fill in 0.25 s, with its text going black and a
  small lift. One accent per slide; everything else is black, white or grey.
- Headlines are bold, **lowercase**, tight-tracked and left-aligned. Kickers are tiny, uppercase and wide-tracked.
- A **full-frame slide** sometimes takes over (the speaker is hidden) with a slow continuous drift of about 2% over
  3 s, so it never sits dead still.

## 2. The TikTok translation (what we ship)
- **Palette:** paper #F4F3EE, white #FFFFFF, ink #0B0B0B, yellow #FFD60A. Yellow replaces the reference's
  gradient as the one accent: marker sweeps, the flipped row, the active caption word and the takeover.
- **Type:** Montserrat only: 900 for heroes and h1, 800 for h2, chips and captions, 600 for body. The minimum on a
  phone is 36 px for kickers and chips and 44 px for any other text that carries meaning.
- **Layout (1080x1920):**
  - Panel: y 0-960 (paper, slow dot drift and a soft yellow glow).
  - Cards: 948 px wide at x 66. Each card is as tall as its content (at most ~610 px) and centred on y 512, which
    keeps it below TikTok's top tabs (y < 200) and at least 24 px above the captions.
  - Captions: y 848-952, a black pill.
  - Speaker: y 960-1920.
  - A 1080x960 window needs less upscaling than a full 9:16 crop: 1.6-2.3x on a 1080p wide shot instead of 2-3x.
- **Captions:**
  - 1-3 words, lowercase, 78 px (shrunk to fit), in a black pill centred on x 540, never wider than 696 px
    (TikTok's rail starts at x 888 below y 840).
  - The spoken word sits on a yellow box.
  - Glued phrases ("wall street", "mom groups") are one token.
  - Hidden during a takeover, because the slide says the words.
- **Takeover on the drop:**
  - The panel jumps to 1920 tall in yellow on the kick's frame, with a hero number (≤ 790 px wide, above y 840
    plus its line and a chip) and a slow 3.5% drift.
  - It retracts in 0.38 s (power3.inOut) on the next sentence.
  - Use it once per video.
- **Sound:** the page pushes cues (card, pop, swipe, hit, boom, whoosh), `render` saves them to `sfx_cues.json`,
  and the mixer places quiet synthesized sounds: card -33 dB, pop -31, swipe -30, hit -23, boom -20, whoosh -25.

## 3. Beat sheet (write it before the page, at the top of index.html)
- One scene per idea. For each beat, choose a device that shows **his words**:
  - a list that builds, with one row flipping;
  - a mock comment thread that gets struck;
  - a forum post whose question types in with the voice;
  - "X → Y" example rows;
  - a hero number counting up and landing on its word;
  - a progress bar that runs into the drop.
- **No invented copy.** Headlines, chips and bubbles are his words, or a two-word label of them. Placeholders stay
  grey skeleton bars.
- Alternate dark and white cards, and never use the same device twice in a row.
- Every time comes from `at("word", n, after)` on the word clock. A typo throws an error, so nothing renders off-beat.
- Long beats (over 6 s) get a second build step, so the card never sits finished and static for long.

## 4. Steps
1. **Edited timeline first.**
   - The words of the cut video with `t0`/`t1` (and `seg`), its `end`, and the drop time if there is a song.
   - Write them to `words.json` (format in the tool's docstring).
   - The base video has the speaker in y 960-1920; its top half is covered.
2. **Page.**
   - `uv run python scripts/card_style.py init <dir> --words words.json` writes the starter, GSAP, Montserrat and
     `data.js`.
   - Replace the example scenes using the primitives: `scene`, `rise`, `pop`, `fadeIn`, `markSweep`, `flip`,
     `typeWords`, `count`, `dimChip`, `takeover`.
3. **Layout gate.**
   - Run `uv run python scripts/card_style.py qa <dir>` until it prints `clean`. One-frame flags during transitions
     are fine.
   - It checks: text overflowing its card or the frame, text under the top tabs or in the right rail, collisions,
     and every card's height (`cards`).
4. **Stills.**
   - Run `... stills <dir> --base base.mp4 --at <one settled time per beat>`.
   - Give the sheets to a `lab-reviewer`, at most `create.footage.panel.review_sheets` images per round. Images
     never enter the main session.
   - Judge stills taken **after** each build lands. A still in mid-wipe will look "half-filled".
5. **Render.** `... render <dir> --base base.mp4 --audio mix.wav --out final.mp4` (≈ 10-15 min for 65 s at 30 fps).
   Then remix with the cues if they changed.

## 5. Learned the hard way (first build, 2026-11-17)
- **Measure only after `document.fonts.ready`.** The page builds inside it. Measuring earlier sized captions and
  cards with the fallback font: pills overflowed the rail and cards spilled into the captions.
- **Centre cards after every scene's content exists** (typed words and bubbles), not at load.
- On a dark card, a lower-half marker plus black text gives **black on black**. Use `.mark.box` (a full box) and
  turn the text black only after the wipe ends.
- To dim an earlier example on a black card, use an outline at 45% white, not a lower opacity. A 36% yellow reads
  as olive.
- Chips side by side overflow 832 px quickly. Put the example on its own line under a label ("kids' products →"),
  or use 36 px chips with a gap of 10.
- Choose line breaks in bubbles (`"|"` in `typeWords`). Never leave an orphan word.
- Keep the takeover number ≤ 790 px wide and centre the whole block. A block sitting high leaves 35% of the frame
  as empty yellow.
- With a wide master and an audience in shot, keep the speaker window's right edge clear of other people's faces
  (never half a face). The speaker may sit a little right of centre.
- One crop height per framing (tight / med / wide differ by ≤ 1.25x). A much wider last shot reads as a different
  camera.
