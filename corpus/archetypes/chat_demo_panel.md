# Chat Demo Panel

`chat_demo_panel` · 18 shots in 8 videos

A cropped chat or agent panel plays a scripted conversation: messages pop in one at a time, the assistant's answer streams in, and the thread scrolls up as it grows. It is the longer demo scene that shows the product actually doing the work.

## When to use
- Demonstrating an AI assistant or support agent answering a real request.
- Showing reasoning steps or tool calls alongside a conversation.
- Walking through a multi-turn exchange that ends in a resolved outcome.

## What you fill in
- **panel_chrome**: the chat window or panel frame, cropped and placed on a branded background
- **messages**: a short scripted list of user and assistant turns in plain language
- **answer_body**: the assistant's longest reply, as bullets or short lines that stream in
- **source_chips** (optional): optional small chips or citations appended to answer lines
- **side_panel** (optional): an optional card beside the chat showing reasoning steps or a mascot
- **avatars** (optional): small avatars marking who is speaking

## The scene, beat by beat
1. The panel slides or pushes into frame over the background, sometimes opened by a cursor click.
2. The user's message types on or pops in as a bubble.
3. The assistant's reply streams in line by line, with chips or status rows appended as it goes.
4. Older bubbles scroll up and out behind a mask as new turns arrive.
5. An optional side card fills in step with each assistant turn.
6. The exchange ends on the resolved outcome before a cut.

Patterns: [masked_scroll](../patterns/masked_scroll.md), [stagger_list_reveal](../patterns/stagger_list_reveal.md), [ai_answer_stream](../patterns/ai_answer_stream.md), [notification_pop](../patterns/notification_pop.md), [chip_append](../patterns/chip_append.md), [prompt_type_on](../patterns/prompt_type_on.md), [ui_camera_push_in](../patterns/ui_camera_push_in.md)

- **GSAP / HyperFrames:** One timeline per scene built from a scripted message array. For each turn, pop the bubble in with a small scale-up and fade on a back or expo ease-out, then tween the inner thread container's y inside an overflow-hidden mask so the stack scrolls up. Stream answer lines with a stagger on opacity and a short upward move, or reveal them left to right with a gradient mask tween, and pop each chip right after its line. Drive the side card's bullets with the same timeline labels so they land with each assistant turn. A slow scale on the panel wrapper gives the gentle camera push.
- **Remotion:** One Sequence per turn, offset by the script's timing. Inside each, a stiff spring drives the bubble's scale and opacity, and a damped spring drives the thread's scroll offset. Stream answer lines with staggered springs or an interpolated mask width, and render the side card from the same turn index.

## Measured
- Scene length: median 6.2 s, 90% interval 3.9 to 10.3 (n=18, 8 videos)
- Motion events per scene: median 1.0 events, 90% interval 0.0 to 2.0 (n=18, 8 videos)
- First motion: median 0.1 s, 90% interval 0.0 to 0.7 (n=8, 4 videos) after the scene starts
- Way in: hard cut 60%, other 36%, zoom through 4%
- Story beat: demo 81%, hook 8%, outcome 8%, proof 4%
- Sound: music 35%, unsure 28%, swoosh reverse 22%, impact 11%

## Sound cues
Music carries most of the scene. Reversed swooshes and impacts tend to come later, as panels or answers land deep into the scene rather than at its start; a pop or click occasionally marks a single bubble or a send. Many cues are unclassified.
- chime: median 5.6 s (n=2, 1 videos) after the scene starts
- click: median 6.4 s (n=4, 1 videos) after the scene starts
- glitch: median 3.3 s (n=1, 1 videos) after the scene starts
- impact: median 16.9 s, 90% interval 12.5 to 21.5 (n=14, 3 videos) after the scene starts
- music: median 7.6 s, 90% interval 5.7 to 9.3 (n=58, 5 videos) after the scene starts
- pop: median 0.1 s (n=1, 1 videos) after the scene starts
- swoosh reverse: median 12.8 s, 90% interval 6.4 to 14.1 (n=32, 3 videos) after the scene starts
- unsure: median 7.1 s, 90% interval 5.5 to 10.0 (n=43, 5 videos) after the scene starts

## Examples
- `zendesk-meet-zendesk-ai-agents-the-most-autonom` s003 (video score 4/5)
- `notion-introducing-the-new-notion-ai` s006 (video score 4/5)
- `raycast-new-raycast-coming-2026` s009 (video score 4/5)
- `clickup-clickup-4-0-just-changed-work-ai-softwar` s033 (video score 4/5)

## Caveats
- Sound counts are dominated by a few long shots from a handful of videos, so cue offsets mostly reflect those shots.
- One member is a real screen recording and another is several scenes merged into one shot, so lengths vary widely.
