---
name: pixel-art
description: Make or improve a pixel-art sprite or animation for a video (a character, an object, an Easter egg) with create/pixel — shapes lit by one light and quantised to hue-shifted ramps, selective outlines, contact shadows, keyed poses — and review it frame by frame until it reads at 1x. Use whenever a reel needs pixel art (a prop's `pixel` style, a cat, a cameo) or a sprite looks low quality.
---

# pixel-art

Pixel art here is **code**: a sprite is a function `frames(anim, ...) -> list[PIL.Image]` that builds lit shapes
for each pose and renders them with `create.pixel.core.Canvas`. Never type grids by hand for characters (they
cannot turn or shade), and never pixelate a smooth drawing with a filter (that is what looked low quality).
Read `create/pixel/core.py`'s docstring, then `create/pixel/kitten.py` and `create/pixel/fred.py` as examples.

## The rules (each one fixed something in a review)
1. **Size first.** Characters are 40-56 px tall natively. Smaller loses the face; bigger stops reading as
   pixel art. Output is an integer nearest-neighbour upscale (`PIXEL_SCALE` 12 in reels).
2. **Ramps, hue-shifted, one shared shadow.** `ramp(base, steps, mid)`: 4-5 steps per material. Darker
   steps move toward blue/purple and lean toward `SHADOW`, lighter toward yellow. A cream belly whose darkest
   step was brown looked dirty; leaning on the shared shadow fixed it.
3. **Light that shows the face.** One light from above, a little left, toward the viewer, half-Lambert. Light
   from the top left on a right-facing character put the face in shadow and lost the eyes.
4. **Shapes are forms.** Ellipses are domes, capsules are tubes, polygons are flat (`flat`). Shading comes
   from the form, so clusters are big and follow it: no pillow shading.
5. **Selective outline.** The silhouette takes the darkest step of what it borders, a step lighter on the lit
   side. Ink only where contrast needs it.
6. **Parts must join.** Separate ellipses leave a dark gap that the outline turns into a black blob (the kitten's
   neck): add a joining shape (`chest`).
7. **Limbs in front need their own edge** (`edge=True`): without it a fin over the body vanishes. Limbs behind
   take `lift=-1` and the contact shadow darkens the body where they meet.
8. **Shape language.** A limb that hangs in front of the face reads as a nose or a beak. Pivot limbs at the
   shoulder/gill, rest them back along the side, give fins a fan shape (narrow root, notched wide tip).
9. **Faces are stamps.** Eyes, mouths and blush are placed pixel by pixel (`stamps`), after shading: 2-3 px
   wide eyes with a white shine; nothing over them (hats sit above the eye line).
10. **Contrast between materials.** Fins and tails a hue step away from the body (red-orange against
    orange), so the silhouette parts read at 1x.

## Lessons from the animation lab (ADR 0029, docs/learnings/animation-lab.md)
16. **Cute faces turn toward the viewer.**
    - A profile head with eyes at its edge read as small squares (Pixie v1).
    - A three-quarter face with both eyes inside the head reads as the comic kitten: big dark eyes, a 2x2
      shine on top, the coloured iris below, a happy-arc blink.
17. **A pale base needs a gentle first shade step.** The ramp maths drops a pale peach straight into mauve,
    and the shaded half of the head became mud. `_soft()` puts the first shade halfway to the base, and the
    head is lit nearly flat (`flat=0.8`): the face side must never be the dark side.
18. **A limb reads only where it breaks the silhouette.**
    - A fin inside the body outline read as a mark on the belly; one at mouth height read as a beak
      (twice: ADR 0028 and again in the lab).
    - Put shoulders on the silhouette's edges, below the mouth.
    - Side on, a raised near limb lies across the face: wave with the far limb, up behind the head.
19. **Stripes at 40 px are noise.** Ray stripes on fins and tails made Fred busy; flat fins with one edge
    read better.
20. **Every gag needs every representation.** The boat existed only in the SVG rig, and a hat drop only as
    a rig tween. When a sprite can't animate a beat, give the container the beat (a squash on the act
    layer), or fall back to the representation that can.

## The icon look (learned from a premium fishing-game icon sheet Robert shared; studied, never copied)
11. **One warm ink outline** (`Canvas(mode="ink")`, ink `#2b1d14`) around every sprite and between fins and
    body: it ties a set of sprites together. Sel-out is for soft, painterly sprites; ink is for icons.
12. **Fish are counter-shaded, not lit like balls** (`shade="counter"`): a dark back, a light belly
    (`blend(back, belly)` ramps) and a pale **rim** inside the belly edge (`rim=True`).
13. **Texture beats smooth shading** at 32 px: `pattern="mottle"` (2 x 2 patches, `pattern_mat` and
    `pattern_mat2` for two hues, like teal and olive on a perch), `spots` (single bright pixels), `scales`,
    and `rays` on fins (stripes along the fin).
