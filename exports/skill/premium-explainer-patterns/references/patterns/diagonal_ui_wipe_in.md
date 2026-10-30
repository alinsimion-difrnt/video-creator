# UI Wipes Over Title

`diagonal_ui_wipe_in`

The product screen sweeps in over a title card along a moving edge, either a slanted diagonal edge or a stack of coloured bands rising from below. Once it lands, the rest of the UI and a caption assemble on top.

## When to use
- Leaving a title or chapter card and handing straight into a product demo
- Keeping scene changes branded and consistent when the video already uses a slash or band motif
- Introducing a feature name over the screen it describes

## Avoid when
- The video has no matching transition style; a lone wipe looks out of place
- Cuts are frequent and a wipe on each would slow the pace

## Build
1. Keep the title card on screen and, for the band style, start nudging it up
2. Sweep the UI layer in with a moving mask: a diagonal clip edge from a corner, or full-width brand-coloured bands rising in quick succession
3. Let the UI land slightly over-scaled and settle to its normal size
4. Make the last band or the revealed screen become the UI background
5. Bring in secondary pieces on top, such as a sidebar sliding from the side or a card fading up
6. Wipe a caption banner across the UI to name the feature after the screen has landed

- GSAP / HyperFrames: A timeline tweening clipPath (a diagonal polygon, or inset for the caption) on the UI layer, together with a scale settling down to one; for bands, a fromTo on yPercent with a small stagger. Use ease-in-out (power inOut) for the sweep and ease-in where the outgoing title accelerates away. Follow with the sidebar slide and caption wipe overlapping the end of the sweep.
- Remotion: Interpolate a wipe progress on frame with an in-out bezier curve and map it to a diagonal polygon clipPath and the UI's settling scale; bands are the same interpolate offset by a few frames each. The caption banner and sidebar use a delayed high-damping spring mapped to inset or translate.

## Measured in premium explainers
- Duration: 173-988 ms (typical 580), 1 videos
- Easing: ease in out 50%, ease in 50%
- Changes: mask reveal 33%, slide right 17%, slide up 17%, fade 8%
- Sound offset to the landing: not measured

## Sound
no typical sound

## Why it reads as premium
A branded wipe turns a scene change into a designed moment instead of a plain cut. Brand-coloured bands or a slash edge that repeats the video's own transition motif make every change feel part of one system, and the last band or revealed screen becomes the product background, so the hand-off into the demo is seamless. Landing the UI first and only then wiping in a bright caption lets viewers take in real product context before reading the feature name, and the banner stays legible on a busy screen without dimming it.

## Caveats
- Seen in only two videos, and timing comes from very few measured elements in one of them, with no confidence interval
- No sound was measured for this pattern
- The two examples differ in style (diagonal edge versus rising bands)
