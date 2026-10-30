# Fred & Pixie: the variants tournament

Robert (2026-10-12), after round 10: "Its nice, but there are some issues. Like pixie looking the other way
while I try to catch him. [...] Learn everything, send to github repo. Now, try 10 completely random ideas and
variations for this build. Improve each 3 times, than make a leaderboard until something wins, and improve
that 5 times. You can play with anything, including video, sound, animations, etc."

## Before the tournament: Pixie and the catch (plan `plans/r11.yaml`, the base of every variant)
- **What was wrong:** Robert lunges to his left in both shots (the cold open and the end).
  - In the cold open, Pixie faced right and sat still until 2.5 s while his hands passed her. Her run off the
    frame was 0.2 s long, under the shortest allowed exit (0.3 s), so the code dropped it silently.
  - At the end, she took Fred from his right side and only ran once the lunge had started. To flee, she had
    to cross his whole body in a few frames.
- **What changed:**
  - **`follow: flee`:** the prop keeps `flee_gap` of its widths ahead of the leading hand (pose
    `lead_path`, median of 5), bolts at `flee_bolt` of its run speed on its own, for `flee_chase_s`, then
    runs off. A chase is keyed from the real hands, like Fred's put-down.
  - **Exits:** a dash shorter than `min_exit_s` is stretched to it, not dropped. An exit may run past its
    last word.
  - **The end, restaged:** she takes Fred on "cute cat" and strolls to his left during "I think I'll call it
    Pixie", so the lunge chases her.
- **Lessons:**
  - A chase has a direction. Read which way the presenter moves, then put the fleeing character ahead of
    him on that side. Staging comes before code: no tracking can rescue a cat on the wrong side of the
    man chasing her.
  - A validation that silently drops an action (the too-short exit) hides bugs. It should stretch the
    action or warn, never quietly do nothing.

## The ten variants

| id | idea |
|---|---|
| v01-doc | A nature documentary: letterbox, grain, Latin species lower-thirds, an orchestral bed |
| v02-arcade | An 8-bit game: a SCORE HUD that counts the gags, level cards, chiptune sounds, GAME OVER |
| v03-hyper | The faster cut: a separate project (`fred-and-pixie-hyper`) with filler phrases cut and tighter pads |
| v04-noir | Noir: Robert in black and white, Fred and Pixie in colour, grain and flicker, chapter cards |
| v05-thriller | A thriller: Pixie peeks in three times before her scene, stings, a heartbeat |
| v06-minimal | Minimal: Fred's story, three widgets, few sounds |
| v07-meme | Meme edition: vine booms with punch-ins, glitch hits, emoji reactions, a dramatic zoom |
| v08-anime | Anime: sparkly eyes on "I like this" and "cute cat", chimes, a dramatic zoom |
| v09-studio | Studio: a split screen with big product cards through the tech part |
| v10-sound | Sound first: the r11 picture with a music bed, foley for Fred and a riser into space |

New kit for the tournament: fx `look` (letterbox, vignette, grain, flicker, tint) and fx `hud` (a game counter
that changes on words).

## Method
- **Seed:** `scripts/tour_variants.py` writes each variant's `i0.yaml` from `plans/r11.yaml`.
- **Iterations i1-i3:** judged on 16-frame `--preview` sheets taken at the same moments for every variant
  (about a minute each, against ~17 min for a render).
- **Scoring:** after i3, each variant is rendered in full and scored by a fresh reel-reviewer on the same
  rubric. That gives the leaderboard.
- **The winner:** five more rounds with full renders and reviews.

## Round two: new ideas need new skills (Robert, twice: "are you actually making new ideas or just small changes?")

The first ten variants (v01-v10 above) were reskins of one edit: stickers, grades and sounds on the same
footage and plan. Their previews looked nearly identical, which was the honest answer to Robert's question.
They were stopped. The tournament restarted with ten ideas, each needing a capability the pipeline did not have:

