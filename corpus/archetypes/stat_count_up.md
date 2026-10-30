# Stat Count Up

`stat_count_up` · 10 shots in 7 videos

A big number counts or ticks up at the centre of a styled backdrop and lands on the headline figure, with a short label, timed to the narration saying it. It turns a claim into proof the viewer can feel.

## When to use
- Backing a claim with a single headline metric such as scale, speed or coverage
- Showing an outcome as a before and after number
- Landing a proof beat right after a feature has been shown

## What you fill in
- **stat_value**: the final figure, with an optional suffix such as plus, percent or times
- **start_value** (optional): where the count begins; a lower number, or zero
- **label**: a short caption saying what the number measures
- **backdrop**: a gradient or brand field, with optional ambient shapes, logos or chips drifting behind
- **second_stat** (optional): an optional second figure that joins the first side by side
- **context_ui** (optional): a dashboard or card the number lives in, when the stat sits inside product interface

## The scene, beat by beat
1. Reveal the backdrop with its slow ambient drift
2. Fade or blur the number in at the centre
3. Count it up quickly, easing out, to land on the final figure as the narration says it
4. Bring in the label and hold while the backdrop keeps drifting
5. Optionally reframe to make room for a second stat
6. Exit with a zoom through, a wipe, a flash or a slide

Patterns: [metric_count_up](../patterns/metric_count_up.md), [layout_reframe](../patterns/layout_reframe.md), [parallax_layers](../patterns/parallax_layers.md)

- **GSAP / HyperFrames:** One timeline per scene. Tween a plain object's value and write it into the number element on update, rounded and formatted with tabular figures, using a power or expo out ease so the count slows as it lands; blur and fade the number in just before. Loop slow linear or sine drifts on the backdrop layers at different speeds. For a second stat, tween the first card's width and slide the second card in from the edge with a power out ease.
- **Remotion:** A Sequence for the stat where interpolate maps frame to value with an ease-out and the number is formatted per frame; a spring drives the number's entrance scale; background layers use per-layer interpolate on translate for parallax; a later Sequence handles the reframe or the exit.

## Measured
- Scene length: median 3.4 s, 90% interval 2.8 to 5.4 (n=10, 7 videos)
- Motion events per scene: median 0.1 events, 90% interval 0.0 to 1.0 (n=10, 7 videos)
- First motion: median 2.3 s (n=3, 3 videos) after the scene starts
- Way in: other 52%, mask wipe 14%, slide 14%, zoom through 14%
- Story beat: proof 52%, outcome 29%, mechanism 19%
- Sound: music 26%, unsure 23%, chime 19%, swoosh reverse 17%

## Sound cues
Music carries the scene; a chime is the most common clear cue and tends to land as the number settles, and a reverse swoosh often builds into the reveal. Impacts are occasional, later in the scene.
- chime: median 2.2 s, 90% interval 1.2 to 3.2 (n=5, 2 videos) after the scene starts
- click: median 1.6 s (n=1, 1 videos) after the scene starts
- impact: median 3.0 s (n=4, 3 videos) after the scene starts
- music: median 3.6 s, 90% interval 2.1 to 5.1 (n=10, 4 videos) after the scene starts
- swoosh reverse: median 2.1 s, 90% interval 0.5 to 2.8 (n=6, 3 videos) after the scene starts
- unsure: median 2.2 s, 90% interval 0.8 to 8.8 (n=8, 4 videos) after the scene starts
- whoosh: median 0.9 s (n=1, 1 videos) after the scene starts

## Examples
- `elevenlabs-introducing-elevenlabs-conversational-ag` s006 (video score 5/5)
- `hubspot-what-is-hubspot` s016 (video score 4/5)
- `warp-introducing-warp-2-0-the-agentic-develo` s018 (video score 4/5)
- `loom-introducing-loom-ai` s008 (video score 4/5)
- `ahrefs-ahrefs-brand-radar-see-any-brand-s-ai-v` s015 (video score 4/5)

## Caveats
- Few shots, and first-motion timing comes from only a handful of them.
- Members are mixed: some count up, some count down or flip cards, and some hold a static stat card with no count.
- Clear sound cues such as the chime come from only a couple of videos.
