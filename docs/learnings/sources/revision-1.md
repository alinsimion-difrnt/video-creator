<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/film/REVISION_1.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# Cut 1 → Cut 2 revision (client notes on the full film, verbatim)
- "The questions at the start are too slow, maybe add more faster? I would also try an animation with many chats
  typing questions and zooming in to 1 conversation when you ask 'where to buy running shoes'"
- "Experience from second 8 to 20 is slow, simple and doesn't keep you interested as nothing really happens."
- "From 24 to 30 it's too simple, use something more nice in design, not elements from our report."
- "From 0:50 to 1:15 feels slow."  - "Same for 1:30 to 1:37"
- "In general, I don't want static slides that sit more than 2-3 seconds."

## Global rules for cut 2
- Something new lands at least every 1.0–1.5 s (a word-synced reveal, a camera move, a cut, a data change).
- No composition is held still for more than 1.5 s. If a frame must be read for ≥2 s, the camera keeps a purposeful
  move (slow push/track toward the next focus, ≥3%/s scale or ≥40 px/s), never idle wobble/breathing/drift loops.
- More shots, shorter shots: prefer cutting to a new angle/close-up over sitting on a wide.
- Bigger, bolder design moments over small UI: depth, scale contrast, 3D layers, real engine logos, orange focus.
- Keep the doctrine (current is LEFT, power3/expo, no bounce/back, reveals 0.05–0.15 s before the word).
- SEAM CONTRACTS IN $S/film/FILM_BRIEF.md ARE UNCHANGED. Segment durations unchanged (exact frames).
- Verify: `ffmpeg -i render.mp4 -vf freezedetect=n=0.002:d=1.2 -map 0:v -f null - 2>&1 | grep freeze_`
  → no freeze longer than 1.5 s (report the list). Plus lint 0/0, check 0 errors/0 warnings, strip-start/end.png
  re-made, NOTES.md updated with a "Cut 2" section.
- Re-render to the same render.mp4 path (keep cut-1 copy as render-cut1.mp4 first).
