# Animation lab: what twenty test reels taught (ADR 0029)

Robert's brief (2026-10-11): the demo "looks decent but" has a hum, an odd stand-in, and animations that are
"strange and clunky". The goal of this round is a skill, not a video: make test reels with `create lab`, review
each one like an animator, fix the cause in code, write down the lesson, and only then make one final demo.

Setup for every lab reel:
- **Photo:** "man sitting on brown armchair while taking photo of a cup" by John Beans, CC BY 2.0
  (flickr.com/photos/147592390@N06/33716260428), via Openverse. It is media, kept in data/ only, never
  committed.
- **Voice:** ElevenLabs "Chris – Charming, Down-to-Earth" (premade), with-timestamps. Word times are real.
- **Review:** a contact sheet, motion strips (frames 0.1 s apart around each beat, cropped to the prop), and
  for some rounds a fresh-eyes reviewer agent that sees only frames.

## Log

### v01 — baseline (the earlier demo plan on the photo and the voice)
- **Seen:**
  - Fred sits on the shin: "lap" was tuned on a drawn figure (3.1 face-heights down).
  - Nothing grounds him: no contact shadow, so he reads as a sticker.
  - Props were not graded like the plate, so they are more saturated than the photo.
  - A green line flickers on the top edge.
  - Style changes cut instantly; toon3d barely differs from illustrated.
  - Pixie's run-off is about four frames: a glitch, not a run.
- **Causes found in the data:**
  - The exit run started at 29.18 s, but the walk to Fred ended at 30.02 s and the grab was at 29.76 s, so
    two tweens fought over Pixie's position.
  - Walk and run durations were fixed, not from distance, so the feet skate.
  - The breathing scale produced odd frame sizes, hence the green chroma line.
  - Reading the code against the animation principles found:
    - no anticipation anywhere;
    - hops as a straight up-down yoyo, not arcs;
    - no secondary motion (only breathing);
    - eyes that never look at anyone;
    - blinks on a metronome;
    - every beat exactly on its word.
  - A torso squash after the breathing tween started froze the breathing forever. In a GSAP timeline a
    later tween's end value wins whenever it is re-rendered on a seek, so layer the properties instead.
- **Fixed (v02):**
  - Contact shadows that shrink while a prop is in the air; props graded like the plate.
  - The lap re-measured (2.45 face-heights; real thighs).
  - Even frame sizes in the breathing.
  - Gait speeds in body widths a second (`props.speeds`); exits wait for the last beat.
  - Visuals lead the word by 0.07 s.
  - A transformation is squash, then a puff of smoke hiding the swap, then a stretch and an elastic settle.
  - Hops are arcs with a crouch, a stretch and a landing squash.
  - Fins sway on their own layer; breathing lives on the `<svg>`.
  - Eyes look up at the presenter and at the camera when he is named; blinks are irregular.
  - The clap winds up first; Fred squashes when the hat lands.

### v02 — the first motion pass, rendered
- **Seen:**
  - Better grounded and softer, but Pixie still reached the lap after the grab, and her exit overlapped the
    walk.
  - She stood under the TikTok caption and button area at the bottom of the frame.
  - The fade to black started while she was still grabbing.
  - The smoke puffs came out above Fred's head, not around his body.
  - The style flashes were blinding: a peak opacity multiplied by 3 in the kit.
  - The automail flash wiped the style filter (a CSS `filter` on the same element).
  - Toon3d still read as "illustrated, but darker".
- **Fixed (v03):**
  - The carry waits for the arrival: carry time = max(word, end of the last move). A walk that cannot arrive
    in time becomes a run (`g_now`).
  - The exit waits for the last beat; `fade_black` starts 0.25 s before the last prop leaves.
  - Spots are clamped above `props.safe_bottom` (master px mapped per room), clear of the TikTok UI.
  - Puffs ring the body's centre; flash peaks are the opacities themselves.
  - The automail flash sits on the rig's parent, so it never overwrites the style filter.
  - **3D for real:** create/render3d/sdf.py ray-marches smooth-unioned ellipsoids with numpy (wrap light,
    toon steps, rim, AO, soft shadows, 2x supersampling, active-ray compaction: ~4 s a frame).
    create/render3d/fred3d.py models Fred (forked tail, fins hinged at the shoulder, hat, moustache,
    automail). The `toon3d` style is now frames, like pixel: a turntable as he becomes 3D (proof he is a
    volume), then idle, hop and wave. Frames are cached by a hash of the model's source.
  - Path legs follow one another: the old `bs + k * leg` overlapped legs whose speeds made them differ.

