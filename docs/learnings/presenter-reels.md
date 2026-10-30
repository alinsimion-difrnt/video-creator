# Presenter TikToks playbook (learned on Robert's Budapest take, 2026-10-09/10)

Read this before editing any presenter video (Robert's own footage, vertical). It condenses what one night of
editing his first real take taught: his taste, the placement rules with numbers, the process that worked, and
the technical traps. Decisions: ADR 0025 (footage), ADR 0026 (reels). Plans: `docs/examples/reel-*.yaml`.

## 0. acme-reel (2026-10-17): the bespoke panel beat the kit (ADR 0034, skill build-panel)
- v1 (kit widgets, four review rounds, reviewers ~6/10). Robert: "boring… too narrow… nothing is of high
  quality… simple, useless animations… AI slop". His list: use the Acme logo; recreate a real ChatGPT chat with
  its logo; always use the real logos of companies named; the 1M euro must feel big; "2 other co-founders" means 3
  in total; real pint and coffee icons; clients like Decathlon and Flip; no pixel art unless asked; smooth,
  Apple-like motion; nothing on his face or mouth.
- v2 (one hand-built panel over a split base): "NOW, NOW THIS IS GREAT… amazing, compared to others." What
  changed: a different device per sentence (boarding pass, calendar, 3D cards, logo wall, hero count-up, service
  tiles, team photos, chat UI, flight map, intro graph); real assets fetched from his own sites; the full 1080 x 840
  area; text 40 px and up; frame-exact stills reviewed before the full render.
- Traps found: the kit's boxes sit inside TikTok's safe area (660 x 580) — narrow by construction; `create review`
  sheets showed each tile 1.25 s late (fixed); two `create reel` runs share one work folder (a render picked up
  another plan's page); difrnt.ro client logos are white (dark tiles); an animation's `from` offset must be reset
  in its `to`.

## The deliverable in one table

| Item | Value |
|---|---|
| Source | One phone take, 89 s, 1080x1920, HDR, variable frame rate, outdoors (Budapest), no external mic |
| Edit | 81.3 s after cuts; 24 shots, none longer than 5 s; the first shot ends by 2.3 s |
| Versions | Layout (product on top, Robert below) and overlay (widgets on his video plus 3 short cutaways) |
| Render | `create reel`, one HyperFrames pass: about 14 min per version then (PNG frames); ~6 min now (JPEG), ~4 min as a `--draft` |
| Sound | His voice cleaned and set to -14.1 LUFS, -1.4 to -1.6 dBTP; formula-made UI sounds 20 dB under the voice |
| QA | `create qa` 17/17 on both |
| Reviews | Five rounds of fresh-context review: layout went 6.5 to 7, overlay 5.5 to 6 |
| Client verdict | "That is, indeed, really great. Both are good." |

## a. What Robert wants (his words, then the rule)

- "The animations are not related to this tiktok in any way."
  - Every graphic shows what he is saying at that moment, word-timed: the query he speaks types in as he says
    it; the sources he names light up as he names them.
  - Never reuse another film's footage as the product half.
- The overlay version was "boring, as you only show some graphics that have no relevant animation."
  - Nothing sits still: cards build (typing, rows lighting up, stars filling, a chart drawing, a count-up, a
    click), drift slowly, and leave.
- "Captions are not great added, as they are on my chest or face."
  - Captions never overlap the presenter.
  - In full shots they go above the head, in the sky band y 300–500. In split shots they sit just above the
    seam.
  - `create qa` enforces this as `captions_clear_body`.
- Two product treatments, by video:
  - split: the product fills the top half and he moves lower;
  - overlay: animations on top of his own video.
- "You're still cutting my head (hair)" and "the circle is useless… only relevant if you actually do big complex
  animations" (seo-budget, 2026-10-17).
  - Split: the whole head, hair included, stays below the seam with clear room (seo-budget: `split_head_gap: 160`,
    seam 940; 90 still clipped). A hair estimate of 0.4 face-heights is not enough for him.
  - No pip (small circle) by default. Use it only for a big, complex full-screen animation that needs the frame,
    and then keep the bubble low and not zoomed in on the face.
- "Create a thumbnail that you add only as the first frame so it gets automatically picked by social media"
  (bing-topics, 2026-10-17): the cover is frame 1 of the delivered file (one frame, 1/30 s), audio copied
  with a 1-frame offset. Recipe in `projects/bing-topics/learnings.md`.
- He liked the cuts. Keep the pacing rules: no shot over 5 s; a visual change inside the first 3 s.

## b. Placement rules (vertical 1080x1920, TikTok)

- **Safe core:** x 120–780, y 288–1248. Above y 840 the safe area reaches x 888. TikTok's description text
  starts around y 1250.
- **Captions:**
  - Full shots: in `caption_top`, ending above the hair. The hair line is the face box raised by 0.4
    face-heights.
  - Leave room for zoom: the push-in and punch-ins grow the head upwards, so the caption also clears
    (face centre - hair) x (zoom - 1) plus 2.5x the gap.
  - Split shots: 16 px above the seam.
  - Cutaways: on top, with the card below.
  - Words not yet spoken stay at least 75% opaque.
  - On bright sky the captions need a tight dark halo.
- **Split:**
  - Seam at y 1040, with his face centre 190 px below it.
  - That clips a little hair at the seam, which split-screen TikToks do anyway.
  - Higher seams squeeze the product cards; lower ones put his mouth under the description.
  - He no longer accepts the clipped hair (seo-budget, ai-poisoning). His hair reaches about 0.9 face-heights
    above the detected face box, not the 0.4 the code assumes. When he sits close to the camera (ai-poisoning,
    4K take): `split_seam: 880` + `split_head_gap: 350`. At 940 with a gap of 160-320 the hair still touched
    the seam. Cost: his mouth sits ~88% down, under the description.
  - Full-face shots in a close take leave no room for captions above the head (hair near y 400 of 1920):
    they land on his hair at every punch-in crop, and `create qa` passes them (same 0.4 estimate). Use split.
- **Product cards:**
  - Lay out at 640 px and grow up to 1.6x into their box.
  - Boxes start 32 px below the safe top (a spring overshoot) and end 40 px above the seam captions.
  - Keep critical text off x > 780 below y 840.
- **Overlays:**
  - Make them dark brand cards. White cards vanished on his white T-shirt.
  - Stickers go beside the face only if the zone is at least 380 px wide; otherwise words wrap one per line.
  - Cards with content go on the chest, where they have room to be read. Beside the face they become too
    small.
  - Keep twice the margin from the face, because zooms move it.

## c. Motion rules that the reviews converged on

- **Entrances:** opacity fast and linear (0.1 s) while a spring (back.out) moves the card. A slow fade reads
  as a muddy grey ghost.
- **Exits** slide up and are done by the item's end time.
- **No empty cards:**
  - Rows, tiles and review text appear dimmed at once and light up on their word.
  - Numbers count up in whole steps as the card lands. An odometer read as broken glyphs mid-roll.
- **Hand-overs:** the next card lands only after the last has left; two cards never crossfade. In split, a
  product card holds until the next card or the layout move, so the product half is never blank.
- **A widget never starts during a layout move.** It waits for the 0.6 s move to finish.
- **Long holds feel dead.** Split anything over ~8 s into two beats, or give it a highlight beat.
- **Graphic and words must agree.** If he says "Budapest… Bucharest… New York", the answer lists all three
  as he says them. A reviewer caught the one card that said only Budapest.
- **End on the brand:** a logo card with the URL. The CTA must hold long enough for its URL to be read.
- **Punch-ins** (1.1x, full shots only) on key words, plus a 1.05 push-in per shot. The source had no zoom of
  its own; this replaced it.
- **Entrance styles** (`spec.motion`, 2026-10-11): rise, pop, slide, flip, focus, pixel. One style per kind of
  beat keeps a video coherent; untested with Robert so far.
- **Pixel art** (`kind: pixel`, `px:` icons): code-drawn sprites in the brand palette with a 3x5 pixel font
  (acme may use a topic palette instead, ADR 0031).
  On his video use `card: true` (dark tile, white frame); without it the ink outline is lost on dark shirts.
- **Grade:** contrast 1.08, saturation 1.14, a touch of warmth. The tone-mapped iPhone HDR source is already
  vivid, so stay light.

- **A long fx beat needs cuts, not one slow push** (Fred & Pixie r08-r09). Seven seconds of one slowly pushing
  frame reads as a still on a phone and on a contact sheet. Cut to a new shot on each new idea. Cut labels
  with the shot; a crossfade caught mid-way looks muddy.
- **A tag or bubble ends at the next cut** (`tag_cut_least_s`). Across a reframe it is stranded at the edge.

## c2. Flow (ADR 0033, Robert 2026-10-17)

Robert on the acme reels: "really simple considering everything that was built", "lackluster, repeating
from one video to another", no "flowing animation from one cut to the other". The rules that came out of it:

- **A plan names a motion style** (`motion: {style: paper | editorial | playful | terminal}`), chosen for the
  topic and different from the brand's last video; the reason goes in `# look:`. Code applies it to every
  widget, hand-over and cut. `classic` (no `motion:`) is the first take's look and stays for Acme.
- **Cards hand over, they do not swap.** The next product card is carried out of the last one: `morph` (one
  surface becomes the next card), `push` (the deck scrolls) or `stack` (cards pile up). The no-crossfade rule
  still holds: nothing fades into something else in the same place. 0.55 s per hand-over (measured card moves).
- **One step label per sequence.** Cards with the same kicker share it; only the step pill flips. Give a
  sequence one kicker and vary `step`.
- **The top half moves with the cuts.** The push-in alternates direction across cuts (no snap back), the
  background and the cards react to each cut, and a card whose word starts just after a cut enters on the cut.
- **Vary the entrance by style, not by whim.** Eight entrances exist (rise, pop, slide, flip, focus, pixel,
  wipe, unfold); the style picks one per kind of widget, a widget overrides for a reason.
- Still to see on his footage: whether `morph` reads on a phone at 0.55 s, and whether the 14 px nudge is felt
  or seen. Both are config numbers (`create.footage.reel`).

## d. Process that worked

Tooling since this take: `create prep` (edl -> reframe -> timing -> edit -> captions after the cut approvals),
`create words` (indexes to write against), the `draft-reel-plan` skill, `create reel
--check` (catches long holds, empty product areas, names said but not shown, text too small, widgets on the
face, under captions or outside the safe area — in ~2 s, before a render; a render refuses a plan with errors),
the UI sounds mixed in by `create reel` itself (`sounds: false` to skip), and `create review` with the
`review-reel` skill for the fresh-eyes round. A fresh agent drafted an overlay plan from the skill alone in four
check rounds (0 errors); its notes on what the skill left unclear are in the skill now.


1. Read the transcript with word indexes first. The plan is written against words, never times.
2. Make three genuinely different variants per type, each one plan file. Preview each with
   `create reel --preview` (seconds per sheet, no render), then render all of them.
3. Audit with contact sheets (one frame every 2.5 s) and motion strips (8 frames 0.1 s apart at entrances).
   Use your own eyes plus a fresh-context reviewer that sees only frames and the client's words.
4. Fix systemic issues in code, not in one plan. Then combine the best of the variants into one final per type.
5. Repeat render, review, fix. Scores plateau around round four or five, where the reviewers start
   contradicting each other (off the chest versus readable; face higher versus a bigger product area). Stop
   there and hand those trade-offs to Robert.

## d0. The flow from the phone (2026-10-11)
Robert: films on his own (no teleprompter, no script tool) and sends the full TikTok video in the chat.
Claude: process-take skill → `create cuts --page` (Robert taps, sends back one line) → `create prep` → two
reel-planner plans → render, `create qa`, `create review` + reel-reviewer → write-post, `create cover` → send.
Robert's touches: approve cuts, choose a version. TikTok only: build no other format (16:9, 1:1, LinkedIn,
YouTube) unless he asks for it.
Since 2026-10-23 (ADR 0035): he approved every proposed cut in 8 of 11 projects and kept back 1-3 in the
others, so he may decide the cuts in the message with the take ("cuts: all", "cuts: all, keep 0:41"):
`create take --approve [--keep 0:41]`, no cut page, no wait. The cut page stays the default otherwise.

## d1. Which setting is which (they look alike)
- `create.footage.reel.check.max_static_s` (5 s, plan check) is stricter than `create.qa.max_static_s` (6 s, the
  finished file): the plan leaves a second of slack for the render.
- `create.footage.reel.check.max_beat_gap_s` (6 s): one card showing nothing new.
- `create.footage.reframe.punch_in` (1.12) is F5's alternating crop between jump cuts; `create.footage.reel.punch_scale`
  (1.1) is a reel's quick zoom on a key word. They stack only if a plan punches during a punched-in shot.
- Plan defaults (ReelPlan): `split_seam` 1040, `push` 1.05, `sounds` true, `captions` top.

## d2. Speed and token cost (measured 2026-10-11, 4-core cloud sandbox, 81 s take)

| Render | Time |
|---|---|
| full size, PNG frame extraction (what the first take used) | ~850 s |
| full size, JPEG extraction (now the reel default) | 358 s |
| half size (`--draft`), PNG | 791 s |
| half size (`--draft`), JPEG | 255 s |

- Frame extraction was the bottleneck, not the page. JPEG is invisible on camera footage (presenter area PSNR
  43.7 dB), so it is the reel default. PNG stays the default for burn, pip and overlay, where screen recordings
  need exact colours.
- `--draft` saves another 30%: use it for review rounds and full size for the deliverable.
- The first take's 18 renders would take about 1.5 h now instead of 4 h; with `--check`/`--preview` catching
  plan errors first, fewer are needed.
- Tokens:
  - Run reviews and drafts as the `reel-reviewer` / `reel-planner` agents (a smaller model, their own context).
  - `create qa` and `--check` print only failures plus a summary.
  - Start a new session per video: the playbook, skills and commands now carry what this session learned.

## e. Technical traps found (all fixed; keep the tests)

- **GSAP tweening clip-path strings between poses gives garbage values.** A circle centre landed at y ~8000
  and the inset jumped, so the presenter vanished for 0.4 s in every split-to-full move. Clip shapes are
  built in CSS from numeric custom properties (`--top`, `--r`, `--cx`, `--cy`). Test:
  `test_layout_kits_never_tween_clip_path_strings`.
- **Every AAC re-encode raised the true peak:** -1.0, then -0.85, then +0.6 dBTP over three passes. Finish
  the voice once with a 4x oversampled limiter, then copy that audio through every later step (`mux`).
- **A commas-in-expressions bug.** An ffmpeg `aevalsrc` formula with a comma broke the lavfi parser; quote it
  (`exprs='…'`). Test: `test_every_sound_recipe_renders`.
- **HyperFrames lints a second root HTML in the project folder** (`multiple_root_compositions`). Preview pages
  live in `preview/` with a `<base href="../">`, and `build()` deletes that folder before a render.
- **YAML reads `off` as false.** Quote layout names.
- **Batch renders read the kit when each variant starts.** Do not edit kit files while a batch is running;
  stage changes in the scratchpad.
- **Python output piped through `grep` is buffered.** Use `python -u` and `grep --line-buffered` when
  watching renders.
- **Seek safety.** Avoid GSAP `onUpdate` for content: renders seek frame by frame. Use display toggles and
  transforms. `tests/test_motion_kit.py` scrubs every widget forwards, backwards and shuffled and compares
  every element's state; on its first run it found five real bugs. The rules it taught:
  - never two tweens on one property at once (a sticker's squash during its pop's scale);
  - never hide with `visibility`: it is inherited, and a backwards scrub restored a parent's "hidden" onto a
    child (a step label's card vanished). Hold opacity at 0 instead;
  - put every property in both states of a `fromTo` (a from-only opacity came back differently);
  - centre with GSAP `xPercent`/`yPercent`, not a CSS `translate(-50%)` that GSAP has to parse;
  - a container appears at t0 with an explicit tween, never a build-time `gsap.set`.
- **Stepped motion lands on whole frames** (`MK.fps` from the edit): one pixel row or shine diagonal per frame
  at most, so the render's frame sampling never skips or doubles a step.
- **Pixel sprites are fill-only grids.** Code adds the ink outline and the edge shading the same way on every
  sprite; shading inner colour boundaries read as speckle, so only the outer edge is shaded.
- **QA and the composer must share rules.** A caption's layout is judged at the group's midpoint in both,
  otherwise the checks disagree with what was placed.

- **A big, low face leaves no room for overlays** (ai-picks, 2026-10-17). With his chin near y 1100 the safe area
  had ~200 px above the head and ~150 px under the chin, and no room beside the face: chest cards sat on the
  beard and captions covered his hair on punched-in shots. Do the layout version, with every widget in the split
  product half after the hook; skip the overlay version for such a take (`overlay_box` now says "no room").
  Captions: `hair_above_face` is 0.6 now (0.4 grazed his hair); chest cards start `reel.chest_chin_gap` (0.15)
  face-heights under the chin. `caption_shirt: true` lets a caption with no air above the head sit on the shirt
  under the chin (Robert allowed it this time); QA accepts it only there.
- **Reviewers misjudge text size from the contact sheet**; check full-size frames before enlarging cards.

## f. What better input would give (for the next take)

- 4K source, so punch-ins stay sharp.
- Eyes about 40% down the frame with plain sky or wall above the head, waist-up and centred, on a tripod.
- A solid mid or dark shirt, not white, and a clip-on mic. Turn off iPhone HDR video.
- Concrete nouns spoken aloud (names, places, queries), numbered steps, half-second pauses between points,
  and lists said one item at a time.
- Real Acme numbers, screenshots or a screen recording, plus 5–10 s of B-roll for cutaways. The finals
  used invented example numbers and restaurant names.

- **Character takes (Fred & Pixie, ten rounds):** a stage for the character inside the safe area (left of
  the presenter, above y ≈ 1400). Palm-up holds of ½-1 s. One slow put-down with a ½ s hold at the lowest
  point. One locked crop through any action beat. Details:
  [`fred-and-pixie-take1.md`](fred-and-pixie-take1.md#direction-for-the-re-shoot).

- **Scripted beats + "explainer hybrid"** (google-ai-links, 2026-10-17): when Robert sends the beats with the take,
  make one plan (full for hook and caveats, split for the beats), skip the cut page if he says "cut the empty
  spaces", and put the cover on frame 0 so platforms pick it. Details: `projects/google-ai-links/learnings.md`.

## f2. Explainer hybrid (ai-mentions, 2026-10-17)
- "Explainer hybrid" is one version, not layout + overlay: full face for the hook and the "why", split with one
  product card per method step, full face for the closing question. Details: `projects/ai-mentions/learnings.md`.
- A card on screen from frame 0 is not a hook change (`hook_visual`): open on his face and split on the hook's
  key words.
- The split product box is ~660 x 490 px: a card with a kicker, 3-4 rows and a footer shrinks to ~0.65x. Keep
  rows to one line each, or let a chat's header carry the step title instead of a kicker.
- Rows must not wait for a late spoken example: land them on earlier words and the example last.
- Card footers: `footer` alone is a source line; with `footer_site` it is the brand footer ("method" left,
  acme.example right) and marks a way of working, not a cited source.
- Cover as the first frame: prepend the cover PNG as exactly one frame and delay the audio by one frame.
- `create cuts` reads "again" as a retake cue even in "again next month": read cue proposals before approving.

## g. Open items

- Robert to judge the formula-made sounds by ear; they were checked by level and spectrum only.
- Music under the voice is not done yet (the Acme v2 film used an ElevenLabs Music bed).
- The widget set is Acme-shaped (AI answers, sources, reviews). A new topic needs new kinds in `motion.js`.
- Cover as frame 0 (ai-poisoning): Robert wants the thumbnail as the first frame so platforms pick it. Done by
  hand (ffmpeg overlay on frame 0, audio copied); copy the render's `.meta.json` next to the shared file or
  `create qa` fails `captions_present`. Worth a `create cover --first-frame` mode.
- A Romanian take has not been edited yet. Captions and function words are per language; check the caption
  widths.
