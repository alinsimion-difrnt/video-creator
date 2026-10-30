# Comparison Split

`comparison_split`

Two sides share the frame, left and right or in stacked lanes, so the viewer compares the old way with the new one or the product against the alternatives. It sets up a contrast that the narration then resolves in the product's favour.

## When to use
- Showing before and after, or old versus new, at a glance
- Framing the problem as a matchup between the product and the usual alternatives
- Backing a claim with a side-by-side result or score

## Slots (what you fill in)
- `left_side`: the first contender: an old version, an alternative or a person, as an image, icon or render
- `right_side`: the second contender, usually the product or the improved version
- `divider` (optional): what separates the halves: a thin line, a diagonal band edge or a centred badge
- `verdict` (optional): a short stat, label or status that says which side wins
- `footnote` (optional): a small disclaimer under a claim
- `background` (optional): two contrasting colour fields or a neutral canvas

## The scene, beat by beat
1. Reveal both sides together, or bring them in from opposite edges
2. Hold the split so the viewer reads the contrast, with a slow push or a gentle drift toward the centre
3. Bring in the verdict between or under the sides as a stat, score bars or a status change
4. Clear everything except the winning side and carry it into the next shot with a scale-up, a zoom or a fast cut

Patterns: 

- GSAP / HyperFrames: One timeline per scene. Tween the two side groups in from opposite edges with mirrored x values and a short stagger, using an expo or power out ease; add a slow scale push on the container with a sine in-out ease for the hold. Fade or blur the verdict in at the centre, fill any score bars left to right with a stagger, then fade the losing side and scale the winner up with a power in ease into the transition.
- Remotion: One Sequence for the scene with two child layers for the sides, each driven by a mirrored spring on translateX; a nested Sequence starts the verdict after the sides settle, and a final Sequence interpolates opacity on the losing side and scale on the winning side into the next scene.

## Measured in premium explainers
- Scene length: 1.6-3.0 s (typical 1.9), 5 videos
- First motion after the scene starts: not measured
- Motion events per scene: 0-0 events (typical 0), 5 videos
- Way in: other 67%, hard cut 14%, zoom through 14%
- impact sound: 0.3-1.8 s (typical 1.0), 3 videos after the scene starts
- music sound: 1.8-5.0 s (typical 2.6), 4 videos after the scene starts
- unsure sound: 1.8-4.2 s (typical 3.1), 3 videos after the scene starts
- whoosh sound: 0.3-0.5 s (typical 0.4), 1 videos after the scene starts

## Sound
No single clear cue. Impact hits are common and tend to land in the first part of the scene as the sides or the verdict arrive; a whoosh sometimes marks the entrance right at the start; music carries the rest.

## Caveats
- No motion events were measured in these shots, so there is no measured pattern mix or first-motion timing; the build notes come from shot descriptions.
- Members are mixed: product renders, illustrated matchups, abstract lanes and footage all count as splits.
- Much of the sound is labelled unsure, so the cue timing is loose.
