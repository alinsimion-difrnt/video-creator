# List Items Arrive In Turn

`stagger_list_reveal` · 11 events in 6 videos

The items of a list, row or panel appear one after another in quick succession, each fading in while rising or sliding a short distance into place, so the group builds up in reading order.

## When to use
- Revealing steps, settings, results or integrations that should read as an ordered set
- Visualising reasoning or progress as a checklist that fills in
- Bringing an empty panel or launcher to life without a hard pop

## Avoid when
- The list is long enough that waiting for the last item drags
- Items are unrelated, so a sequence implies an order that is not there

## How to build it
1. Lay out the final list, then offset each item slightly below or to the side and make it transparent
2. Optionally grow or unmask the container first, overlapping its growth with the first items
3. Bring each item to its resting place with a fade and short slide, starting each a beat after the previous one
4. Keep every item on the same distance, ease and baseline so the cascade reads as one rhythm
5. Add grouping or focus cues, such as a tray or a selection highlight, as the last item lands

- **GSAP / HyperFrames:** One gsap.fromTo() on the item selector from {autoAlpha: 0, y or x offset, optional filter blur} to rest, with an ease_out family (power2.out or power3.out) and a small stagger in reading order. Run the container's scale, height or clipPath reveal on the same timeline with '<' so they overlap; use ease_in_out (power2.inOut) for any accompanying camera drift. A back.out ease suits an occasional spring_overshoot pop on the first item.
- **Remotion:** For item i, compute spring({frame: frame - i * delay, fps}) with high damping (no overshoot) and map it to opacity, translate and optional blur with interpolate(). Drive the container from its own spring or an interpolate() with Easing.out, and fade any grouping tray in after the last item's delay.

## Measured
- Duration: median 689 ms, 90% interval 581 to 756 (n=43, 5 videos)
- Easing: ease out 53%, ease in out 21%, spring overshoot 11%, linear 7%
- Changes: fade 43%, slide up 27%, slide left 13%, blur in 6%
- Elements: list item 43%, logo 22%, card 10%, avatar 6%
- Sound: music 55%, impact 17%, swoosh reverse 17%, unsure 11%; offset to the landing median 9 ms, 90% interval -79 to 105 (n=43, 2 videos)

## Sound
No typical sound: most detected audio is music. When an effect is used it is a light impact or reverse swoosh landing roughly with the cascade, sometimes a faint tick per item.

## Why it reads as premium
A tight cascade lets the eye read the items as an ordered sequence instead of a block that pops in all at once, which turns a flat row of icons or steps into a quick roll call or a visible line of reasoning. Every item sharing the same short travel, soft ease-out and baseline gives the reveal a single rhythm, and overlapping the container's growth with the items means the panel never shows empty space. Small finishing cues, like a tray fading in behind the last icon or a selection highlight arriving with the first row, tell the viewer how the group fits together and where to look next.

## Examples
- `anthropic-introducing-claude-design-by-anthropic-l` e004 (video score 4/5)
- `notion-introducing-notion-ai-connectors` e001 (video score 4/5)
- `notion-introducing-the-new-notion-ai` e014 (video score 4/5)
- `raycast-new-raycast-coming-2026` e002 (video score 4/5)
- `zendesk-meet-zendesk-ai-agents-the-most-autonom` e027 (video score 4/5)

## Caveats
- Few events, from a small number of videos
- Sound timing comes from only two videos, so the sound guidance is weak
