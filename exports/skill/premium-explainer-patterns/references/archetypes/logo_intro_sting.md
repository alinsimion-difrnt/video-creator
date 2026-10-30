# Logo Intro Sting

`logo_intro_sting`

The brand mark or wordmark resolves at the centre of a clean background, often with a product line or tagline, and holds briefly before handing off to the first idea. It opens the video and tells the viewer whose story this is.

## When to use
- As the cold open or first beat of a launch or explainer video
- When the narration opens by naming the product
- As a short brand moment before cutting into the product interface

## Slots (what you fill in)
- `logo`: the brand mark or wordmark as a vector
- `product_line` (optional): a product name or short subline under the logo
- `tagline` (optional): one short claim that follows the logo
- `background`: a solid colour, a soft gradient or near-black
- `decoration` (optional): light accents such as drifting bands, sparkles or a faint grid
- `handoff_element` (optional): the first piece of interface or layout that leads into the next scene

## The scene, beat by beat
1. Start on the empty background, or fade up from dark
2. Resolve the logo: assemble it from fragments, wipe it on, draw its stroke or fade it up
3. Fade or slide in the product line or tagline under it
4. Hold the lockup briefly while the narration names the product
5. Hand off by blurring the logo out, reframing it into a page or interface, or zooming through

Patterns: [logo_resolve](../patterns/logo_resolve.md), [blur_crossfade](../patterns/blur_crossfade.md), [layout_reframe](../patterns/layout_reframe.md)

- GSAP / HyperFrames: One timeline per scene. Resolve the logo with a clip-path wipe, a stroke-dashoffset draw or a staggered gather of fragments into place, using a power or expo out ease; fade the subline up in parallel. Hold, then either tween blur and opacity on the logo while the next layer fades in, or tween the container's scale and position to reframe it into the next layout.
- Remotion: A Sequence for the logo with a spring driving scale or a clip reveal and interpolate for opacity; a nested Sequence starts the subline or tagline after the logo settles; a closing Sequence overlaps the next scene and interpolates blur and opacity for the handoff.

## Measured in premium explainers
- Scene length: 1.3-3.9 s (typical 2.6), 12 videos
- First motion after the scene starts: 0.1-1.5 s (typical 0.2), 4 videos
- Motion events per scene: 0-1 events (typical 0), 12 videos
- Way in: other 64%, zoom through 16%, hard cut 9%
- chime sound: 1.4-2.9 s (typical 2.4), 2 videos after the scene starts
- impact sound: 2.7-4.0 s (typical 3.6), 2 videos after the scene starts
- music sound: 1.1-2.6 s (typical 1.5), 4 videos after the scene starts
- swoosh reverse sound: 1.3-2.2 s (typical 1.7), 3 videos after the scene starts
- unsure sound: 0.2-2.8 s (typical 2.2), 6 videos after the scene starts

## Sound
Mostly music and mixed accents. A reverse swoosh building into the logo is the most common clear cue, landing in the middle of the scene; a soft chime can mark the lockup, and an impact sometimes hits late as the handoff begins.

## Caveats
- First-motion timing comes from only a few shots and has a wide spread.
- Many sound cues are labelled unsure, and each specific cue type comes from only a few videos.
