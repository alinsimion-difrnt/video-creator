# Spotlight On One Thing

`spotlight_focus`

Out of a busy screen, one item is singled out: the rest dims, shrinks or loses colour while the chosen item grows, lights up or gains a selection mark, often with a gentle camera push toward it.

## When to use
- The narration names one item inside a dense interface, map or grid
- Showing a selection or keyboard step as real product behaviour
- Narrowing from many options to the single hero feature
- Pointing at the one part of a view that matters before explaining it

## Avoid when
- Everything on screen is equally important to the message
- The view is already sparse and the item is obvious
- Several spotlights would follow each other too quickly to read

## Build
1. Lay out the full context so the viewer sees the whole view first
2. Pick the one focus item and keep it on its own layer
3. Dim, desaturate or shrink everything else, keeping it faintly visible for context
4. Raise the focus item: scale it up, shift its colour to the accent or move the selection mark onto it
5. Optionally push the camera in toward the focus item at the same time
6. Keep captions on an unscaled layer, or clear them once the focus lands

- GSAP / HyperFrames: Build a timeline that tweens the context elements to low opacity and lower saturation (or smaller scale, staggered from the centre) with an ease-in or power ease-in-out, while the focus item tweens scale or colour with an ease-out; add a parallel scale tween on the parent layer with a transform origin on the focus for the camera push. For UI selection steps, use tl.set to swap the selected class instantly, and keep any background drift on a separate linear (ease: 'none') tween. Use back-style overshoot only on the hero item when it should feel lively.
- Remotion: Drive context opacity and scale with interpolate and an ease-in or ease-in-out Easing curve, and the focus item or camera push with a spring (high damping for a calm settle, lower damping for a slight overshoot). For instant selection hops, derive the selected index from the frame with no interpolation, and keep any background drift as a linear interpolate.

## Measured in premium explainers
- Duration: 377-955 ms (typical 438), 3 videos
- Easing: ease in 38%, linear 31%, ease out 13%, spring overshoot 12%
- Changes: fade 23%, color shift 20%, highlight 11%, scale up 11%
- Sound offset to the landing: -152-246 ms (typical 47), 2 videos

## Sound
Often a short accent such as a chime, glitch or impact placed right around the moment focus lands, sometimes just before or just after it; in other cases only the music bed carries it. Treat sound as optional.

## Why it reads as premium
The spotlight cuts a crowded, unreadable view down to one legible thing without cutting away, so the viewer keeps a sense of scale while knowing exactly where to look. It does this with restraint: the surroundings fade to a ghost rather than vanishing, the accent colour is reserved for the focus, and selection changes happen as honest, instant interface steps rather than fake tweens. Layering two moves, such as a push-in plus dimming, or a zoom plus a small emphasis on the key element, guides the eye in stages instead of relying on boxes, arrows or callouts.

## Caveats
- Seen in only four videos, and timing was measured in only three of them
- Sound timing comes from just two videos and its spread is wide, so treat the sound placement as a loose guide
- The pattern mixes instant selection hops with smooth zoom-and-dim moves, so the timing spread is wide
