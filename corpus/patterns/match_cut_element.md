# Match Cut On Shared Shape

`match_cut_element` · 2 events in 2 videos

A hard cut jumps to a new shot or a new framing, but a shared object or shape stays in the same place on screen, so the eye follows it across the cut and the change feels continuous.

## When to use
- Linking two different shots or angles through a common object
- Jumping in scale on a key word while keeping the composition locked
- Giving a story-led, cinematic rhythm to a sequence of scenes

## Avoid when
- No element can sit in a matching position and shape in both shots
- The viewer needs to track a precise spatial move, where a continuous transition reads better

## How to build it
1. Choose the anchor element both shots share and note its screen position and size
2. Frame or lay out the incoming shot so that anchor lands in the same region
3. Cut instantly from the first shot to the second, ideally on a spoken word or beat
4. Right after the cut, add a short drift or settle (slight scale or outward move, a colour shift) so the new shot feels already in motion

- **GSAP / HyperFrames:** Use timeline set calls to swap visibility of the two layouts at the same time (no transition tween), then a short fromTo on the anchor and its neighbours animating scale, xPercent and gradient position with an ease-out (power-type) or ease-in-out family; a gentle back-type ease can add a small overshoot to the settle.
- **Remotion:** Place the two shots in back-to-back Sequence blocks with no transition, aligning the anchor's position. Inside the second Sequence, interpolate with an ease-out curve drives a slight scale and translate drift; a spring with light overshoot is an option for the settle.

## Measured
- Duration: median 224 ms (n=4, 2 videos)
- Easing: ease out 27%, spring overshoot 27%, ease in out 25%, ease in 21%
- Changes: scale up 39%, color shift 26%, slide left 13%, slide right 13%
- Elements: icon 53%, background 27%, other 20%
- Sound: unsure 100%; offset to the landing median -235 ms (n=3, 1 videos)

## Sound
no typical sound

## Why it reads as premium
Keeping one shape or object fixed in the frame across a cut gives the eye a handhold, so a jump in angle or scale reads as continuous action rather than a jarring edit. Landing the cut on a narrated word gives it purpose, and a short drift after the cut folds the edit into a sense of forward motion. The result feels cinematic and deliberate without needing any visible transition effect.

## Examples
- `elevenlabs-introducing-eleven-v4-and-eleven-v4-turb` e010 (video score 4/5)
- `servicenow-what-are-servicenow-ai-agents` e015 (video score 3/5)

## Caveats
- Seen in only two videos with very few measured elements; no confidence interval could be computed
- Measured durations describe the post-cut drift, since the cut itself is instant
- All sound labels are unsure, so no sound guidance is given
