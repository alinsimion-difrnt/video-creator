<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/film/A/NOTES.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# Segment A (film-a): global 0.000-19.667 s, frames 0-590, local = global

Source: src/a.tpl + src/build.py (inlines the real OpenAI mark) -> comp/index.html. One paused timeline; one `apply()`
writer (onUpdate) derives typing, caret blink, bar width and the card camera purely from tl.time() (seek-safe).
Check: lint 0/0; check ok, layout 0/0, contrast 0/0 (check.json). Render: 590 frames, with audio-A.

## Beats (local = global seconds)
- 0.03-1.03 shot 1: a white circle pops (expo.out) and unfurls into the kf01 prompt bar (expo.inOut 0.75 s); send 0.72, plus 0.85.
- 1.00 navy caret in the empty bar (bar camera at 0.84). 1.12-3.48 "People ask AI about everything now": the bar's text
  rapid-fires through 7 everyday questions as hard in-place swaps, accelerating (0.38 -> 0.23 s): "Is this mole normal?"
  1.12, "Cheap flights to Rome?" 1.50, "How do I fix a leaky tap?" 1.85, "Best laptop for students?" 2.16, "Gift ideas
  for dad?" 2.44, "Is it safe to eat raw eggs?" 2.70, "Why is my sourdough flat?" 2.93 (held through "now").
  3.48 the bar clears to a solid caret (0.42 s beat).
- 3.90 "Where to buy": typing starts; push-in step 0.84->0.89. "running shoes" is typed 4.37-4.78
  (spoken 4.44-4.84); "Best running shoes for flat feet?" complete at 5.29.
- 5.88 shot 2, "eat" (5.96): hard in-place swap to "Where to eat tonight near me?" + push step 0.89->0.94 (power3.out).
- 7.22 shot 3, "CRM" (7.32): hard swap to "Which CRM should a small agency use?" + push step to 0.975, then a slow
  push to exactly 1.0 (= kf01) arriving on the send press.
- 9.16 "use" (9.24): send button presses (scale .86, darker orange) and releases.
- 9.30 shot 4: the question lifts out of the bar (the bar drops away, power3.in) and becomes a large white chat
  bubble, centred, rising 1.05 s power3.out ("And when someone asks").
- 11.40-12.10 "ChatGPT" (11.58): the answer card blooms around the bubble (expo.out), the real ChatGPT mark lands in
  the header (11.46), the rule draws, the bubble docks top-right at 34 px type and turns ChatGPT grey. It is the same
  element all the way (no handoff jump). Thinking dot 11.75-12.2, then the answer streams as skeleton texture
  (steps ease) 12.14-13.31 ("for the best CRM").
- 14.18 "Example data" tag. Rows land one per beat (power3.out 0.45 + streamed skeleton): Northwind 14.20 ("They"),
  Contoso 14.60 ("short"), Fabrikam 14.86 ("list"), Tailspin 15.76 ("Four").
- 16.42 "maybe": a grey numeral 5 arrives. 16.68 "five": the empty slot opens in orange (width expo.out), numeral turns
  #028C77, caret blinks from 17.2. 17.5 = kf02 composition with rows still at full ink.
- 17.85 shot 6 "Is yours one of them?": rows/header/bubble dim (rows .4), slot halo goes and fill becomes #EBF8F6;
  the camera pushes on the slot (scale 1 -> 4/3 Hermite, pan power3.inOut done at 19.40). 18.40-19.05 everything
  but slot + numeral fades out (card surface last). Caret solid from 18.90.

## Seam A->B state (frame 590 = B's first frame; my last frame 589 is 1/30 s earlier)
- Card camera: s(t) composite; at t=19.6667 the slot is exactly 640x120 at centre (960,540), radius 20, 4 px #00AA90
  border, #EBF8F6 fill, no halo/shadow. Scale velocity at the cut: +8.0 %/s relative (Hermite end slope), pan at rest
  since 19.40 (pure growth around the slot centre).
- Numeral "5": Space Grotesk 700, 64 px, #028C77, right edge of the glyph at x=600 (40 px left of the slot), centred
  vertically on y=540 (box 90 px card = 120 px line-height at the cut).
