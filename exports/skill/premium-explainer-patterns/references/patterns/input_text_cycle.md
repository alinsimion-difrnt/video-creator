# Rotating Word Slot

`input_text_cycle`

The start of a sentence stays fixed while its ending, a word, phrase or option pill, keeps flipping vertically to the next alternative with a soft blur, like a slot machine, until a final line lands.

## When to use
- Listing several use cases, audiences, data sources or integrations inside one sentence
- A headline that should read as both marketing copy and product UI
- Building rhythm on music beats before a payoff line

## Avoid when
- The alternatives are long or need explaining; viewers only catch a glance of each
- The stem would have to reflow as the words change width

## Build
1. Set the fixed sentence stem and a masked slot where the changing part sits
2. Bring the first option into the slot from below, fading and sharpening from a blur as it rises
3. For each swap, push the current option up and out with a blur while the next rises in from below, overlapping slightly
4. Optionally keep faint, blurred neighbours above and below so the options feel like a continuous wheel
5. Resize a pill to fit each new label so the sentence keeps reading naturally
6. Resolve the cycle with a plain-type completion or the last option, landing in the same rhythm

- GSAP / HyperFrames: Inside an overflow-hidden slot, run a timeline per swap: gsap.to the outgoing word (yPercent up, opacity to zero, blur up, ease-in) and an overlapping gsap.fromTo on the incoming word (from below with blur to rest, ease-out). For a wheel of pills, tween the whole stack's y with ease-in-out and set each pill's opacity and blur by its distance from the slot.
- Remotion: Use a damped spring per swap with no overshoot as the progress value; map it with interpolate to translateY, opacity and blur on the incoming word, and drive the outgoing word with a short ease-in interpolate. For a wheel, derive each pill's offset, opacity and blur from its distance to the current index plus progress.

## Measured in premium explainers
- Duration: 124-421 ms (typical 191), 3 videos
- Easing: ease in out 40%, ease in 40%, ease out 20%
- Changes: fade 34%, slide up 29%, blur in 16%, blur out 13%
- Sound offset to the landing: -337-21 ms (typical -122), 1 videos

## Sound
No typical sound; the corpus examples sit under music only. Place each swap on a music beat rather than adding an effect.

## Why it reads as premium
Holding the sentence stem still and swapping only its ending turns a list of features into one line that keeps rebuilding, so the viewer reads a claim instead of a bullet list. The vertical flip with motion blur sells speed without harsh edges, and faint neighbouring options make it feel like a wheel with more to come. A steady cadence locked to the music builds rhythm, and ending on a plain-type payoff gives the cycle a clear resolution without a cut.

## Caveats
- Seen in only three videos, with most events from a single one
- Members are mostly headline word swaps and option pills rather than literal input fields, so the pattern name may be narrower than what was observed
- Sound timing comes from a single video
