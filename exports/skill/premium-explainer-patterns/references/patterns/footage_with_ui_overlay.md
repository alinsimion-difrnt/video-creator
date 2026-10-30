# UI Layered Over Footage

`footage_with_ui_overlay`

A product window or card sits as a layer on top of live-action footage. The footage keeps playing underneath while the UI either stays put as a frosted overlay or slides off to hand the frame back to the people on screen.

## When to use
- Showing the product inside a real-world story rather than cutting to a screen recording
- Switching between a presenter and the product without a hard cut
- Pairing an action in the footage with the notification or approval it triggers

## Avoid when
- The footage is busy behind the card and makes the UI hard to read
- The UI needs close reading; a full-screen product shot works better

## Build
1. Lay the footage as the full-frame base layer and leave it untouched
2. Place the UI window or card above it, with a frosted semi-transparent fill or a framed window so it reads as a separate surface
3. Let the actors' own movement carry the shot while the overlay holds still
4. To hand back to the footage, slide the UI layer off the side of the frame with an accelerate-then-settle move
5. Optionally add a soft shadow on the leading edge while it travels

- GSAP / HyperFrames: The footage element does not animate. The overlay exits with a single gsap.to on xPercent past the frame edge, using an ease-out or a smooth power inOut ease; a linear move is also seen. For an overlay entrance, a fromTo on opacity, y, scale and a blur filter with an ease-out, optionally with a light overshoot.
- Remotion: An OffthreadVideo in a full AbsoluteFill as the base, with the UI in an AbsoluteFill above. The exit is an interpolate on translateX with an Easing.inOut curve rather than a spring; a card entrance can use a high-damping spring on opacity and translateY, with backdropFilter blur for the frosted look.

## Measured in premium explainers
- Duration: 163-627 ms (typical 351), 2 videos
- Easing: ease out 41%, spring overshoot 31%, linear 28%
- Changes: slide left 54%, other 46%
- Sound offset to the landing: 130-172 ms (typical 151), 1 videos

## Sound
no typical sound

## Why it reads as premium
Treating the UI as a physical layer over the real set puts the product inside the story instead of breaking away to a screen capture. A frosted card composited onto a meeting shot reads as part of the scene, and sliding a product window off a presenter returns the story to them without a cut, so the narration keeps flowing. Because the footage itself stays still or simply plays on, the only designed motion is the overlay, which makes that move feel deliberate rather than like a generic wipe.

## Caveats
- Seen in only two videos, with very few measured elements and no confidence interval
- Much of the measured motion is actors moving in the footage, not the UI itself
- In one example the overlay never animates, so its entrance timing was not measured
