# Logo Close

`logo_close`

The last scene: a closing tagline or call to action builds, then shapes or the final UI resolve into the brand mark and wordmark, which hold on a clean background. It leaves the viewer with the brand and one thing to do next.

## When to use
- As the final scene of almost any explainer.
- When the narration ends on a call to action or a payoff line.
- To bookend a video whose opening used the same logo animation.

## Slots (what you fill in)
- `tagline` (optional): a short closing line or slogan
- `cta_line` (optional): what to do next, such as try it, visit or availability
- `logo_mark`: the brand symbol as a vector
- `wordmark`: the brand or product name lockup
- `lead_in_visual` (optional): the last product view or shapes that collapse into the logo
- `url_or_price` (optional): a small line under the lockup with a web address, price or date
- `background`: a plain or gradient end-card field

## The scene, beat by beat
1. The previous scene clears, shrinks or washes out to the end-card background.
2. A tagline or call to action builds word by word, with keywords tinted as they are spoken.
3. The tagline clears and shapes or the lead-in visual converge into the logo mark.
4. The wordmark slides or wipes out beside or below the mark as the lockup recentres.
5. An optional small line with the address, price or date fades in beneath.
6. The lockup holds while the music finishes, then fades out to the background.

Patterns: [logo_resolve](../patterns/logo_resolve.md), [kinetic_word_reveal](../patterns/kinetic_word_reveal.md), [layout_reframe](../patterns/layout_reframe.md), [prompt_type_on](../patterns/prompt_type_on.md), [input_text_cycle](../patterns/input_text_cycle.md), [whip_transition](../patterns/whip_transition.md)

- GSAP / HyperFrames: One timeline for the close: scale and opacity tweens to clear the last view, a per-word stagger for the tagline with an expo ease-out and colour tweens on keywords, then the logo built from shapes that tween position, scale and border radius into place with a back or expo ease-out, a mask or x tween revealing the wordmark, a long hold, and a final opacity fade.
- Remotion: A Sequence for the tagline and a later Sequence for the lockup; tagline words and logo parts each enter on a spring offset by index, the wordmark reveal uses an interpolated clip or translate, and the end of the composition holds the lockup with a closing interpolate to fade.

## Measured in premium explainers
- Scene length: 4.4-10.2 s (typical 6.9), 49 videos
- First motion after the scene starts: 0.2-1.6 s (typical 0.6), 14 videos
- Motion events per scene: 0-1 events (typical 0), 49 videos
- Way in: other 32%, hard cut 32%, zoom through 17%
- chime sound: 1.7-6.7 s (typical 2.8), 11 videos after the scene starts
- glitch sound: 0.2-2.0 s (typical 1.3), 3 videos after the scene starts
- impact sound: 1.3-11.7 s (typical 3.2), 9 videos after the scene starts
- music sound: 2.7-12.3 s (typical 5.1), 21 videos after the scene starts
- swoosh reverse sound: 1.0-4.4 s (typical 2.2), 16 videos after the scene starts
- unsure sound: 0.9-6.6 s (typical 2.4), 28 videos after the scene starts
- whoosh sound: 0.4-0.4 s (typical 0.4), 1 videos after the scene starts

## Sound
Music carries the close and usually resolves under the held logo; a reverse swoosh or chime often marks the logo resolving, with an occasional impact. Treat the music ending as the main cue.

## Caveats
- Members are mixed: some shots fold a whole closing montage or a final demo into the same shot as the logo.
- First-motion timing comes from a minority of shots.
- Some members are only a trailing blank fade after the logo, which lowers the motion stats.
