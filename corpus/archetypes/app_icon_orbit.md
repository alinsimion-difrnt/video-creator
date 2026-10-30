# App Icon Orbit

`app_icon_orbit` · 12 shots in 4 videos

App icons or interface cards gather in a ring around a central brand mark or headline, then turn, glow or change state together. It shows the product as the hub that connects or replaces many tools.

## When to use
- Showing that the product connects to or replaces many other apps
- Landing an outcome beat where scattered tools become one place
- Turning a ring of broken or alerting tools into healthy ones

## What you fill in
- **hub**: the central brand mark, ring or headline the icons orbit
- **icons**: a set of generic app icons, logo badges or small interface cards
- **status_badge** (optional): a small badge on each icon, such as an alert dot that becomes a check
- **caption** (optional): a short line beside or under the ring, built word by word with the narration
- **background**: a gradient field that can shift colour to mark the change

## The scene, beat by beat
1. Start on the background, fading up from dark or out of the previous zoom
2. Bring in the hub at the centre
3. Fly or fan the icons into a ring around it, one after another
4. Change their state together: glow, swap to full colour, pop status badges, or shift the background
5. Rotate the ring slowly while the caption builds
6. Exit by drifting the ring out of frame, zooming through or flashing to white

Patterns: 

- **GSAP / HyperFrames:** One timeline per scene. Position icons on a circle with trigonometry inside a rotating container; stagger them in with scale and opacity from small, using a back out ease for a slight overshoot, or along curved paths from the corners with motion blur. Tween the background gradient and swap icon filters on one beat, pop the status badges with a short back out stagger, then run a slow linear rotation on the container and a power in drift for the exit.
- **Remotion:** One Sequence for the ring; each icon gets its own spring delayed by its index for the entrance, with position computed from its angle; the container's rotation is a linear interpolate over the scene; a nested Sequence drives the state change and badge springs; a final Sequence handles the drift or flash out.

## Measured
- Scene length: median 1.0 s, 90% interval 0.2 to 2.4 (n=12, 4 videos)
- Motion events per scene: median 0.0 events, 90% interval 0.0 to 0.0 (n=12, 4 videos)
- First motion: not measured after the scene starts
- Way in: other 46%, crossfade 23%, zoom through 23%, hard cut 8%
- Story beat: outcome 62%, demo 15%, hook 15%, problem 8%
- Sound: music 42%, chime 17%, impact 17%, unsure 17%

## Sound cues
No typical sound. Music carries most of these scenes; a chime or click can mark icons arriving or a state change, but each comes from a single video.
- chime: median 1.1 s (n=1, 1 videos) after the scene starts
- click: median 0.7 s (n=1, 1 videos) after the scene starts
- impact: median 5.5 s (n=2, 1 videos) after the scene starts
- music: median 1.6 s (n=4, 2 videos) after the scene starts
- unsure: median 0.5 s (n=2, 1 videos) after the scene starts

## Examples
- `datadog-datadog-overview-see-inside-the-platfor` s010 (video score 4/5)
- `clickup-clickup-4-0-just-changed-work-ai-softwar` s036 (video score 4/5)
- `clickup-clickup-4-0-world-s-first-converged-ai` s018 (video score 4/5)
- `zapier-zapier-s-newest-product-features-build` s001 (video score 4/5)

## Caveats
- Few videos, and several members are very short slivers split by the cut detector from one continuous move, so the measured length runs short.
- No motion events or patterns were measured, so the build notes come from shot descriptions only.
- Each sound cue comes from only one or two videos.
