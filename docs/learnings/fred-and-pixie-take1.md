# Fred & Pixie, take 1: ten rounds on the TikTok cut (practice for the re-shoot)

Robert (2026-10-12): "I will not post this one, as I want to film again. Work on the TikTok video as much as
possible until you improve your skills. Improve animation, cutting, design. Do screenshots of your final work
and see what is not right. Purpose: a better direction and a better workflow for when I film again." He also
said:
- pixel Fred over the drawn one;
- no pixel-art version of Robert;
- the tracking was wrong: Fred did not follow his arm and did not sit in the right place.

The project is `projects/fred-and-pixie-tiktok/` (the same take, `spans.yaml` → `cut-notes.yaml`). Plans are
`plans/rNN.yaml`. Every round:
1. render the full TikTok;
2. screenshot it (a contact sheet, motion strips, crops at full size);
3. run a fresh-eyes review (`create review` and the reel-reviewer agent);
4. write down what is wrong and why, fix the cause in code or in the plan, and render the next round.

## Before round 1: tracking and cutting

### Tracking: check it on frames, not in a render
- **Tool:** `scripts/pose_check.py` draws the skeleton, the hand points and both palms (green: from the hand
  model; orange: the body model's guess) on a contact sheet of real frames. Judge tracking there first: in a
  render you only see that Fred is off, not why.
- **What it showed on the put-down (104-106.6 s):** in the deep lean the body model collapsed onto his head
  and chest. The crop followed the last pose, so it shrank with a bad pose and never recovered. His hands were
  in plain sight the whole time.
- **What it showed on the fish beat (86-104 s):** the raised hand was found, but the lower, palm-up hand (the
  one Fred stands on) was not. Seen palm up, the body model's wrist, index and pinky are 15 px apart, so a hand
  crop sized from them was 60 px wide and showed nothing.
- **Fixes (create/footage/pose.py):**
  1. One fixed, generous body crop around the chair (a seated presenter in a static shot does not move).
  2. The MediaPipe hand landmark model runs on each hand at full resolution. The crop is placed from the
     body pose, then from the hand's own last points (MediaPipe's own tracking design).
  3. Hand crops are at least 1.5 face heights wide. When the body's hand points bunch together, four turns
     are tried and the most confident one is kept.
  4. Every frame is sampled (30 fps), with a median of 5 to drop single bad frames.
- **Result:** both palms are found in nearly every frame of both beats, including the lean.
- **New mode `follow: palm`:** Fred stands on the lower palm and moves with it through the style and accessory
  beats. `follow: hand` (the put-down) now rides the hand that reaches lowest.

### Cutting a short version
- **The tool:** a short version is its own project whose cut notes list `keep_only` spans. They are generated
  from word ranges by `scripts/short_spans.py`.
- **Bug in the first cut:** padding of ±0.2 s around each span pulled in the neighbouring words ("I've",
  "that", "so", "Like,") and dropped the "So" before "take a look". Spans now stop halfway to the
  neighbouring word.
- **Bug in the edit render:** 40 segments of one 4K master in one ffmpeg graph were killed (memory). Each
  segment is now its own seeked input. A test checks it stays frame-exact.

## Rounds

### Round 1: what the kit could already do (99.5 s, plan `plans/r01.yaml`)
- **Fresh-eyes review:** 5/10 overall, hook 3, pacing 4, gag clarity 4. "Would not post."
- **Works:** the transformation run (19-30 s). The photo fish lands on his palm, the 3D spin and pixel Fred
  sit between his hands, then the name tag, moustache and hat. Tracking holds.
- **Wrong, and why:**
  1. **Fred on Robert's knee for 40 s.** The put-down was right (the floor by his left foot), but the hop into
     TikTok's safe area put him on the knee: on this framing the floor right of the chair lies entirely
     under TikTok's bottom UI (it starts at y 1460, the UI at 1480) and the action rail. **Lesson:** a
     safety rule that moves a character must not move it somewhere meaningless. Where his hand puts him is
     the truth; frame the next take so the floor is in the safe area.
  2. **Pixie floats at shoulder height.** `floor_right` is measured in face heights, which does not fit a
     wide shot of a seated presenter. Then, once given a floor spot, `stop_short` aimed her at the plan's
     palm spot: carries were linked before the hand-follow keys existed. Follows now run first.
  3. **The hook (0-10 s) has only captions,** and the glitch is two bars for 0.4 s.
  4. **Black-hole silence: 7 s of a man sitting** (the explainer was not built yet).
  5. **Process cards:**
     - the shredder text came out 9 px tall on the chest;
     - the code card showed "font: font: mono" (its `to` is the value, not the line);
     - stickers clipped at the left edge.
  6. **No end card.**
