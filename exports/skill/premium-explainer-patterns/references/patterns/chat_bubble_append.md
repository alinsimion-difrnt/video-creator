# Chat Bubble Pops In

`chat_bubble_append`

A new message bubble, often with its sender's avatar, pops in at the bottom of a chat and drifts up into place while the earlier messages nudge upwards to make room.

## When to use
- Showing a conversation between a customer and an AI agent turn by turn
- Making a reply feel live, as if it is arriving right now
- Chaining one message after another so a demo keeps momentum

## Avoid when
- The full conversation must be readable at once; animating each bubble then just delays it
- Messages arrive so fast that the bubbles overlap their own entrances

## Build
1. Bring in the chat panel first and let it settle fully before any message arrives
2. Push the existing bubbles up slightly to open a slot at the bottom
3. Pop the new bubble and its avatar in together as one unit: fade up from slightly smaller and slightly lower
4. Optionally grow the bubble from a small pill before its text appears, so the reply slot shows first
5. Chain the next content, such as a reply or a row of cards, right after the bubble settles

- GSAP / HyperFrames: Timeline: a gsap.to moving existing bubbles up with a soft ease-in-out, then a fromTo on avatar and bubble (autoAlpha, scale from slightly smaller, y from slightly lower) with an ease-out (power out) and a tiny stagger between avatar and bubble. A light overshoot (back.out) is an option for a bouncier pop. Set transformOrigin at the bubble's top or tail edge.
- Remotion: One high-damping spring for the existing bubbles' upward drift; a delayed spring per new bubble mapped to opacity, scale and translateY. Keep damping high for the usual smooth ease-out settle, or lower it slightly for a small overshoot. Stagger later items by a frame offset on the spring.

## Measured in premium explainers
- Duration: 528-720 ms (typical 589), 1 videos
- Easing: ease out 90%, spring overshoot 10%
- Changes: slide up 54%, pop 30%, fade 10%, scale up 5%
- Sound offset to the landing: -245-274 ms (typical 18), 1 videos

## Sound
No typical sound: the mix is mostly unsure or music, with an occasional reverse swoosh near the bubble's arrival.

## Why it reads as premium
It mimics how real chat feels. The panel lands first so the eye reads the frame before the message, then each bubble arrives with its avatar as one decelerating unit, small and low then settling into place. Nudging the older messages up instead of jumping the layout keeps the composition balanced, and showing the empty reply slot before the text reads as genuine turn-taking. Chaining the next message right after keeps a conversation demo moving without feeling rushed.

## Caveats
- Seen in only two videos
- Timing and sound offset were measured in a single video
- Sound offset spread is wide, so there is no reliable sync point
