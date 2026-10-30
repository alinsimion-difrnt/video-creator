<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/film/FILM_BRIEF.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# Acme v2 — final film build brief (shared by all segment builders)

$S = /tmp/claude-0/-home-user-explainer-video-creator/d8546e8e-2ef6-5546-bc1d-4c1a0ec27017/scratchpad
Work only in the scratchpad. Never touch the git repo. No paid APIs (never `--describe`, never `capture`).

The 105 s film is built as 7 segments (A–G), each its own HyperFrames composition rendered to its own MP4.
They are concatenated frame-exactly and the master audio is laid on top. So each segment must END and START in
exactly the state its seam contract says (below): the viewer must not see the join.

## Read first
1. $S/wow/BRIEF.md — brand, real logo assets, composition contract, seek-safe GSAP rules, motion doctrine,
   commands. Everything there applies.
2. $S/research/hf-skills/_repo-dev-skills/motion-doctrine/SKILL.md — seam law, the current (LEFT), carriers,
   no idle wobble, stillness before climax.
3. The approved storyboard $S/sb2/storyboard-v2.html (32 shots, decisions at the bottom) and the APPROVED KEY FRAMES
   $S/keyframes/png/kf01…kf10.png with their source in $S/keyframes/src/ (tokens.css, kfNN.html, build.py which
   inlines real SVG logos). The key frames are the settled frames your animation must move INTO — reuse their
   HTML/CSS directly (same tokens, same components, same fictional data). Notes: $S/keyframes/NOTES.md.
4. Your segment's word list: $S/film/segments/words-<SEG>.txt (local times = seconds from your segment start).
   Your segment audio for preview renders: $S/film/segments/audio-<SEG>.m4a (include it in your comp like the wow
   tests do so your review render has sound; the final film uses the master audio).

## Fixed decisions (client)
- Fictional data only: your brand "Acme CRM" (the one orange focal brand); competitors Northwind, Contoso, Fabrikam,
  Tailspin; personas Greg (CEO), Nadia (marketer), Liam (student); restaurant "Patty Lane"; bank "Larkfield Bank";
  agency prospect "Litware Travel" (others: Wingtip Toys, Woodgrove Dental). "Example data" tag whenever data shows.
  No real company as a tracked brand. Real logos ONLY for AI engines and sources.
- Rename the Facebook group to "Toddler Parents Club" (not "Parents in Business").
- Product UI only where the line promises product (Competitor breakdown, Pitch reports, gap-sites card, answers);
  idea lines are expressive. Never a full dashboard; one component, zoomed.
- One orange accent moment per frame. power3/expo eases; no bounce/back/elastic; no idle drift/breathing; reveals
  land on their spoken word (start 0.05–0.15 s before the stressed word).

## Frame clock
30 fps. Segment boundaries in frames (global): A 0–590, B 590–927, C 927–1379, D 1379–1643, E 1643–2585,
F 2585–2906, G 2906–3154. Your composition `data-duration` = your local duration from the words file (exact,
4 decimals). Segment id = lowercase letter (`film-a` … `film-g`).

## Seam contracts (global frame coordinates, 1920x1080; "cut" = first frame of the next segment)
- **A→B (cut 19.667 s): match cut on the empty slot.** A ends with the empty orange slot #5 isolated and centred:
  a rounded rect 640x120 (radius 20, 4px #00AA90 border, #EBF8F6 fill, a navy caret at its left inside) centred at
  (960,540); the numeral "5" in #028C77 Space Grotesk 64px sits 40px left of it; everything else faded out. A
  pushes in on it so that at the cut it is exactly that size and still growing at ~8%/s (scale velocity). B's first
  frame shows the identical slot + numeral, continues the same push for ≥0.25 s, then morphs (the outline curls into
  the Acme "G" on "Ack-me").
- **B→C (cut 30.900 s): cut-the-curve LEFT.** B's final content (the competitor table, kf04) accelerates left in the
  last 0.30 s (power4.in, x 0→−640px, blur 0→16px, opacity stays 1 until the last 2 frames). C's first content
  enters already moving left: starts at x +640px offset, blur 16px, decelerates power4.out over 0.45 s to rest.
- **C→D (cut 45.967 s): match cut on the prompt bar.** C ends on the kf01-style prompt bar (same component as kf01:
  1100x112, centred at (960,540), text "Which CRM should a small agency use?", orange send button), everything else
  gone, still settling the last 2% of a scale-in (scale 0.98→1.0 ending exactly at the cut). D's first frame is the
  identical bar at scale 1.0.
- **D→E (cut 54.767 s): push into the Perplexity answer.** D ends by pushing the camera into the Perplexity phone
  until its answer fills the frame and resolves into a full card: at the cut the screen shows the Perplexity answer
  card (white card, Perplexity header with real icon, question bubble "Which CRM should a small agency use?",
  answer list 1 Acme CRM (orange chip) / 2 Northwind / 3 Contoso) with the card rect x 410–1510, y 120–960, and the
  camera still pushing (scale velocity ~+6%/s). E's first frame is that identical card and continues the push
  ≥0.25 s.
- **E→F (cut 86.167 s): cut-the-curve LEFT** (same parameters as B→C). E's final content is the kf08 payoff.
- **F→G (cut 96.867 s): zoom-through forward.** F's last 0.24 s: everything accelerates toward camera (power3.in,
  scale 1→1.3, blur 0→16px, opacity 1→0.15 linear). G's first frame: the orbit cast at scale 0.75, blur 16px,
  opacity 0.15, growing (expo.out to scale 1 / blur 0 / opacity 1 over 0.5 s) while the orbit is already spinning.
  The "Signed" chip from F is one of the orbiting cast in G.

## Per-segment deliverables ($S/film/<SEG>/)
- comp/index.html (+ assets/, audio), src/ (templates/scripts), render.mp4 (with segment audio, exact duration),
  check.json (lint 0/0; check ok, layout 0 errors / 0 warnings — declare deliberate layering), NOTES.md (beats with
  local+global times, what each shot does, seam states, weaknesses), strips: strip-start.png and strip-end.png
  (30 fps, first and last 0.6 s — these prove the seam contract), plus your own review strips.
- Review in motion every round (10–30 fps strips across every move; full-res stills of settled beats; 480px
  legibility). At least 3 render rounds. Bar: premium SaaS launch quality, matching the approved key frames.
- Final message ≤ 12 lines: beats, seam states achieved, check result, weaknesses.
