<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/film/B/NOTES.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# film-b: segment B (s03, shots 7-11, kf03 + kf04)

Global 19.6667-30.9000 s (frames 590-926), local duration 11.2333 s, 337 frames, 30 fps. Composition id `film-b`.
Build: `python3 src/build.py` (src/index.tpl, which inlines the real logo and engine SVGs; the logo's G ring and arrow are
separate paths, split the same way as wow/t5-close). The CSS goes to comp/assets/film-b.css and the script to
comp/assets/film-b.js; the timeline is registered inline. This keeps index.html under lint's 300-line limit.

## Beats (local / global)
- 0.00-0.44 / 19.67-20.11 (shot 7): the A->B contract state (empty orange slot 640x120 + "5", centred). The push
  continues: scale 1 -> 1.048 over 1.2 s, ds/dt = 0.08/s at frame 0.
- 0.36-0.66: the numeral leaves left with a blur. The fill and caret fade as the outline starts to move.
- 0.44-1.06 / 20.11-20.73 ("Ack-me" 0.57): the outline stays a clean rounded rect while it rounds into a circle
  (w, h -> 2R, radius -> R). It opens a 90 degree gap at the right, thickens from 4 px to the ring weight and slides
  onto the G centre. At 1.00-1.06 it hands off to the real G ring path.
- 0.88-1.22: the real arrow path swings in and locks (expo.out). 0.96-1.38: E O f l u x unroll. Logo held 1.3-1.72.
- 1.72-2.34 / 21.39-22.01: the logo shrinks and docks top-left as the app's sidebar logo, turning navy. The sidebar,
  nav and breadcrumb (Overview > Visibility) appear around it.
- 2.30-3.67 / 21.97-23.34 (shot 8, "tracks" 2.45): Acme CRM's visibility card rises in (white, 1.5x). The number counts
  0 -> 41% by "recommends" (3.77). "Rank #2" appears at 3.40. "Example data" tag.
- 4.28-4.92 / 23.95-24.59: the product world slides away left. Your card shrinks into kf03's navy brand card (the
  carrier) as the report hero, date line and OVERVIEW pill build around it.
- 4.77 / 5.89 / 6.77 (shot 9, words 4.89 / 6.01 / 6.89 = global 24.56 / 25.68 / 26.56): each engine row (real icon +
  name) lands on its word. Its line draws into the brand card and its flow pulse settles at the kf03 position.
  Footer "1,284 answers read" at 7.45. The frame at ~7.7 equals kf03.
- 7.78-8.77 / 27.45-28.44 (shot 10, "Every day" 8.01): the flows clear and the engine rows dim. Your orange daily line
  draws over 7 days into the brand card's edge (today = 41%), with the date labels "1 Oct" ... "7 Oct" ticking in
  under the line head.
- 8.86-9.16 / 28.53-28.83: the report leaves left (power4.in, -520 px, blur 16). The table arrives on the same leftward
  travel (+520 px, blur 16 -> 0, expo.out 0.6 s). The same three engine icon objects fly from their kf03 rows into
  kf04's column headers (power3.inOut 0.74 s, 56 -> 60 px).
- 9.22-10.13 (shot 11, "competitors" 9.29): the title, column labels and 4 rows build, and the bars fill. At 9.90-10.33
  ("you" 10.01) the Acme CRM row tints orange and the YOU chip lands. 10.20-10.71 ("pick" 10.33): competitor ticks land
  one by one. The frame at ~10.7 equals kf04.
- 10.933-11.233 / 30.60-30.90: B->C exit.

