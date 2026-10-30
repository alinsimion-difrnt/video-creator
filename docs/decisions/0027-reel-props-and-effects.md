# 0027 — Reel props and effects: characters in the room, effects on the presenter, explainer widgets

- **Status:** accepted (Robert's idea, 2026-10-11; built and checked on a synthetic take the same day)
- **Date:** 2026-10-11
- **Milestone:** Phase 2, presenter reels (follows ADR 0026)

## Context
Robert wants a TikTok that shows what AI editing can do. He sits on a couch and talks about the project. During
the video:
- a fish appears on his lap ("Fred"), switches between 3D, illustrated and pixel art, and gets a moustache and
  a top hat;
- Robert turns anime and turns into a block person for a moment;
- explainer beats run: videos shredded into frames, "everything is code" (a colour and a font change live), the
  R2 bucket, and creator agents → reviewer agents → Robert's taste;
- at the end a pixel cat ("Pixie") grabs Fred and runs off, and the video fades to black.

There is no external editing and no video generation, and no pay-per-use API (CLAUDE.md). He gives the fish as
a PNG.

## Decision
- **Props in room space** (`ReelPlan.props`, create/footage/props.py, create/kit/props.js):
  - A prop is placed on the take's master. It is either a named spot by the presenter's median face (`lap`,
    `shoulder_right`, `floor_left` ... in face sizes, config `create.footage.reel.props.anchors`) or shares of
    the master.
  - The page has two room layers inside the presenter's zoom. Each edit segment gets one transform from master
    to frame (its F5 crop), so a prop stays on the couch through the push-in, punch-ins, layout moves and jump
    cuts.
  - Named spots are clamped on screen in every shot they span.
  - `create reel --check` warns `prop-offscreen` when a crop cuts a prop away.
- **Everything is timed from words.**
  - A prop enters as its first word starts and has left by the end of its last.
  - Beats change its style, add or remove accessories, move it, make it act (jump, spin, wiggle, look), show a
    name tag or a speech bubble, or have it carry another prop.
  - When it carries a prop, the carried prop leaves its spot and appears in the carrier's mouth, in the look it
    had at that moment.
  - Walk and run cycles play while the cat moves.
- **Art is code** (create/footage/props_art.py, Pillow and numpy, written into the render folder, never committed):
  - Robert's PNG is used trimmed, or with its plain background flood-filled away if it has no transparency.
  - `illustrated`: flat colours (median-cut palette) and an ink outline.
  - `pixel`: N cells across (config `pixel_cells`), a small palette and a one-cell outline.
  - `toon3d`: a height map from the blurred silhouette, Blinn-Phong lit, so it reads as clay or 3D.
  - The fallback fish and the cat are drawn in code. The cat is a 26 × 18 pixel grid with stand, walk, run and
    grab frames.
  - Accessories come smooth or as pixels, to match the prop's style.
- **Effects** (`ReelPlan.fx`), all timed to words:
  - `anime`: an SVG toon filter (posterise plus Laplacian ink lines), big eyes and blush on the face per segment,
    sparkles, and speed lines.
  - `blocky`: an SVG pixelate filter (sample a dot per block, dilate), pixel hearts and a hotbar of coloured
    blocks. No game assets or names.
  - `grade`: hue, saturation and contrast, tweened.
  - `caption_font`: the karaoke captions switch family (heading, body, mono).
  - One-shot hits: `shake`, `flash` and `glitch`.
  - `fade_black`.
- **Explainer widgets** in create/kit/motion.js: `shredder`, `code` (values retyped on their words; pair them
  with `grade` / `caption_font`), `bucket` and `agents`. "R2" appears as text with a generic pail icon.
- **Matte where needed** (`create matte`, stage f7_matte):
  - HyperFrames 0.8.137's `remove-background` runs u2net_human_seg locally through ONNX Runtime (CoreML on a
    Mac) and writes VP9 WebM with alpha. No API is called.
  - Only the spans the plan needs are cut out: props with `behind: true`, and anime, which puts its speed lines
    behind Robert. Each span is padded, cut frame-exactly from the edited video and matted on its own. The
    clips are listed in `data/create/<p>/footage/matte/matte.json`.
  - The reel shows each clip over the presenter (same grade and filters) only during its span, with the props
    behind it under it.

