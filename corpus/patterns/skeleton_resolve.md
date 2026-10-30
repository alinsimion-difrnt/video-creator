# Placeholders Resolve Into Data

`skeleton_resolve` · 7 events in 2 videos

An empty or loading view (grey placeholder bars, a blank panel or a spinner) fills in with the real content: headers first, then numbers, cards or text appear almost instantly in place. The frame around it stays still, so the data seems to land where it belongs.

## When to use
- Showing that the product computes or fetches data live
- Switching a report, view or version and landing the new data on the narrated word
- Presenting structure first and data second, such as an empty chart that then populates
- Trimming a real loading wait down to a near-instant swap

## Avoid when
- The viewer needs to read the individual values as they appear
- The loading state would make the product look slow
- There is no real placeholder or empty state to resolve from

## How to build it
1. Keep the surrounding window chrome, sidebar or frame fixed throughout.
2. Show the empty state: placeholder bars, a blank panel, a spinner or a dim loading overlay.
3. Remove the placeholder or spinner almost instantly rather than with a slow fade.
4. Reveal the structure first (header band, title, axis chips), then the data cells, cards or bubbles.
5. Sweep the data in with a very quick stagger across columns or items so it reads as a data load, not a designed animation.
6. Optionally add a tiny scale settle on the new view, and time the arrival to the narration.

- **GSAP / HyperFrames:** Use tl.set to hide the spinner or skeleton, then gsap.fromTo on the content with autoAlpha from hidden to visible, a very short power ease-in or ease none, and a tiny stagger along the grid axis (headers before cells). A light back.out spring-overshoot or ease-in-out scale settle can follow on the whole panel. A faithful replica of a native load uses tl.set steps with no tween at all.
- **Remotion:** Switch from the placeholder layer to the content at a fixed frame, then drive each cell or block's opacity with interpolate over a frame or two, offset per column or item. Use no spring for the data itself; a highly damped spring or interpolate with Easing.out is only for an optional panel scale settle.

## Measured
- Duration: median 42 ms, 90% interval 42 to 98 (n=16, 1 videos)
- Easing: ease in 69%, spring overshoot 19%, ease in out 12%
- Changes: fade 80%, other 11%, color shift 2%, highlight 2%
- Elements: metric 30%, body text 14%, button 14%, ui panel 14%
- Sound: none; offset to the landing not measured

## Sound
No typical sound: no sound cues were tagged for this pattern.

## Why it reads as premium
Instead of cutting to a finished screen, premium product demos let the viewer watch the data arrive inside a stable frame, which makes the product's computation feel live and real. The wait is trimmed to almost nothing, so the product feels fast rather than slow, and showing structure before data teaches the layout of the view before the numbers fill it. Landing the resolve on the narrated promise, such as the moment the voiceover names the insight or the new forecast, makes cause and effect obvious without any added graphics.

## Examples
- `workday-workday-adaptive-planning-demo-finan` e049 (video score 3/5)
- `atlassian-introduction-to-jira-product-discovery` e028 (video score 3/5)

## Caveats
- Seen in only two videos, both screen-recorded tutorials, and timing was measured in just one of them.
- Measured durations are close to a single frame, so they reflect recorded UI loads rather than a designed animation.
- No sound was measured, and several members are spinner-to-content swaps rather than true placeholder bars.
