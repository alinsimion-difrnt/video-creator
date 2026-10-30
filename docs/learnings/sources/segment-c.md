<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/film/C/NOTES.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# Segment C (film-c): s04, shots 12-16, key frame kf05

Global 30.900-45.967 s (frames 927-1379), local duration 15.0667 s, 452 frames at 30 fps.
Source: `src/index.src.html` (single file); `src/build.sh` splits it into `comp/index.html` + `comp/assets/film-c.css` +
`comp/assets/film-c.js` (the HTML stays under the lint size limit; the timeline registers inline on `window.__timelines["film-c"]`).
`render.mp4` = `render-raw.mp4` trimmed to exactly 452 frames / 15.0667 s (the renderer emits one extra frame at t = duration).

## Beats (local s / global s)
| local | global | word | what lands |
|---|---|---|---|
| 0.00-0.45 | 30.90 | Here's | B->C entry: table + "Example data" arrive already moving left (x +640, blur 16 -> 0, power4.out 0.45) |
| 0.36-1.20 | 31.26 | how it works | visibility bars fill in the 4 rows (sequenced UI life) |
| 1.48-2.03 | 32.38 | First, | step numeral "1" rises through its mask (expo.out) + "STEP" |
| 2.22-3.47 | 33.12 | your questions | "Your questions" rises; camera pushes 1.30x -> 1.38x anchored on Add prompt |
| 3.56-4.16 | 34.46 | You add | Add prompt pressed; dialog opens out of the button (expo.out); table + step dim/blur behind |
| 4.02-5.27 | 34.92 | the ones your customers... | "Simplest CRM for a 3-person team?" types in; counter flips to "1 prompt" |
| 5.62-6.30 | 36.52 | ask | Add pressed; dialog drops out; the typed line flies (white pill) into row 1 while rows below make room; row lands with a navy bar + wash, count 4 -> 5 |
| 6.42-7.17 | 37.32 | and we suggest | camera scrolls (1.38x -> 1.20x, pan up); "Suggested for you" panel with 3 prompts + Track buttons slides in from the right |
| 7.36-7.66 | 38.26 | few more | Track pressed x3 (-> "Tracking") |
| 7.56-8.23 | 38.46 | more. | rows make room; the three prompts fly into rows 1-3 (Queued); count -> 8 |
| 8.28-8.60 | 39.18 | Then | row "Which CRM should a small agency use?" lifts (shadow, 1.02x) and becomes a question bubble |
| 8.52-9.41 | 39.42 | we ask them | table + step exit LEFT (power3.in, blur 10); bubble rises to centre at 2.0x (carrier) |
| 9.46-10.10 | 40.36 | as different people | bubble fans into three copies that land on the three kf05 column bubbles; columns open; Greg/Nadia/Liam land 9.70-9.84, role chips 10.04-10.20 |
| 10.62-10.95 | 41.52 | (pause) | rank numerals + skeleton bars appear (answers pending) |
| 11.08-11.82 | 41.98 | because a CEO | Nadia and Liam dim; Greg's list lands 11.40 (Acme CRM #1 orange), verdict #1 at 11.70 |
| 11.80-12.50 | 42.70 | and | Nadia in focus; list lands 11.84 (Acme #3), verdict #3 at 12.10 |
| 12.20-13.20 | 43.10 | a student | Liam in focus; list lands 12.28, "Not mentioned" 12.58, verdict "–" 12.80 |
| 13.00-13.86 | 43.90 | don't get the same answer | all three full; verdict row washes in L->R at 13.44 (= kf05, fixed) |
| 13.92-14.52 | 44.82 | (tail) | content clears; three column plates fold into one bar shape (power3.inOut) |
| 14.52-15.0667 | 45.42 | -> cut | C->D: prompt bar, scale 0.90 -> 1.00 power3.out ending exactly at the cut; text and send button fade in |

## Seam states
- **Start (B->C):** frame 0 = content at x +640 px, blur 16 px, opacity 1, decelerating power4.out to rest at 0.45 s
  (`strip-start.png`, frames 0-17).
- **End (C->D):** only the prompt bar on the dotted canvas. Bar 1100x112, centred at (960,540), radius 56, white,
  1 px #E5E7EB hairline, kf01 3-layer shadow; plus circle 68 px at left 22; text "Which CRM should a small agency use?"
  Inter 400 40 px #111827 at x 116 (bar-local), vertically centred; orange #00AA90 send circle 78 px (right 16, top 16) with a
  white up arrow. No caret. Scale 0.98 is passed at ~14.80 s; the last frame (local 15.033) is at 0.9999, so D's
  frame 0 at 1.0 is continuous (`strip-end.png`, last 18 frames). D must match this component exactly.

## kf05 fixes
- Acme CRM is orange at most once per column (Greg #1 and Nadia #3; Liam has none). The footer label "Acme CRM" is
  navy-70 and all verdicts (#1, #3, –) are navy (#3E0863). The verdict row washes in on "same answer".
- Lists are 46 px chips (≈ 11.5 px at 480 px wide, readable; see `review/r5-480.png`); verdicts 92 px.

## Rounds
1. First build: table at 1.0x, too small and half empty; Example data tag sat on the Add button; flyers crossed rows bare.
2. Table recut to a 1.30x crop (Mentions column dropped, Visibility kept), camera keyframes K0/K1/K2, flyers become white pills
   with a lift shadow, carrier bubble 2.0x.
3. Camera scroll moved to the panel entrance so the filing flight happens on a still table; tag moved bottom-left for
   the table shots (kf05 position for the columns); caret gap fixed; CSS/JS split for lint.

## Checks
lint 0/0; `check --at-transitions`: ok true, layout 0 errors / 0 warnings, contrast ok. Deliberate layering is declared
(dialog and Suggested panel over the table, inserted rows, flyers, carrier copies, the table's camera crop, step masks).

## Weaknesses
- The bar is the contract size (1100x112), not kf01's 1540x184; component proportions are adapted (40 px text).
- Orange is on twice in shots 12-14 only when the dialog's Add button sits over the blurred header Add button.
- 10.3-11.1 s rests on skeleton bars only (pending answers) — calm, but it is the quietest stretch.
- The three-plate fold (14.06-14.52) reads as blank white cards for ~0.4 s before the bar text arrives.
- Flyers still pass over existing rows for a few frames (white pills keep them legible).

## Cut 3 (REVISION_2 + coordinator notes)
Source: `src/index.src.html` (the cut-2 source is kept as `src/index.cut2.html`, its notes as `NOTES-cut2.md` and its render as `render-cut2.mp4`).
Floor #EEF1F5 with layered contact shadows. Orange appears only on the Acme chips.

**Every step is one physical object**, built from the kf01 prompt bar pill (1100x112 base, shown at 1.21–1.8x, text 48–72 px):
- 0.00–0.45: B→C entry (x +640, blur 16 → 0, power4.out). It brings in a stack of four question pills and a 900 px numeral "1", which is the back plane at 3x the cut-2 size.
- From 0.36: the visibility bars fill. 0.45–3.5: the stack pushes in slowly (1.21 → 1.26x) with numeral parallax.
- 1.48: on "First", the numeral lands solid. 2.22: "Your questions" rises.
- 3.58: on "You add", a composer bar inflates out of row 1 toward the camera (1.7x), with depth of field on the stack.
- 3.92–5.22: it types and grows with each keystroke while the camera keeps pushing (1.7 → 1.8x). This replaces the cut-2 dialog hold at 35.0–36.6 s.
- 5.62: on "ask", the navy send presses. The bar deflates into row 1 and the rows below drop with weight; the new row lands with a squash.
- 6.42–6.9: on "suggest", three "Suggested for you" chips puff in from depth (blur 10 → 0, scale 1.45 → 1.2).
- 7.30: Track is pressed three times. 7.64–8.24: the chips fall into slots 1–3 (power3.in, landing squash) and the rows drop three slots.
- 8.26: the row "Which CRM should a small agency use?" lifts and becomes the prompt bar (plus icon and navy send fade in).
- 8.52–9.32: the bar rises to the top at 1.3x. The stack leaves LEFT (power3.in, blur 14) and stays big until the columns land.
- 9.12: on "as different people", the Greg, Nadia and Liam columns fan out of the bar with their lists already filling (9.28–9.75), so no empty cards.
- Focus pops on the spoken word:
  - "CEO", 11.36: Greg gets the orange Acme chip and #1.
  - 11.86: Nadia gets #3.
  - "student", 12.26: Liam gets "Not mentioned" and "–".
- 12.98: all three level. 13.40: the verdict row washes in, with a slow camera push throughout.
- C→D, 13.92–15.0667: the bar comes down to centre (scale 0.94). From 14.12 the columns fall into it (power3.in, blur 12) and stay big until 14.6. The bar then scales 0.94 → 1.0 (power3.out) and ends exactly at the cut; 0.98 is passed at about 14.65.

**Seams:**
- Start: identical to the cut-2 start.
- End: the kf01 bar at 1100x112, centred at (960,540), with a navy #3E0863 send button. I compared C's last frame with D's current frame 0: floor #EEF1F5 on both, PSNR 50.5 dB.

**Checks:** lint 0/0; check ok, layout 0/0, contrast ok; freezedetect (d = 1.2 s) finds no freezes; 452 frames.

**Weaknesses:**
- 0–1.5 s: the numeral is a 16% ghost until "First".
- During the end fold, the bar passes over the column headers for about 0.3 s.
- 14.65–15.07 s: the bar is alone on the floor (0.4 s), as the seam requires.
- Below the four-row stack in shot 12, about 25% of the frame is floor.

## Final (REVISION_3: zoom out 0.92)
- All foreground sits in `#stage`, scaled 0.92 about (960,540). The floor and dot grid stay full-bleed. Seam geometry maps through the scale automatically: the end bar is 1012x103 centred at (960,540).
- Title-safe fixes:
  - The stack moved to x 500, so the pills' right edge sits about 115 px from the frame edge.
  - The lifted row no longer scales up (it lifts 8 px instead), so it stays inside 96 px.
  - "Example data" moved to the top-right.
  - The question bar moved to y 112 and the persona cards to y 200–940 (height 740; rows at 188, 294, 400; slot at 506). The column push is now 1.05 about (960,500), so the verdicts stay above y 930, clear of the caption band.
  - The 900 px numeral is a background plane and still bleeds off the left edge on purpose.
- Checks: lint 0/0; check ok, layout 0/0, contrast ok; freezedetect clean; 452 frames. Cut 3 is kept as render-cut3.mp4 and src/index.cut3.html.
