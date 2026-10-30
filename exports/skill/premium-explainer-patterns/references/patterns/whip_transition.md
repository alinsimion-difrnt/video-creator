# Fast Whip To Next Scene

`whip_transition`

The current scene shoots off screen in a very fast, motion-blurred sweep, as if the camera was flicked, and the next scene sweeps in behind it and settles, often with a headline landing as the blur clears.

## When to use
- Jumping between two related scenes while keeping the sense of one continuous world
- Marking a change of time, place or topic that the narration calls out
- Adding energy between beats of a fast feature reel

## Avoid when
- The video is calm or instructional and needs a gentle pace
- Several whips would land back to back and tire the viewer
- The outgoing scene holds detail the viewer still needs to read

## Build
1. Pick the whip direction (up or sideways) and keep both scenes on one shared container
2. Accelerate the outgoing content off frame while adding a strong motion blur
3. Bring the incoming scene in from the opposite side with blur, decelerating as it arrives
4. Clear the blur as the new scene settles into place
5. Land the headline or key word as the motion resolves, line by line if there are several

- GSAP / HyperFrames: A timeline: a to tween moving the outgoing scene by xPercent or yPercent with a filter blur on an ease-in (power-type), overlapping a fromTo bringing the incoming scene in with an ease-out and blur returning to zero. Headline lines follow with a staggered fromTo on opacity and y; an ease-in-out or back-type ease can give the landing a slight overshoot.
- Remotion: Use interpolate on translateX or translateY with an ease-in curve for the exit and an ease-out curve for the entry, plus a blur filter that peaks mid-whip. Background elements and headline lines can settle on a spring, mildly underdamped if a small overshoot is wanted, driving translate and opacity.

## Measured in premium explainers
- Duration: 645-1473 ms (typical 1403), 1 videos
- Easing: spring overshoot 34%, ease out 33%, ease in 17%, ease in out 16%
- Changes: slide up 43%, fade 21%, blur out 14%, blur in 7%
- Sound offset to the landing: not measured

## Sound
no typical sound

## Why it reads as premium
A whip reads as the camera itself moving rather than an edit, so two scenes feel like parts of one continuous space instead of separate clips. The heavy motion blur hides the hand-off and keeps the cut energetic, while timing the landing to a narrated change gives the move a reason. Letting the new headline arrive only as the blur clears, with a short empty beat or oversized type layered over the footage, turns the landing frame into a clear message moment.

## Caveats
- Seen in only two videos, and element timing was measured in only one of them
- Measured durations cover the settling elements and headline, not just the whip itself, so they run longer than the sweep
- No sound was measured for this pattern
