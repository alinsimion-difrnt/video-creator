# Words Arrive With Momentum

`kinetic_word_reveal` · 28 events in 12 videos

A headline appears word by word (or as one big word), each piece fading in while it slides, scales or sharpens from a blur and then settles softly into place.

## When to use
- Title cards and taglines that should feel spoken rather than pasted on
- Landing a key word exactly on the narration or a music hit
- Swapping one statement for the next so the new line reads as the answer to the old one
- Turning a product name into a bold, cinematic moment

## Avoid when
- Long sentences or body copy, where staggered words slow reading
- Several animated headlines in a row, which makes the effect feel routine
- The background is already busy and moving fast

## How to build it
1. Split the headline into words, and the key word into letters if it gets its own accent.
2. Start each word invisible and offset: a little low, to one side, slightly larger, or blurred.
3. Bring the words in one after another with a short stagger, fading up while they travel to rest.
4. Let the motion decelerate so each word glides into place rather than stopping hard.
5. Give the final or most important word a small extra accent, such as a wobble, tilt or sparkle pop.
6. When replacing a line, send the old one out in the same direction the new one arrives so the motion stays continuous.

- **GSAP / HyperFrames:** Split the text into word spans and use tl.from or tl.fromTo on autoAlpha plus y or x, with optional scale and filter blur, eased mostly with a power ease-out (an ease-in-out for slower glides) and a stagger between words. Use a back ease-out only for a small overshoot accent on the key word or a decorative pop; for line swaps, tween the old line out with an ease-in and overlap the new line's entry using a '<' position offset.
- **Remotion:** Give each word its own spring delayed by its index, using a heavily damped config so it settles without overshoot, and map that progress through interpolate to opacity, translate, scale and blur. Reserve a lightly damped spring for the accent word or sparkle; plain interpolate with an Easing.out curve works for clip-path or mask reveals.

## Measured
- Duration: median 577 ms, 90% interval 501 to 692 (n=67, 11 videos)
- Easing: ease out 55%, ease in out 26%, ease in 7%, spring overshoot 6%
- Changes: fade 35%, slide up 13%, color shift 12%, slide left 10%
- Elements: headline 71%, background 15%, icon 3%, other 3%
- Sound: music 36%, unsure 36%, swoosh reverse 21%, impact 8%; offset to the landing median 45 ms, 90% interval -37 to 149 (n=49, 8 videos)

## Sound
No typical sound: most events sit on music or an unclear cue. When there is a cue it is often a reverse swoosh building into the word's landing, sometimes a soft impact, lined up closely with the reveal.

## Why it reads as premium
Type that moves with weight reads as voice: words that streak, rise or rack into focus and then settle feel like they are being said, not displayed. The best examples time the key word to the narration or a beat and give it a tiny physical reaction, which puts emphasis exactly on the idea being sold. Overlapping a departing line with an arriving one in a single direction makes successive statements feel like one thought, and depth cues such as blur and scale turn a plain title card into something cinematic without stock effects.

## Examples
- `meta-introducing-meta-quest-3-coming-this-f` e005 (video score 5/5)
- `attio-introducing-ask-attio` e005 (video score 4/5)
- `elevenlabs-introducing-eleven-v4-and-eleven-v4-turb` e016 (video score 4/5)
- `hubspot-what-is-hubspot` e008 (video score 4/5)
- `loom-introducing-loom-ai` e001 (video score 4/5)

## Caveats
- Sound timing varies widely: cues land before, on or after the reveal, so treat the sound guidance as loose.
- Measured timing mixes whole-line reveals with per-word staggers; the duration describes the overall move, not each word.
- Several examples come from the same video, so its house style is over-represented.