| id | idea | new skill (where) |
|---|---|---|
| n01-hole | Robert is pulled into the black hole with Fred | the presenter's cut-out composited into a generated scene: it starts where he sat, is torn off the chair, passes behind the disk's near half, spaghettified (`blackhole` spec `presenter`; matte spans) |
| n02-pixelroom | the room turns pixel art when Fred does; Robert stays real | room-only effects: filter the plate, draw his cut-out over it unfiltered (`blocky` spec `room_only`) |
| n03-clone | an AI twin of Robert | a second presenter from his own cut-out at another moment (HyperFrames `data-media-start` trims into the clip), a one-colour hologram (`clone`) |
| n04-hands | the cards ride on his hand | widgets anchored to the pose-tracked palm, never above the chin (`hold: palm`) |
| n05-bullet | bullet time on "Pixie, no!" | the frame as seen, its depth from a local model (Depth Anything V2 Small, ONNX), a 2.5D camera swing rendered to a clip (`freeze`, create/footage/depth.py) |
| n06-beat | a beat-cut music video | a generated bed whose beats are measured in code; hits snap to beats, bars pulse, Fred bobs on the beat (`music`, create/footage/beatgrid.py) |
| n07-comic | a moving comic book | the footage drawn as a comic (filter, halftone on the presenter only), sound-word bursts, a comic-page recap whose panels are stills of the composited page (`comic`, `burst`, `panels`) |
| n08-wall | words painted on the slatted wall | a room surface measured in code (wood mask, fitted edges), a homography onto it, masked to the wood (`wall`, create/footage/surface.py) |
| n09-loop | a seamless TikTok loop | an edit that stops on the cold open's first frame (425.5 s), so the replay continues the action (projects/fred-and-pixie-loop) |
| n10-faces | Fred reacts word by word | an expression system for pixel Fred (shock, smug, terror, happy, angry) plus emotes over his head |

### What building them taught
- **Measure before drawing, even for art.**
  - The wall's plane comes from a colour mask and line fits, not from my eye.
  - The beat grid comes from the audio, not from the prompted BPM. It agreed anyway: 109.97 against 110.
  - Fred's eye line came from his sprite. Round 9's censor bar showed what a stale guessed anchor costs.
- **Expressions live where nothing covers them.** The moustache hides Fred's mouth and the hat his brow, so
  faces drawn there were invisible. At his size on a phone even the eye reads as a speck, so a big emote over
  the head carries the emotion and the face only confirms it.
- **The composited frame is an asset.** Comic panels and bullet time both need the moment as the viewer sees
  it, characters included. `stills()` (factored out of `--preview`) renders the page itself, and that becomes
  the input.
- **The sandbox has hard edges.**
  - Chromium refuses a CSS mask image from a `file://` page (inline it as a data URI).
  - librosa's numba beat tracker segfaults here; the Phase 1 audio tests crash for the same reason.
  - Previews never seeked the cut-out videos: one frozen Robert over a moving room. Fixed: each still now
    decodes the clip's own frame with alpha.
- **Concurrency.** `create reel --check` and `--preview` rebuild the project's render folder: two at once
  delete each other's frames. One preview queue for the project, and renders on a copy
  (`fred-and-pixie-tiktok-r`; its footage files and matte.json names carry the project id and must be renamed).
- **A render folder is single-use while a render runs.** The first n10 render scored 6.5 with "no expressions,
  no emotes". I had run two `--check` builds on the render copy during the render. They rebuilt its page at
  full size with another plan's data, and the renderer picked that up partway through. HyperFrames' own
  snapshot of the right page showed every face and emote on time. Rule: only the render queue touches the
  render copy, and a surprising review starts with checking the video against its page.

## The 9/10 push (base r12-r26, plans `plans/tour2/base/`)

Fifteen rounds, each reviewed by two fresh reviewers and averaged (scores in `data/fred/tour2/scores.md`).
Best: **r25, 7.6** (7.8 / 7.4). Every round landed between 6.5 and 7.6; r26 fixed what r25's reviewers named
and scored 7.25. The same render gets about ±0.3 from two reviewers, so late rounds move noise, not quality.

What really moved scores:
- Reviewing the full-resolution render (r20): half-size drafts made 66 px text "read" as 28 px.
- Filling silences with comic bursts on the wall (r22-r23) and punch-ins in the back half (r25).
- A real bug found by reading reviews against frames: since r18 the censor bar's `face` spot sat inside a
  trailing comment in `props.js` and fell back to the box corner, so the bar landed on Robert's lap (r24).

What stops a 9 on this take (the edit cannot fix it):
- Robert sets Fred on the floor at bottom right (34.8 s), so Fred, his gags, Pixie's catch and the "mew" all
  live under TikTok's rail and description. Moving Fred contradicts the footage.
- One locked medium shot for 67 s. Punch-ins help a little; zooms past ~1.12x crop Fred at the bottom edge.
- Reviewers judge from stills and scaled crops. They under-read text sizes (they called 44 px code 12-20 px)
  and misplaced the end-card credit twice, so chasing their sizes past ~64 px only crowds the frame.

For the re-shoot (to reach 9):
- Set Fred down on the chair arm or the side table on the LEFT, around y 900-1150, not on the floor.
- Leave the left third of the frame clear for cards, and keep hands below the chest when not gesturing.
- Shoot two sizes (wide and a medium close-up) or a slow push, so the edit can cut between them.
- Leave a beat of silence before "Pixie, no!" so the cold open reads without a mid-sentence caption.
