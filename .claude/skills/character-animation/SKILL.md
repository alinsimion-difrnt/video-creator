---
name: character-animation
description: Animate characters and props in a presenter reel (Fred the fish, Pixie the cat, any prop or effect in create/kit/props.js and fred.js) so they move like characters, not stickers, and test them on a stand-in reel with `create lab` (stock photo + ElevenLabs voice) before Robert's footage exists. Use when a reel's animation looks "strange", "clunky" or cheap, when adding a new act, gag, prop or effect, or when tuning 3D Fred (create/render3d). Holds the motion rules, the timing rules and the review loop, each learned from a lab render (docs/learnings/animation-lab.md).
---

# character-animation

Props are timed by Python (`create/footage/props.py`: tracks, moves, acts, carries, sprite schedules) and
played by GSAP in the page (`create/kit/props.js`, `create/kit/fred.js`). Python decides *when*. The page
decides *how it looks*. Read docs/learnings/animation-lab.md first: every rule below was a bug in a render.

## The loop: a lab reel, reviewed like an animator
1. Write a spec, `docs/lab/vNN.yaml`: a short script (8-25 s), a voice id and a `plan`.
   - The plan is a reel.yaml whose `word`/`until`/`marks`/`punches` fields are words of the script ("fish",
     "fish#2" for the second one).
   - Put the question it answers in the header comment.
2. `uv run create lab docs/lab/vNN.yaml --photo data/lab_photo_jb2.jpg --draft`. This gives you:
   - the plate from the photo (a breathing zoom, an optional `cut_at` jump cut) and an ElevenLabs voice
     with word times (cached);
   - the reel rendered at draft size, `data/lab/out/vNN-draft.mp4`;
   - motion strips, `vNN-study*.jpg`: 8 frames 0.1 s apart around every beat, cropped to the prop;
   - a green-edge scan of every frame.

   `--preview 2.1,8.8` renders single frames in about a minute for a quick look.

   **Once Robert has filmed, test on his take, in his voice** (ADR 0030; he asked for it). Instead of
   `script`/`voice`, write `take: {project: <p>, from: 85.6, to: 108.6, x: 0.555}`. That is a span of the
   master, cropped vertically around `x` (a share of its width), with his sound and Scribe's words.
   `--photo` is still required by the CLI and is ignored. Generated voices are only for narration he asks
   for (the black-hole explainer).
3. Review in this order (each layer finds what the others miss). **Usage:** images are the costliest input
   and every one you Read stays in context for the rest of the session. Read the data and the green-edge scan
   yourself; send the images to the `lab-reviewer` subagent instead (at most `create.lab.review_images` paths
   per version, only the strip pages and frames for beats that changed since the last version), with the
   spec's question and what you changed. Open an image yourself only to check one specific claim it made.
   - **Sprite sheets at 5-6x** (`create pixel …`, or composite frames yourself) for character design.
     At phone size you only see that something is off, not what.
   - **Study strips** for motion (arcs, anticipation, timing, overlap).
   - **A contact sheet of full frames** (12-18 evenly spaced) for placement, captions and the frame
     edges. Strips are cropped, so a prop near a strip's edge is not near the frame's edge: check a full
     frame before chasing a placement bug.
   - **The data** (`data/lab/<name>/data/create/<name>/render/reel/reel-data.json`): moves, acts, carry,
     t0/t1. When two things fight, the times show it.
4. Fix the cause in code (with a test when it is timing). Log what you saw, the cause, the fix and the
   lesson in docs/learnings/animation-lab.md. Render the next version.

A draft takes 3-8 minutes (3D frames are cached, `data/create/_cache/fred3d/<model hash>/`). Batch specs in
one background job and review one while the next renders.

## Acting in and out of the scene (Robert, 2026-10-13, after the Fred & Pixie r25)
Robert on r25: "the edits are strange... the animations are overused. Fred should have been doing stuff in
and out of the animation: exit, come in, do something, do it again, go away, maybe be smaller in the back and
do something there." A character is a performer with entrances and exits, not a sticker parked for a minute.
- **Give him scenes, not a seat.** Plan Fred as short acts (2-6 s), each with an entrance, one action and an
  exit. Between acts he is off screen. A minute of him parked at the frame edge reads as clutter.
- **Repeat with a variation.** Do the gag, then do it again bigger or wrong (the rule of three), then leave.
- **Use depth.** Fred can be small in the background (behind the chair, on the shelf) doing his own thing
  while Robert talks, then come forward for his beat. Scale and a softer contrast sell the distance.
- **Fewer effects, each earned.** One idea per beat. A burst, a sticker, a card and a prop gag on the same
  line cancel each other out. Cut until each remaining one carries a joke or a fact.
- Studies behind these rules: studies/pixel-art (character acting) and studies/tiktok (graphics density).

## Motion rules
- **Ground everything.** A contact shadow under each prop, shrinking and fading in the air, hidden in the
  boat. Props are graded like the plate (`.room { filter: var(--grade) }`). Without both, a prop is a sticker.
- **Anticipation before every action:**
  - a squash before a transformation;
  - the fins wind down before the clap;
  - a crouch before a hop;
  - the cat's pounce (crouch, butt wiggles, leap) before a grab;
  - the victim startles before it is grabbed.
- **Squash and stretch on contact:** hops land squashed; a drop is a stretched fall, a landing squash and an
  elastic settle. `bounce.out` is a ball, not a body (its first rebound is 75% of the fall).
- **Arcs, not yoyos:** a hop is up with `power2.out` and down with `power2.in`, with the shadow scaling.
- **Secondary and overlapping motion on separate layers:** breathing on the `<svg>`, sway on inner wrapper
  groups, acts on the torso. In a seeked GSAP timeline, a later tween of the same property freezes an
  earlier looping one.
