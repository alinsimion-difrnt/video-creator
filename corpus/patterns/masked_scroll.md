# Content Scrolls Inside A Window

`masked_scroll` · 35 events in 10 videos

A list, chat thread or stack of cards slides up (or down) inside a fixed frame, so old items leave through the frame's edge and new ones arrive, while everything around the frame stays still.

## When to use
- Showing progress piling up, such as an agent finishing steps or a chat getting new replies
- Revealing how much is in a list or menu without cutting away
- Linking one statement to the next as if they were lines of one continuous document
- Moving the viewer's reading position to where the next beat begins

## Avoid when
- The scroll is tiny and incidental; it reads as an accidental nudge, not an authored move
- The surrounding interface also moves, which removes the calm anchor the mask provides
- The viewer needs to read the content that flies past

## How to build it
1. Put the moving content in a container clipped by a fixed panel or window so nothing shows outside its edges.
2. Keep headers, footers, overlays and neighbouring panels outside the clipped container so they stay put.
3. Move the whole content container up (or down) as one piece, easing into a soft stop on the item that matters next.
4. Fade or slide the newly arriving item in as it enters the window, landing it in its slot.
5. Optionally keep a scrollbar thumb, a cursor or a gentle camera push in sync with the scroll.
6. Start the next beat, such as streaming text or a reply, right where the scroll settles.

- **GSAP / HyperFrames:** Wrap the content in an overflow-hidden viewport and tween the inner container with gsap.to on y, usually a power ease-out or a power ease-in-out for a fast jump between distant positions; linear or stepped tweens suit terminal-style hard redraws. Bring the new row in with gsap.fromTo on y and autoAlpha, placed on the timeline with '<' so it travels with the scroll, and tie any scrollbar thumb to the same progress.
- **Remotion:** Drive the container's translateY with interpolate and an Easing.out or Easing.inOut curve, clamped at the end, inside an overflow:hidden element; or use a well-damped spring for a softer settle, with a lightly underdamped spring only when a small overshoot is wanted. Map scrollbar, push-in scale and the new item's opacity from the same progress value.

## Measured
- Duration: median 453 ms, 90% interval 355 to 667 (n=73, 7 videos)
- Easing: ease out 29%, ease in out 28%, linear 17%, ease in 15%
- Changes: slide up 52%, fade 15%, slide down 11%, color shift 6%
- Elements: body text 18%, card 17%, list item 16%, ui panel 12%
- Sound: music 50%, unsure 20%, impact 15%, chime 11%; offset to the landing median 165 ms, 90% interval 104 to 216 (n=55, 4 videos)

## Sound
No typical sound: the bed is mostly music or unclear. When a cue is present it is usually a soft impact or chime landing just after the scroll starts.

## Why it reads as premium
The mask does the heavy lifting: content advances while the frame, headers and side panels stay anchored, so the viewer keeps their place and never feels a cut. A single continuous scroll compresses a long run of work or a long list into one readable gesture that says 'a lot happened', and decelerating into the next important item gives the move a clear landing that hands off straight into the next beat. Details like a frosted overlay blurring content beneath it or a synced scrollbar make it feel like real, living software rather than a slideshow.

## Examples
- `anthropic-introducing-claude-design-by-anthropic-l` e007 (video score 4/5)
- `attio-introducing-ask-attio` e012 (video score 4/5)
- `raycast-new-raycast-coming-2026` e003 (video score 4/5)
- `warp-introducing-warp-2-0-the-agentic-develo` e005 (video score 4/5)
- `zendesk-meet-zendesk-ai-agents-the-most-autonom` e013 (video score 4/5)

## Caveats
- Timing spread is wide: quick jumps and slow screen-recorded scrolls are grouped together, so pick the short or long end to suit the content.
- Easing is mixed with no dominant family; ease-out and ease-in-out lead only narrowly.
- Sound offsets come from only a few videos, so the sound guidance is weak.
