<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/film/REVISION_2.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# Cut 2 → Cut 3 (shared brief for all segment builders)

Context: since cut 2 we ran 16 test directions and two independent reviews ($S/ten/review/REVIEW.md,
$S/six/review/REVIEW.md — read the "Ten improvements for the current 105 s film" section of the latter, and the
"Moments worth stealing" tables). Robert has not rejected the light-UI film; cut 3 lifts it with what we learned.
Keep the voice, music, durations and frame counts. Keep the film's world (light UI, Acme tokens) — this is a
lift, not a new direction. REVISION_1.md rules still hold (something new every 1.0–1.5 s; no frame still >1.5 s).

## Global fixes (every segment)
1. Hero object ≥40% of the frame; no frame >30% empty for >0.5 s — including during transitions and whips. Drive
   carriers from camera progress so the outgoing object stays big until the incoming one lands.
2. Depth on white: cards #FFFFFF on a #EEF1F5 floor with real soft contact shadows (layered box-shadows), a subtle
   depth-of-field blur on background planes, slight perspective/parallax. White must never read flat or milky.
3. Phone-first type: questions ≥44 px, meaningful labels ≥32 px, nothing important under 28 px at 1080p.
4. Orange (#00AA90) means only "your brand / Acme": no orange send buttons, outlines or decorations (use navy).
5. No placeholder/empty states on any spoken line (no blank card waiting for content).
6. Motion blur on fast moves (sub-frame or directional blur filter on the moving layer).
7. Avoid "report UI" look: when product UI is shown, show ONE component, big, physical (shadow, depth), never a
   screen of small widgets.

## Seam contracts
Unchanged EXCEPT A→B (see the A and B messages). Every other seam exactly as in FILM_BRIEF.md.

## Deliverables
Re-render to render.mp4 (cut 2 kept as render-cut2.mp4). lint 0; check 0/0 (declare layering); freezedetect clean
(no hold >1.2 s except G's designed final settle ≤1.0 s); strip-start/end.png re-made; NOTES.md "Cut 3" section.
Review in motion (10 fps strips + full-res beat stills) every round, ≥2 rounds. One render at a time on the box.
Final reply ≤8 lines.
