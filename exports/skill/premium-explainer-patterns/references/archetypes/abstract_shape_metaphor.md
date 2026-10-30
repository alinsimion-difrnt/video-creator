# Abstract Shape Metaphor

`abstract_shape_metaphor`

A brief, full-frame abstract image of soft shapes, gradient orbs, outlines or dot fields stands in for an idea such as growth, voice or data. It bridges two scenes and gives the narration a visual metaphor instead of literal interface.

## When to use
- Explaining how something works with a metaphor rather than a screen.
- Bridging between scenes with a short visual beat that carries a shape forward.
- Opening a video on mood before the product appears.

## Slots (what you fill in)
- `metaphor_shape`: the main form, such as an orb, a growing stem, an outline circle or a dot field
- `background`: a flat or softly blurred pale or brand-coloured field
- `palette` (optional): a few brand colours used for gradients or particles
- `carry_element` (optional): the shape that continues into the next scene for a match cut

## The scene, beat by beat
1. A soft, out-of-focus field appears with the shape just entering or barely visible.
2. The shape settles into place or multiplies into a field as the narration names the idea.
3. The camera flies into or scales past the shape.
4. The shape carries through to the next scene as a match cut or a zoom-through.

Patterns: [match_cut_element](../patterns/match_cut_element.md)

- GSAP / HyperFrames: One short timeline per scene. Build shapes as SVG or divs with radial gradients and a CSS blur filter, and tween their scale, position and blur on a sine in-out. For a dot field, generate many small circles and give each a tiny looping offset with a random stagger. End by tweening the container's scale well past full frame on an expo ease-in for a zoom-through, keeping the carry element's position for the next scene.
- Remotion: One Sequence, usually short. Interpolate blur and scale from the frame index, drive the main shape with a soft, low-stiffness spring, and use seeded noise per particle for jitter. Place the carry element in a shared layer so the next Sequence starts from the same position.

## Measured in premium explainers
- Scene length: 0.4-2.7 s (typical 1.6), 3 videos
- First motion after the scene starts: 0.7-1.7 s (typical 1.4), 1 videos
- Motion events per scene: 0-1 events (typical 0), 3 videos
- Way in: other 52%, zoom through 38%, crossfade 10%
- chime sound: 0.6-0.6 s (typical 0.6), 1 videos after the scene starts
- impact sound: 3.1-3.1 s (typical 3.1), 1 videos after the scene starts
- music sound: 2.3-2.3 s (typical 2.3), 1 videos after the scene starts
- swoosh reverse sound: 1.0-1.0 s (typical 1.0), 1 videos after the scene starts
- unsure sound: 0.3-2.1 s (typical 1.6), 2 videos after the scene starts

## Sound
no typical sound

## Caveats
- Few shots from only a few videos; first motion is measured in a single video.
- Sound cues are mostly unclassified, so no clear cue is recommended.
- Most motion is labelled other, so the build notes lean on member descriptions.
