<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/film/G/NOTES.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# Segment G (film-g): orbit collapse into Acme, end card

Global 96.8667–105.1333 s (frames 2906–3154), local duration 8.2667 s. Scene s09, storyboard shot 32, key frame kf10.
Based on the judged wow/t5-close (round 3). Source: src/index.tpl + src/build.py (inlines the real SVGs),
src/layout.py (frame-0 phase search), src/sim.py (pose simulator used to tune ring A), src/search2.py (time-window search, not adopted).

## Beats (local / global)
- 0.00 / 96.87 F→G seam: the whole cast (#cast: rings, trails, discs, chips) at scale 0.75 (origin frame centre), blur 16px,
  opacity 0.15, already turning. 0.00–0.50 it grows to 1 / 0px / 1 on expo.out (readable from ~0.12).
- 0.12–0.30 / 96.99–97.17 the readable orbit: 3 engines (136px discs, never under 98px), 10 sources (100px, never under 72px),
  the green "Signed" chip (kf09 style) and the orange Acme CRM chip at the front of ring C. "Example data" tag.
  Radius now collapses on power4.in (was power3.in) and the spin boost on u^4 (0.4 turn, was 0.6 on u^3), so the orbit
  holds its size while it is read. Ring A was shifted +0.1 rad and slowed (0.6 rad/s) so Acme never covers ChatGPT.
- 0.30–0.63 / 97.17–97.50 spiral collapse: sources arrive 0.50–0.56, engines 0.57–0.59, Signed 0.60, Acme CRM last at
  0.63, pulled into the arrow tip. Tag fades 0.52–0.67.
- 0.50 / 97.37 the G ring draws out of the impact point (mask sweep) as the mark scales 0.55→1; "Ack-me" at 0.61.
- 0.56–0.86 arrow swings in and locks (~0.70). 0.68–1.07 mark steps into place, EOflux unrolls.
- 1.96 / 98.83 "Free plan" (on "free" 2.33). 3.01–3.67 it slides aside, divider, "No card needed" (~3.3; "need" 3.89).
- 3.87 / 100.74 acme.example; 4.20–4.60 orange underline. 4.60–8.2667 / 101.47–105.13 still hold = kf10 (cta top 614,
  underline 30px under the URL). Verified: no pixel change after 4.7 s (ffmpeg scene filter, 0 changes).

## Seam states
- Start (strip-start.png, 30 fps, 0–0.6 s): frame 0 = cast at 0.75 / blur 16 / opacity 0.15, moving; grows over 0.5 s
  while spinning. Z direction matches F's exit (growing = push). The Signed chip is in the cast.
- End (strip-end.png): the kf10 end card, static (film's last frame).

## Rounds
1. Port: seam entry wrapper, Signed chip, bigger discs (depth scale 0.72–1.12), kf10 positions, new phase search. Spin
   rose too early: the orbit was already collapsing by 0.35 and Acme sat on ChatGPT at 0.4.
2. power4.in radius + u^4 spin boost: clean orbit to ~0.30 (sim gap >= 1.2). Acme still crossed ChatGPT 0.33–0.40.
3. Ring A +0.1 rad, 0.6 rad/s (sim.py): chips clear of every disc through 0.40; frame 0 spacing 1.41.

## Check
lint 0/0; check ok=true; runtime/layout/motion/contrast 0 errors, 0 warnings (overlaps declared on #cast, discs, logo).
render.mp4 has 249 video frames (assemble.sh trims to 248).

## Weaknesses
- The seam contract leaves only ~0.2 s of fully sharp, full-size orbit (0.12–0.32) before the collapse that must land
  on "Ack-me" at 0.61. The storyboard wants the orbit to start at the end of s08: segment F should show the cast
  (incl. Signed) orbiting in its last beat, or the orbit reads as a flash.
- 0.30–0.45 discs pass over each other during the collapse (declared, by design); Gemini/Reddit cross ~0.33.
- The arrow appears mid-swing at 0.56 while the last engines arrive; 0.56–0.60 is busy.
- Tagline centring relies on fixed bundled font widths (as in t5).

## Cut 3 (REVISION_2 + review item 9: "animate the end card")
Cut 2 kept as render-cut2.mp4 and src/index-cut2.tpl. The F→G seam and the orbit/collapse (0–0.63) are unchanged.
- Floor #EEF1F5 (global fix 2). Signed text darkened to #15803D (contrast at the seam frame).
- End card lives in #stage, which the camera pushes at a constant ~2.9%/s from scale 0.82 (0.90) to 1.0 (7.34),
  so it never holds. Only the last 0.93 s (7.34–8.27) is still: the designed final settle. The dot floor stays put, which gives parallax.
  The impact point and Acme's arrow-tip target are solved in stage coordinates, so the collapse still lands at (960,440).
- Bigger: logo 900px (47% of the width; 738px on screen at 0.9 s), tagline 68px, URL 64px with a 6px orange underline.
- 0.50–1.35: one landing move. The G draws at impact, the mark grows 0.55→1 (expo.out) while it travels to its place
  (power3.inOut, 0.64–1.26), and the arrow locks at ~0.70. EOflux unrolls from 0.74 to 1.2.
- 2.21 "Free plan" rises out of an 8px blur, alone and centred (on "free" 2.33). 3.40–3.90 it slides aside, the divider
  grows (3.66) and "No card needed" lands (3.76, on "need" 3.89 / "card" 4.13).
- 4.42 acme.example rises (unspoken; after "card."). 4.82–5.37 the orange underline sweeps.
- 5.55–6.43: the cast settles in. The three engines (ChatGPT, Gemini, Perplexity, real logos, 120px discs) come to rest under the URL.
- Checks: lint 0/0; check ok, contrast/layout/motion 0/0. freezedetect n=0.002 d=1.2: none.
  At d=0.5 it flags from 7.2, because the slow push is under the n threshold; frame-diff shows pixels change until 7.33.
  249 frames (assemble trims to 248). strip-start.png and strip-end.png re-made.
- Rounds: (1) power1.out push froze from 6.3. (2) Linear push with an eased tail froze from 7.1. (3)–(5) faster push
  (S0 0.82) running to 7.28, plus the contrast fix.
- Weaknesses: frame 0 is faint by contract (opacity 0.15, blur 16), although the cast spans ~65% of the width. The orbit is fully
  readable for only ~0.2 s. From 1.35 to 2.2 the logo is alone, with only the push moving. The final 0.93 s is a hard still.
- Cut 3b: the F→G contract changed to frame 0 = scale 0.75, blur 12px, opacity 0.4, growing to full over 0.5 s (expo.out).
  "Free plan" now types on letter by letter from 1.80 to 2.30 (anticipating "There's" at 1.89; complete on "free" 2.33),
  which fills the thin stretch. lint 0/0, check ok 0/0, freezedetect d=1.2 none. strip-start.png and strip-end.png re-made.

## Final (REVISION_3: zoom out 0.92)
Cut 3 kept as render-cut3.mp4 and src/index-cut3.tpl. All foreground (cast, end-card stage, tag) sits in #fg, scaled 0.92 about (960,540);
the floor and dot grid stay full-bleed. The seam contract maps through #fg automatically. The "Example data" tag moved to the top right, out of
the captions band. End frame: logo, tagline and URL end above y≈760, and the engine row ends at y≈916 (<930). The smallest
source disc is 66px. lint 0/0, check ok (0/0 all categories), freezedetect d=1.2 none. strip-start.png and strip-end.png re-made.
