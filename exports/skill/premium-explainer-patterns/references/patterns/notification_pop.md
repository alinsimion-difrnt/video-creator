# Message Card Pops In

`notification_pop`

A new message, notification or small UI card appears with its avatar or icon, fading in while it rises or grows slightly and then gently decelerates into place. It feels like something just arrived rather than being switched on.

## When to use
- A new chat message, reply or alert arrives in a conversation or feed
- An overlay card appears over footage or a scene to tie the product to a story beat
- Landing a message on the exact narrated line that introduces it

## Avoid when
- Many cards arrive at once, where a staggered list reveal reads better
- The message should feel like it is being written, where typing or streaming fits better
- The surrounding thread is moving, which blurs the sense of a single arrival

## Build
1. Place the card where it will rest, grouped with its avatar or icon so they move as one unit.
2. Start it invisible, slightly lower and slightly smaller than its final state.
3. Fade it in quickly while it rises and grows into place with a long, decelerating settle and no bounce.
4. If the card has inner content, reveal the header first, then the icon and title, then the inner panel in quick nested stages.
5. Keep the rest of the thread or scene still so the new arrival is the only motion.
6. Time the arrival to the narration line that introduces the message.

- GSAP / HyperFrames: Use gsap.fromTo on the bubble and avatar together with autoAlpha, a small y offset and a slight scale, using a strong power or expo ease-out, with no stagger or a tiny one. For an overlay card, chain nested fromTo tweens (card scaleY from its top edge, then icon and title fades, then the inner panel scale) overlapped with negative position offsets. Spring overshoot is rare; keep it settling without a bounce.
- Remotion: Drive translateY and scale from a critically or heavily damped spring (no overshoot) applied to bubble and avatar together, with opacity from a fast interpolate over the first part of the spring. For nested overlay cards, use a second delayed spring for the inner panel.

## Measured in premium explainers
- Duration: 519-654 ms (typical 603), 2 videos
- Easing: ease out 76%, ease in out 8%, linear 8%, spring overshoot 8%
- Changes: fade 38%, slide up 27%, scale up 19%, pop 11%
- Sound offset to the landing: -220-379 ms (typical 88), 1 videos

## Sound
No typical sound: the arrivals usually sit on the music bed with no distinct cue.

## Why it reads as premium
The card and its avatar travel as one unit, so the message reads as a single object being delivered, and a fast fade with a long decelerating settle makes it feel calm and real rather than abruptly switched on. Letting the avatar overhang the panel edge, or rendering the card as frosted glass over footage, adds depth and keeps the product inside the story's space. Because the rest of the thread stays still and the arrival is timed to the narration, the viewer's eye goes straight to the new message.

## Caveats
- Seen in only two videos, and most member events come from a single chat-style video.
- Few events and measured elements overall, so the timing range is indicative.
- Sound offset comes from a single video with very few measurements and no confidence interval.