## Evidence (cloud sandbox, a drawn presenter on a couch, 21.7 s, two shots with a punch-in)
- Contact sheets showed all of the following:
  - Fred popping onto the lap.
  - photo → toon3d → illustrated → pixel.
  - The moustache popping in and the top hat dropping in, carried into the pixel style.
  - A "blub" bubble and the name tag.
  - Pixie walking in and carrying Fred, hat and moustache still on, then running off.
  - Anime with speed lines and blocky with its HUD.
  - A hue grade with the mono caption font.
  - The four widgets: frames grid, a retyped colour with its swatch, counts ticking, the agent loop with the meter.
- First-pass bugs found in the sheets:
  - The cat started below the frame. Named spots are now clamped on screen.
  - Name tags were placed below a prop on the lap, off the frame. They now go above it.
- Matte: 0.8 s a frame on the cloud CPU for u2net_human_seg. A 90 s take would take ~35 min whole, and
  span-only matting takes about a minute per 2-3 s span. The VP9 alpha tag is present (`ALPHA_MODE=1`).

## Consequences
- A plan can now say "the fish is on his lap, turns pixel on 'pixel', gets a hat on 'hat'". The planner skill
  (draft-reel-plan) lists props, fx and the new widgets.
- Named spots come from the median face. If Robert leans far during a prop's stay, the prop does not follow him.
  It stays on the couch, which is the point.
- Anime eyes use the segment's median face, so Robert should hold still for those 2-4 s.
- The cut-out quality is u2net_human_seg's: hair edges are soft. A prop peeking behind the shoulder reads
  well, but a prop tucked tight against hair would show the edge.
- Still open for Robert's eye: where `lap` lands on his real footage, the cat's look, the anime eyes on his real
  face, and the sounds for props (none yet; `create reel` adds UI sounds only for widgets).

## Addendum: upright Fred, the kitten, the alchemist (2026-10-11, Robert's second note)
- Robert asked for a Fred who sits on his tail, walks on it, uses his fins as arms, rows a boat through the
  air, reads, writes, texts and builds. That needs moving parts, so a PNG cannot do it.
  - `art: fred` is a rig drawn in SVG (create/kit/fred.js): tail, torso, head, a front and a back fin, each a
    group GSAP rotates about its pivot.
  - Accessories are drawn into the head, so they move with him and take his style. A steel fin and tail
    (`automail`) is one of them.
  - Activities (`hold`) loop until the next one: book pages flip, the pencil writes, the phone glows, the
    hammer builds three blocks.
  - `ride: boat` with `path` rows him through spots in the air. Without a boat he hops on his tail.
  - Styles are filters on the drawing: illustrated as drawn, toon3d (diffuse and specular lighting), pixel
    (the pixelate filter at w / `pixel_cells`).
  - His `photo` style is Robert's PNG, so the joke can start from a plain fish picture.
- Pixie is now a tiny kitten: a big head, big eyes and short legs, with the palette in the plan (`colors`). It
  is an homage to the kitten of Ben Hed's "Pixie and Brutus" (Pet Foolery). Text sources describe her as a
  tiny, joyful, oblivious kitten next to Brutus, a retired military German Shepherd. They do not describe her
  colouring, so the default palette is a neutral grey and Robert picks the colours. The drawing is original:
  no copy of the comic's art.
- Fullmetal Alchemist homage, for "a process that wouldn't cost me an arm and a leg":
  - In the series, Edward lost his left leg in the failed attempt to bring back his mother. He gave his right
    arm to bind his brother Alphonse's soul to a suit of armour, and wears automail (steel prosthetics).
  - Here, Fred gets `automail` (a steel fin and tail: his "arm and leg"), claps his fins together over his
    head (`do: clap`, Edward's circle-free transmutation), and `fx: alchemy` draws a transmutation circle
    under him with sparks and a flash.
  - The circle is an original geometric drawing (rings, a triangle, a square, ticks), not one from the series.
- Checked on the synthetic take with a contact sheet: the photo becomes the rig; toon3d, illustrated and pixel;
  a wave; the book, notepad, phone and hammer with blocks; the moustache and hat; automail with the clap and
  the circle; the boat along a path; the kitten walking in, grabbing Fred (he flails) and running off.

## CLAUDE.md lines (Robert applies; an agent may not edit CLAUDE.md)
In "Commands", after the `create reel` line from ADR 0026, add:
```
uv run create matte <project> [--plan f] (F7: presenter cut-out where reel props go behind him, ADR 0027) |
```
