# Blur Out, Blur In

`blur_crossfade` · 5 events in 4 videos

The current layout softens, fades and drifts away while the next one comes into focus in its place, sharpening from a blur and settling gently. It replaces a hard cut with something that feels like a camera pulling focus.

## When to use
- Changing section or page without breaking the feeling of one continuous session
- Moving from a busy interface to a single centred statement
- Handing off from an opening title or logo to the first product visual
- Swapping a content pane while a sidebar or frame stays put

## Avoid when
- The change should feel sudden or dramatic, where a hard cut or whip lands better
- Both layouts share an element that could carry a match cut instead
- Rapid back-to-back scene changes, where repeated blurs feel mushy

## How to build it
1. Decide what stays fixed (a sidebar, the canvas, the centre position) so the eye has an anchor.
2. Send the outgoing layout away: fade it, blur it and optionally drift it in one direction.
3. Slightly overlap the incoming layout so it starts appearing before the outgoing one is fully gone.
4. Bring the incoming elements in from a blur to sharp, with a small upward settle or a slight scale-down to rest.
5. Stagger the incoming items lightly so the new layout assembles rather than pops in as one block.
6. Optionally let the new headline deepen from a pale tint to its full colour as it sharpens.

- **GSAP / HyperFrames:** Use a timeline: gsap.to on the outgoing group (opacity to zero, a blur filter up, an optional y or x drift) with a power ease-in, then gsap.fromTo on the incoming children (opacity, blur filter down to none, a small y or scale settle) with a power ease-out and a light stagger, overlapped using a negative position offset. A back.out spring-overshoot suits small incoming items; keep transforms subtle and avoid large scale changes.
- **Remotion:** Drive the outgoing layer with interpolate on frame for opacity, blur and translate, using Easing.in. Drive incoming items with a spring (high damping, or a mild overshoot) or interpolate with Easing.out, mapping progress to opacity, blur radius and a small translateY, each item delayed a frame or so after the last.

## Measured
- Duration: median 442 ms, 90% interval 366 to 529 (n=10, 2 videos)
- Easing: ease out 51%, spring overshoot 21%, ease in 10%, linear 10%
- Changes: fade 40%, slide up 18%, blur in 15%, blur out 7%
- Elements: card 31%, headline 18%, body text 12%, background 8%
- Sound: swoosh reverse 43%, unsure 39%, chime 17%; offset to the landing median -10 ms (n=2, 1 videos)

## Sound
Often paired with a reverse swoosh, sometimes a soft chime, landing almost exactly on the visual change; many cases had no clearly identifiable cue.

## Why it reads as premium
Pulling focus instead of cutting keeps a scene change soft and continuous, so the story moves from one step to the next as a single gesture rather than a jolt. Premium explainers keep an anchor in place (a persistent sidebar, a fixed centre point, a clean background) while only the content swaps, and they keep the motion travelling in one consistent direction, so the handoff reads as the same product session continuing. The incoming layout sharpening from a blur, sometimes deepening from a tint to full brand colour, gives a polished settling finish that a plain opacity fade lacks.

## Examples
- `hubspot-what-is-hubspot` e011 (video score 4/5)
- `workday-workday-adaptive-planning-demo-finan` e002 (video score 3/5)
- `elevenlabs-introducing-elevenlabs-conversational-ag` e007 (video score 5/5)
- `datadog-datadog-overview-see-inside-the-platfor` e001 (video score 4/5)

## Caveats
- Durations were measured in only a couple of videos.
- Sound offset rests on very few measurements from a single video and has no confidence interval.
- Some member events are plain crossfades with little or no actual blur, so the blur share of changes is modest.
