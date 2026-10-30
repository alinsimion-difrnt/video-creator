# Presenter To Camera

`presenter_to_camera` · 98 shots in 10 videos

A person speaks directly to the viewer in a locked or gently drifting medium shot, sometimes with a name tag or a supporting graphic beside them. The scene gives the explainer a human voice and carries claims, reasons and proof in the speaker's own words.

## When to use
- A founder or customer states the problem, the reason or the result in their own words.
- To add trust and warmth between product demo scenes.
- When a spoken claim needs a quick visual proof card next to the speaker.

## What you fill in
- **presenter_clip**: filmed footage of the speaker, medium or close framing
- **spoken_line**: the sentence or two the speaker says in this scene
- **name_tag** (optional): a lower third with the speaker's name and role
- **support_card** (optional): a window or card that slides in beside the speaker to prove the point
- **keyword** (optional): one spoken word shown large behind or beside the speaker

## The scene, beat by beat
1. Hard cut in on the speaker, usually on a sentence boundary.
2. The speaker talks with the frame locked or slowly drifting.
3. A name tag eases in at the lower left early in the first appearance.
4. Optionally a support card slides in and its content scrolls or appends to prove the claim.
5. Cut away to a tighter angle or the next scene at the end of the sentence.

Patterns: [masked_scroll](../patterns/masked_scroll.md), [chip_append](../patterns/chip_append.md)

- **GSAP / HyperFrames:** One timeline per scene over the footage layer: a short opacity and y tween for the lower third with an ease-out (power family), an x tween sliding any support card in from the side with an ease-out, and a linear y tween for content scrolling inside a masked card; keep the footage itself untouched.
- **Remotion:** An OffthreadVideo of the presenter in one Sequence; the lower third and support card are child Sequences starting on narration words, each entering with a critically damped spring on translate and opacity, and scrolling content driven by a linear interpolate over the Sequence's frames.

## Measured
- Scene length: median 3.8 s, 90% interval 3.3 to 4.7 (n=98, 10 videos)
- Motion events per scene: median 0.0 events, 90% interval 0.0 to 0.0 (n=98, 10 videos)
- First motion: median 1.0 s, 90% interval 0.4 to 2.5 (n=12, 2 videos) after the scene starts
- Way in: hard cut 65%, other 21%, slide 5%, crossfade 5%
- Story beat: demo 23%, mechanism 22%, outcome 22%, proof 14%
- Sound: music 25%, unsure 24%, swoosh reverse 19%, impact 15%

## Sound cues
Mostly the speaker's voice over a music bed. When an effect is used it is a reverse swoosh or impact landing on a graphic entrance or a punchy spoken word, with an occasional chime; otherwise no typical sound.
- chime: median 4.5 s, 90% interval 3.1 to 5.5 (n=28, 3 videos) after the scene starts
- click: median 1.6 s (n=3, 1 videos) after the scene starts
- impact: median 1.8 s, 90% interval 1.3 to 2.4 (n=34, 5 videos) after the scene starts
- music: median 2.9 s, 90% interval 2.3 to 3.3 (n=63, 5 videos) after the scene starts
- speech: median 1.7 s (n=2, 1 videos) after the scene starts
- swoosh reverse: median 2.1 s, 90% interval 1.6 to 2.8 (n=43, 5 videos) after the scene starts
- unsure: median 2.4 s, 90% interval 1.9 to 2.9 (n=57, 7 videos) after the scene starts
- whoosh: median 1.7 s (n=3, 2 videos) after the scene starts

## Examples
- `cursor-introducing-cursor-3` s002 (video score 4/5)
- `servicenow-what-does-servicenow-do` s009 (video score 4/5)
- `clickup-clickup-4-0-just-changed-work-ai-softwar` s002 (video score 4/5)
- `warp-introducing-warp-2-0-the-agentic-develo` s020 (video score 4/5)

## Caveats
- Measured motion comes from very few videos; most presenter shots have no detected motion event.
- Members are mixed: some are plain talking heads, others are graphics laid over or replacing the speaker.
- Most of the pattern mix is unnamed, so the named patterns cover only overlay moments.
