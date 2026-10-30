# App Icon Orbit

`app_icon_orbit`

App icons or interface cards gather in a ring around a central brand mark or headline, then turn, glow or change state together. It shows the product as the hub that connects or replaces many tools.

## When to use
- Showing that the product connects to or replaces many other apps
- Landing an outcome beat where scattered tools become one place
- Turning a ring of broken or alerting tools into healthy ones

## Slots (what you fill in)
- `hub`: the central brand mark, ring or headline the icons orbit
- `icons`: a set of generic app icons, logo badges or small interface cards
- `status_badge` (optional): a small badge on each icon, such as an alert dot that becomes a check
- `caption` (optional): a short line beside or under the ring, built word by word with the narration
- `background`: a gradient field that can shift colour to mark the change

## The scene, beat by beat
1. Start on the background, fading up from dark or out of the previous zoom
2. Bring in the hub at the centre
3. Fly or fan the icons into a ring around it, one after another
4. Change their state together: glow, swap to full colour, pop status badges, or shift the background
5. Rotate the ring slowly while the caption builds
6. Exit by drifting the ring out of frame, zooming through or flashing to white

Patterns: 

- GSAP / HyperFrames: One timeline per scene. Position icons on a circle with trigonometry inside a rotating container; stagger them in with scale and opacity from small, using a back out ease for a slight overshoot, or along curved paths from the corners with motion blur. Tween the background gradient and swap icon filters on one beat, pop the status badges with a short back out stagger, then run a slow linear rotation on the container and a power in drift for the exit.
- Remotion: One Sequence for the ring; each icon gets its own spring delayed by its index for the entrance, with position computed from its angle; the container's rotation is a linear interpolate over the scene; a nested Sequence drives the state change and badge springs; a final Sequence handles the drift or flash out.

## Measured in premium explainers
- Scene length: 0.2-2.5 s (typical 1.0), 4 videos
- First motion after the scene starts: not measured
- Motion events per scene: 0-0 events (typical 0), 4 videos
- Way in: other 46%, crossfade 23%, zoom through 23%
- chime sound: 1.1-1.1 s (typical 1.1), 1 videos after the scene starts
- click sound: 0.7-0.7 s (typical 0.7), 1 videos after the scene starts
- impact sound: 4.5-6.5 s (typical 5.5), 1 videos after the scene starts
- music sound: 0.5-7.3 s (typical 1.6), 2 videos after the scene starts
- unsure sound: 0.1-0.9 s (typical 0.5), 1 videos after the scene starts

## Sound
No typical sound. Music carries most of these scenes; a chime or click can mark icons arriving or a state change, but each comes from a single video.

## Caveats
- Few videos, and several members are very short slivers split by the cut detector from one continuous move, so the measured length runs short.
- No motion events or patterns were measured, so the build notes come from shot descriptions only.
- Each sound cue comes from only one or two videos.
