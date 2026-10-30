# Layers Drift At Different Speeds

`parallax_layers`

Separate layers of a flat scene (tiles, logos, background shapes, a foreground pill or headline) move at different speeds or in different directions, so the picture feels like it has depth. Often the headline or focal element stays calm while the layers around it drift.

## When to use
- Keeping a held card or collage alive while the narration plays
- Opening a reel with a collage that settles around a title
- Giving a flat diagram or logo network a sense of space
- Adding a feeling of speed behind a static message

## Avoid when
- The viewer must read dense text inside the moving layers
- Every layer would move at the same rate, which reads as a plain slide rather than depth
- The scene already has strong camera motion competing for attention

## Build
1. Split the scene into layers by depth: back (background shapes or tiles), middle (cards, nodes, icons) and front (headline, pill or a defocused particle).
2. Keep the focal element on its own layer and keep it still or nearly still.
3. Give each other layer its own direction and speed; nearer layers move faster, farther layers slower, and opposing directions add energy on an opening.
4. For a hold, use a slow continuous drift or a gentle sine bob with varied phase per element so nothing moves in lockstep.
5. For an entrance, let the layers settle into place from opposite sides while the title lands in the calm centre.
6. Optionally add a blurred foreground element that crosses quickly to sell shallow depth of field.

- GSAP / HyperFrames: Put each depth layer in its own container. For entrances, use gsap.fromTo per layer on x/y with opposing start offsets, a back.out spring-overshoot or a power ease-out, and a light stagger within a layer. For holds, use gsap.to with a sine ease-in-out yoyo repeat, or ease none for constant drift, varying speed per layer. A fast foreground particle uses a power ease-in with a blur filter.
- Remotion: Map each layer's translate from frame: a spring (moderate damping, slight overshoot) interpolated between opposing start offsets for entrances, or a linear interpolate or Math.sin of frame for continuous drift on holds, with a different speed or amplitude multiplier per layer. Keep the focal layer unanimated or animate only its colour.

## Measured in premium explainers
- Duration: 319-684 ms (typical 505), 3 videos
- Easing: spring overshoot 38%, ease in out 28%, ease out 28%, ease in 7%
- Changes: other 33%, slide up 15%, fade 15%, color shift 12%
- Sound offset to the landing: -393--94 ms (typical -285), 1 videos

## Sound
No typical sound: the motion usually rides on the music bed; where a cue was tagged it was a reverse swoosh landing slightly before the motion.

## Why it reads as premium
Parallax gives a flat composition real depth for almost no production cost: when the back tiles, mid-layer nodes and a front headline move at different rates or in opposing directions, the eye reads a three-dimensional space instead of a slide. On holds, a slow, varied drift keeps the frame breathing so a static card never looks frozen, yet it stays quiet enough not to compete with the narration. A still focal element against the moving field becomes a clear anchor, and a fast defocused particle crossing the foreground sells a shallow depth of field that feels filmed rather than built.

## Caveats
- Durations were measured in only a few of the videos, and continuous drifts on holds have no natural end, so the duration figures describe entrances better than ambient drift.
- Sound offset comes from a single video only.
- A large share of changes are labelled other, because slow ambient drift does not fit the standard change types.
