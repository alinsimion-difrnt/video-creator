# Comparison Split

`comparison_split` · 12 shots in 5 videos

Two sides share the frame, left and right or in stacked lanes, so the viewer compares the old way with the new one or the product against the alternatives. It sets up a contrast that the narration then resolves in the product's favour.

## When to use
- Showing before and after, or old versus new, at a glance
- Framing the problem as a matchup between the product and the usual alternatives
- Backing a claim with a side-by-side result or score

## What you fill in
- **left_side**: the first contender: an old version, an alternative or a person, as an image, icon or render
- **right_side**: the second contender, usually the product or the improved version
- **divider** (optional): what separates the halves: a thin line, a diagonal band edge or a centred badge
- **verdict** (optional): a short stat, label or status that says which side wins
- **footnote** (optional): a small disclaimer under a claim
- **background** (optional): two contrasting colour fields or a neutral canvas

## The scene, beat by beat
1. Reveal both sides together, or bring them in from opposite edges
2. Hold the split so the viewer reads the contrast, with a slow push or a gentle drift toward the centre
3. Bring in the verdict between or under the sides as a stat, score bars or a status change
4. Clear everything except the winning side and carry it into the next shot with a scale-up, a zoom or a fast cut

Patterns: 

- **GSAP / HyperFrames:** One timeline per scene. Tween the two side groups in from opposite edges with mirrored x values and a short stagger, using an expo or power out ease; add a slow scale push on the container with a sine in-out ease for the hold. Fade or blur the verdict in at the centre, fill any score bars left to right with a stagger, then fade the losing side and scale the winner up with a power in ease into the transition.
- **Remotion:** One Sequence for the scene with two child layers for the sides, each driven by a mirrored spring on translateX; a nested Sequence starts the verdict after the sides settle, and a final Sequence interpolates opacity on the losing side and scale on the winning side into the next scene.

## Measured
- Scene length: median 1.9 s, 90% interval 1.6 to 2.9 (n=12, 5 videos)
- Motion events per scene: median 0.0 events, 90% interval 0.0 to 0.0 (n=12, 5 videos)
- First motion: not measured after the scene starts
- Way in: other 67%, hard cut 14%, zoom through 14%, crossfade 5%
- Story beat: demo 29%, problem 24%, proof 24%, hook 19%
- Sound: music 31%, unsure 31%, impact 30%, whoosh 8%

## Sound cues
No single clear cue. Impact hits are common and tend to land in the first part of the scene as the sides or the verdict arrive; a whoosh sometimes marks the entrance right at the start; music carries the rest.
- impact: median 1.0 s, 90% interval 0.3 to 1.8 (n=11, 3 videos) after the scene starts
- music: median 2.6 s, 90% interval 2.0 to 5.0 (n=9, 4 videos) after the scene starts
- unsure: median 3.1 s, 90% interval 1.8 to 4.2 (n=9, 3 videos) after the scene starts
- whoosh: median 0.4 s (n=2, 1 videos) after the scene starts

## Examples
- `meta-introducing-meta-quest-3-coming-this-f` s004 (video score 5/5)
- `duolingo-introducing-duolingo-chess` s001 (video score 4/5)
- `zendesk-meet-zendesk-ai-agents-the-most-autonom` s004 (video score 4/5)
- `fullstory-behavioral-data-made-simple-by-fullstory` s002 (video score 4/5)
- `profound-introducing-profound` s045 (video score 4/5)

## Caveats
- No motion events were measured in these shots, so there is no measured pattern mix or first-motion timing; the build notes come from shot descriptions.
- Members are mixed: product renders, illustrated matchups, abstract lanes and footage all count as splits.
- Much of the sound is labelled unsure, so the cue timing is loose.
