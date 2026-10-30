# Prompt Types Itself In

`prompt_type_on`

Text appears character by character in a focused input or prompt field, often with a blinking caret, while the view gently drifts to keep the field centred and the cursor heads for the send button.

## When to use
- Showing a user asking an AI assistant a question or giving it an instruction
- Filling in a configuration form or renaming something live in the product
- Setting up the moment just before an answer or result appears

## Avoid when
- The typed text is long enough that viewers cannot read it at the typing pace
- The input content does not matter to the story; show the result instead

## Build
1. Open or focus the input, marking focus with a ring or glow
2. Reveal the text character by character, in small bursts for a realistic cadence, with a caret after the last character
3. Let the field grow if the text wraps, and drift or scroll the view so the field stays near the centre
4. Move the cursor toward the send button or next field while typing finishes
5. On send, clear the input and show the same text as a sent message bubble that softly rises in
6. Hand focus to the next field or start the answer so momentum continues

- GSAP / HyperFrames: Type with a linear tween using TextPlugin (or a character-split stagger with a near-zero duration per character). Run parallel tweens with ease-out for the view drift, field growth and focus glow, ease-in-out for cursor travel, and a light back-style overshoot for a sent bubble or panel pop.
- Remotion: Slice the string by a frame-driven character count from interpolate with clamping, and toggle caret opacity on a frame cycle. Drive the view drift and field height with a damped spring or interpolate with an ease-out curve, and the cursor with an ease-in-out interpolate.

## Measured in premium explainers
- Duration: 313-959 ms (typical 533), 3 videos
- Easing: ease out 50%, linear 25%, spring overshoot 13%, ease in out 13%
- Changes: slide up 28%, typewriter 20%, fade 16%, highlight 12%
- Sound offset to the landing: 25-198 ms (typical 67), 2 videos

## Sound
No settled sound: labelled moments split evenly between music, an impact and a reverse swoosh, landing just after the visual change. A soft impact or reverse swoosh on send works if the mix has room.

## Why it reads as premium
Typing reads as a real product interaction rather than a mockup, especially when the characters arrive in quick, uneven bursts and the caret is visible. Premium versions run several things at once: the text types, the view drifts to keep the field centred, a focus glow leads the eye, and the cursor is already moving toward the next control. That makes the step feel effortless and fast. The send beat is handled cleanly, with the input clearing and the message rising into the thread, so the viewer is primed for the answer without a pause.

## Caveats
- Timing comes from few measured elements in only a handful of videos, and the confidence interval is wide
- Sound evidence comes from just two videos with no agreement on the effect
- Measured durations cover the surrounding moves as well as the typing itself; set typing speed by readability
