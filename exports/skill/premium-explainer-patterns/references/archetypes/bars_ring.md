# Chart Card Build

`bars_ring`

A clean chart card appears and its data builds on screen: bars grow, a line draws across, or a ring fills in, often with a tooltip value following along. It turns a product claim into visible proof during the demo.

## When to use
- Showing a trend, share or comparison the product tracks
- Proving a claim with data right after the narration names it
- Singling out one bar, segment or series to make a point

## Slots (what you fill in)
- `chart_kind`: bars, line, stacked area, donut or ring
- `data_series`: the values or series to plot, kept short and readable
- `chart_label` (optional): a short all-caps label or panel title above the chart
- `highlight_item` (optional): one bar, segment or tooltip row to single out with colour or an outline
- `tooltip_value` (optional): a value that follows the line tip and counts up
- `legend_items` (optional): legend labels for each series or segment
- `background` (optional): a solid brand field or dark gradient stage behind the card

## The scene, beat by beat
1. The chart card or panel slides or fades into frame on a simple background
2. The axes or baseline settle and the label appears
3. The data builds: bars grow from the baseline in a stagger, a line draws left to right, or a ring sweeps clockwise
4. A tooltip or value rides the leading edge and counts up as the data lands
5. One item is singled out with a colour change or outline on the narration cue
6. The card holds briefly, then exits with a push, slide or blur into the next scene

Patterns: 

- GSAP / HyperFrames: One timeline per scene. Bring the card in with a short ease-out slide or an opacity-and-blur fade. Grow bars with scaleY from zero, transform-origin at the bottom, staggered left to right with power2.out or a soft back.out. Draw lines and rings with a stroke-dashoffset tween on an SVG path (sine.inOut or power1.inOut). Tween a tooltip along the path end with a counter tween on its number, snapped to integers. Add the highlight as a colour or outline tween placed at the narration word's time, then exit with a fast horizontal slide plus blur.
- Remotion: A Sequence for the card entrance, a Sequence for the data build and a Sequence for the highlight and exit. Drive bar heights with spring() offset per bar index (high damping, no overshoot) and line or ring drawing with interpolate() over strokeDashoffset. The tooltip value is interpolate() on the same progress, rounded. The highlight Sequence starts on the narration word's frame.

## Measured in premium explainers
- Scene length: 1.6-4.1 s (typical 3.0), 5 videos
- First motion after the scene starts: not measured
- Motion events per scene: 0-0 events (typical 0), 5 videos
- Way in: other 62%, push 15%, blur 8%
- click sound: 3.4-6.4 s (typical 4.9), 1 videos after the scene starts
- glitch sound: 0.6-2.7 s (typical 1.9), 2 videos after the scene starts
- impact sound: 0.6-2.7 s (typical 0.6), 2 videos after the scene starts
- music sound: 1.4-4.8 s (typical 3.1), 1 videos after the scene starts
- swoosh reverse sound: 0.1-1.4 s (typical 0.4), 2 videos after the scene starts
- unsure sound: 0.8-1.6 s (typical 1.3), 2 videos after the scene starts

## Sound
No typical sound. Labels are mixed and often unsure; when a cue is heard it is usually a soft impact or a reverse swoosh near the start as the card lands, with the occasional glitch or click later on a highlight.

## Caveats
- No measured motion events or patterns for these shots; the build is drawn from the shot descriptions, and the chart draw-on pattern has no card yet.
- Mixed members: bar, line, stacked area and donut charts are grouped together.
- Sound labels are mixed and largely unsure, so there is no reliable sound cue.
