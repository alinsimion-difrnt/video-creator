<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/film/REVISION_3.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# Cut 3 → final (client note: "maybe zoom out a little, some elements are too close to screen border")

Same change in EVERY segment, so all seams stay matched:
1. Wrap all foreground content (everything except full-bleed background layers: floor colour, dot grid, background
   blur planes) in one container scaled 0.92 about the frame centre (960,540). Background layers stay full-bleed so
   no frame edge ever shows. Seam contract geometry now maps through this transform (x' = 960+0.92(x-960),
   y' = 540+0.92(y-540)) on both sides automatically — do not hand-adjust contract numbers.
2. Title-safe rule after the scale: no text, logo or UI card closer than 5% to any edge (96 px left/right, 54 px
   top/bottom) when it is meant to be read, except deliberate motion exits/entries (whips, cut-the-curve, things flying
   past the lens) and out-of-focus foreground depth layers. Fix the remaining offenders in your listed ranges.
3. Bottom 150 px will carry burned-in captions (white pill, centred, ~44 px). Keep important content out of
   y > 930 where possible (move it up, don't shrink further).
Re-render render.mp4 (keep render-cut3.mp4 first), lint/check/freezedetect, strip-start/end.png, NOTES "Final" section.
Reply ≤4 lines.
