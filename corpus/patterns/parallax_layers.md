# Layers Drift At Different Speeds

`parallax_layers` · 5 events in 5 videos

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

## How to build it
1. Split the scene into layers by depth: back (background shapes or tiles), middle (cards, nodes, icons) and front (headline, pill or a defocused particle).
2. Keep the focal element on its own layer and keep it still or nearly still.
3. Give each other layer its own direction and speed; nearer layers move faster, farther layers slower, and opposing directions add energy on an opening.
4. For a hold, use a slow continuous drift or a gentle sine bob with varied phase per element so nothing moves in lockstep.
5. For an entrance, let the layers settle into place from opposite sides while the title lands in the calm centre.
6. Optionally add a blurred foreground element that crosses quickly to sell shallow depth of field.

- **GSAP / HyperFrames:** Put each depth layer in its own container. For entrances, use gsap.fromTo per layer on x/y with opposing start offsets, a back.out spring-overshoot or a power ease-out, and a light stagger within a layer. For holds, use gsap.to with a sine ease-in-out yoyo repeat, or ease none for constant drift, varying speed per layer. A fast foreground particle uses a power ease-in with a blur filter.
- **Remotion:** Map each layer's translate from frame: a spring (moderate damping, slight overshoot) interpolated between opposing start offsets for entrances, or a linear interpolate or Math.sin of frame for continuous drift on holds, with a different speed or amplitude multiplier per layer. Keep the focal layer unanimated or animate only its colour.

## Measured
- Duration: median 505 ms, 90% interval 319 to 667 (n=14, 3 videos)
- Easing: spring overshoot 38%, ease in out 28%, ease out 28%, ease in 7%
- Changes: other 33%, slide up 15%, fade 15%, color shift 12%
- Elements: logo 24%, headline 21%, card 18%, other 10%
- Sound: music 50%, swoosh reverse 25%, unsure 25%; offset to the landing median -285 ms, 90% interval -393 to -94 (n=10, 1 videos)

## Sound
No typical sound: the motion usually rides on the music bed; where a cue was tagged it was a reverse swoosh landing slightly before the motion.

## Why it reads as premium
Parallax gives a flat composition real depth for almost no production cost: when the back tiles, mid-layer nodes and a front headline move at different rates or in opposing directions, the eye reads a three-dimensional space instead of a slide. On holds, a slow, varied drift keeps the frame breathing so a static card never looks frozen, yet it stays quiet enough not to compete with the narration. A still focal element against the moving field becomes a clear anchor, and a fast defocused particle crossing the foreground sells a shallow depth of field that feels filmed rather than built.

## Examples
- `figma-introducing-figma-motion-your-canvas-no` e001 (video score 5/5)
- `hubspot-what-is-hubspot` e007 (video score 4/5)
- `elevenlabs-introducing-eleven-v4-and-eleven-v4-turb` e003 (video score 4/5)
- `elevenlabs-introducing-elevenlabs-conversational-ag` e033 (video score 5/5)
- `datadog-datadog-overview-see-inside-the-platfor` e017 (video score 4/5)

## Caveats
- Durations were measured in only a few of the videos, and continuous drifts on holds have no natural end, so the duration figures describe entrances better than ambient drift.
- Sound offset comes from a single video only.
- A large share of changes are labelled other, because slow ambient drift does not fit the standard change types.
