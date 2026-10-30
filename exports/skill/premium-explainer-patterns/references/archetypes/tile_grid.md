# Tile Grid

`tile_grid`

Many tiles, such as app windows, integration icons, video clips or small UI widgets, sit in a grid or wall that the camera pulls out to reveal or glides across. The scene shows breadth: many use cases, integrations or projects at once.

## When to use
- To show that the product covers many integrations, use cases or projects.
- As a pull-out transition from one view into a wall of related views, then into the next one.
- When one tile should grow to centre stage while the others make room.

## Slots (what you fill in)
- `tiles`: a set of similar items: screenshots, icons, clips or widgets
- `hero_tile` (optional): the tile the camera starts from, lands on or enlarges
- `caption` (optional): a short headline over or beside the grid
- `status_chip` (optional): a small label that pops onto the hero tile
- `background`: a plain dark or light field behind the grid

## The scene, beat by beat
1. Start close on one tile or on an empty field.
2. Tiles stagger in, or the camera pulls out to reveal the full wall.
3. The wall drifts slowly or the camera glides across it.
4. Focus moves to one tile: it highlights, enlarges while others shrink, or gains a chip.
5. The camera pushes into the chosen tile or the grid clears for the next scene.

Patterns: [layout_reframe](../patterns/layout_reframe.md), [card_wall_stagger](../patterns/card_wall_stagger.md), [parallax_layers](../patterns/parallax_layers.md), [spotlight_focus](../patterns/spotlight_focus.md), [stagger_list_reveal](../patterns/stagger_list_reveal.md), [ui_camera_push_in](../patterns/ui_camera_push_in.md), [kinetic_word_reveal](../patterns/kinetic_word_reveal.md)

- GSAP / HyperFrames: Lay the tiles out on one large canvas in a CSS grid inside a wrapper; one timeline per scene with a staggered from tween for tile entrances (opacity, y or scale, power ease-out), scale and x/y tweens on the wrapper for pull-outs and glides (power or expo in-out), a slow linear drift for the wall, and a grid-size or scale tween to enlarge the hero tile.
- Remotion: A single Sequence holding the tile canvas; tile entrances use a spring delayed by tile index, the camera is an interpolated scale and translate on the wrapper keyed to frame, and a child Sequence on the narration cue springs the hero tile larger and pops its chip.

## Measured in premium explainers
- Scene length: 1.0-3.3 s (typical 2.4), 15 videos
- First motion after the scene starts: 0.3-1.0 s (typical 0.6), 6 videos
- Motion events per scene: 0-1 events (typical 0), 15 videos
- Way in: other 51%, zoom through 22%, hard cut 19%
- chime sound: 0.8-1.6 s (typical 1.6), 2 videos after the scene starts
- impact sound: 0.3-0.8 s (typical 0.3), 4 videos after the scene starts
- music sound: 0.6-2.3 s (typical 1.9), 6 videos after the scene starts
- swoosh reverse sound: 0.6-2.2 s (typical 1.8), 5 videos after the scene starts
- unsure sound: 0.4-2.8 s (typical 1.0), 11 videos after the scene starts
- whoosh sound: 3.9-3.9 s (typical 3.9), 1 videos after the scene starts

## Sound
Usually a reverse swoosh or unlabelled whoosh on the pull-out or reveal, with an occasional early impact as tiles land; music carries the rest.

## Caveats
- Few shots and videos, and measured motion and sound come from only a handful of them.
- Members are mixed: icon rows, video walls, bento widget grids and window walls, and some shots chain other scene types.
- Most of the pattern mix is unnamed, and several members carry no pattern labels.