- **Tooling found:**
  - `create review` failed on drafts: its crop zones are in full-size pixels. They are now scaled to the
    video.
  - The plan check's "static" warning ignores props.

### Round 2 (plan `plans/r02.yaml`): 5.5/10
- **Changed:**
  - Fred stays where the hand puts him.
  - Pixie gets a measured floor spot.
  - The hook: a Fred peek.
  - The process cards: a counter, stickers, the code card fixed.
  - Gag sounds: ElevenLabs effects through the plan's new `audio:` cues.
  - The black-hole cutaway with a 7 s narration (written for accuracy and length), Fred spiralling in.
  - The RIP card.
- **Seen:**
  - Pixie, Fred and the chase finally read: she walks on the floor, grabs him, runs left as Robert dives.
  - The black hole works, but turning the disk element tilted the whole ellipse. The gradient must spin
    inside a fixed ellipse.
  - Fred mostly stands in the corner. A jump is not a gag, and the reviewer could not tell what he "did".
  - His "100?!" bubble ran off the right edge.
  - Nothing happened in the first 20 s apart from one sticker.
- **Lesson:** a gag needs a prop the viewer recognises in a fraction of a second (popcorn, a camera, a
  sign). Acts like jump or spin only punctuate.

### Round 3 (plan `plans/r03.yaml`): 6.5/10
- **Changed:**
  - A cold open: cut notes `open_with` put "No!" and the lunge first, then a VHS rewind. Its words are said
    twice on the timeline.
  - Hook cameos.
  - Pixel gag items (`create/pixel/items.py`) on Fred's words, at his own pixel size.
  - `{frame: [x, y]}` spots.
  - Bubbles flip near the edge.
- **Seen:**
  - Gag-to-word relevance went from 5 to 8; the pixel set reads as one family.
  - Cameos placed in master shares fell off a face-following crop: a cameo needs a spot in the shot,
    hence `{frame: …}`.
  - The cold-open characters were too small to read in 1 s.
  - Unsaid caption words, dimmed by opacity, washed out on the light wall: opacity fades the outline too.
  - Fred and his items sit under TikTok's action rail.

### Round 4 (plan `plans/r04.yaml`): 6.8/10
- **Changed:**
  - Unsaid words are opaque and muted, with a stronger halo.
  - Bigger cold-open characters.
  - A `close_with` hold of the empty chair, so the RIP card can be read.
  - A safe-area credit line.
  - Gags in the 35-42 s gap.
- **Tried and dropped:** Fred hopping to "the floor between Robert's feet". Drawn in front of his shins, it
  read as his lap.
