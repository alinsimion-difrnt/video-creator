# Title Card

`title_card`

A short, centred headline on a clean field reveals word by word or rises from a mask, sometimes with a small label pill or drifting media tiles around it. It names the product, feature or chapter so the viewer knows what comes next.

## When to use
- Introducing the product or a new feature by name near the start.
- Marking a chapter break before a new demo section.
- Landing a short claim between demo beats while the narration names it.

## Slots (what you fill in)
- `headline`: the feature or product name, or one short claim
- `eyebrow` (optional): an optional small label above the headline, such as an introducing pill
- `background`: a solid or gradient field, or a tilted product screenshot behind the title
- `accent_media` (optional): optional tiles, logos or cutouts that drift in around the title
- `accent_colour` (optional): the brand colour the key word switches to as it lands

## The scene, beat by beat
1. The field appears, often already in place from the previous cut.
2. An optional eyebrow dot grows into a pill and its label fades in.
3. The headline reveals word by word or slides up from a mask and its key word takes the accent colour.
4. Accent tiles or logos drift in from the edges with a light stagger and parallax.
5. The card holds briefly, then hands off with a cut or a soft blur crossfade.

Patterns: [kinetic_word_reveal](../patterns/kinetic_word_reveal.md), [logo_resolve](../patterns/logo_resolve.md), [parallax_layers](../patterns/parallax_layers.md), [ui_camera_push_in](../patterns/ui_camera_push_in.md), [blur_crossfade](../patterns/blur_crossfade.md)

- GSAP / HyperFrames: One timeline per scene. Wrap each headline line in an overflow-hidden mask and tween words from below with opacity on an expo ease-out, staggered per word. Tween the eyebrow from a dot to a pill by width on an ease-out, then fade its label. Add accent tiles as separate layers sliding from the edges at different speeds for parallax, staggered, and tween the key word's colour on its entry. Close with a hold and an optional blur-plus-opacity crossfade.
- Remotion: One Sequence for the field and eyebrow, one for the headline with per-word staggered springs driving translateY and opacity, and one for the accent layers whose springs use different stiffness to read as depth. Use a crossfade with an interpolated blur at the end when not hard cutting.

## Measured in premium explainers
- Scene length: 2.1-3.4 s (typical 2.7), 19 videos
- First motion after the scene starts: 0.0-0.6 s (typical 0.1), 6 videos
- Motion events per scene: 0-1 events (typical 0), 19 videos
- Way in: other 43%, hard cut 39%, crossfade 10%
- chime sound: 1.5-4.0 s (typical 2.6), 5 videos after the scene starts
- impact sound: 0.7-2.7 s (typical 1.5), 4 videos after the scene starts
- music sound: 0.9-1.9 s (typical 1.4), 7 videos after the scene starts
- swoosh reverse sound: 0.2-1.3 s (typical 0.3), 2 videos after the scene starts
- unsure sound: 0.4-1.4 s (typical 1.1), 9 videos after the scene starts

## Sound
A soft chime is the most common cue, landing as the title settles; music often lifts early in the scene, and a reversed swoosh can lead in right at the start. An occasional impact marks the headline landing.

## Caveats
- Members are mixed: pure kinetic type, titles over tilted product screenshots, and one very short transitional shot.
- First motion is measured on only some of the shots.