### v03 — 3D Fred, rendered; a craft pass on the sprites
- **Seen:**
  - The turntable reads: one spin as he becomes 3D tells the viewer he is a volume, not a filter.
  - 3D Fred filled half his box, so he looked smaller than his other styles.
  - The moustache was two black dots.
  - The poof was a huge opaque cotton ball that hid him for about 0.4 s, the same on every change.
  - Pixie walked onto Fred and stood in front of him before the grab.
  - Her name tag drifted over his face as she moved toward him.
  - Sprite sheets at 6x showed the real problems with the characters:
    - Pixie's eyes were small squares at the edge of a profile head;
    - the shaded half of her head (her face, since the light is top left) was a muddy mauve;
    - pixel Fred's near fin sat at mouth height and read as a duck's bill;
    - his ray-striped fins and tail were noise at 40 px.
- **Fixed (v04+):**
  - 3D frames are framed like the rig (tail on the box's bottom edge).
  - A handlebar moustache with curled tips.
  - Poof: seven smaller puffs that pop in for 0.07 s, then burst outward and fade in 0.3 s.
  - `stop_short`: a carrier's last move ends beside its prey, its mouth at the prey's near edge.
  - Tags last 1.5 s.
  - Pixie:
    - a three-quarter face with big dark eyes, a 2x2 shine on top and the light-blue iris below;
    - a happy-arc blink;
    - a softer fur ramp (`_soft`: the first shade step halfway to the base);
    - the head lit nearly flat.
  - Pixie got a **pounce** (crouch, two butt wiggles, the leap, the landing) that plays into every carry.
    It replaces the generic squash: anticipation the viewer can read.
  - Pixel Fred:
    - fins on the silhouette's edges, below the mouth; no ray stripes; a black hat;
    - he waves with the far fin up behind his head (side on, any raised near fin lies across his face);
    - the "clap" is a cheer: the far fin up, the near fin punching forward;
    - hops fling the fins outward.
- **Lessons:**
  - Judge characters on a 6x sheet before judging them in a video; at phone size you only see that
    something is off, not what.
  - A limb reads only where it breaks the silhouette.
  - A pale base colour needs a gentler first shade step than the ramp maths gives.
  - The light direction is a design decision: a face turned away from the key light needs flatter shading,
    or the cute side of the character is the dark side.

### v05 — Fred's day (hops, book, pencil, phone, hammer, a boat path, 3D on the way home)
- **Seen:**
  - The drop entrance uses `bounce.out`, whose first rebound is 75% of the fall, so he rebounds like a
    rubber ball.
  - The book, pencil, phone and hammer are drawn at fin scale and can't be read on a phone.
  - His pupil sits at the top of a big white eye most of the time. That reads as eye-rolling, not as
    looking at the presenter.
  - "In 3D" during the boat ride swapped him to 3D frames, and the boat (drawn only in the rig)
    vanished: he hung in mid-air.
  - The study crop made him look off-screen once. The full frame showed he wasn't, so check a full
    frame before chasing a placement bug.
- **Fixed:**
  - Drop: a stretched fall (power2.in, 0.32 s), a landing squash, an elastic settle, dust on the landing,
    and the shadow growing as he nears the ground.
  - Items show at 1.45x about their own centre.
  - Eyes rest on the camera; he looks up only with purpose (a hat landing, the clap, briefly when named),
    then back at us.
  - `riding_at`: while he rides, frame styles fall back to the rig, which carries the style's filter.
- **Lessons:**
  - Library eases are designed for UI, not for characters: bounce.out is a ball, not a body. Build
    landings from a fall, a squash and a settle.
  - Every prop drawn in only one representation (the rig's boat) is a trap for the others.

### v04 — the process beats (shredder, code edit, R2 bucket, agents) and Pixie from the left
- **Seen:**
  - The "one line of code changes the colour" gag hue-rotated the whole frame: the presenter went green and
    purple. It is the ugliest frame in the series.
  - Pixie ran toward Fred, and both vanished before the grab. In the data:
    - Fred's own exit (the end of "not") came before the grab, which waits for her arrival;
    - her run to the lap started while her walk-in was still running, so two tweens wrote one position;
    - the shake hit on the word, 0.5 s before the grab it was meant to punctuate.
  - The widget cards sit small in the product area (pre-existing; noted, not this round's subject).
- **Fixed:**
  - Captions colour the spoken word with `var(--cap-active)`. `caption_font {accent}` recolours the brand
    accent (spoken word, tags, cards) as the code edit types. The skill now says never to pair a colour
    edit with a hue grade.
  - A move waits for any move still running.
  - The victim stays until it is snatched (`t1 = carry time`).
  - shake, flash and glitch on a carry's word land on the grab.
- **Lessons:**
  - Times derived from other times (an arrival, a grab, an exit) must flow one way: compute the action,
    then everything that depends on it.
  - An effect that touches the presenter's skin is almost always wrong. Change the graphics, not the
    person.

### v06 — anime mode, blocky mode, Pixie dropping onto a shoulder
- **Seen:**
  - Blocky mode reads at once (pixelated presenter, hearts, a hotbar), and pixel Fred belongs in it.
  - Anime mode was a garish posterize: five levels per channel shift hues independently, so skin went
    orange and the walls green.
  - Pixie "on the shoulder" floated in the air beside his head: the shoulder spot was 1.25 face-heights
    below the face centre, but a seated person's shoulder line is lower.
  - A thin green line on the frame's top or left edge, around 2.0–2.7 s in **every** lab video. Cause: the
    plate's breathing zoom `1 + 0.006 sin(...)` went below 1 for half of each cycle, so the crop asked for
    more pixels than the scaled frame had. Uninitialised YUV is green. (The v01 note blamed odd sizes;
    that was half the story.)
  - Captions sat over the face: this photo has no headroom above the head. Robert's framing should leave
    some; the reel check flags it.
- **Fixed:**
  - Anime: seven levels on a softer image (blur 2.2), lighter ink, saturation 1.18. It now looks like cels
    with hues kept.
  - Shoulders at 1.55 face-heights.
  - The breathing zoom is always ≥ 1.008.
  - `create lab` now scans every render for green edge rows or columns (`lab.green_edges`) and warns.
- **Lessons:**
  - A glitch that shows at the same time in every video is in the shared plumbing, not the content.
  - Measure it across the whole video (a frame scan), not by eye on a few stills.

### v07 — 3D first with accessories, the automail flash, alchemy, Pixie's pounce
- **Seen:**
  - The smaller poof works: the new look shows by the third frame.
  - The turntable and the 3D accessories work, and the automail flash reads.
  - The pounce and `stop_short` work: she stops beside him, crouches and leaps.
  - In 3D, a new hat or moustache simply appears on the next frame. The rig's hat drop is hidden behind
    the frames, so the gag has no landing.
  - The snatched Fred was full size and upright, in front of her face: he read as standing beside her, not
    as being carried.
  - The render took 54 minutes: 102 3D frames at ~50 s each. Four pool workers each let numpy's small
    matrix products start a BLAS thread per core (oversubscription), and the cache key read the model
    source from disk at call time, so a running process could file old-code frames under the new key.
- **Fixed:**
  - With a frame style, an accessory added mid-stay gets a landing: a squash, an elastic settle and
    sparkles.
  - A carried prop is at most 0.7 of the carrier and lies sideways in the mouth (rotation −72° about the
    bite point).
  - 3D speed:
    - spawned workers with one BLAS thread each;
    - float32;
    - tetrahedral normals (4 scene evaluations, not 6);
    - 14 shadow steps;
    - no rotation matmul for unrotated primitives.

    That is about 2.5x faster per frame, and parallel.
  - `fred3d.VERSION` is hashed at import, so the key always matches the code that rendered.
- **Lessons:**
  - Every representation of a character needs every gag's beat. When one representation cannot animate
    a beat, give the container (the act layer) the beat.
  - A cache key must describe the code that produced the value, not the code on disk.

### v08 — a recoloured Pixie on the shoulder, a dance, a speech bubble, pixel Fred carried off
- **Seen:**
  - The white-and-grey Pixie (`colors`) with amber eyes and a blue bandana is still clearly Pixie. The
    recolour keeps the character.
  - The shoulder perch now sits on the shoulder line.
  - Shoulder to floor, she *walked* diagonally down through the air.
  - The grab happened from the floor while Fred was on the lap. `stop_short` had moved her beside him in x
    but left her at floor height.
  - The sideways carry reads as a cat with a fish. But pivoted at his end, the fish lay across her head.
- **Fixed:**
  - Moves with a height change of more than half the prop's height become a `jump` gait:
    - the kitten's crouch, then the leap held in the air, then the landing (`jump` frames);
    - an arc on the act layer (power2.out up, yoyo down), the shadow shrinking under it;
    - speed `jump: 2.6` body widths a second.
  - `stop_short` puts the carrier on the prey's surface too (its y).
  - The carried prop is centred on the mouth, at most 0.55 of the carrier, lying crosswise (78°), head
    forward.
- **Lessons:**
  - "Beside" is two coordinates. Every helper that places one character relative to another must set both.
  - Pick the gait from the geometry of the move, not only from the character.

### v09 — a drawn fish swims through, 3D Fred carried off; v04 re-rendered
- **Seen:**
  - The swimming fish (`art: fish`, idle swim, swim exit) reads, though it is small at 0.16.
  - A carried 3D Fred shows his 3D idle frame crosswise in her mouth, and the jump from the floor to the
    lap works.
  - Pixie's name tag popped while she was still walking in from the edge, so the frame cut it to "xie".
  - v04 again: the accent recolour works. The spoken word and icons turn green with the typed value; skin
    is untouched.
  - The timing chain is now right, but her walk-in plus the run left the grab 0.4 s before the end. The
    exit run got 0.06 s, two frames: a glitch.
  - The explainer cards are still small inside the split's product box (tall cards, height-limited).
    That is outside this round; noted for the widget work.
- **Fixed:**
  - A tag waits for the entrance to finish.
  - An exit with less than `props.min_exit_s` (0.3 s) left is dropped: the prop stays to the end, and
    `create reel --check` warns `prop-exit-cut` ("start its beats earlier").
- **Lessons:**
  - When there isn't time for an action, cutting it is better than squeezing it.
  - The check should say so, because the real fix is in the plan.

### v10 — quick-fire styles (3D, flat, pixel, 3D again, a moustache, a wave)
- **Seen:**
  - Four transformations in four seconds still read as four, each with its own short poof.
  - The 3D moustache lands with a squash (v07's fix).
  - The second "3D" played the full turntable again. The spin is a reveal, and a second one repeats the
    joke.
- **Fixed:** the turntable plays only the first time he becomes 3D. Later 3D spans start on the idle.

### v11 — the accessory parade, then Pixie takes the crown
- **Seen:**
  - Sunglasses, a crown over the top hat, and a bow tie all read at phone size.
  - "Lose the hat" clears it.
  - The "Queen Pixie" payoff never lands: her exit starts right after the grab, so the tag leaves the
    frame with her.
- **Lesson (plan, not code):** a payoff needs a beat of stillness. Give the winner `exit: none`, or put
  her exit after the line.

### v12 — final candidate A (the original script, every fix so far)
- **Seen:**
  - It holds together end to end: the fish photo, the 3D spin, pixel, the "Fred" tag and wave, the hat
    landing, automail, the alchemy circle, the phone, Pixie walking in, the pounce, the crosswise carry,
    the shake and the fade.
  - Zoomed in, the phone reads (a steel fin holding it, eyes on it); at thumbnail size it is a small
    yellow card near his face, which is acceptable.
  - **Pacing:** nothing happens for the first 5.7 s ("Hi, my name is Robert, this video is entirely
    edited by AI") except captions. On TikTok the first second is the hook.
- **Next:** v13 tries a hook-first script. The fish appears on the first sentence and the open is cut to
  one line.

### v13 — final candidate B: hook first, 22 s
- **Seen:**
  - The fish is on screen by 1.3 s ("This fish is AI.") and the styles come fast. It is a much better
    first second than v12's.
  - The cat payoff got rushed: she enters on "cat" and grabs on "no" two seconds later, so her walk
    becomes a run and there is no "cute" beat before the betrayal.
- **Lesson:** cut setup, never the payoff's build-up. The final takes v13's open and v12's cat beat ("What
  is this cat? Cute. I'll call her Pixie.").

### v14 — the long version with the process as one cutaway
- **Seen:**
  - The process (shredder, code edit, bucket, agents) ran as one 15 s cutaway of white cards: no presenter,
    no Fred. It feels like another video.
  - The skill already says to keep cutaways to 2-4 s; the plan broke its own rule.
- **Lesson (plan):** split the process into short cutaways, with the presenter and Fred reacting between
  them. Or keep the demo on the characters and leave the process for its own video.

### v15 — Pixie behind the presenter (the matte)
- **Seen:**
  - The matte works on the still plate.
  - At the shoulder spot, the presenter's own silhouette hid all but a sliver of her: "behind" read as
    "missing".
- **Fixed:**
  - `matte.alpha_at` reads the matte's alpha at a frame.
  - `props.peek_y` raises a behind prop until `props.peek_share` (0.5) of its box shows outside the
    person, so she peeks over the shoulder. It is measured, not guessed, and checked against a synthetic
    mask.

### v16 — the boat while 3D
- **Seen:**
  - The fallback works: no floating 3D Fred.
  - But the stand-in rig with the old clay filter was pale and washed out, so it read as a different
    character from the saturated 3D frames.
- **Fixed:** the clay filter's highlight is softer (k2 0.9 → 0.35), and its saturation is lifted 1.3x.
  The stand-in now matches the 3D frames.
- **Lesson:** a stand-in must be matched to what it stands in for. Compare them side by side, not from
  memory.

### v17 — v15 again with `peek_y`
- **Seen:** Pixie now peeks over the left shoulder from behind, her head and ears above the shoulder line
  and her body hidden by him. "Behind" reads as behind. She turns to camera on "feel".

### v18, v19 — final candidates C and D
- **Seen (C):** v13's hook with v12's cat build-up. The cat now has "What is this cat? Cute. I'll call her
  Pixie." to walk in, look and be named before the betrayal.
- **Seen (D):** C plus a matched transformation. When Fred goes pixel, the presenter goes blocky (hearts,
  a hotbar) for the beat. Pixel Fred standing in a blocky world is the strongest single frame of the
  series.
- **Choice:** D's structure, plus v17's peek on "wait", becomes the final (v20).

### v20 — the final demo
- **Plan:** v19 plus v17's peek on "wait". Pixie peeks over his shoulder from behind, pops away, walks in
  from the right, is named, pounces and grabs. The shake hits on the grab, then the fade.
- **Rendered:** `data/lab/out/v20.mp4` at full size (1080×1920), after the audit's fixes. Media, never
  committed.
- **First full render:**
  - With the audit's pounce fix, the grab correctly comes after the pounce, about 24.1 s.
  - The lab's 1.4 s tail then left no time to run off: she stayed (`prop-exit-cut`) and the fade began in
    the last 0.4 s.
  - `create.lab.tail_s` is now 2.4, and the final was re-rendered.
  - For Robert's cut: keep about 2 s after "Pixie, no!". `create.qa.max_tail_s` (1.5) will flag that;
    see ADR 0029's follow-up.

## The audit (a fresh-eyes code review of the round)
A reviewer agent read the whole diff and simulated the timing code. It confirmed six bugs I had not seen in
any render:
1. **`peek_y` measured in the wrong space.** The matte is in frame pixels and props are in master pixels.
   That is right only when the room transform is the identity (the lab's first shot), and wrong for any
   real take. Now mapped through the room.
2. **The kitten's jump looped.** Short jumps never reached the landing frame; long ones crouched again in
   mid-air. Jump windows now *fit* their frames to the move.
3. **The pounce played over the end of the walk.** The carry time equalled the arrival, so the pounce
   window overlapped the walk tween and she skated. The grab now waits for arrival plus the pounce's own
   length.
4. **A carry could be timed and placed from beats after it.** The max over all moves included later ones,
   and `stop_short` then rewrote a move away from the prey. Only the moves up to the carry's beat count
   now.
5. **`stop_short` changed height but not gait.** A walk could still climb through the air. It now becomes
   a jump.
6. **The accent recolour reached the captions only.** It was set on `#stage`, while tags and cards live
   elsewhere. It is now set on `#canvas`.

It also flagged, and these were fixed:
- a race between two runs sharing the 3D cache: frames are now written to a temp file and moved into
  place;
- the cache key could disagree with a worker's re-imported code: workers now assert `VERSION`;
- a fade with an early `until` could end before it started;
- `alpha_at` could read a matte made for an older plate: it now checks the plate stamp;
- the exit run sloped from the old height.

Rule fixes:
- the thresholds this round introduced moved to config (`min_travel_s`, `jump_rise`, `approach`,
  `carry_max`, `tag_s`, `create.lab.*`);
- `POUNCE_S` and `TURN_S` became `once_s()`, measured from the frames themselves;
- the lab's brand project is configurable.

Every fix has a regression test.

**Lesson:** renders find what *looks* wrong. A review that reads the code and simulates it finds what is
wrong but has not shown up yet: the coordinate-space bug would have hit Robert's real 4K footage on day
one. Do both.

## Robert's verdict on v20 (2026-10-12)
"Decent, can't say I love the fish, but it's better."

**Open item for the next round:** Fred's design, which is the weakest part.
- Start from Robert's own fish PNG once he sends it (`style: photo`, then the illustrated rig).
- Before changing code, ask what he dislikes: the shape, the face, the colours, or how he moves.

## Take 1 (Robert's own footage, ADR 0030)

### v21 — the carp Fred on a still of take 1
- **Seen:**
  - The redesign holds in all three styles at phone size: the photo, the 3D spin (olive back, scales), pixel
    with blocky Robert, then the illustrated wave and name, the moustache and the hat.
  - The photo fish lies on his lower palm, with his hands framing it as he filmed.
- **Robert:** "Fred is decent." He wants the tests in his own voice, the steel limbs on **him** (not Fred), and
  Fred following his hands when he is put on the floor.
- **Lesson:** once a take exists, test on it. A stand-in voice on his video felt wrong to him; `create lab`
  now takes `take:` spans.

### v22 — the fish beat on the real take, Fred carried down by hand
- **Seen:** Fred rode the wrong hand to his knee. The hand nearest Fred at "leave" was the one going to the
  knee; the other hand put him on the floor, far right, under TikTok's action rail.
- **Fixed:**
  - The carrying hand is the one that reaches lowest in the span.
  - The prop settles into the palm.
  - A release under the platform's UI hops into the safe area (`safe_right` 888, `safe_bottom`).
- **Lesson:** "follow my hands" means the hand that does the action, which is visible only over the whole
  span, not at its first frame.

### v23 — automail on Robert, the circle under the chair
- **Seen:**
  - The first steel was pale (it read as a white cast).
  - The leg plate was as wide as a pipe: its width came from the thigh, which is foreshortened when seated.
  - Robert: in Fullmetal Alchemist it is the **right arm and the left leg**, and the circle goes **under his
    feet**, not over them.
- **Fixed:**
  - Gunmetal plates with bands, a ridge, ringed joints and a mechanical hand, from a reference sheet Robert
    shared (studied, not copied).
  - Plate width from the lower segment.
  - Default limbs `right_arm` and `left_leg`.
  - The circle goes behind the matte when there is one.
- **Lesson:** a homage has to be right in its details (which arm, which leg). Ask, or check the source,
  before drawing.