- **The framing lesson of this take:**
  - On a 9:16 crop of this wide shot, every bit of floor is at y ≥ 1460, under TikTok's bottom UI (1480),
    and right of the chair is the action rail.
  - A floor stage for Fred inside the safe area does not exist here, whatever the code does.
  - Next take: put the camera lower or further back, or sit left of centre, so the floor beside the chair
    is above y ≈ 1400 in the vertical crop. Or give Fred a stage at chest height (a side table, a shelf, the
    chair's arm).
- **Bug:** two transformation gags in a row (dog, bird) showed both Fred and the bird. The first swap's
  "back to Fred" fired inside the second. Swaps now end where the next swap begins.

### Round 5 (plan `plans/r05.yaml`): 6.5/10
- **Changed:**
  - A 2 s cold open ("Pixie, no!", Pixie bolts with Fred) and a louder rewind.
  - Gag items 1.5x (`gag_scale`); Fred bobs between gags (`idle: bob`).
  - A held zoom on "zoom in ... zoom out" (`zooms:`).
  - The cut tightened to 95 s: the fish beat ends on the put-down, the black-hole run-up starts at "allow".
- **Seen:** a plateau. Each fix exposed the next problem. The cold open showed an empty frame before the
  snatch. 10-20 s was still dead. A name tag hid under the captions. The black-hole labels sat in the UI zone.
- **Lesson:** past ~6.5, a score moves on the worst 5 seconds, not the average. Read the reviewer's
  timestamps first and fix the dead spans before polishing anything.
- **Tooling:** `scripts/plan_remap.py` moves a plan's word indexes to a new cut. Without it, every re-cut
  broke the plan by hand.

### Round 6 (plan `plans/r06.yaml`): 7.0/10, "almost postable"
- **Changed:**
  - Pixie starts with Fred already in her mouth (`carry` on the prop's first word is instant).
  - A filler line was cut ("and I will actually teach you this").
  - A sticker beat on "edit videos".
  - Name tags go beside the head when they would be high (`tag_side_above`).
  - Black-hole labels moved up and Fred made bigger.
  - Robert's pauses before Pixie were trimmed like any others (89 s).
- **Seen:** small dog/bird swaps left 60-67 s dead. The Pixie tag sat in the action rail. A ghost screenshot
  sticker crowded 37-45 s.
- **Open issue:** overlays arrive ~0.4 s late at the very start of a render (a render race). Workaround: the
  cold open starts 0.4 s earlier on a still frame. Not fixed.

### Round 7 (plan `plans/r07.yaml`): 7.0/10
- **Changed:**
  - Dog and bird 1.35x with "woof!"/"tweet!" bubbles.
  - Fred reads a pixel book (`book`, held) while the black hole is set up.
  - Tags near the right edge go beside the head.
  - The ghost sticker was removed and the spiral flattened.
  - The RIP card comes 1 s sooner.
- **QA:**
  - Loudness and true peak pass (-14.4 LUFS, -1.9 dBTP).
  - These fail by design: the draft frame size, a 7.1 s word gap (the black-hole narration), a 5.5 s tail
    (the card) and pacing at the black hole.
  - QA does not count narration or fx as activity; that rule change is Robert's call.
- **Seen:**
  - Bubbles and tags tiny on a phone; caption orange low contrast; the chest crowded at 37-57 s.
  - The black-hole frames repetitive; the code card small; the FMA beat brief.
  - A reframe jump at 34.7 s; Fred static between gags.

### Round 8 (plan `plans/r08.yaml`): 7.0/10
- **Changed:**
  - Tags and bubbles at 60 px over the room's scale. Tags near the right edge lift left (`.lift`).
  - A thicker caption stroke.
  - The API-key sticker and the bucket gag were cut: the censor bar and the bucket widget already say it.
  - The automail held to "look".
  - Widgets may grow 2x (`fit_up`).
  - The black hole swells and its stars drift.
- **Seen:** tags, captions and the code card now read on a phone. Pacing did not move: the black hole still
  showed three near-identical frames. One slow push over 7 s reads as a still. The chest is still the only
  place for cards.
- **Lesson:** a slow push is not motion on a contact sheet or on a phone. A long beat needs cuts: a new shot
  for each new idea, as an editor would cut.

### Round 9 (plan `plans/r09.yaml`): 7.5/10
- **Changed:**
  - The black hole cuts to a new shot on each label: wide, then a tilted close-up, then a low angle. Each
    shot has its own push.
  - Light streaks fall in on "not even light escapes".
  - Fred spirals inside the shot and is stretched on the "spaghetti" line, not before it.
  - Fred speaks in the quiet 75-82 s ("still here!", "that's...?").
- **Tried and dropped:** cards beside the face (`position: left`). The wall strip left of Robert is about
  300 px wide; the cards were squashed and clipped. On this framing, the chest is the only card zone.
- **Seen:**
  - The black hole now reads as three shots.
  - The censor bar sat on Fred's hat brim. The page's eye line (0.46 of the width) was measured on the old
    sprite, not the carp, and nobody re-measured it after the redesign.
  - The Pixie tag was stranded at the frame edge when the crop reframed on the lunge.
  - The label crossfade looked muddy.
- **Lesson:** every hard-coded anchor on a sprite (eye, hand, hat) has to be re-measured when the art
  changes. Better still, export the anchors with the sprite.

### Round 10 (plan `plans/r10.yaml`): 7.5/10
- **Changed:**
  - The censor bar sits on the carp's eye (0.66 of the width, measured on the sprite).
  - Black-hole labels hard-cut with their shot and pop in. There is a flash into space and back.
  - Tags and bubbles end at the next cut once they have been up for `tag_cut_least_s` (tested).
  - Fred looks up on "told Claude" and jumps on "Cloudflare".
  - The RIP credit is 48 px.
- **Still wrong, needs the re-shoot:** at 83.3 s the crop reframes to follow the lunge. Every overlay in
  master space jumps with it: Fred lands on Robert's knee and Pixie leaves the frame. An action beat needs one
  held crop, or a wider frame that does not have to follow him.

### The curve
| Round | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| Score | 5 | 5.5 | 6.5 | 6.8 | 6.5 | 7.0 | 7.0 | 7.0 | 7.5 | 7.5 |

- **Rounds 1-4:** big gains from structure: a cold open, gags tied to words, captions that read, an end hold.
- **Rounds 5-8:** polish moved single sub-scores but not the overall. Each fix exposed the next weakest
  5 seconds.
- **Rounds 9-10:** the black hole cut into shots, plus anchor and tag fixes.
- **The final reviewer:** "the fixes are real but small, and the footage is the ceiling." Its three
  footage changes for the re-shoot:
  1. a wider, lower frame with room for Fred above the UI;
  2. more physical energy (gestures, a lean, a standing beat);
  3. a darker, even background behind the captions, and short clean takes.
- **Left for the re-shoot:** the 12-20 s stretch is thin (one pill); the end-card credit sits near the
  description zone.
- **Not a problem:** the reviewer read the automail beat as "off-style clip art". Robert asked for that beat;
  it stays.

## Direction for the re-shoot

What ten rounds showed. Most of what held the cut at 7-7.5 was in the footage, not in the edit.

### Framing (the biggest lever)
- **Leave Fred a stage inside the safe area.** A 9:16 frame is 1080x1920. TikTok's caption and buttons cover
  y > ~1480 and the action rail covers x > ~900. On take 1, all the floor was under the UI.
  - Put the camera lower or further back, so the floor beside the chair is above y ≈ 1400 in the vertical
    crop.
  - Or sit left of centre and give Fred a stage at chest or knee height on the left: a side table, a stool,
    the chair's arm.
  - Fred's home should be left of Robert. The right side belongs to the UI.
- **Shoot for the vertical crop.** Or film vertical: a 4K landscape cropped to 9:16 leaves a 1215 px wide
  strip, and every card ends up on the chest because nothing else is free.
- **Keep the camera and chair locked.** Avoid big moves that force a reframe in the middle of an action beat
  (the lunge at the end). Overlays live in the master's space, so a reframe moves them all at once. If you
  need to lunge, lunge inside a frame wide enough to hold it.

### Hands (so Fred follows the arm)
- **Palm-up holds:** hold the hand still for a beat (½-1 s) at each pose: show Fred, style change, put-down.
  The hand model needs the palm in frame and not blurred.
- **The put-down:** one slow, continuous move to where Fred should stand. Keep the hand fully in frame. Hold
  it at the lowest point for ~½ s before lifting it away, because Fred is released at the lowest point.
  Move away from the spot after release.
- **Same hand every time.** Do not swap hands while holding Fred, and do not cross the hand over the body or
  the face.
- **Fast moves:** use 1/120 s or faster shutter (or film at 60 fps) so the hand is sharp in motion.
- **Check tracking before editing.** `scripts/pose_check.py` on the beat; the palms must be green (hand model)
  on every frame.

### Performance and script (for the cut)
- **Bring physical energy.** Use gestures, point at Fred, lean toward the camera, and add a standing beat.
  Seated and still for 40-52 s read as static, whatever the overlays did.
- **Use a darker, even wall behind the caption band, and keep the lamp out of it.** Captions on the pale
  wall needed a heavy stroke.
- **Say each gag line cleanly, then pause ½ s.** Gags are cut to words. A breath after "screenshots",
  "bucket", "free", "API key" leaves room for the item to land.
- **Keep the run-up to the explainer short.** The black-hole set-up ran 8 s of talk; aim for one line.
- **Film the cold open ("Pixie, no!") as its own clean take**, with Pixie's run toward the left.
- **The ending:** say the last line, then hold still for 2 s in the chair, then leave the frame. The end card
  needs a clean hold.

### Workflow that worked
1. `spans.yaml` (word ranges) → `scripts/short_spans.py` → `cut-notes.yaml` → `create prep`.
2. Write the plan, then `create reel --check` (fast; it catches word and spot errors).
3. **`create reel --preview t1,t2,…` at the risky moments before every full render.** A few frames in a
   minute, against ~20 min for a full draft. It caught the squashed left-side cards, the hidden light
   streaks, the spaghetti timing and the stranded tag before any render.
4. Full `--draft` → `scripts/reel_shots.py` → `create review` → the reel-reviewer agent. Read its timestamps
   and fix the worst 5 seconds first.
5. After any re-cut, `scripts/plan_remap.py` moves the plan to the new word indexes.

### Open issues in the tools
- Overlays arrive ~0.4 s late at the very start of a render (a render race). Worked around by opening on a
  still frame.
- `create qa` counts neither narration nor fx as activity. The black-hole narration fails "word gaps" and
  "pacing" by design. That rule change is Robert's call.
- Sprite anchors (eye, fin, hat) are constants in `props.js`. They should be exported with each sprite.
- The palm-follow keeps Fred at chest height over the torso for the whole fish beat (20-35 s). That is right
  for holding him, but it covers the gestures. On the re-shoot, hold him to the side, away from the chest.
