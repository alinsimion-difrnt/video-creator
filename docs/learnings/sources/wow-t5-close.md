<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/wow/t5-close/NOTES.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# t5-close: everything collapses into the logo

Idea: the film's cast (3 AI engines, 10 cited sources, your brand chip) orbits the centre on three tilted 3D
orbits; on "Ack-me" it all spirals in and the Acme mark forms out of the collapse, then the end card holds.

## Beats (s) — round 3 (8.26 s, 0.60 s pre-roll; "Ack-me" 0.60)
- 0.00 frame 0 alive: three tilted rings spread over ~84% of the frame width. Phases were chosen offline (src/layout.py) so every pair of discs is at least 1.6x the 1.3x-radii gap. Depth shows through scale (0.55-1.15) and opacity (0.6-1), with no blur. The Acme chip sits at the front of its ring. "Example data" tag.
- 0.00-0.62 the cast spirals in counter-clockwise: radius (and depth z) to 0 on power3.in, spin rising. Arrivals are staggered by distance: outer sources 0.50-0.52, inner sources 0.54-0.56, engines 0.58-0.60. The chip arrives last, at 0.62, pulled into the arrow tip. Faint navy speed trails.
- 0.50 the G ring is hidden until here, then its arc draws out of the impact point (mask sweep, counter-clockwise like the spiral) as the mark scales 0.55->1 (expo.out).
- 0.53-0.83 the arrow swings in and locks (~0.68, expo.out, no overshoot).
- 0.66-1.04 the mark steps into place and the E O f l u x wordmark unrolls.
- 1.95 "Free plan" (60px) is visible by 2.2, ahead of "free" at 2.32.
- 3.00-3.66 "Free plan" slides aside, the divider grows and "No card needed" lands (~3.3).
- 3.86 acme.example (56px, no pill). 4.20-4.60 one orange underline draws under it. Held end card from 4.6 to 8.26.

## Iterations

1. Base build: deterministic projected orbits driven by one proxy tween; fixed a CTA overlap and declared the arrow swing (data-layout-allow-orbit).
2. Added exact projected orbit paths; wordmark letters ordered left to right; CTA row centred as a whole.
3. Tightened the collapse (objects faded at ~45% radius); reduced depth blur.
4. Judge round (scores 7/7/8/8/6/5/8/6/WOW 4): collapse moved earlier (logo resolved by ~1.0, wordmark by 1.4); power3.in radius; gaussian motion blur replaced by directional navy trails; depth by scale/opacity; chip pulled into the arrow tip as the arrow locks; CTA bigger (52/46px), lands on its words; URL pill hairline without shadow; underline as the finishing move.
5. Judge round 2 (7/7/8/8/6/6/9/7/WOW 5): audio re-cut with a 0.60 s pre-roll so the convergence finishes on "Ack-me"; G hidden until impact and drawn by a mask sweep instead of fading in; frame-0 layout de-overlapped by search; depth blur removed; end card enlarged (logo 770px, tagline 60px, URL 56px); pill dropped for underline only; motion done by 4.6.

## Check
lint 0/0; check ok=true, layout 0 errors, 0 warnings.

## Known weaknesses
- The arrow becomes visible at 0.53 mid-swing while the last engines are still arriving, so the frames from 0.53 to 0.58 are a little busy.
- The tagline centring relies on fixed text widths (257/443 px at 60px) of the bundled fonts.
- From 4.6 s on the frame is a pure hold (3.7 s, by design, since this is the film's end).
