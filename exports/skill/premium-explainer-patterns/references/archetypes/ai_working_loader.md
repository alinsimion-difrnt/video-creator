# AI Working Loader

`ai_working_loader`

A small status pill, card or row shows the AI at work: a spinner or sparkle turns, a shimmer sweeps the label, and the status words cycle through what it is doing. It is a short bridge between a request and its result that makes the wait feel purposeful.

## When to use
- Between a sent prompt and the generated result
- Showing the AI reaching into several connected tools or sources
- A brief beat that builds anticipation before a reveal

## Slots (what you fill in)
- `status_label`: a short present-tense action, like designing or scanning
- `status_cycle` (optional): a few alternative status labels to swap through
- `working_icon`: a sparkle, spinner ring, avatar or pulsing dots that move while working
- `source_icons` (optional): app icons paired with each status row or label
- `backdrop` (optional): the blurred or dimmed context behind the loader, or a living visual such as a rotating globe
- `result_view` (optional): the finished output the loader resolves into

## The scene, beat by beat
1. The request card collapses or the view cuts to a compact status pill or card
2. The working icon starts moving: a spin, pulse or animated face
3. A light shimmer sweeps across the label while the status words cycle or new status rows append
4. Finished rows dim to a muted colour to read as done
5. The loader blurs or fades away and the result resolves in, or the scene hard-cuts to it

Patterns: 

- GSAP / HyperFrames: One timeline per scene. Loop the icon with a repeating linear rotation or a yoyo scale pulse on the dots. Run the shimmer as a repeating tween of a gradient mask position across the label (linear or sine.inOut). Swap status labels with short opacity crossfades on a fixed interval, or append each new status row with a left-to-right mask reveal (power2.out) and then tween the previous row's colour to grey. End with a blur-and-fade out of the loader overlapping a blur-in of the result view.
- Remotion: One Sequence for the loader and one for the result. Drive rotation and shimmer from the frame number with interpolate() and modulo for looping. Each status label or row is its own Sequence with a short interpolate() fade or mask reveal; dimming is interpolate() on colour. The exit crossfades blur and opacity between the two Sequences; springs are not needed.

## Measured in premium explainers
- Scene length: 1.6-2.4 s (typical 2.1), 6 videos
- First motion after the scene starts: not measured
- Motion events per scene: 0-0 events (typical 0), 6 videos
- Way in: hard cut 64%, other 36%
- unsure sound: 0.7-1.9 s (typical 1.2), 2 videos after the scene starts

## Sound
No typical sound. The only measured cues are labelled unsure, scattered through the middle of the scene.

## Caveats
- No measured motion events or patterns, so none are listed; the descriptions suggest input text cycle and blur crossfade.
- Few shots, and the loader style varies: status pill, status rows, shimmer over a card, spinner card.
- No reliable sound: every measured cue is labelled unsure.
