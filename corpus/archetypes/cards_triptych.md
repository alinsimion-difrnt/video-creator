# Feature Cards Triptych

`cards_triptych` · 8 shots in 5 videos

A small set of cards, panels or icon tiles enter together and settle side by side or in an overlapping cascade, each standing for one feature, theme or benefit. It lets the viewer take in a few parallel ideas at once before the video unpacks them.

## When to use
- Previewing a few features or benefits that later scenes will explain
- Showing variations of one thing, such as themes or page types
- A summary beat that groups outcomes before a close

## What you fill in
- **cards**: a few cards, panels or icon tiles, each standing for one idea
- **card_labels** (optional): a short label or icon under or on each card
- **layout**: a side-by-side row, an overlapping collage or a diagonal cascade
- **background** (optional): a solid or gradient stage that keeps the cards readable
- **cue_words** (optional): narration words that introduce each card

## The scene, beat by beat
1. The previous view pushes out or a single card shrinks to make room
2. The cards fly or slide in with a short stagger, often with blur clearing as they land
3. They settle into a row, collage or cascade, sometimes timed to the narration naming each one
4. The group holds with a slow drift or gentle rotation for depth
5. The cards collapse back together, push out or zoom through into the next scene

Patterns: 

- **GSAP / HyperFrames:** One timeline per scene. Exit the previous view with a y or x translate plus motion blur. Enter the cards from below or the side with a staggered tween of y, opacity and a blur filter clearing to sharp (power3.out). For a carousel of icon tiles, scale the new tile into the centre while the previous one shrinks and moves to a side slot (power2.inOut). Hold with a slow linear or sine drift per card at different speeds for parallax, then reverse the stagger or push the group out.
- **Remotion:** One Sequence for the entrance and hold and one for the exit. Offset each card's spring() by its index for the stagger, with damping high enough to avoid overshoot. Drive the slow drift with interpolate() over the full Sequence length at a different rate per card. Blur is interpolate() from a high value to zero on each card's own progress.

## Measured
- Scene length: median 5.2 s, 90% interval 1.8 to 6.4 (n=8, 5 videos)
- Motion events per scene: median 0.0 events, 90% interval 0.0 to 0.0 (n=8, 5 videos)
- First motion: not measured after the scene starts
- Way in: other 50%, push 27%, zoom through 13%, crossfade 10%
- Story beat: demo 32%, agitate 24%, outcome 24%, mechanism 21%
- Sound: unsure 39%, chime 24%, music 19%, impact 13%

## Sound cues
No typical sound. Labels are mixed and often unsure; a soft impact or music hit may land as the cards settle, and chimes can mark each card in some videos.
- chime: median 5.3 s, 90% interval 2.5 to 8.0 (n=5, 1 videos) after the scene starts
- impact: median 1.2 s (n=3, 3 videos) after the scene starts
- music: median 1.4 s (n=4, 2 videos) after the scene starts
- swoosh reverse: median 0.5 s (n=1, 1 videos) after the scene starts
- unsure: median 2.7 s, 90% interval 1.8 to 4.5 (n=9, 3 videos) after the scene starts

## Examples
- `conductor-conductor-ai-get-found-in-ai-search` s026 (video score 4/5)
- `datadog-consolidate-your-tools-with-datadog-s-ec` s007 (video score 4/5)
- `scrunch-scrunch-the-internet` s006 (video score 4/5)
- `zapier-zapier-s-newest-product-features-build` s009 (video score 4/5)
- `typeform-apply-your-brand-assets-to-a-typeform-wi` s005 (video score 3/5)

## Caveats
- No measured motion events or patterns, so none are listed; card wall stagger and parallax layers fit the descriptions.
- Mixed members: overlapping web-page collages, rotating cubes, icon carousels and a plain screen recording are grouped together.
- Few shots, and the chime cues come from a single video.
