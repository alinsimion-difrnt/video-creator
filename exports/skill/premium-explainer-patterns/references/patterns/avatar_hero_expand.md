# Avatar Grows Into Hero

`avatar_hero_expand`

A small round avatar or decorative orb lifts out of its place and grows into a large centred hero object while the surrounding UI shrinks and fades behind it. The reverse also appears: the hero shrinks back down to become a small avatar badge on a message.

## When to use
- Moving from a UI choice (a clicked card or template) to the product concept it represents
- Turning a brand visual into the concrete product object without a cut
- Introducing an agent or presenter whose face or orb should carry identity across scenes

## Avoid when
- There is no recognisable small object to start from; the handoff then reads as a random zoom
- The surrounding UI still needs to be read while the hero grows

## Build
1. Measure the small avatar's on-screen position and size so the hero can start exactly there
2. Fade out or shrink back the surrounding headline or panel to make room and add depth
3. Move the avatar towards centre while scaling it up into the hero size
4. If the hero becomes something else (a video bubble, a voice orb), reveal the new content inside the circle as it grows
5. Let a small finishing detail, such as a status badge, pop onto the rim last
6. For the reverse, shrink the hero towards a corner and fade the message bubble in beneath it so it lands as the badge

- GSAP / HyperFrames: A timeline with FLIP-style fromTo on the avatar: start from its measured rect (small scale, offset x/y) and tween to centre at full scale. Run a parallel tween scaling down and fading the panel or headline. The hero travel is mostly linear or ease-out, with ease-in-out (power inOut) for the combined move; finishing badges use a slight overshoot ease (back.out). Text lines inside a following bubble can stagger softly.
- Remotion: One spring (high damping, no overshoot) as shared progress, interpolated into the orb's scale and translate and the panel's scale and opacity. A delayed spring with a circular overflow mask reveals the inner content; a separate lower-damping spring gives the badge its small overshoot. An outer scene wrapper can scale with a gentle interpolate for a camera push.

## Measured in premium explainers
- Duration: 1072-1249 ms (typical 1160), 1 videos
- Easing: linear 43%, ease out 29%, ease in out 14%, spring overshoot 14%
- Changes: fade 24%, scale down 21%, slide up 21%, slide right 13%
- Sound offset to the landing: 86-153 ms (typical 86), 1 videos

## Sound
A soft chime is the typical cue, sometimes a reverse swoosh, landing just after the move starts.

## Why it reads as premium
The object the viewer was already looking at becomes the star. Rather than cutting from a UI or brand world to a product shot, one continuous shape carries identity across the change: a tiny template avatar swells into the agent's hero orb, or a background orb turns into the presenter's camera bubble. The receding panel behind it adds depth, and saving a small product cue such as a record badge for last gives the move a clear landing. Played in reverse, the same object becoming an avatar badge on a chat message hands the concept back into a concrete demo.

## Caveats
- Seen in only two videos
- Timing and sound offset were measured in a single video
- Mixes forward (grow into hero) and reverse (shrink into badge) events
