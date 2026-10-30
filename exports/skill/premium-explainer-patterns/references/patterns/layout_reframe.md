# Layout Shifts Into Place

`layout_reframe`

Without a cut, everything on screen moves together into a new arrangement: elements slide, shrink or grow to make room, and new pieces fade in to fill the gaps, so one layout becomes the next.

## When to use
- Turning a title card or single line into the real product screen
- Showing the immediate result of an action, such as a new row appearing in a table
- Making room for a headline or answer while keeping earlier content as the anchor

## Avoid when
- The new state has nothing in common with the old one, so a transition would read better
- Elements move on different eases and the shift starts to feel like several unrelated motions

## Build
1. Group the elements that stay on screen so they can move as one unit
2. Decide the anchor element the viewer should track from the old layout into the new one
3. Move, shrink or grow the group to its new position on one shared ease
4. Fade and lift new elements into the space that opens, with a light stagger
5. Fade out or collapse anything that no longer belongs at the same time
6. Let the frame settle before the next action starts

- GSAP / HyperFrames: Use one timeline with to() or fromTo() tweens on x, y, yPercent and scale for the moving group, sharing an ease_out family (power2.out or power3.out) or ease_in_out (power2.inOut) for the main move. Add fromTo() tweens on autoAlpha and y for incoming items with a small stagger, positioned with '<' so they overlap the main move. For a shape that turns into another shape, GSAP Flip.from() captures the old state. Use back.out only for small accent pops (spring_overshoot), and linear for spinners or counters riding along.
- Remotion: Drive the shared move with one spring() at high damping (no overshoot) or with interpolate() and Easing.out or Easing.inOut, and map that single progress value to every element's translate and scale so they move together. Fade incoming children with interpolate() on opacity, offset by a frame or so per item. Reserve low-damping springs for a small reward pop.

## Measured in premium explainers
- Duration: 304-814 ms (typical 624), 11 videos
- Easing: ease out 43%, ease in out 27%, linear 13%, spring overshoot 9%
- Changes: fade 27%, slide left 17%, slide down 10%, scale down 9%
- Sound offset to the landing: -228-245 ms (typical 120), 3 videos

## Sound
No single typical sound: most detected audio is music or unclear. When an effect is used it is usually a reverse swoosh landing just after the shift begins, occasionally a chime or click.

## Why it reads as premium
The screen never cuts: one shared ease moves every layer at once, so the change reads as a single deliberate gesture rather than a set of separate animations. Something the viewer is already looking at (a greeting, a prompt, a table) stays as the anchor and becomes part of the new layout, which keeps attention continuous and makes the product feel responsive, as when a table makes room in place for a new item instead of opening a modal. New content arriving with a soft fade and rise lets the interface build around the message calmly and in step with the narration.

## Caveats
- Sound timing comes from only a few videos, so the sound guidance is weak
- A broad pattern: it covers both large title-to-product reframes and small in-product table reflows, which run at quite different speeds
