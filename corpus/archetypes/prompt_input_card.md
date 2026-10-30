# Prompt Input Card

`prompt_input_card` · 30 shots in 13 videos

A clean, rounded prompt box sits on a calm background while a request types into it with a caret, often followed by a press on the send button. It shows the viewer how simply they ask the product for something, usually as the hook or the start of a demo.

## When to use
- Opening an AI feature by showing the question a user would ask.
- Starting a demo beat where the request leads into the product's answer.
- Showing a menu of presets or modes attached to an input field.

## What you fill in
- **greeting** (optional): an optional short line above the input that sets the tone
- **prompt_text**: the request the user types, one sentence in plain language
- **input_chrome**: the prompt box itself with its send button and small controls
- **context_ui** (optional): simplified surrounding interface such as suggestion chips or a short list
- **preset_menu** (optional): an optional popover of modes or presets with a moving highlight
- **handoff_element** (optional): what the sent prompt turns into, such as a chat bubble or a thinking label

## The scene, beat by beat
1. The background and an optional greeting fade up on their own.
2. The prompt box and any surrounding interface assemble beneath it with a gentle stagger.
3. The camera pushes in so the input fills more of the frame.
4. The request types on character by character with a blinking caret.
5. A cursor moves to the send button and presses it, or a preset highlight moves to the chosen option.
6. The interface clears and the prompt hands off to the next scene as a bubble or a thinking state.

Patterns: [layout_reframe](../patterns/layout_reframe.md), [spotlight_focus](../patterns/spotlight_focus.md)

- **GSAP / HyperFrames:** One timeline per scene. Stagger the interface pieces in with opacity and a small upward move on an expo or sine ease-out. Tween the camera wrapper's scale toward the prompt box on a slow sine in-out. Type the prompt with a stepped tween over a text counter plus a blinking caret, then tween the cursor to the send button and play a quick scale-down press. End with a fade of the surrounding interface and a scale of the prompt into its handoff element.
- **Remotion:** One Sequence for the assembly, one for the push-in and typing, one for the send and handoff. Drive the push-in with a heavily damped spring, slice the prompt string by an interpolated character count for the typing, and use a stiff, short spring for the button press and popover entrance.

## Measured
- Scene length: median 2.7 s, 90% interval 2.2 to 3.7 (n=30, 13 videos)
- Motion events per scene: median 0.0 events, 90% interval 0.0 to 0.0 (n=30, 13 videos)
- First motion: median 0.6 s (n=4, 4 videos) after the scene starts
- Way in: hard cut 37%, other 37%, zoom through 16%, crossfade 11%
- Story beat: demo 56%, hook 32%, proof 8%, agitate 2%
- Sound: music 37%, unsure 24%, swoosh reverse 14%, click 9%

## Sound cues
Music usually carries the scene. When there are cues, a reversed swoosh tends to land early as the box arrives, and a soft click marks the send press shortly after; an impact or glitch occasionally punctuates the handoff. Many cues are unclassified, so treat sound as optional.
- chime: median 7.0 s (n=2, 2 videos) after the scene starts
- click: median 1.5 s, 90% interval 1.1 to 1.6 (n=5, 3 videos) after the scene starts
- glitch: median 1.8 s (n=2, 1 videos) after the scene starts
- impact: median 1.2 s (n=3, 3 videos) after the scene starts
- music: median 3.4 s, 90% interval 1.5 to 5.7 (n=23, 4 videos) after the scene starts
- swoosh reverse: median 0.9 s, 90% interval 0.1 to 2.7 (n=6, 5 videos) after the scene starts
- unsure: median 1.6 s, 90% interval 0.8 to 2.5 (n=9, 5 videos) after the scene starts

## Examples
- `attio-introducing-ask-attio` s001 (video score 4/5)
- `figma-introducing-figma-motion-your-canvas-no` s016 (video score 5/5)
- `google-introducing-the-google-pixel-9-pro` s001 (video score 4/5)
- `raycast-new-raycast-coming-2026` s008 (video score 4/5)
- `zendesk-meet-zendesk-ai-agents-the-most-autonom` s007 (video score 4/5)

## Caveats
- Most member shots have no counted motion event, so motion timing here is thin and first motion is measured on few shots.
- The most common pattern label is other; the typing itself has no measured pattern in this set.
- Sound cues are sparse and many are unclassified.
