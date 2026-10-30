# Cards Fill The Wall

`card_wall_stagger`

A wall or grid of cards builds up piece by piece: each card fades, slides or grows into its spot a moment after the one before, softly coming into focus, until the whole layout settles.

## When to use
- Showing breadth: a library, a set of use cases or a family of products
- Building a hierarchy where parent cards arrive before their child items
- Turning a single clip or screen into one item among many
- Giving each item a brief moment to register before the full picture lands

## Avoid when
- Only a couple of items need to be shown
- Each card needs to be read in detail while it is moving
- The narration is about one specific item rather than the collection

## Build
1. Lay out the final wall or grid first, then hide each card at its start state
2. Choose an order: from one corner, from the centre, parents before children, or random
3. Bring each card in with a fade plus a slide, scale or blur clearing, offset slightly from the previous card
4. Optionally scale the whole wall at the same time, as if the camera pulls back to reveal it
5. Bring in smaller satellite items, icons or connector lines after their parent cards
6. Land any headline last over the settled wall, and keep a slow drift going so it stays alive

- GSAP / HyperFrames: Use a timeline with gsap.fromTo on the card selector, animating opacity plus y/x, scale or filter blur, with a stagger object (each, from: 'start', 'center', 'end' or 'random', grid for tiled layouts). Ease-in and ease-out power curves dominate; use power ease-in-out for a container scale that pulls back the camera, a linear yoyo for idle drift, and back.out only for small pop-in icons. Overlap groups with position parameters so children start before parents fully settle.
- Remotion: For each card, offset the frame by its index and drive a spring (high damping, no overshoot) mapped through interpolate to opacity, translate, scale and blur. Animate the container scale with interpolate and an Easing.inOut curve. Use a low-damping spring only for small icons that should pop.

## Measured in premium explainers
- Duration: 527-2680 ms (typical 1586), 2 videos
- Easing: ease in 33%, ease out 30%, ease in out 18%, linear 14%
- Changes: fade 31%, blur in 18%, scale up 14%, scale down 10%
- Sound offset to the landing: -465--465 ms (typical -465), 1 videos

## Sound
Sound is often absent or unclear; where present it is a whoosh or reverse swoosh that leads into the motion, starting ahead of the cards arriving. Treat it as optional.

## Why it reads as premium
The stagger turns a crowd of items into a sequence the eye can follow, so a dense layout fills the screen without ever feeling cluttered. Soft blur clearing and gentle scale changes make cards feel like they are coming into focus rather than popping on, and ordering them by hierarchy or from a clear origin explains the structure as it builds. Pulling back from a single item to a wall with depth and slow drift makes an abstract idea such as a content library or a platform of agents feel spatial and tangible.

## Caveats
- Seen in only 3 videos, with timing measured in only 2 of them
- Sound timing comes from a single video, so the lead-in placement is a weak guide
- Wide timing spread: quick tile entries and long wall reveals are grouped together
