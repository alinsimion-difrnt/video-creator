# Logo Builds Into Lockup

`logo_resolve` · 21 events in 10 videos

Shapes, icons or blurred type move, merge and sharpen until they settle into the brand logo, often with the mark arriving first and the wordmark joining it to complete the lockup.

## When to use
- Opening or closing a video on the brand
- Showing that many tools or features fold into one product
- Turning a product motif (an orb, a waveform, an icon) into the brand mark

## Avoid when
- The logo is already on screen and a second build would feel repetitive
- The build is so long or busy that the final mark is not given time to hold

## How to build it
1. Clear or cut away the previous content so the frame is calm
2. Start from pieces related to the brand: scattered parts of the mark, product icons, a soft shape, or blurred type
3. Optionally add a small anticipatory squeeze or contraction before the main move
4. Move, merge or morph the pieces into the mark on one shared ease, sharpening any blur as they land
5. Slide the mark aside and fade the wordmark in next to it to form the lockup
6. Ease in faint secondary elements, such as a tagline or background shapes, and hold the final frame

- **GSAP / HyperFrames:** Split the logo into SVG parts and build with a timeline: fromTo() tweens on x, scale, autoAlpha and filter blur using an ease_out family (power3.out, expo.out) for arrivals and ease_in_out (power3.inOut) for converging moves. For playful assembly use back.out or elastic.out on part scale (spring_overshoot) with a stagger from random, center or edges. Bring the wordmark in with a short autoAlpha and x tween overlapping the mark's settle.
- **Remotion:** Drive each part from its own spring() with a small per-part frame delay: high damping for clean slides and blur-to-sharp arrivals, lower damping where parts should pop and settle. Use interpolate() with Easing.inOut for converging rows and for blur and outline scale; layer the hero mark on top so other pieces tuck behind it.

## Measured
- Duration: median 618 ms, 90% interval 407 to 693 (n=40, 9 videos)
- Easing: ease out 42%, ease in out 29%, spring overshoot 14%, linear 9%
- Changes: fade 19%, morph 14%, slide left 12%, scale up 10%
- Elements: logo 60%, icon 19%, headline 15%, background 4%
- Sound: music 50%, unsure 20%, swoosh reverse 17%, chime 7%; offset to the landing median 130 ms, 90% interval 64 to 192 (n=25, 4 videos)

## Sound
No typical sound: most detected audio is music or unclear. When an effect is used it is usually a reverse swoosh arriving just after the logo starts to form.

## Why it reads as premium
The logo is assembled from its own geometry or from the product's visual motifs instead of a plain fade, so the brand moment reads as designed motion and often tells a story by itself, such as many tools collapsing into one or a voice orb becoming a waveform. Directional blur resolving to crisp type, a small wind-up before the merge, and one shared ease across all pieces give the build weight and intent. Letting the mark land alone before the wordmark joins keeps the hierarchy clear, and faint secondary elements add depth without pulling focus.

## Examples
- `google-introducing-the-google-pixel-9-pro` e003 (video score 4/5)
- `hubspot-what-is-hubspot` e001 (video score 4/5)
- `zendesk-meet-zendesk-ai-agents-the-most-autonom` e032 (video score 4/5)
- `attio-introducing-ask-attio` e018 (video score 4/5)
- `elevenlabs-introducing-eleven-v4-and-eleven-v4-turb` e001 (video score 4/5)

## Caveats
- Relatively few events overall, and sound timing comes from only a few videos
- Builds vary a lot in length, from quick slides to multi-stage morphs, so the timing spread is wide