- **Eyes act:** at rest they look at the camera. They look up only with purpose (a hat landing, the clap,
  briefly when named), then come back. A pupil parked at the top of a big eye reads as eye-rolling.
  Blinks come at irregular gaps.
- **Transformations:** a squash (t−0.12), seven small puffs that pop in for 0.07 s, the swap under them,
  then the puffs burst outward and fade in 0.3 s; a stretch and an elastic settle. The new look must be
  visible within about 4 frames. Big opaque clouds read as cotton balls.
- **Readable at phone size:**
  - items held at 1.45x;
  - limbs that break the silhouette (a limb inside the body outline reads as a mark on the belly);
  - nothing raised across a side-on face (it reads as a beak);
  - tags short (1.5 s).
- **Visuals lead the voice** by `props.lead_s` (0.07 s).

## Timing rules (props.py; tunables in `create.footage.reel.props`)
- **Travel:**
  - Gaited moves take their time from distance and speed (`speeds`, in body widths a second; at least
    `min_travel_s`, at most `max_travel_s`): feet never skate.
  - A walk that cannot arrive before a carry becomes a run.
  - A walker's move up or down more than `jump_rise` prop heights is a `jump`: an arc on the act layer,
    with its frames fitted to the move.
  - A move waits for any move still running. Legs of a path follow one another.
- **Carries:**
  - A carry happens on arrival plus the pounce (its frames' own length, `once_s`), never across the room.
  - Only moves up to the carry's beat count toward the arrival.
  - The carrier stops beside its prey, on its surface (`stop_short`, `approach`), and jumps if that is a
    climb.
  - The prey stays until it is snatched, even past its own `until`.
  - The carried prop is at most `carry_max` of the carrier and lies crosswise.
- **Exits and hits:**
  - Exits wait for the last beat. An exit with less than `min_exit_s` left is dropped (the prop stays, and
    the check warns `prop-exit-cut`).
  - `fade_black` starts after the last prop leaves and never ends before it starts.
  - shake, flash and glitch on a carry's word land on the grab.
  - Tags wait for the entrance (`tag_s` long).
- **Placement:**
  - Spots are clamped on screen in every shot of the stay, and above `safe_bottom` (TikTok's UI).
  - `behind` props are raised until `peek_share` of them shows outside the matte. The matte is in frame
    pixels, props in master pixels: map through the room (`room_at`). A test with identity rooms hides
    this.
- **Derivation:** times derived from other times flow one way. Compute the action, then everything that
  depends on it.
- **Animation lengths come from the frames** (`once_s`), never from a constant beside them.

## Styles of Fred
- `illustrated`: the SVG rig (fred.js).
- `pixel`: frames from create/pixel/fred.py (skill pixel-art).
- `toon3d`: frames from create/render3d/fred3d.py.
  - A ray-marched SDF model (smooth-unioned ellipsoids and boxes; wrap light, toon steps, rim, AO, soft
    shadows).
  - Animations: turn (a turntable played once as he becomes 3D: the proof he is a volume), idle, hop, wave.
  - Each accessory set renders once, in parallel (spawned workers, one BLAS thread each; four workers with
    default BLAS threads ran about 10x slower), written atomically, and cached under `fred3d.VERSION`: a
    hash of the code as imported, which workers check.
  - Pose = a few numbers (`Pose`); a new anim is a list of poses in `poses()`.
- Frame styles fall back to the rig while he rides the boat (the boat exists only in the rig) and in a
  carrier's mouth they show their idle frame.

## The presenter's body (pose, ADR 0030)
- `create/footage/pose.py`: BlazePose (local ONNX) gives 33 body points at 15 fps, cached.
- **`follow: hand`** (a beat): the prop rides the hand that reaches lowest in the span (the put-down hand,
  v22) and settles into the palm. It is released at the hand's lowest point and hops into the safe area if
  that is under TikTok's UI. Use it whenever he hands, takes or sets down a prop.
- **`automail`** (fx): gunmetal plates keyed to his joints. The default is Edward Elric's `right_arm` and
  `left_leg`; get a homage's details right. Pair it with `alchemy` under the chair. With `create matte`,
  the circle sits under his feet.

## Effects on the presenter
- Never touch skin colour: a hue grade turns people green. A code edit "recolours the video" with
  `caption_font {accent}` (the spoken word, tags and cards take the new accent).
- Anime: cel bands with hues kept (seven levels, soft), big eyes on the median face, speed lines, 2-4 s.
  Blocky: pixelated presenter, hearts and a hotbar; pixel Fred belongs in it.

## Lab pitfalls
- The plate's breathing zoom must stay ≥ 1, or the crop shows uninitialised (green) rows. `create lab` scans
  for this.
- A plan word that occurs more than once needs `#n` ("I#3"). The plan is validated after the voice: fix and
  rerun (the voice is cached).
- Queue renders in one background command (`for v in …; do create lab …; done`), not as a second job that
  waits on the first. `pgrep -f "bin/create lab"` matches the waiting shell's own command line, so the
  waiter waits on itself; use `pgrep -f "[b]in/create lab"` if you must wait.
- Media (the photo, voices, renders) stays in data/. Never commit it.
- `--preview t1,t2` before a full draft when the question is about one or two moments: a minute, not 3-8.
- After a round, ask a fresh-eyes reviewer agent to read the diff and *simulate* the timing code. Renders
  find what looks wrong; a review finds what is wrong but has not shown up yet (the audit found six such
  bugs, among them the coordinate-space one).
