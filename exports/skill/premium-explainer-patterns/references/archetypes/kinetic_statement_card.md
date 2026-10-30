# Kinetic Statement Card

`kinetic_statement_card`

A short headline builds word by word on a clean background, sometimes with one word or chip that cycles through options or a small icon that supports it. The scene states one idea loudly between demos: the hook, the problem, the mechanism or the outcome.

## When to use
- To open the video or a new section with one clear claim.
- To name a problem or a payoff in words before showing it in the product.
- When a list of things the product covers can be shown as one phrase with a cycling slot.

## Slots (what you fill in)
- `headline`: one short claim, one or two lines
- `emphasis_word` (optional): the word that gets an underline, colour or weight change
- `cycling_options` (optional): a short list of words or chips that swap in one slot of the phrase
- `support_visual` (optional): a small icon, logo or illustration that pops in near the text
- `background`: a plain light or dark field, optionally with soft drifting shapes

## The scene, beat by beat
1. Start on the empty background, with motion beginning almost immediately.
2. The headline reveals word by word or line by line from a mask.
3. An emphasis touch lands: an underline draws on or one word changes colour.
4. Optionally a slot in the phrase cycles through options, or icons pop in beside the text.
5. The text resolves to its final state and holds briefly.
6. The card clears or reframes to make room for the next scene.

Patterns: [kinetic_word_reveal](../patterns/kinetic_word_reveal.md), [input_text_cycle](../patterns/input_text_cycle.md), [layout_reframe](../patterns/layout_reframe.md), [logo_resolve](../patterns/logo_resolve.md), [masked_scroll](../patterns/masked_scroll.md), [stagger_list_reveal](../patterns/stagger_list_reveal.md), [chip_append](../patterns/chip_append.md)

- GSAP / HyperFrames: One timeline per card: split the headline into words and tween each from a masked offset or low opacity with a short stagger and an expo or power ease-out; draw any underline with a stroke-dashoffset tween; for a cycling slot, chain y and blur tweens that swap the label on the beat; finish with a scale and translate tween on the text group to clear or reframe.
- Remotion: A Sequence per card; each word's opacity and translate come from a spring offset by its index times a small frame delay; a cycling chip uses child Sequences per option with a spring slide in and out; a closing interpolate on scale and position hands off to the next scene.

## Measured in premium explainers
- Scene length: 1.7-4.6 s (typical 3.2), 21 videos
- First motion after the scene starts: 0.0-1.4 s (typical 0.3), 7 videos
- Motion events per scene: 0-1 events (typical 0), 21 videos
- Way in: hard cut 41%, other 35%, zoom through 16%
- chime sound: 1.8-5.8 s (typical 3.5), 4 videos after the scene starts
- impact sound: 0.3-3.3 s (typical 1.5), 12 videos after the scene starts
- music sound: 0.4-3.3 s (typical 0.7), 10 videos after the scene starts
- swoosh reverse sound: 1.1-3.4 s (typical 1.7), 7 videos after the scene starts
- unsure sound: 1.0-5.4 s (typical 2.1), 13 videos after the scene starts

## Sound
Often an unlabelled or reverse-swoosh hit as the text builds, with a soft impact on the key word and music carrying the rest; chimes appear in a few videos. No single dependable cue.

## Caveats
- First-motion timing comes from a minority of shots and videos.
- Some members run several type cards and even a short UI moment inside one shot, so the mix is broad.
- Nearly half of sound cues are unlabelled, so SFX timing is weak.
