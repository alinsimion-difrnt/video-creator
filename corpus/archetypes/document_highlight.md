# Document Highlight Callout

`document_highlight` · 10 shots in 6 videos

A document, report, table or answer card fills the frame while the camera holds close and highlights or outline boxes land on the exact lines the narration talks about. It points the viewer's eye at the one detail that proves the point.

## When to use
- Explaining how the product works by pointing at the part of a page that matters
- Walking through a report or table one figure or line at a time
- Showing what the product marks up, tags or finds inside content

## What you fill in
- **document**: the page, report, table or answer card being shown
- **focus_regions**: the lines, columns or rows to highlight, in narration order
- **highlight_style**: a translucent colour bar, an outline box, or a colour tag flash
- **cue_words**: the narration words each highlight lands on
- **tags** (optional): small badges or chips that pop onto the document to show markup
- **frame** (optional): the window, card or tilted plane that holds the document

## The scene, beat by beat
1. The document card settles in, or the view crossfades or cuts to the page
2. The camera pushes in close on the area of interest, sometimes with a slight tilt
3. Text or rows type or stream in where the content is being produced
4. A highlight sweeps or an outline box draws around the first region on its cue word
5. The highlight moves to the next region, or tags pop on, as the narration continues
6. The view holds while the narration lands, then blurs, crossfades or cuts out

Patterns: 

- **GSAP / HyperFrames:** One timeline per scene, with labels at the narration word times. Push the document layer in with a scale and position tween (power2.out), optionally with a small rotationX or rotationY for tilt. Reveal a highlight as a translucent rect whose width or height tweens from zero (power2.out), or an outline drawn with stroke-dashoffset or faded in and out. Move the outline to the next region with a short position-and-size tween. Pop tags with a scale tween using back.out. Exit with a blur and opacity tween.
- **Remotion:** A Sequence for the push-in and hold, and one Sequence per highlight starting on its cue word's frame. Use spring() with high damping for the camera push, interpolate() for highlight size and outline stroke, and a lightly underdamped spring() for tag pops. The final Sequence crossfades or blurs out.

## Measured
- Scene length: median 8.7 s, 90% interval 3.8 to 15.9 (n=10, 6 videos)
- Motion events per scene: median 0.0 events, 90% interval 0.0 to 0.0 (n=10, 6 videos)
- First motion: median 0.0 s (n=1, 1 videos) after the scene starts
- Way in: other 51%, crossfade 18%, hard cut 15%, push 8%
- Story beat: demo 40%, mechanism 36%, agitate 9%, proof 9%
- Sound: music 31%, click 24%, unsure 16%, impact 13%

## Sound cues
Mostly a music bed under the narration with sparse effects. Clicks and reverse swooshes come late in the scene as highlights move or the page changes; soft impacts can mark a highlight landing. A chime is rare.
- chime: median 29.6 s (n=1, 1 videos) after the scene starts
- click: median 13.4 s, 90% interval 11.7 to 16.2 (n=9, 2 videos) after the scene starts
- impact: median 6.0 s, 90% interval 0.7 to 20.1 (n=5, 2 videos) after the scene starts
- music: median 5.5 s, 90% interval 4.1 to 18.0 (n=13, 4 videos) after the scene starts
- swoosh reverse: median 18.5 s, 90% interval 9.4 to 25.4 (n=5, 1 videos) after the scene starts
- unsure: median 12.4 s, 90% interval 2.0 to 23.4 (n=6, 2 videos) after the scene starts

## Examples
- `workday-workday-adaptive-planning-demo-finan` s010 (video score 3/5)
- `ahrefs-ahrefs-brand-radar-see-any-brand-s-ai-v` s006 (video score 4/5)
- `conductor-conductor-ai-get-found-in-ai-search` s009 (video score 4/5)
- `fullstory-behavioral-data-made-simple-by-fullstory` s006 (video score 4/5)
- `amplitude-find-onboarding-funnel-drop-off-amplit` s007 (video score 3/5)

## Caveats
- Almost no measured motion events and the only pattern label is other, so no pattern cards are listed; spotlight focus and ui camera push in fit the descriptions.
- Mixed members: some shots are long multi-phase scenes that also include typing, particle and logo moments.
- Scene length varies widely, so sound offsets are spread out and hard to generalise.
