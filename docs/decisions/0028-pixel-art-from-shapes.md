# 0028 — Pixel art from shapes: a renderer, sprites, and a review loop

- **Status:** accepted (Robert: "the pixel art seems low quality", 2026-10-11)
- **Date:** 2026-10-11
- **Milestone:** Phase 2, presenter reels (follows ADR 0027)

## Context
ADR 0027 made pixel art in two ways, and both looked low quality next to real pixel art:
- the cat was a grid typed by hand: flat colours, no light, stiff legs;
- Fred's `pixel` style was the smooth drawing run through a pixelate filter: blurred blocks with wrong colours.

Robert asked for a skill and code that make pixel art properly, and for small standalone animations to learn
on until they are high quality.

## Decision
- **create/pixel/core.py renders sprites from shapes.** Ellipses are domes, capsules are tubes, polygons are
  flat. They are rasterised at native resolution with no anti-aliasing, then:
  - lit by one light (half-Lambert, from above toward the viewer);
  - quantised to hue-shifted ramps that all lean toward one shared shadow colour;
  - given a selective outline in the darkest step of what each pixel borders (lighter on the lit side);
  - given contact shadows where a part in front meets a part behind, and internal edges on limbs in front;
  - cleaned of orphan pixels;
  - upscaled by an integer with nearest-neighbour only.

  Faces are pixel stamps.
- **Sprites are code with keyed poses.** create/pixel/kitten.py (Pixie: idle, walk, run, grab, look) and
  create/pixel/fred.py (Fred: idle, hop, wave, clap, row, every accessory as shapes). Each animation is a
  table of poses, one row per frame.
- **Reels use them.**
  - `art: cat` writes the kitten's frames. Fred's `pixel` style is his pixel frames for each accessory set
    he wears while pixel. The SVG filter is gone.
  - Python schedules which frame shows when (`sprite_schedule`): moves play their cycle, acts with frames
    play once, a carry shows the grab, and the idle cycle loops at rest. The page only follows the schedule.
- **Review loop as a tool and a skill.**
  - `create pixel <sprite>` writes a frame sheet, an onion skin, a GIF and an MP4 per animation.
  - `.claude/skills/pixel-art` holds the rules and the loop.

## Evidence (the review rounds, each a contact sheet at 5-14x)
- **Kitten v1:** too dark; the light from the top left put her face in shadow. The fix was half-Lambert light
  from the front.
- **Kitten v2, zoomed:**
  - A black blob under the chin. The fix was a chest shape joining the head and body.
  - Brown shadows on cream. The fix was ramps that lean toward a shared purple shadow.
  - Stripes poking out of the outline. The fix was moving them inside the body.
- **Kitten motion:**
  - The tail snapped between curled and straight. It now always curls and sways a little.
  - The gallop read as a walk. Walk and run are now keyed tables.
  - The onion skins show clean arcs.
- **Fred v1-v7:**
  - His front fin hanging over the belly read as a beak. It now pivots behind the gill and rests back along
    his side.
  - The fins were sausages; they are now fans.
  - The fins vanished against the body. They now have an internal edge and a redder ramp.
  - The clap could not reach above his head. It is now a one-frame smear of long fins.
  - The hat's brim covered his eye; it moved up. The moustache stuck out past his face; it is smaller.
- **In a reel** (synthetic take): pixel Fred waves during his pixel moment, and the kitten walks in, idles and
  grabs Fred.

## Addendum: Pixie's look (2026-10-11)
- Robert linked the series' page on Webtoons. Its cover shows Pixie with pale peach fur and bold dark tabby
  stripes on her head, back and ear tips. She has white inner ears, huge light-blue eyes with big black
  pupils, a white muzzle with two tiny fangs and a pink plaid bandana. The cover was looked at in the sandbox
  only and was not saved to the repository.
- The kitten's default palette and features follow those traits: peach fur, dark stripes and ear tips, white
  inner ears, light-blue eyes (a dark rim, the iris, a pupil and a shine), a white muzzle with fangs, and a
  pink bandana with plaid checks.
- The drawing is still the shape-built pixel kitten (an homage, not a copy). `colors` gains `iris` and
  `bandana`.

## Addendum: the icon look (2026-10-11)
- Robert shared a sheet of premium fishing-game icons as an example. We have no rights to it, so it was
  studied at zoom in the sandbox and never copied or committed.
- What makes them work:
  - a single warm dark ink outline;
  - counter-shaded bodies (a dark back, a light belly with a pale rim);
  - texture instead of smooth shading (two-hue mottle, single-pixel spots, rayed fins in a contrasting colour);
  - bodies that bend, deep with big fins;
  - tiny two-pixel eyes.
- The renderer gained these as features:
  - `Canvas(mode="ink")`;
  - `Shape(kind="spine")`, a tube along a curve;
  - `shade="counter"`, `blend()` ramps and `rim`;
  - patterns `mottle` (two hues), `spots`, `scales` and `rays`.
- create/pixel/fishes.py draws a study set of five species: perch, trout, goldfish, bluefin and salmon.
  Four rounds of side-by-side comparison drove it:
  - thin S-curved bodies read as seals, so they became deeper bodies on one gentle arc;
  - the tail fans and dorsal fins got bigger and spinier;
  - the mottle got a second hue;
  - stray outline pixels that wrapped across the canvas edge were fixed (outlines no longer wrap).
- Pixel Fred took the same look: ink, a darker back, a lighter belly with a rim, scales, rayed fins and tail.
  Pixie took the warm ink.
- A drawn fish's `pixel` style is now the goldfish icon.

## Consequences
- New pixel props are a `frames()` function plus an `art` kind. The skill says how to review them.
- The renderer is pure Python and small. A 48 × 40 frame renders in a few milliseconds, so a reel with
  hundreds of frames builds in seconds.
- Robert should judge the kitten's colours (`colors` in the plan) and both sprites at phone size.

## CLAUDE.md lines (Robert applies; an agent may not edit CLAUDE.md)
In "Commands", add:
```
uv run create pixel kitten|fred [--anims a,b] [--acc top_hat,moustache] (sprite previews; skill pixel-art, ADR 0028) |
```
