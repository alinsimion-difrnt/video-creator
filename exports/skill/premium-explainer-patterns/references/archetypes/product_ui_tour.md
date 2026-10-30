# Product UI Tour

`product_ui_tour`

The viewer watches the real or recreated product interface being used: a cursor clicks through views while the frame pushes in on the part that matters. The scene shows how the product works rather than telling.

## When to use
- Demo beats where the narration walks through a feature step by step.
- When one workflow needs to be shown end to end inside the app.
- To ground a claim from an earlier scene in the actual interface.

## Slots (what you fill in)
- `ui_surface`: a screen recording or recreated app view, full-bleed or as a framed window
- `cursor_path`: the ordered clicks and hovers that carry the workflow
- `focus_regions`: the panels or controls the camera pushes in on
- `typed_input` (optional): a prompt or field value typed on during the demo
- `result_state`: the new item, answer or status that appears after the action
- `caption` (optional): an optional short on-screen label naming the feature

## The scene, beat by beat
1. Open on the full app view so the viewer knows where they are.
2. The cursor moves to the first control and clicks it.
3. The camera pushes in on the region that changes, cropping away chrome.
4. Input types on or content streams or scrolls inside a masked panel.
5. The result appears: a new row, chip, toggle or answer resolves into place.
6. The frame reframes back out to the full view, ready for the next feature or a cut.

Patterns: [cursor_guided_demo](../patterns/cursor_guided_demo.md), [layout_reframe](../patterns/layout_reframe.md), [ui_camera_push_in](../patterns/ui_camera_push_in.md), [masked_scroll](../patterns/masked_scroll.md), [scale_dissolve_transition](../patterns/scale_dissolve_transition.md), [ai_answer_stream](../patterns/ai_answer_stream.md), [skeleton_resolve](../patterns/skeleton_resolve.md), [prompt_type_on](../patterns/prompt_type_on.md)

- GSAP / HyperFrames: Build the UI as one large DOM canvas inside a wrapper and drive a single timeline per scene: scale and translate tweens on the wrapper for push-ins and reframes (smooth power or expo in-out eases), a scripted cursor element tweened between targets with click pulses, text tweens for typed input, and a short stagger for streamed lines or list rows inside a masked, upward-scrolling container.
- Remotion: One Sequence for the scene holding the app canvas; camera framing comes from interpolated scale and translate keyed to frame, with a critically damped spring for each push-in and reframe; child Sequences offset the cursor moves, typing and result reveals so each starts on its own narration word.

## Measured in premium explainers
- Scene length: 1.6-5.3 s (typical 3.1), 41 videos
- First motion after the scene starts: 0.4-2.0 s (typical 1.0), 14 videos
- Motion events per scene: 0-0 events (typical 0), 41 videos
- Way in: other 40%, hard cut 28%, zoom through 16%
- chime sound: 1.1-8.3 s (typical 3.5), 17 videos after the scene starts
- click sound: 1.2-10.9 s (typical 2.4), 12 videos after the scene starts
- glitch sound: 7.0-19.4 s (typical 14.6), 2 videos after the scene starts
- impact sound: 0.9-4.7 s (typical 2.2), 21 videos after the scene starts
- music sound: 1.3-11.2 s (typical 3.3), 28 videos after the scene starts
- swoosh reverse sound: 1.0-9.9 s (typical 3.5), 22 videos after the scene starts
- typing sound: 2.7-7.1 s (typical 4.2), 1 videos after the scene starts
- unsure sound: 1.2-10.1 s (typical 2.9), 33 videos after the scene starts
- whoosh sound: 0.6-1.7 s (typical 1.0), 3 videos after the scene starts

## Sound
Mostly music bed under the demo; when there is a cue it is a reverse swoosh or a soft impact landing on a camera push-in, with an occasional chime when a result appears and light clicks on cursor taps. Many cues are unlabelled, so treat sound as optional.

## Caveats
- Most shots have no code-detected motion event, so first-motion timing rests on a minority of shots and videos.
- Members range from short close-ups to long continuous screen recordings; long members carry most of the pattern evidence.
- A large share of sound cues are unlabelled or music, so specific SFX timing is weak.
