# Prompt Input Card

`prompt_input_card`

A clean, rounded prompt box sits on a calm background while a request types into it with a caret, often followed by a press on the send button. It shows the viewer how simply they ask the product for something, usually as the hook or the start of a demo.

## When to use
- Opening an AI feature by showing the question a user would ask.
- Starting a demo beat where the request leads into the product's answer.
- Showing a menu of presets or modes attached to an input field.

## Slots (what you fill in)
- `greeting` (optional): an optional short line above the input that sets the tone
- `prompt_text`: the request the user types, one sentence in plain language
- `input_chrome`: the prompt box itself with its send button and small controls
- `context_ui` (optional): simplified surrounding interface such as suggestion chips or a short list
- `preset_menu` (optional): an optional popover of modes or presets with a moving highlight
- `handoff_element` (optional): what the sent prompt turns into, such as a chat bubble or a thinking label

## The scene, beat by beat
1. The background and an optional greeting fade up on their own.
2. The prompt box and any surrounding interface assemble beneath it with a gentle stagger.
3. The camera pushes in so the input fills more of the frame.
4. The request types on character by character with a blinking caret.
5. A cursor moves to the send button and presses it, or a preset highlight moves to the chosen option.
6. The interface clears and the prompt hands off to the next scene as a bubble or a thinking state.

Patterns: [layout_reframe](../patterns/layout_reframe.md), [spotlight_focus](../patterns/spotlight_focus.md)

- GSAP / HyperFrames: One timeline per scene. Stagger the interface pieces in with opacity and a small upward move on an expo or sine ease-out. Tween the camera wrapper's scale toward the prompt box on a slow sine in-out. Type the prompt with a stepped tween over a text counter plus a blinking caret, then tween the cursor to the send button and play a quick scale-down press. End with a fade of the surrounding interface and a scale of the prompt into its handoff element.
- Remotion: One Sequence for the assembly, one for the push-in and typing, one for the send and handoff. Drive the push-in with a heavily damped spring, slice the prompt string by an interpolated character count for the typing, and use a stiff, short spring for the button press and popover entrance.

## Measured in premium explainers
- Scene length: 2.0-5.1 s (typical 2.7), 13 videos
- First motion after the scene starts: 0.2-9.9 s (typical 0.6), 4 videos
- Motion events per scene: 0-0 events (typical 0), 13 videos
- Way in: hard cut 37%, other 37%, zoom through 16%
- chime sound: 1.9-10.5 s (typical 7.0), 2 videos after the scene starts
- click sound: 1.1-1.7 s (typical 1.5), 3 videos after the scene starts
- glitch sound: 1.4-2.2 s (typical 1.8), 1 videos after the scene starts
- impact sound: 0.6-15.5 s (typical 1.2), 3 videos after the scene starts
- music sound: 0.9-6.6 s (typical 3.4), 4 videos after the scene starts
- swoosh reverse sound: 0.1-2.6 s (typical 0.9), 5 videos after the scene starts
- unsure sound: 1.0-2.5 s (typical 1.6), 5 videos after the scene starts

## Sound
Music usually carries the scene. When there are cues, a reversed swoosh tends to land early as the box arrives, and a soft click marks the send press shortly after; an impact or glitch occasionally punctuates the handoff. Many cues are unclassified, so treat sound as optional.

## Caveats
- Most member shots have no counted motion event, so motion timing here is thin and first motion is measured on few shots.
- The most common pattern label is other; the typing itself has no measured pattern in this set.
- Sound cues are sparse and many are unclassified.
