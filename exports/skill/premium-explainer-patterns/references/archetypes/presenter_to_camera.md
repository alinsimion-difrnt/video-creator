# Presenter To Camera

`presenter_to_camera`

A person speaks directly to the viewer in a locked or gently drifting medium shot, sometimes with a name tag or a supporting graphic beside them. The scene gives the explainer a human voice and carries claims, reasons and proof in the speaker's own words.

## When to use
- A founder or customer states the problem, the reason or the result in their own words.
- To add trust and warmth between product demo scenes.
- When a spoken claim needs a quick visual proof card next to the speaker.

## Slots (what you fill in)
- `presenter_clip`: filmed footage of the speaker, medium or close framing
- `spoken_line`: the sentence or two the speaker says in this scene
- `name_tag` (optional): a lower third with the speaker's name and role
- `support_card` (optional): a window or card that slides in beside the speaker to prove the point
- `keyword` (optional): one spoken word shown large behind or beside the speaker

## The scene, beat by beat
1. Hard cut in on the speaker, usually on a sentence boundary.
2. The speaker talks with the frame locked or slowly drifting.
3. A name tag eases in at the lower left early in the first appearance.
4. Optionally a support card slides in and its content scrolls or appends to prove the claim.
5. Cut away to a tighter angle or the next scene at the end of the sentence.

Patterns: [masked_scroll](../patterns/masked_scroll.md), [chip_append](../patterns/chip_append.md)

- GSAP / HyperFrames: One timeline per scene over the footage layer: a short opacity and y tween for the lower third with an ease-out (power family), an x tween sliding any support card in from the side with an ease-out, and a linear y tween for content scrolling inside a masked card; keep the footage itself untouched.
- Remotion: An OffthreadVideo of the presenter in one Sequence; the lower third and support card are child Sequences starting on narration words, each entering with a critically damped spring on translate and opacity, and scrolling content driven by a linear interpolate over the Sequence's frames.

## Measured in premium explainers
- Scene length: 2.5-6.1 s (typical 3.8), 10 videos
- First motion after the scene starts: 0.3-2.5 s (typical 1.0), 2 videos
- Motion events per scene: 0-0 events (typical 0), 10 videos
- Way in: hard cut 65%, other 21%, slide 5%
- chime sound: 1.8-6.4 s (typical 4.5), 3 videos after the scene starts
- click sound: 0.5-3.1 s (typical 1.6), 1 videos after the scene starts
- impact sound: 1.0-3.2 s (typical 1.8), 5 videos after the scene starts
- music sound: 1.2-4.5 s (typical 2.9), 5 videos after the scene starts
- speech sound: 0.8-2.7 s (typical 1.7), 1 videos after the scene starts
- swoosh reverse sound: 0.7-4.0 s (typical 2.1), 5 videos after the scene starts
- unsure sound: 1.1-4.0 s (typical 2.4), 7 videos after the scene starts
- whoosh sound: 1.5-1.9 s (typical 1.7), 2 videos after the scene starts

## Sound
Mostly the speaker's voice over a music bed. When an effect is used it is a reverse swoosh or impact landing on a graphic entrance or a punchy spoken word, with an occasional chime; otherwise no typical sound.

## Caveats
- Measured motion comes from very few videos; most presenter shots have no detected motion event.
- Members are mixed: some are plain talking heads, others are graphics laid over or replacing the speaker.
- Most of the pattern mix is unnamed, so the named patterns cover only overlay moments.
