# Stat Count Up

`stat_count_up`

A big number counts or ticks up at the centre of a styled backdrop and lands on the headline figure, with a short label, timed to the narration saying it. It turns a claim into proof the viewer can feel.

## When to use
- Backing a claim with a single headline metric such as scale, speed or coverage
- Showing an outcome as a before and after number
- Landing a proof beat right after a feature has been shown

## Slots (what you fill in)
- `stat_value`: the final figure, with an optional suffix such as plus, percent or times
- `start_value` (optional): where the count begins; a lower number, or zero
- `label`: a short caption saying what the number measures
- `backdrop`: a gradient or brand field, with optional ambient shapes, logos or chips drifting behind
- `second_stat` (optional): an optional second figure that joins the first side by side
- `context_ui` (optional): a dashboard or card the number lives in, when the stat sits inside product interface

## The scene, beat by beat
1. Reveal the backdrop with its slow ambient drift
2. Fade or blur the number in at the centre
3. Count it up quickly, easing out, to land on the final figure as the narration says it
4. Bring in the label and hold while the backdrop keeps drifting
5. Optionally reframe to make room for a second stat
6. Exit with a zoom through, a wipe, a flash or a slide

Patterns: [layout_reframe](../patterns/layout_reframe.md), [parallax_layers](../patterns/parallax_layers.md)

- GSAP / HyperFrames: One timeline per scene. Tween a plain object's value and write it into the number element on update, rounded and formatted with tabular figures, using a power or expo out ease so the count slows as it lands; blur and fade the number in just before. Loop slow linear or sine drifts on the backdrop layers at different speeds. For a second stat, tween the first card's width and slide the second card in from the edge with a power out ease.
- Remotion: A Sequence for the stat where interpolate maps frame to value with an ease-out and the number is formatted per frame; a spring drives the number's entrance scale; background layers use per-layer interpolate on translate for parallax; a later Sequence handles the reframe or the exit.

## Measured in premium explainers
- Scene length: 2.8-5.4 s (typical 3.4), 7 videos
- First motion after the scene starts: 1.6-2.8 s (typical 2.3), 3 videos
- Motion events per scene: 0-1 events (typical 0), 7 videos
- Way in: other 52%, mask wipe 14%, slide 14%
- chime sound: 1.2-3.0 s (typical 2.2), 2 videos after the scene starts
- click sound: 1.6-1.6 s (typical 1.6), 1 videos after the scene starts
- impact sound: 1.7-3.4 s (typical 3.0), 3 videos after the scene starts
- music sound: 1.7-5.2 s (typical 3.6), 4 videos after the scene starts
- swoosh reverse sound: 0.6-2.7 s (typical 2.1), 3 videos after the scene starts
- unsure sound: 0.8-9.1 s (typical 2.2), 4 videos after the scene starts
- whoosh sound: 0.9-0.9 s (typical 0.9), 1 videos after the scene starts

## Sound
Music carries the scene; a chime is the most common clear cue and tends to land as the number settles, and a reverse swoosh often builds into the reveal. Impacts are occasional, later in the scene.

## Caveats
- Few shots, and first-motion timing comes from only a handful of them.
- Members are mixed: some count up, some count down or flip cards, and some hold a static stat card with no count.
- Clear sound cues such as the chime come from only a couple of videos.