14. **Curves and big fins.** Bodies bend along a `spine` (one gentle arc, head up and right, or a curl). A deep
    body, a large forked tail, a spiny dorsal fin and belly fins make it read as a fish; thin bodies read as
    seals.
15. **Contrasting fins** (orange or red against green or blue), a tiny two-pixel eye (light, dark), a gill
    line a step darker, an ink notch for the mouth.

## From the pixel-art study (studies/pixel-art/findings.md: 68 subjects, 57 clips, 39 timed GIFs)
Numbers are measured (studies/pixel-art/metrics/saint11-*.json); the subjects behind each rule are in findings 7.
- **Timing.** Hold each drawing 80 ms for body moves, 100 ms for everything else. Do not tween the sprite
  smoothly across the frame.
  - A blink is one 30 ms frame inside slower holds.
  - An impact is one 20 ms frame.
  - A wind-up is held about 300 ms.
  - An idle is long and quiet: characterIdle.gif cycles over 6000 ms.
- **Acting in and out.**
  - Build the reel on exits and returns. Fred leaves at least twice and comes back each time with one visible
    change. Give him a home shot he returns to.
  - Each exit is an event, and a different one each time: a flash knock-off, a flash plus a puff, a pixel
    dissolve, a flip, afterimages.
  - Hold the empty frame a beat after he leaves, with the evidence left behind.
- **Depth.**
  - One "small in the background" beat per reel: tiny on a paler far layer or in a sharp tilt-shift band, doing
    one task with 1-2 px moves. Then cut to him big.
  - Fred and Pixie swap near and far; the one not acting stays still.
- **Restraint.**
  - One moving thing per beat and one big effect moment per reel. Effects last 0.8-1.6 s and dissipate.
  - The rest is held poses or one ambient loop (cinemagraph).
  - When he listens, only the eyes and mouth move.
  - Use a pose library cut on beats, not loops.
  - Repeat gags in threes and escalate.
- **The look.**
  - One fixed palette of about 16-20 colours with hue-shifted ramps (warm lights, cool or purple shadows).
  - A selective coloured outline, one key light and a contact shadow.
  - Integer scale only.
  - The hero is warm and saturated on a desaturated, cooler background.
  - Test as a flat grey silhouette and at thumbnail size.

## Animation rules
- **Key the poses, don't drive them with one sine.** A sine on every leg made the walk read as shuffling and
  the gallop as a walk. Write a table: one row per frame with every limb angle, the bob and the lifts
  (`WALK`, `RUN` in kitten.py).
- **Cycles:** idle 6-8 frames @ 8 fps (breathe one pixel, a blink, a tail sway that keeps the curl), walk 8 @ 12
  (diagonal pairs, one pixel of bob on the passing positions, the swinging foot lifted), run 6 @ 14 (gather,
  push, stretch in the air, reach, plant), hop 6 @ 12 (squash, stretch, up, top, down, squash).
- **Integer moves only.** Bobs and lifts are whole pixels; parts that do not move are drawn the same (no
  boiling). Python schedules every frame (`create/footage/props.py: sprite_schedule`), the page only shows it.
- **Textures move with the body.** Patterns are pinned to each shape's anchor (`_anchor`), or scales and
  mottle slide across a hopping body (boiling).
- **Airborne means all of it.** In a hop's air frames the tail (feet) leaves the ground too, or it reads as a
  stretch. Give the canvas headroom (`Canvas(oy=...)`) so hats are not cut at the top of a jump.
- **Smears are allowed** for one frame (Fred's clap stretches his fins over his head).
- **Cycles that fit a move:** a jump's frames are spread over the move (`fit`), so a jump of any length ends
  on its landing frame. A pounce plays once *after* the walk ends, never over it.

## Review loop (do not skip it)
1. `uv run create pixel kitten|fred|fishes --out data/create/_pixel [--anims a,b] [--acc top_hat,moustache]` writes per
   animation a frame sheet, an onion skin (all frames over each other: arcs and spacing), a GIF and an MP4.
2. Look at the sheet at 5-8x **and** at a single frame at 10-14x. Write down what a pixel artist would fix:
   readability of the face at 1x, dark blobs, dirty colours, lone pixels, limbs that read as something else,
   jitter between frames in the onion skin.
3. Fix one thing at a time in code, re-render, compare. Stop only when nothing on that list is left.
   When a reference exists, put it beside yours at the same zoom and native size and list the differences
   (that is how the fish icons got their two-hue mottle and their deep bodies).
4. In a reel: `create reel --preview` times inside the sprite's moments; the contact sheet shows it at size.
5. Media never goes into git: previews live under `data/` (gitignored) or the scratchpad.

## Adding a sprite
1. `create/pixel/<name>.py` with `W, H, FPS` and `frames(anim, ...)`; materials in `ramps()`.
2. A reel prop uses it through `create/footage/props_art.py` (a new `art` kind writing frames per animation,
   `Art.frames` cycles and `Art.fps`), and `sprite_schedule` picks frames from moves, acts and carries.
3. Tests: frame sizes, palettes, and that the schedule plays the cycle while it moves.
