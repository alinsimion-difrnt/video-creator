# Virtual Camera Move Over UI

`ui_camera_push_in`

A virtual camera moves over a product screen without cutting: it pushes in to a detail, pans sideways across it, or pulls out to show the whole interface. The UI itself stays put; the frame around it travels.

## When to use
- The narration names one control, row or result and the viewer needs to see it up close
- A dense full-screen UI must become readable without a cut
- Showing cause and effect: close on a click, then pull out to reveal what it changed
- Keeping a static screen alive during a long narrated line with a barely visible drift

## Avoid when
- The target detail is not known yet; a move that lands on nothing reads as aimless
- Several camera moves would stack back to back and make the viewer seasick
- The UI is low resolution and will turn soft when enlarged

## Build
1. Put the whole UI (screenshot or live layout) inside one camera wrapper so everything moves together
2. Pick the end framing: the control, list or panel the narration is about, and set the transform origin there
3. Animate the wrapper's scale and translate together toward that framing; reverse the values for a pull-out, or translate only for a sideways pan
4. Time the move to a narration beat or the gap between sentences so it has a clear reason
5. Optionally add motion blur during travel that resolves to sharp on arrival
6. Once the frame settles, bring in the follow-up detail such as the pointer arriving on the named control

- GSAP / HyperFrames: One gsap.fromTo on the camera wrapper animating scale plus xPercent/yPercent, with transformOrigin at the target. Mostly an ease-out (power or expo out) for snappy arrivals, ease-in-out (power or sine inOut) for smooth glides and slow drifts, linear for continuous background motion; occasionally a slight overshoot ease. No stagger: children ride along with the wrapper. Chain the pointer or content change on the timeline after the move, and add an optional yoyo blur tween for motion blur.
- Remotion: Drive one progress value per move, either interpolate on frame with an Easing.out or Easing.inOut curve, or a critically damped spring with no overshoot. Map it to scale and translate on a single AbsoluteFill wrapping the UI; a pull-out maps from a large scale back to one. Content swaps and pointer moves are separate Sequences or interpolations timed after the camera lands.

## Measured in premium explainers
- Duration: 291-845 ms (typical 562), 6 videos
- Easing: ease out 43%, ease in out 18%, ease in 16%, linear 16%
- Changes: scale up 25%, fade 19%, color shift 8%, other 7%
- Sound offset to the landing: -189-48 ms (typical -59), 4 videos

## Sound
Often no distinct sound (many hits are unsure or just music). When there is one it is usually a soft impact or a reverse swoosh, sometimes a click or chime, landing just before the move starts or right on it.

## Why it reads as premium
The camera does the viewer's looking for them. Instead of asking people to hunt across a busy full-screen interface, a smooth eased move crops away browser chrome and sidebars and lands exactly on the thing the voice is talking about, and pulling back out afterwards shows the consequence in context. Because there is no cut, the viewer keeps their sense of where the detail sits in the whole product, and a crisp settle, sometimes after motion blur, makes the UI feel like a real physical surface. Even a barely perceptible drift keeps a static page from looking frozen.

## Caveats
- Merged pattern: push-ins, sideways pans and pull-outs share one card, so the timing spread covers both snap moves and slow drifts
- Durations were measured in only some of the videos where the pattern appears
- Sound offset comes from a handful of videos and many sound labels are unsure