- Caret: navy #3E0863, 4 x 60 px, radius 2, its left edge 28 px inside the slot's outer left edge (x=668), vertically
  centred; solid (not blinking) for the last 0.77 s.
- Background: canvas #F5F7FA + the tokens.css #dots grid (static, not scaled). Nothing else visible from 19.06.
- Measured on frame 589: border x 642-1277 / y 480-599 (antialiased edges excluded), numeral x 569-600, caret x 669-671 /
  y 511-569. strip-start.png / strip-end.png = first / last 18 frames (0.6 s at 30 fps).

## Rounds
1. Base build. Bar overlapped the card during the lift; empty white card for 1.3 s; push steps too timid; 1.4 s dead
   hold on Q3.
2. Bigger push steps (0.84/0.89/0.94/1.0), Q3 hold carries a slow push into the send; faster opening; card bloom moved to "ChatGPT".
3. Lift redesigned: question becomes a large centred white bubble, then docks into the card on "ChatGPT".
5. (Coordinator fix) The hook: placeholder replaced by 7 rapid hard-swapped everyday questions on "about everything";
   clears at 3.48, then the running-shoes typing as before. Seam end unchanged (re-measured).
4. Removed the bubble handoff (3 px jump at 12.1 s): the flying bubble now lives in the card. Numeral nudged 3 px to
   meet the 40 px gap. Fixed z-order (bar was covering the question for 0.24 s).

## Weaknesses
- 10.4-11.4 is a held centred bubble (narration "And when someone asks"): a deliberate pause, but quiet.
- Answer prose is skeleton texture by design; it reads as streaming but is low-contrast at 480 px.
- Push in shot 6 is a modest 1.33x (fixed by kf02 size + the 640 px contract); the drama comes from the clear-out.
- The fastest swaps (0.23 s) are skimmable, not fully readable, by design (the "everything" texture).

# Cut 2 (client: opening too slow, 8-20 s "nothing happens", no static holds)
Cut-1 render kept as render-cut1.mp4, cut-1 source as src/a-cut1.tpl. Seam A->B unchanged (re-measured on the last
frame: slot border y 480-599, numeral right edge x 600-601, caret x 669-671; identical to cut 1).
- 0.00-3.85 WALL OF CHATS: 24 chat windows in CSS 3D (4 depth layers; real ChatGPT/Gemini/Perplexity marks), each
  typing its own buyer question at 30-42 chars/s, clearing and retyping (seeded schedules, ~30 questions, fictional
  names only). Camera always moving: dolly z -3000 -> -2200 plus a decelerating track (220/60 px -> 0).
- 3.85-4.80 DIVE on "Where to buy running shoes": Hermite z-move (speed matched to the dolly, ~3000 px/s peak), near
  windows fly out past the lens/edges, far ones fade 4.42-4.82; the hero ChatGPT window's frame falls away (4.40)
  and its input becomes the kf01 bar; send turns orange 4.40. "running shoes" typed 4.37-4.78 (unchanged).
- 4.80-9.34 bar push never stops: 0.86->0.89 (landing), 5.88 swap + 0.89->0.945 over 1.34 s, 7.22 flips to "Which
  CRM should" and " a small agency" types on the voice (7.86-8.73), " use?" on "use" (9.11-9.25); push to 1.0 at the
  send press 9.34.
- 9.44 lift into the centred bubble + camera push 1.0->1.26 on it until 11.40.
- 11.40 "ChatGPT": pull back (arrival) as the card blooms; mark lands; bubble docks.
- 11.80 thinking dot; 12.02-13.42 camera pushes in (1.32x) while the first answer sentence streams word by word.
- 13.42-14.14 travel down to row 1 (1.55x close-up). Names fly in from the right (LEFT current) and the camera
  tracks each: Northwind 14.20, Contoso 14.56, Fabrikam 14.84, slow track 15.00-15.55, Tailspin 15.76.
  Screen-fixed "Example data" tag 14.08-18.4 (visible in close-ups).
