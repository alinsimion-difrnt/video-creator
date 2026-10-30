# Kinetic Statement Card

`kinetic_statement_card` · 66 shots in 21 videos

A short headline builds word by word on a clean background, sometimes with one word or chip that cycles through options or a small icon that supports it. The scene states one idea loudly between demos: the hook, the problem, the mechanism or the outcome.

## When to use
- To open the video or a new section with one clear claim.
- To name a problem or a payoff in words before showing it in the product.
- When a list of things the product covers can be shown as one phrase with a cycling slot.

## What you fill in
- **headline**: one short claim, one or two lines
- **emphasis_word** (optional): the word that gets an underline, colour or weight change
- **cycling_options** (optional): a short list of words or chips that swap in one slot of the phrase
- **support_visual** (optional): a small icon, logo or illustration that pops in near the text
- **background**: a plain light or dark field, optionally with soft drifting shapes

## The scene, beat by beat
1. Start on the empty background, with motion beginning almost immediately.
2. The headline reveals word by word or line by line from a mask.
3. An emphasis touch lands: an underline draws on or one word changes colour.
4. Optionally a slot in the phrase cycles through options, or icons pop in beside the text.
5. The text resolves to its final state and holds briefly.
6. The card clears or reframes to make room for the next scene.

Patterns: [kinetic_word_reveal](../patterns/kinetic_word_reveal.md), [input_text_cycle](../patterns/input_text_cycle.md), [layout_reframe](../patterns/layout_reframe.md), [logo_resolve](../patterns/logo_resolve.md), [masked_scroll](../patterns/masked_scroll.md), [stagger_list_reveal](../patterns/stagger_list_reveal.md), [chip_append](../patterns/chip_append.md)

- **GSAP / HyperFrames:** One timeline per card: split the headline into words and tween each from a masked offset or low opacity with a short stagger and an expo or power ease-out; draw any underline with a stroke-dashoffset tween; for a cycling slot, chain y and blur tweens that swap the label on the beat; finish with a scale and translate tween on the text group to clear or reframe.
- **Remotion:** A Sequence per card; each word's opacity and translate come from a spring offset by its index times a small frame delay; a cycling chip uses child Sequences per option with a spring slide in and out; a closing interpolate on scale and position hands off to the next scene.

## Measured
- Scene length: median 3.2 s, 90% interval 2.8 to 3.6 (n=66, 21 videos)
- Motion events per scene: median 0.0 events, 90% interval 0.0 to 0.0 (n=66, 21 videos)
- First motion: median 0.3 s, 90% interval 0.1 to 1.3 (n=14, 7 videos) after the scene starts
- Way in: hard cut 41%, other 35%, zoom through 16%, crossfade 3%
- Story beat: outcome 19%, mechanism 19%, hook 17%, problem 14%
- Sound: unsure 49%, swoosh reverse 14%, chime 14%, music 13%

## Sound cues
Often an unlabelled or reverse-swoosh hit as the text builds, with a soft impact on the key word and music carrying the rest; chimes appear in a few videos. No single dependable cue.
- chime: median 3.5 s, 90% interval 2.7 to 5.7 (n=20, 4 videos) after the scene starts
- impact: median 1.5 s, 90% interval 0.4 to 3.3 (n=17, 12 videos) after the scene starts
- music: median 0.7 s, 90% interval 0.5 to 2.8 (n=22, 10 videos) after the scene starts
- swoosh reverse: median 1.7 s, 90% interval 1.3 to 2.4 (n=26, 7 videos) after the scene starts
- unsure: median 2.1 s, 90% interval 1.4 to 2.5 (n=73, 13 videos) after the scene starts

## Examples
- `meta-introducing-meta-quest-3-coming-this-f` s016 (video score 5/5)
- `notion-introducing-the-new-notion-ai` s003 (video score 4/5)
- `attio-introducing-ask-attio` s003 (video score 4/5)
- `notion-introducing-notion-ai-connectors` s004 (video score 4/5)
- `loom-introducing-loom-ai` s001 (video score 4/5)

## Caveats
- First-motion timing comes from a minority of shots and videos.
- Some members run several type cards and even a short UI moment inside one shot, so the mix is broad.
- Nearly half of sound cues are unlabelled, so SFX timing is weak.
