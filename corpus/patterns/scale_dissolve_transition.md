# Zoom And Dissolve Transition

`scale_dissolve_transition` · 8 events in 5 videos

One screen fades away while it grows or shrinks, and the next screen fades in while settling to its normal size, so the change feels like one continuous zoom instead of a cut.

## When to use
- Moving between two product screens while keeping the sense of one continuous app
- Handing off from a loading or prompt state to the finished result
- Changing topic or section without a hard cut, such as from a demo into a feature tile
- Hiding a time jump in a screen recording while a menu or cursor stays continuous

## Avoid when
- The two screens are unrelated and a clean cut would read more honestly
- Fast-paced montage where a dissolve would blur the rhythm

## How to build it
1. Stack the outgoing and incoming layers in the same frame
2. Start fading the outgoing layer while scaling it slightly up or down, optionally with a touch of blur or drift
3. Overlap the start of the incoming layer so both are briefly visible
4. Bring the incoming layer in from slightly oversized or undersized and let it settle to full size as it reaches full opacity
5. Keep any anchor element, like a cursor or open menu, continuous across the change
6. Start the next action, such as typing, dragging or a caption, right as the new layer settles

- **GSAP / HyperFrames:** Use a timeline: gsap.to on the outgoing layer (opacity to zero, scale change, ease-in) and an overlapping gsap.fromTo on the incoming layer (opacity and scale to rest) placed with a negative offset. Settle the incoming layer with a back-style overshoot ease or a strong ease-out; linear only for slow ambient drift.
- **Remotion:** Interpolate the outgoing layer's opacity and scale with an ease-in curve; drive the incoming layer's scale and opacity with a spring that has a little overshoot, or a damped spring if the settle should be calm. Both layers live in one Sequence so the overlap is exact.

## Measured
- Duration: median 566 ms, 90% interval 403 to 743 (n=11, 3 videos)
- Easing: spring overshoot 45%, ease in 27%, ease out 18%, linear 9%
- Changes: fade 35%, scale up 17%, scale down 13%, slide right 8%
- Elements: ui panel 33%, cursor 12%, card 11%, button 10%
- Sound: music 54%, unsure 35%, whoosh 11%; offset to the landing median -317 ms, 90% interval -364 to -46 (n=8, 1 videos)

## Sound
No typical sound; most moments sit under music or an unclear bed. When a whoosh is used, it tends to lead the visual change slightly rather than follow it.

## Why it reads as premium
The zoom-and-dissolve keeps the viewer inside one continuous product world: the scale change carries momentum from one surface to the next, so a jump between screens, projects or sections reads as a camera move rather than an edit. The best versions overlap the outgoing and incoming layers, settle the new layer with a soft spring, and keep an anchor like a cursor or menu steady through the change. They also land straight on the next action, so the demo never pauses after the transition.

## Examples
- `anthropic-introducing-claude-design-by-anthropic-l` e012 (video score 4/5)
- `hubspot-what-is-hubspot` e005 (video score 4/5)
- `elevenlabs-introducing-eleven-v4-and-eleven-v4-turb` e004 (video score 4/5)
- `elevenlabs-introducing-elevenlabs-conversational-ag` e010 (video score 5/5)
- `datadog-datadog-overview-see-inside-the-platfor` e025 (video score 4/5)

## Caveats
- Timing was measured on few elements from only a handful of videos, so treat the duration range as indicative
- Sound offsets come from a single video, so the whoosh lead is not yet a corpus-wide habit
- Members split between zooming in and pulling out; the direction should follow the story, not a rule
