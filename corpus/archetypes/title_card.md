# Title Card

`title_card` · 23 shots in 19 videos

A short, centred headline on a clean field reveals word by word or rises from a mask, sometimes with a small label pill or drifting media tiles around it. It names the product, feature or chapter so the viewer knows what comes next.

## When to use
- Introducing the product or a new feature by name near the start.
- Marking a chapter break before a new demo section.
- Landing a short claim between demo beats while the narration names it.

## What you fill in
- **headline**: the feature or product name, or one short claim
- **eyebrow** (optional): an optional small label above the headline, such as an introducing pill
- **background**: a solid or gradient field, or a tilted product screenshot behind the title
- **accent_media** (optional): optional tiles, logos or cutouts that drift in around the title
- **accent_colour** (optional): the brand colour the key word switches to as it lands

## The scene, beat by beat
1. The field appears, often already in place from the previous cut.
2. An optional eyebrow dot grows into a pill and its label fades in.
3. The headline reveals word by word or slides up from a mask and its key word takes the accent colour.
4. Accent tiles or logos drift in from the edges with a light stagger and parallax.
5. The card holds briefly, then hands off with a cut or a soft blur crossfade.

Patterns: [kinetic_word_reveal](../patterns/kinetic_word_reveal.md), [logo_resolve](../patterns/logo_resolve.md), [parallax_layers](../patterns/parallax_layers.md), [ui_camera_push_in](../patterns/ui_camera_push_in.md), [blur_crossfade](../patterns/blur_crossfade.md)

- **GSAP / HyperFrames:** One timeline per scene. Wrap each headline line in an overflow-hidden mask and tween words from below with opacity on an expo ease-out, staggered per word. Tween the eyebrow from a dot to a pill by width on an ease-out, then fade its label. Add accent tiles as separate layers sliding from the edges at different speeds for parallax, staggered, and tween the key word's colour on its entry. Close with a hold and an optional blur-plus-opacity crossfade.
- **Remotion:** One Sequence for the field and eyebrow, one for the headline with per-word staggered springs driving translateY and opacity, and one for the accent layers whose springs use different stiffness to read as depth. Use a crossfade with an interpolated blur at the end when not hard cutting.

## Measured
- Scene length: median 2.7 s, 90% interval 2.1 to 3.2 (n=23, 19 videos)
- Motion events per scene: median 0.2 events, 90% interval 0.0 to 1.0 (n=23, 19 videos)
- First motion: median 0.1 s, 90% interval 0.0 to 0.6 (n=8, 6 videos) after the scene starts
- Way in: other 43%, hard cut 39%, crossfade 10%, slide 6%
- Story beat: demo 37%, hook 37%, mechanism 12%, proof 9%
- Sound: chime 30%, music 26%, unsure 24%, swoosh reverse 10%

## Sound cues
A soft chime is the most common cue, landing as the title settles; music often lifts early in the scene, and a reversed swoosh can lead in right at the start. An occasional impact marks the headline landing.
- chime: median 2.6 s, 90% interval 1.6 to 3.5 (n=17, 5 videos) after the scene starts
- impact: median 1.5 s, 90% interval 0.5 to 2.6 (n=5, 4 videos) after the scene starts
- music: median 1.4 s, 90% interval 1.0 to 1.9 (n=13, 7 videos) after the scene starts
- swoosh reverse: median 0.3 s, 90% interval 0.2 to 1.5 (n=6, 2 videos) after the scene starts
- unsure: median 1.1 s, 90% interval 0.8 to 1.3 (n=14, 9 videos) after the scene starts

## Examples
- `figma-introducing-figma-motion-your-canvas-no` s004 (video score 5/5)
- `datadog-datadog-overview-see-inside-the-platfor` s007 (video score 4/5)
- `notion-introducing-the-new-notion-ai` s007 (video score 4/5)
- `zendesk-meet-zendesk-ai-agents-the-most-autonom` s006 (video score 4/5)

## Caveats
- Members are mixed: pure kinetic type, titles over tilted product screenshots, and one very short transitional shot.
- First motion is measured on only some of the shots.
