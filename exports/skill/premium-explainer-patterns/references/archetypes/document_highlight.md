# Document Highlight Callout

`document_highlight`

A document, report, table or answer card fills the frame while the camera holds close and highlights or outline boxes land on the exact lines the narration talks about. It points the viewer's eye at the one detail that proves the point.

## When to use
- Explaining how the product works by pointing at the part of a page that matters
- Walking through a report or table one figure or line at a time
- Showing what the product marks up, tags or finds inside content

## Slots (what you fill in)
- `document`: the page, report, table or answer card being shown
- `focus_regions`: the lines, columns or rows to highlight, in narration order
- `highlight_style`: a translucent colour bar, an outline box, or a colour tag flash
- `cue_words`: the narration words each highlight lands on
- `tags` (optional): small badges or chips that pop onto the document to show markup
- `frame` (optional): the window, card or tilted plane that holds the document

## The scene, beat by beat
1. The document card settles in, or the view crossfades or cuts to the page
2. The camera pushes in close on the area of interest, sometimes with a slight tilt
3. Text or rows type or stream in where the content is being produced
4. A highlight sweeps or an outline box draws around the first region on its cue word
5. The highlight moves to the next region, or tags pop on, as the narration continues
6. The view holds while the narration lands, then blurs, crossfades or cuts out

Patterns: 

- GSAP / HyperFrames: One timeline per scene, with labels at the narration word times. Push the document layer in with a scale and position tween (power2.out), optionally with a small rotationX or rotationY for tilt. Reveal a highlight as a translucent rect whose width or height tweens from zero (power2.out), or an outline drawn with stroke-dashoffset or faded in and out. Move the outline to the next region with a short position-and-size tween. Pop tags with a scale tween using back.out. Exit with a blur and opacity tween.
- Remotion: A Sequence for the push-in and hold, and one Sequence per highlight starting on its cue word's frame. Use spring() with high damping for the camera push, interpolate() for highlight size and outline stroke, and a lightly underdamped spring() for tag pops. The final Sequence crossfades or blurs out.

## Measured in premium explainers
- Scene length: 3.7-15.7 s (typical 8.7), 6 videos
- First motion after the scene starts: 0.0-0.0 s (typical 0.0), 1 videos
- Motion events per scene: 0-0 events (typical 0), 6 videos
- Way in: other 51%, crossfade 18%, hard cut 15%
- chime sound: 29.6-29.6 s (typical 29.6), 1 videos after the scene starts
- click sound: 11.4-16.3 s (typical 13.4), 2 videos after the scene starts
- impact sound: 2.1-9.7 s (typical 6.0), 2 videos after the scene starts
- music sound: 3.8-22.4 s (typical 5.5), 4 videos after the scene starts
- swoosh reverse sound: 12.8-22.9 s (typical 18.5), 1 videos after the scene starts
- unsure sound: 2.0-19.0 s (typical 12.4), 2 videos after the scene starts

## Sound
Mostly a music bed under the narration with sparse effects. Clicks and reverse swooshes come late in the scene as highlights move or the page changes; soft impacts can mark a highlight landing. A chime is rare.

## Caveats
- Almost no measured motion events and the only pattern label is other, so no pattern cards are listed; spotlight focus and ui camera push in fit the descriptions.
- Mixed members: some shots are long multi-phase scenes that also include typing, particle and logo moments.
- Scene length varies widely, so sound offsets are spread out and hard to generalise.
