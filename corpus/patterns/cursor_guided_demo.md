# Cursor Leads The Demo

`cursor_guided_demo` · 59 events in 8 videos

A mouse pointer glides across the product screen, lands on a button, list row or panel and clicks it, and the interface reacts right away so the viewer sees the feature working.

## When to use
- Showing how a feature is used, one action at a time
- Turning a narrated claim into a visible cause and effect
- Pointing the eye at a detail (a citation, a field, a menu option) before it matters

## Avoid when
- The screen is already busy and a moving pointer would compete with it
- The message is abstract and there is no real interaction to show
- The cursor path would wander or jitter instead of going straight to its target

## How to build it
1. Lay out the interface in its starting state with the cursor parked off target or just entering the frame
2. Move the cursor along one smooth, eased path straight to the target, optionally with slight motion blur
3. Swap the cursor sprite (arrow to hand or crosshair) as it arrives
4. Play a short press: the cursor or target squashes slightly and springs back
5. Trigger the result of the click: a highlight, colour change, dropdown, or new panel sliding or fading in
6. Let hover tints follow the cursor across rows or options, then move the cursor out of the way so the result can be read

- **GSAP / HyperFrames:** Use a timeline: a to() tween on the cursor's x and y with an ease_in_out or ease_out power ease (power2.inOut or power2.out), a tl.set() to swap the cursor sprite on arrival, then a tiny scale yoyo for the press. Follow it with fromTo() tweens on the reacting element (autoAlpha, scale, y, backgroundColor or clipPath) using an ease_out family such as power3.out, or back.out for a spring_overshoot pop. Stagger reacting icons or rows lightly; drive hover tints with tl.call() or quick backgroundColor tweens as the cursor crosses each row.
- **Remotion:** Drive cursor position with interpolate() and Easing.inOut or Easing.out (or Easing.bezier) between the start and target points, and pick the cursor sprite by frame threshold. Animate the press and the UI reaction with spring() (moderate damping, no overshoot for focus rings; allow slight overshoot for pops) mapped to scale, opacity and translate. Compute hovered rows from the cursor's current y each frame.

## Measured
- Duration: median 410 ms, 90% interval 227 to 532 (n=57, 7 videos)
- Easing: ease out 27%, ease in 25%, ease in out 22%, spring overshoot 19%
- Changes: highlight 21%, fade 21%, color shift 11%, slide down 10%
- Elements: list item 25%, cursor 18%, button 14%, ui panel 10%
- Sound: music 52%, unsure 23%, chime 13%, impact 13%; offset to the landing median 75 ms, 90% interval -189 to 138 (n=23, 5 videos)

## Sound
No typical sound: most detected audio here is music or unclear. When a distinct effect is used it is a soft chime or light impact landing near the click.

## Why it reads as premium
The cursor carries intent: it travels on one clean, decelerating path to exactly the control that matters, and that single click visibly changes the product state with no cut, so the feature is demonstrated rather than explained. Real feedback (a press-in, a radial fill, a focus ring snapping tight, hover tints following the pointer) makes the interaction feel tactile, and the pointer then gets out of the way so the result stays readable while the narration lands.

## Examples
- `anthropic-introducing-claude-design-by-anthropic-l` e010 (video score 4/5)
- `hubspot-what-is-hubspot` e003 (video score 4/5)
- `loom-introducing-loom-ai` e003 (video score 4/5)
- `notion-introducing-notion-ai-connectors` e022 (video score 4/5)
- `notion-introducing-the-new-notion-ai` e001 (video score 4/5)

## Caveats
- Easing is split fairly evenly between ease-out, ease-in and ease-in-out, so pick per move rather than treating one as standard
- Sound timing was measured on fewer events and videos than motion timing, and the offset range spans both before and after the action