## Seam states
- A->B (frame 0): slot 640x120, radius 20, 4 px #00AA90 border, #EBF8F6 fill, centred at (960,540). Navy caret
  4x60 at x=668. Numeral 5 (Space Grotesk 700, 64 px, #028C77) with the glyph at x 568-601. Measured against
  film/A's last frame: same within 1 px. The push continues at +8%/s for 1.2 s, so the morph starts mid-push.
  The dots grid is static (unscaled), as in A.
- B->C (last 0.30 s): #s11 (the table, its tag and the header icons) goes x 0 -> -640, power4.in, blur 0 -> 16.
  Opacity stays 1 until the last two frames (0.6, then 0.3 on the final frame). See strip-end.png.

## Check
lint 0 errors / 0 warnings. check ok=true; layout 0 errors / 0 warnings (4 info: off-canvas text during the
in-segment leftward cut). Deliberate layering is declared (morph, logo, flows into the brand card, flying icons,
camera crop, sidebar slide).

## Iterations
1. Base build. The check flagged the svg id "flow" as a connector (renamed it "streams") and the file length (CSS and
   JS moved to assets).
2. Morph: the first versions (point lerp, then a polar lerp) made lemon and blob shapes. Replaced by a rounded-rect ->
   circle morph with an opening gap, which reads as the slot curling into the G. The fill now fades faster.
3. Fixed the day labels and a stray round-cap dot of the daily line that showed before shot 10. The chart is hidden
   until 7.86. Moved "Rank #2" off the brand name. Shortened the white -> navy card swap (0.3 s). Matched the caret
   and numeral to A's measured frame.

## Weaknesses
- The arrow swings in semi-transparent over the ring for ~4 frames (0.88-1.0), the same move as t5-close.
- The white -> navy colour swap of the carrier card passes through a mid-blue for ~0.15 s.
- Shot 8 holds still ~0.6 s (3.7-4.28) after "Rank #2". The hero card shows empty for ~0.3 s before ChatGPT lands.
- The sidebar nav labels are generic (Overview / Prompts / Engines / Sources / Pitch reports) and seen only briefly.

Review strips: strip-start.png, strip-end.png (30 fps, first/last 0.6 s), strip-morph.png and review/*.png.

## Cut 2 (client: "24-30 s too simple, not elements from our report")
Local 0-4.28 is unchanged (A->B start, the G morph, the dock, the shot-8 visibility card). Local 4.28-9.36 (global
23.95-29.03) is replaced: the kf03 report hero and the daily line chart are gone, and a 3D "engine stage" takes their
place. The cut-1 render is kept as render-cut1.mp4 and its source as src/index-cut1.tpl. The edit script is
src/cut2.py + src/cut2-tl.js.
- 4.30: the "A" monogram flies out of the visibility card (carrier) and becomes the big orange Acme CRM mark at
  centre-left. The product world slides away left.
- 4.75 / 5.87 / 6.75 (ChatGPT 4.89, Gemini 6.01, Perplexity 6.89): each real engine logo disc comes forward out of
  depth (z -900, rotateY -70 -> 0, expo.out). The camera (CSS 3D rig) travels to it. Three answer beams draw from
  the disc into the mark, and answer packets stream along them. Each arrival hits the mark with a pulse and an orange
  ripple. Your share for that engine lands as a 190 px kinetic number with an engine tag ticker:
  41.8% -> 36.4% -> 47.9% (the same data as the kf04 table).
- 7.42 ("Every day" 8.01): the camera pulls back to the whole system, then keeps a slow push. All engines stream at
  once. A day ticker rolls "Every day · 01 Oct" -> "07 Oct" while the number ticks day by day 34 -> 41%.
- 8.68-9.36 ("against" 8.97): the number clears. Four rival chips (Northwind, Contoso, Fabrikam, Tailspin) slot in
  around your mark from the camera (scale 1.5 + blur -> rest), staggered.
- 9.36-10.0 ("competitors" 9.29): the cast flies into kf04. The engine logos go to the column headers, your mark to the
  Acme row monogram, and Northwind/Contoso/Fabrikam to their rows. Tailspin drops away right, not picked. The table
  builds under the cast. The rest is unchanged: the row tints on "you", ticks land on "pick", and the B->C exit
  (cut-the-curve LEFT) is the same.
- Freeze check (`freezedetect=n=0.002:d=1.2`): no freezes at all. Seams are unchanged (strip-start/strip-end re-made).
  New strip: strip-cut2.png.
- Weaknesses: the stage's elements sit at about 1.08x camera max, so the engine discs are mid-size rather than huge.
  The rival chips are on screen for only ~0.5 s before they fly into the table.

## Cut 3 (coordinator round 2: "still the report's layout; push the design much further")
Cut-2 render and source kept as render-cut2.mp4 / src/index-cut2.tpl. Cut-3 pieces: src/c3.css, c3.html, c3-build.js,
c3-tl.js, applied by src/c3apply.py, plus small follow-up edits in index.tpl. Local 0-4.28 and the kf04 table + B->C
exit are unchanged; the shot-8 card number bug (class clash) is fixed.
- 4.30: the monogram flies out of the card and becomes your mark at top-left. It holds the HUD: a 240 px rolling-digit
  odometer (tenths roll continuously and carry) and "of AI answers name Acme CRM".
- 4.75 / 5.87 / 6.75: each engine gets a full-frame moment on its name. Its wash colour comes up (ChatGPT green,
  Gemini blue-violet, Perplexity teal). The real logo disc (460 px, 3D tilt rotateY -48 -> 14) comes out of depth,
  blurred on the way in. The camera pushes 0.3x -> 1.34x and then flies past it (scale 3.4, out to the right, blur 24)
  as the next engine arrives. Halo rings and blurred ghost cards fill the depth. Answer cards (engine icon, brand, rank;
  one in three "Acme CRM" in orange) pour out in depth (perspective rotateY, near-camera blur) and arc LEFT over the top
  into your mark. Each Acme arrival pulses the mark with an orange ripple, and the odometer rolls 41.8 -> 36.4 -> 47.9.
- 7.42 ("Every day" 8.01): strong pull-back (Z backward). Perplexity shrinks to the bottom right. ChatGPT and Gemini
  come back from in front of the camera (scale 2.6, blurred) to the left and top right. The mark and number move to
  centre. All three engines pour cards in, the day ticker rolls 01 -> 07 Oct and the odometer rolls day by day to
  41.0%. The camera keeps a slow push (1.0 -> 1.06).
- 8.72 ("against"): the four rivals land with weight (scale 1.8 -> 1, blur, power4.out), and the mark recoils on each
  landing. They are readable for ~0.8-1.0 s.
- 9.8-10.3: the cast flies into kf04. The engine logos go to the column headers, the mark goes to the Acme row
  monogram, the rivals go to their rows, and Tailspin drops away. The row tints and YOU chip land at 10.24-10.3, ticks
  on "pick" 10.3.
- Fixed bugs: labels no longer overlap on the fly-past (the old name leaves first, the new one lands at +0.32 s). There
  is no near-empty frame (the logo is large from its first frames; the number appears with the first roll). Camera
  moves are 0.3 -> 1.34x per engine.
- freezedetect (n=0.002, d=1.2): none.
- Weaknesses: the number shows 00.0% for ~0.2 s before the first roll. The cards are busy around the mark at
  arrivals. The rival hold (9.0-9.8) is the calmest stretch (stage push only).
- Cut 3 polish (round 3):
  - The number never reads 00.0. It starts at 31.6% and fades in at 5.30 as it rolls to 41.8%.
  - Cards are thinned to at most 3 in flight (0.25 s apart, 0.6 s each): 4 + 3 + 3 cards in the engine moments and 4 in
    the pull-back.
  - Every card now arcs over the top (control point 20% along the path, 200-320 px above), so the paths stay clear
    of the big number and no chip covers another's text.

## Cut 3b (REVISION_2: new A->B seam, live feed, day time-lapse, big rivals)
The previous version is kept as render-cut3a.mp4 and src/index-cut3a.tpl. Edit scripts: src/c4apply.py, c4feed.js, c4tl7.js.

### A->B start-frame geometry (frame 0 = global frame 590)
- Floor #EEF1F5 (tokens `--canvas` overridden), with the static tokens dot grid.
- Slot: rounded rect 1240x200 centred at (1010,540) (x 390-1630, y 440-640), radius 40, 6 px #00AA90 border drawn as an
  SVG stroke on the centreline (1234x194, r 37), #EBF8F6 fill.
- Caret: navy #3E0863, 6x100 px, radius 3, at x 430-436 (40 px inside the slot's left edge), y 490-590.
- Text: "Your brand?" in Space Grotesk 600 64 px #028C77, box left at x=460, 80 px line box centred on y=540.
- Numeral: "5" in Space Grotesk 700 120 px #028C77; the glyph's right edge is measured at x=342 (box 5-347, 150 px
  line box centred on y=540).
- Push: scale about (1010,540), s(t) = 1 + 0.048(1-(1-t/1.2)^2), so ds/dt = 0.08/s at frame 0. It continues to 1.2 s;
  the morph starts at 0.25 s.
- Measured on frame 0: border left x 390-395, caret x 430-435, numeral glyph x 280-342.

### Beats (local)
- 0.16-0.36: the numeral and "Your brand?" leave left with a blur. 0.25-0.55: the slot outline rounds into the G ring
  (rect -> circle, the gap opens, the stroke thickens 6 -> 49 px). The arrow locks at 0.40-0.70 and the letters unroll
  from 0.44. The logo is 1000 px wide (52%) and complete on "Ack-me" (0.57). It slowly pushes 1 -> 1.04 until 1.57.
- 1.57-2.17: the logo docks into the header of a big live answer feed card (1600x880, layered shadow). The card rises
  in with a 3D tilt.
- 1.6-4.45 ("It tracks which brands AI recommends"): real-looking answers from ChatGPT, Gemini and Perplexity (real
  icons, 44 px text) scroll through a navy read band. Each brand is boxed as it is read (navy; Acme CRM in orange), and
  the "N brands found" pill counts up from 2 to 14. It pulses on "brands".
- 4.40: the just-read Acme CRM box lifts out as the orange mark. 4.45: the feed flies past the camera into the first
  engine.
- 4.75-7.42: the approved engine moments (unchanged).
- 7.4-8.86 ("Every day"): pull-back time-lapse. "Every day · Day N" with the day number in 96 px rolls Day 1 -> 30 over
  1.35 s, while the odometer rolls the daily share to 41.0% and cards pour in.
- 8.92 ("against"): four rival chips land big (60 px names, 80 px monograms) with weight. They are readable ~0.7-0.9 s.
  9.8: they fly into the kf04 rows (scale 0.9).
- kf04 now has a layered deep shadow. The B->C exit is unchanged.
- Freezedetect: none.
- Weaknesses: the read band is often between lines (boxes land just as a line crosses it). The Acme box -> mark lift
  is small and quick. A's cut 3 was not available to compare against, so the caret height (100 px) and text x (460)
  are my reading of the contract.

## Final (REVISION_3: zoom out 0.92, title-safe, caption zone)
The cut 3 version is kept as render-cut3.mp4 and src/index-cut3.tpl.
- All foreground content is wrapped in #zoom, which is scaled 0.92 about (960,540). The floor colour and dot grid stay
  full-bleed. The scale is applied after every carrier measurement, so the flights still land exactly. The seam
  geometry maps through x' = 960+0.92(x-960), y' = 540+0.92(y-540) on both sides. Frame 0 now shows the slot at
  1140.8x184 centred at (1019.2,540); the B->C exit is -640 px local (-589 px on screen).
- Edge fixes:
  - kf04 is now a whole card inside the frame (local 40,40 1840x920; on screen ~114-1806 x, 80-926 y), with 160 px
    rows, columns at 660/1040/1420, and the Example data tag inside the card.
  - Answer-card arcs are lowered (apex ~y 150+), clear of the top edge.
  - The feed card is shorter (800 px), clear of the caption zone.
  - The engine name sits higher, so it stays above y 930 at full push.
- Exempt by design: the engines flying past or returning past the lens, and the blurred ghost cards in depth.
