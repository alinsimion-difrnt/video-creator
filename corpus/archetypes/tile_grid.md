# Tile Grid

`tile_grid` · 33 shots in 15 videos

Many tiles, such as app windows, integration icons, video clips or small UI widgets, sit in a grid or wall that the camera pulls out to reveal or glides across. The scene shows breadth: many use cases, integrations or projects at once.

## When to use
- To show that the product covers many integrations, use cases or projects.
- As a pull-out transition from one view into a wall of related views, then into the next one.
- When one tile should grow to centre stage while the others make room.

## What you fill in
- **tiles**: a set of similar items: screenshots, icons, clips or widgets
- **hero_tile** (optional): the tile the camera starts from, lands on or enlarges
- **caption** (optional): a short headline over or beside the grid
- **status_chip** (optional): a small label that pops onto the hero tile
- **background**: a plain dark or light field behind the grid

## The scene, beat by beat
1. Start close on one tile or on an empty field.
2. Tiles stagger in, or the camera pulls out to reveal the full wall.
3. The wall drifts slowly or the camera glides across it.
4. Focus moves to one tile: it highlights, enlarges while others shrink, or gains a chip.
5. The camera pushes into the chosen tile or the grid clears for the next scene.

Patterns: [layout_reframe](../patterns/layout_reframe.md), [card_wall_stagger](../patterns/card_wall_stagger.md), [parallax_layers](../patterns/parallax_layers.md), [spotlight_focus](../patterns/spotlight_focus.md), [stagger_list_reveal](../patterns/stagger_list_reveal.md), [ui_camera_push_in](../patterns/ui_camera_push_in.md), [kinetic_word_reveal](../patterns/kinetic_word_reveal.md)

- **GSAP / HyperFrames:** Lay the tiles out on one large canvas in a CSS grid inside a wrapper; one timeline per scene with a staggered from tween for tile entrances (opacity, y or scale, power ease-out), scale and x/y tweens on the wrapper for pull-outs and glides (power or expo in-out), a slow linear drift for the wall, and a grid-size or scale tween to enlarge the hero tile.
- **Remotion:** A single Sequence holding the tile canvas; tile entrances use a spring delayed by tile index, the camera is an interpolated scale and translate on the wrapper keyed to frame, and a child Sequence on the narration cue springs the hero tile larger and pops its chip.

## Measured
- Scene length: median 2.4 s, 90% interval 2.0 to 2.9 (n=33, 15 videos)
- Motion events per scene: median 0.0 events, 90% interval 0.0 to 1.0 (n=33, 15 videos)
- First motion: median 0.6 s, 90% interval 0.3 to 1.0 (n=9, 6 videos) after the scene starts
- Way in: other 51%, zoom through 22%, hard cut 19%, slide 4%
- Story beat: demo 39%, outcome 21%, proof 17%, hook 11%
- Sound: unsure 39%, music 23%, swoosh reverse 22%, impact 9%

## Sound cues
Usually a reverse swoosh or unlabelled whoosh on the pull-out or reveal, with an occasional early impact as tiles land; music carries the rest.
- chime: median 1.6 s (n=4, 2 videos) after the scene starts
- impact: median 0.3 s, 90% interval 0.2 to 0.9 (n=6, 4 videos) after the scene starts
- music: median 1.9 s, 90% interval 0.7 to 2.3 (n=12, 6 videos) after the scene starts
- swoosh reverse: median 1.8 s, 90% interval 0.6 to 2.1 (n=16, 5 videos) after the scene starts
- unsure: median 1.0 s, 90% interval 0.6 to 1.8 (n=24, 11 videos) after the scene starts
- whoosh: median 3.9 s (n=1, 1 videos) after the scene starts

## Examples
- `elevenlabs-introducing-elevenlabs-conversational-ag` s004 (video score 5/5)
- `figma-introducing-figma-motion-your-canvas-no` s025 (video score 5/5)
- `meta-introducing-meta-quest-3-coming-this-f` s028 (video score 5/5)
- `notion-introducing-notion-ai-connectors` s001 (video score 4/5)

## Caveats
- Few shots and videos, and measured motion and sound come from only a handful of them.
- Members are mixed: icon rows, video walls, bento widget grids and window walls, and some shots chain other scene types.
- Most of the pattern mix is unnamed, and several members carry no pattern labels.
