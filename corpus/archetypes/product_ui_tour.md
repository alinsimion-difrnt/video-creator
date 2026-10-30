# Product UI Tour

`product_ui_tour` · 308 shots in 41 videos

The viewer watches the real or recreated product interface being used: a cursor clicks through views while the frame pushes in on the part that matters. The scene shows how the product works rather than telling.

## When to use
- Demo beats where the narration walks through a feature step by step.
- When one workflow needs to be shown end to end inside the app.
- To ground a claim from an earlier scene in the actual interface.

## What you fill in
- **ui_surface**: a screen recording or recreated app view, full-bleed or as a framed window
- **cursor_path**: the ordered clicks and hovers that carry the workflow
- **focus_regions**: the panels or controls the camera pushes in on
- **typed_input** (optional): a prompt or field value typed on during the demo
- **result_state**: the new item, answer or status that appears after the action
- **caption** (optional): an optional short on-screen label naming the feature

## The scene, beat by beat
1. Open on the full app view so the viewer knows where they are.
2. The cursor moves to the first control and clicks it.
3. The camera pushes in on the region that changes, cropping away chrome.
4. Input types on or content streams or scrolls inside a masked panel.
5. The result appears: a new row, chip, toggle or answer resolves into place.
6. The frame reframes back out to the full view, ready for the next feature or a cut.

Patterns: [cursor_guided_demo](../patterns/cursor_guided_demo.md), [layout_reframe](../patterns/layout_reframe.md), [ui_camera_push_in](../patterns/ui_camera_push_in.md), [masked_scroll](../patterns/masked_scroll.md), [scale_dissolve_transition](../patterns/scale_dissolve_transition.md), [ai_answer_stream](../patterns/ai_answer_stream.md), [skeleton_resolve](../patterns/skeleton_resolve.md), [prompt_type_on](../patterns/prompt_type_on.md)

- **GSAP / HyperFrames:** Build the UI as one large DOM canvas inside a wrapper and drive a single timeline per scene: scale and translate tweens on the wrapper for push-ins and reframes (smooth power or expo in-out eases), a scripted cursor element tweened between targets with click pulses, text tweens for typed input, and a short stagger for streamed lines or list rows inside a masked, upward-scrolling container.
- **Remotion:** One Sequence for the scene holding the app canvas; camera framing comes from interpolated scale and translate keyed to frame, with a critically damped spring for each push-in and reframe; child Sequences offset the cursor moves, typing and result reveals so each starts on its own narration word.

## Measured
- Scene length: median 3.1 s, 90% interval 2.7 to 3.5 (n=308, 41 videos)
- Motion events per scene: median 0.0 events, 90% interval 0.0 to 0.0 (n=308, 41 videos)
- First motion: median 1.0 s, 90% interval 0.8 to 1.4 (n=57, 14 videos) after the scene starts
- Way in: other 40%, hard cut 28%, zoom through 16%, crossfade 8%
- Story beat: demo 69%, mechanism 10%, outcome 7%, hook 4%
- Sound: unsure 35%, music 29%, swoosh reverse 14%, impact 12%

## Sound cues
Mostly music bed under the demo; when there is a cue it is a reverse swoosh or a soft impact landing on a camera push-in, with an occasional chime when a result appears and light clicks on cursor taps. Many cues are unlabelled, so treat sound as optional.
- chime: median 3.5 s, 90% interval 2.8 to 5.6 (n=56, 17 videos) after the scene starts
- click: median 2.4 s, 90% interval 1.7 to 8.2 (n=24, 12 videos) after the scene starts
- glitch: median 14.6 s (n=4, 2 videos) after the scene starts
- impact: median 2.2 s, 90% interval 1.8 to 2.9 (n=105, 21 videos) after the scene starts
- music: median 3.3 s, 90% interval 2.8 to 3.8 (n=356, 28 videos) after the scene starts
- swoosh reverse: median 3.5 s, 90% interval 2.5 to 4.5 (n=132, 22 videos) after the scene starts
- typing: median 4.2 s (n=4, 1 videos) after the scene starts
- unsure: median 2.9 s, 90% interval 2.6 to 3.3 (n=309, 33 videos) after the scene starts
- whoosh: median 1.0 s (n=4, 3 videos) after the scene starts

## Examples
- `elevenlabs-introducing-elevenlabs-conversational-ag` s002 (video score 5/5)
- `anthropic-introducing-claude-design-by-anthropic-l` s013 (video score 4/5)
- `datadog-datadog-overview-see-inside-the-platfor` s012 (video score 4/5)
- `warp-introducing-warp-2-0-the-agentic-develo` s012 (video score 4/5)
- `atlassian-introduction-to-jira-product-discovery` s004 (video score 3/5)

## Caveats
- Most shots have no code-detected motion event, so first-motion timing rests on a minority of shots and videos.
- Members range from short close-ups to long continuous screen recordings; long members carry most of the pattern evidence.
- A large share of sound cues are unlabelled or music, so specific SFX timing is weak.
