# Chat Demo Panel

`chat_demo_panel`

A cropped chat or agent panel plays a scripted conversation: messages pop in one at a time, the assistant's answer streams in, and the thread scrolls up as it grows. It is the longer demo scene that shows the product actually doing the work.

## When to use
- Demonstrating an AI assistant or support agent answering a real request.
- Showing reasoning steps or tool calls alongside a conversation.
- Walking through a multi-turn exchange that ends in a resolved outcome.

## Slots (what you fill in)
- `panel_chrome`: the chat window or panel frame, cropped and placed on a branded background
- `messages`: a short scripted list of user and assistant turns in plain language
- `answer_body`: the assistant's longest reply, as bullets or short lines that stream in
- `source_chips` (optional): optional small chips or citations appended to answer lines
- `side_panel` (optional): an optional card beside the chat showing reasoning steps or a mascot
- `avatars` (optional): small avatars marking who is speaking

## The scene, beat by beat
1. The panel slides or pushes into frame over the background, sometimes opened by a cursor click.
2. The user's message types on or pops in as a bubble.
3. The assistant's reply streams in line by line, with chips or status rows appended as it goes.
4. Older bubbles scroll up and out behind a mask as new turns arrive.
5. An optional side card fills in step with each assistant turn.
6. The exchange ends on the resolved outcome before a cut.

Patterns: [masked_scroll](../patterns/masked_scroll.md), [stagger_list_reveal](../patterns/stagger_list_reveal.md), [ai_answer_stream](../patterns/ai_answer_stream.md), [notification_pop](../patterns/notification_pop.md), [chip_append](../patterns/chip_append.md), [prompt_type_on](../patterns/prompt_type_on.md), [ui_camera_push_in](../patterns/ui_camera_push_in.md)

- GSAP / HyperFrames: One timeline per scene built from a scripted message array. For each turn, pop the bubble in with a small scale-up and fade on a back or expo ease-out, then tween the inner thread container's y inside an overflow-hidden mask so the stack scrolls up. Stream answer lines with a stagger on opacity and a short upward move, or reveal them left to right with a gradient mask tween, and pop each chip right after its line. Drive the side card's bullets with the same timeline labels so they land with each assistant turn. A slow scale on the panel wrapper gives the gentle camera push.
- Remotion: One Sequence per turn, offset by the script's timing. Inside each, a stiff spring drives the bubble's scale and opacity, and a damped spring drives the thread's scroll offset. Stream answer lines with staggered springs or an interpolated mask width, and render the side card from the same turn index.

## Measured in premium explainers
- Scene length: 3.4-11.2 s (typical 6.2), 8 videos
- First motion after the scene starts: 0.0-0.6 s (typical 0.1), 4 videos
- Motion events per scene: 0-3 events (typical 1), 8 videos
- Way in: hard cut 60%, other 36%, zoom through 4%
- chime sound: 5.6-5.7 s (typical 5.6), 1 videos after the scene starts
- click sound: 4.3-10.8 s (typical 6.4), 1 videos after the scene starts
- glitch sound: 3.3-3.3 s (typical 3.3), 1 videos after the scene starts
- impact sound: 10.3-22.0 s (typical 16.9), 3 videos after the scene starts
- music sound: 3.5-10.9 s (typical 7.6), 5 videos after the scene starts
- pop sound: 0.1-0.1 s (typical 0.1), 1 videos after the scene starts
- swoosh reverse sound: 3.9-18.0 s (typical 12.8), 3 videos after the scene starts
- unsure sound: 3.6-13.5 s (typical 7.1), 5 videos after the scene starts

## Sound
Music carries most of the scene. Reversed swooshes and impacts tend to come later, as panels or answers land deep into the scene rather than at its start; a pop or click occasionally marks a single bubble or a send. Many cues are unclassified.

## Caveats
- Sound counts are dominated by a few long shots from a handful of videos, so cue offsets mostly reflect those shots.
- One member is a real screen recording and another is several scenes merged into one shot, so lengths vary widely.
