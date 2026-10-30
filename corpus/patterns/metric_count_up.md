# Number Counts To Target

`metric_count_up` · 1 events in 1 videos

A key number changes step by step on screen, counting toward its final value, and then settles a little larger with a small accent so the final figure lands as the takeaway.

## When to use
- The narration makes a claim about a number: time saved, speed, growth or scale
- Turning an abstract metric into something that feels physical and earned
- Building tension toward a single headline figure

## Avoid when
- The exact figure matters less than the idea behind it
- Several numbers would compete on screen at once
- There is no time for the final value to rest and be read

## How to build it
1. Show the starting value on a clear card or label with its caption
2. Step the number toward the target, for example by flipping or tearing off cards to reveal the next value
3. Speed the steps up as the count nears the end to build tension
4. Let the final value settle slightly larger than the steps before it
5. Draw a small accent line or mark near the final value to close the beat
6. Time the landing to the word in the narration that names the unit or claim

- **GSAP / HyperFrames:** Stack one node per value with only the top visible, and in a timeline tween each top node off with rotation, a small 3D tilt, translate and autoAlpha, overlapping successive tweens more and more (or ramp the timeline's timeScale) so the count accelerates. Settle the final node with a scale tween and a gentle overshoot, then draw the accent rule with a scaleX tween from a left transform origin. Easing was not measured for this pattern, so choose ease families by eye.
- **Remotion:** Compute each step's start frame with shrinking gaps, and drive each outgoing card's rotate, translate and opacity with interpolate and an easing curve, clamped on both sides. Use a spring with slight overshoot for the final value's scale, and interpolate the accent rule's scaleX. For a plain digit counter, interpolate the value and round it per frame.

## Measured
- Duration: not measured
- Easing: none
- Changes: rotate 25%, scale up 25%, count up 8%, draw on 8%
- Elements: label 40%, card 20%, metric 20%, other 20%
- Sound: chime 75%, unsure 25%; offset to the landing not measured

## Sound
Usually a light chime as the count lands; its exact placement relative to the motion was not measured.

## Why it reads as premium
Counting on screen makes a numeric claim feel physical rather than stated: each step is a small, tangible event, and an accelerating rhythm builds anticipation before a calm, enlarged landing on the final figure. Real-feeling details such as 3D tilt and contact shadows on the outgoing cards, plus a single accent drawn on at the end, give the moment weight, and syncing the landing to the narration lets the number and the claim hit together.

## Examples
- `elevenlabs-introducing-elevenlabs-conversational-ag` e035 (video score 5/5)

## Caveats
- Seen in only 1 video and 1 event, so this card describes a single example
- Timing was not measured: duration, easing and sound offset are all missing
- The only example counts down rather than up; the build applies in either direction