- 15.95-16.95 pull back to the full list (kf02 framing); "maybe" grey 5 (16.42); "five" orange slot (16.68).
- 17.30 push to the slot starts (Hermite, 8 %/s at the cut); 17.85 rows dim; 18.40-19.05 clear-out (as cut 1).
Freezedetect (n=0.002, d=0.8): no freezes at all (cut 1 had 9.97-11.43, 11.93-14.27, 15.87-17.87).
Weaknesses: wall text on the back layer is texture-size (~12 px); 16.95-17.30 is the stillest moment (0.35 s, caret
blink); close-ups are framed on a mostly white card (names 62 px).

## Cut 2, round 2 (coordinator notes)
- Wall rebuilt: 15 windows in 4 depth planes. Front plane (6 windows plus the hero, sharp): 576 px wide at t=0, question
  text 30 px. Mid (3 windows): 404 px, blur 3 px, 80 %. Far (3 windows): 284 px, blur 7 px, 55 %. Foreground (2 windows,
  blur 9 px) sweep out past the edges in the dive. Darker hairlines (#D9DEE5) and stronger shadows.
- Front windows send in a stagger, one every 0.42 s (plus the hero's 2): about 2.5-3 questions per second. Each send
  is a button press plus an answer shimmer (3 lines stream in steps).
  Camera z -1600 -> -1150 with a truck LEFT (200/50 px -> 0), then the dive.
- The hero is the front-centre ChatGPT window. It sends 2 questions (1.05, 2.48), and at 3.24-3.26 ("now.") the crowd
  dims to 55 % and its send turns orange. The dive lands on it.
- Frame 440 bug: the "Example data" tag moved to the bottom-right of the frame. The question bubble fades out while
  the camera is close in (13.45) and returns with the pull-back (16.05), so it is never cropped.
- build.py strips comment/blank lines and collapses CSS so lint stays 0/0 (file-size warning).

## Cut 2, round 3: the typed text matches the voice
- Hero types "Where to buy running shoes?" word-synced from 3.90 to 5.02.
- 5.56 hard swap to "Where to eat tonight?" (on "Where", 5.64).
- (round 4) Reverted: from 6.96 types "Which CRM should a small agency use?" word-synced (Which 6.96, CRM 7.28, should 7.52, a 7.94, small 8.04-8.30, agency 8.34-8.80, use? 9.12-9.30); bubble matches; consistent with C/D.
  "a small agency" 7.84-8.86, "should use?" 9.00-9.32. The bubble shows the same text.
- Send press at 9.34; everything else unchanged.
- Note: segments C/D still use "Which CRM should a small agency use?" (C->D prompt-bar contract).
- Freezedetect: none. Check: 0/0.

# Cut 3 (REVISION_2 + six/review "Ten improvements")
Cut 2 kept as render-cut2.mp4 / src/a-cut2.tpl / NOTES-cut2.md. Source now src/a.tpl (HTML+CSS) + src/a.js (inlined by build.py).
Floor #EEF1F5 everywhere; orange only for the slot ("your brand"); every send button is navy.
- 0.00-1.12 A question sits near the lens over the wall: "Cheap flights to Lisbon in May?", 80 px, in a pill 1,460 px wide.
  It sends at 0.46 and whips LEFT out of frame (0.70-1.12, power3.in, blur up to 14 px). The 15-window 3D wall continues
  as in cut 2. On "now." (3.24) the front-centre ChatGPT window is singled out.
- 3.85-4.80 The dive, unchanged. The window's input bar becomes the first question pill (frame and plus fade, 4.40-4.90).
- Questions are pills that grow with every keystroke (80 ms ease per key) and stack as they arrive, typed on the voice:
  - "Where to buy running shoes?" 3.90-5.02, sent 5.06
  - "Where to eat tonight?" 5.56-6.46, sent 6.50
  - "Which CRM should a small agency use?" 6.96-9.30, sent 9.34
  The camera fits the stack: about 1.5x, then 1.4x, then 1.23x. Type is 64 px world, about 77-95 px on screen.
  The stack is kept centred horizontally and vertically.
- 9.42-11.40 THE DIVE THROUGH THE "o" OF "should":
  - Log-space zoom (power3.inOut on ln K) about the o's counter, to about 200x. The stage is blurred up to 4 px with zoom speed.
  - A floor-coloured lens sits in the counter, and the ChatGPT answer card sits inside it at the same log rate.
  - The card lands at 1.6x, framed on its top: header, question bubble and the real answer prose (40 px), already
    there on "ChatGPT" (11.58).
- 11.42-13.96 The camera keeps travelling (1.6 -> 1.65x). The 4th line of the answer streams on "for the best CRM?" (12.46).
- 13.98 Camera whips to row 1 (1.45x). Names (52 px, white pills with layered contact shadows, plus a 30 px descriptor)
  fly in from the right on 14.20, 14.56, 14.84 and 15.76, and the camera tracks each one.
- 15.95-16.95 Pull back to the whole card (0.92x). "maybe": 5 (16.42). "five": the orange slot opens (16.68).
- 17.30 The seam push starts (Hermite to 2x about the slot, pan settles by 19.40). 17.85 rows dim. 18.06-18.40 "Your
  brand?" types on "Is yours". Everything else is cleared by 19.15.

## A->B final state (exact, at the cut = global frame 590; matches B's "Cut 3b" start frame)
- Floor #EEF1F5 plus the static tokens dot grid; nothing else visible.
- Slot: 1240x200 rounded rect centred at (1010,540) (x 390-1630, y 440-640), radius 40, 6 px #00AA90 border, #EBF8F6 fill.
- Caret: navy #3E0863, 6x100, radius 3, at x 430-436, y 490-590.
- "Your brand?": Space Grotesk 600 64 px #028C77, box left x=460, 80 px line box centred on y=540.
- "5": Space Grotesk 700 120 px #028C77, glyph right edge at x~342, vertically centred on 540.
- Scale velocity at the cut: +8 %/s (ds/dt = 0.16 at s = 2), origin at the rect centre. Pan at rest since 19.40.
- Measured on frame 589 (1/30 s before the cut, so 0.27 % smaller):
  - border x 392-1627 / y 440-639
  - caret x 432-436 / y 491-588
  - numeral glyph x 282-343 (x ~341.4 at the cut)
- Implementation: card scale 2 at the cut. Card slot 620x100, border 3, radius 20. Caret 3x50 at 17/22 inside the
  padding box. Text 32 px at 32/27. Numeral 60 px, box right edge 106.4.
- Freezedetect (d=0.8): none. Check: lint 0/0, check ok 0/0.
- Weaknesses:
  - The dive's middle (10.2-10.9) reads as a blurred navy ring with a small card in it.
  - The landing frame keeps about 30 % white below the answer prose until the camera travels.
  - Before "five", the close-ups sit on a mostly white card.

# Final (REVISION_3: zoom out 0.92, title-safe)
render-cut3.mp4 / src/a-cut3.tpl / a-cut3.js are the previous versions.
- All foreground (the 3D wall stage including the question stack, the near-lens question, the answer card and the
  Example-data tag) sits in #fg, scaled 0.92 about (960,540). The floor colour and the dot grid stay full-bleed.
  The seam geometry maps through x' = 960 + 0.92(x - 960), y' = 540 + 0.92(y - 540). Measured on the last frame:
  border x 438-1573 / y 448-631 on frame 589 (at the cut: x 435.6-1576.4, y 448-632, which is the cut-3 contract mapped through 0.92). The lens culling in the dive uses the expanded
  frame corners.
- Title-safe fixes:
  - Wall: the camera truck is now y only. The front 6 windows sit in a 3x2 ring around the hero, all inside
    96/54 px after the scale. The blurred mid and far layers still bleed off-frame as background.
  - The near-lens question moved up to y 724-908, clear of the caption band.
  - The answer card's landing framing is 1.58x (header x >= 96 after the scale); the travel is 1.6x.
  - In the close-ups the header and bubble fade (13.98) and the answer prose fades (14.62); both return with the
    pull-back (16.05).
  - The pull-back is now 0.85x, so the slot stays above the caption band.
  - The Example-data tag is at the top right.
- Lint 0/0, check ok 0/0 (contrast 0/0), freezedetect (d=0.8) none, 590 frames.
