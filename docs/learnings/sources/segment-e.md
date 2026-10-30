<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/film/E/NOTES.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# Segment E (film-e): s06 + s07, storyboard shots 20–28, key frames kf07 + kf08

Global 54.767–86.167 s (frames 1643–2585), local duration 31.4000 s (942 frames, checked).
Build: `src/index.tpl` + `src/build.py` -> `comp/index.html` (`python3 src/build.py`). The base is chain-36 (approved).
Its whole timeline is a child timeline added to the master at H = 139/30 = 4.6333 s (local 0 of chain-36 = global 59.40).
B-local times below are chain-36's cloud clock: B = local − 18.433.

## Beats (local / global)
- 0.00–2.60 / 54.77: D→E contract. The Perplexity answer card is at rect 410–1510 × 120–960. The camera keeps pushing,
  starting at 6 %/s and easing out (power2.out, ×1.078). At 0.85 ("read") the chrome (header, bubble, numerals) dims to 40 % and the dot grid fades.
- 2.09–3.69 / 56.86 ("Who got mentioned"): an x-ray reading line runs down the answer at 300 px/s. Each brand it crosses
  lights up: a leader line draws and a rank badge pops. The line runs at 406 px/s. #1 Acme CRM (orange) at 2.76 ("mentioned" 2.89), #2 Northwind at 3.10, #3 Contoso at 3.44.
- 3.97–4.63 ("order"): internal seam 0 at 4.30, cut-the-curve LEFT with chain-36's own parameters (300 px, 0.33 s,
  power4 in/out, 8 px blur). The Larkfield Bank Perplexity card lands at chain-36's opening rect at 4.633.
- 4.63–14.05: chain-36's x-ray, retimed by +4.633 s. The bank verdicts are now in the kf07 style: Space Grotesk labels,
  navy digits, and colour only on the sign ("Interest rates +2", "Mobile app +1", "Fees −1"). The match cut moves
  bank→restaurant at 12.12 (vertical wipe LEFT). The restaurant phrases land earlier (12.78–13.63) so the payoff gets room.
- 13.58–14.40 / 68.35 ("if it rates the burger"): the payoff is kf07. The chart becomes the verdict board through an
  identical-rect swap, then a FLIP morph of 0.45 s: the Burger row grows into the orange-ringed hero ("Burger" 150 px, "+2" 250 px),
  and Waiting time −1 and Price +1 shrink into the small rows. The answer card slides left and becomes the blurred ghost.
  The torn slip "the best burger in town" rises into its kf07 hover pose with the dotted trail. It dives into the dashed
  third slot and lands at 14.08 on "burger" (14.05). The slot fills green and the counter rolls +2 → +3. Hold until 14.69.
- 15.03 / 69.80 ("And fourth"): cut-the-curve LEFT, the board exits and the answer card enters. 15.05–19.27 is chain-36 unchanged:
  the Sources row pills light on the words, the Z push, the re-host morph at 18.58, and the shatter at 19.27.
- Clusters (round-E changes). The clusters now sit left to right in world x (R < F < S), so wide→R, R→F and F→S all carry the content LEFT.
  - r/smallagency: the pill lands on "Reddit" (21.63). Cards appear at 21.53 and 21.73. The camera leaves at 22.55, so the last card is readable for 0.82 s.
  - Toddler Parents Club (renamed): the pill appears at 22.83 on "Parent". Cards appear at 23.53 ("Facebook"), 24.23 and 24.89 ("children's").
    The camera leaves at 25.73, so the last card is readable for 0.84 s and no card is alone for more than 0.70 s.
  - Campus Hub (student forum): the pill appears at 26.05 on "Student". Cards appear at 26.58 ("forums"), 27.13 and 27.73.
    The camera leaves at 28.53, so the last card is readable for 0.80 s and the longest single card hold is 0.55 s.
- 28.53–29.30 ("Those are the places"): the payoff is kf08. The cloud pulls back and dims to about 30 %. The Campus Hub pill grows into its
  place card, and the r/smallagency and Toddler Parents Club cards arrive from the right mid-flight (LEFT). Together they form
  the kf08 stack (800×164, rotated −2.5° / 1.5° / −1°). Orange rings appear at 29.21 / 29.28 / 29.35 ("places" 29.23).
- 29.21–30.30: the real "Where competitors are cited and you aren't" card slides in from the right (no orange in its bars).
  The orange arrow draws into it from 29.75 to 30.17, and "Next" (#028C77) lands at 30.09 ("next" 30.19). Hold until 31.10.
- 31.10–31.40: E→F contract. #film (everything) uses power4.in, x 0 → −640 and blur 0 → 16 px. Opacity stays 1 until the
  last 2 frames (then fades to 0 linearly).

## Seam states
- In (frame 0): the card pixel-matches D's last frame. The card content is D's own `#fp` phone-space CSS (`.crm .ph`) at the ×1.44 card scale:
  - card rect 410–1510 × 120–960;
  - Perplexity tile 86 px at (445, 178); hairline y 293;
  - bubble right edge 1478, top 327;
  - chips at x 511, tops 512 / 650 / 788;
  - the frame-level "Example data" tag at right 56, top 44, and D's dot grid;
  - no Sources row.
  The diff against seg-D's last frame is edge antialias only (see seam-DE-sidebyside.png, work/diff0.png, cmp0.png).
  The push continues at 6 %/s, easing out. At 0.85 ("read") the dot grid fades out and the header, bubble and numerals dim to 40 %.
  The frame tag leaves with the card at the 4.30 cut.
- Out (31.40): see strip-end.png. kf08 accelerates LEFT with the B→C parameters.
- Internal seam gate (ledger.json, seam-gate.txt): PASSED, 0 fail, 0 warn across 5 seams. The head cut 4.30 matches
  speeds at 1.00. The board→card seam has a speed ratio of 2.63 (passes).

## Checks
lint 0/0; `check --at-transitions` ok, layout 0 errors / 0 warnings (deliberate layering is declared).
There were 4 render rounds (work/r1.mp4, work/r2.mp4, round 3, and render.mp4 = round 4, which has the D-matched head).
- r1 fixed the stack hand-over: cards started from off-screen pills, two were invisible or tiny, and the frames were empty.
- r2 fixed the push stalling before the reading line, and the cards in the stack now arrive LEFT.

## Weaknesses
- Round 4 (coordinator): the D→E content pop is fixed. The head card is rebuilt from D's `#fp` CSS. It has no Sources row, and the dots and tag are frame-level as in D.
  The head card has no Sources row at any time; Sources come with the bank card.
- The rank badges #1–#3 repeat the list numerals by design (measured rank vs. list). Contoso's badge is readable for only about 0.5 s before the exit.
- The kf07 slip is smaller than in the key frame (40 px text), and it is on screen for about 0.5 s.
- From chain-36: the phrase flights still travel RIGHT into the chart, and some white shards linger at 19.3–19.9.
  The pull-back to the wide view (S→wide) moves content right, because it is mostly Z backward.
- During the stack flight the Campus Hub card briefly crosses the Toddler card (about 0.15 s).

## Cut 2 (client: "0:50–1:15 feels slow")
The cut-1 render is kept as render-cut1.mp4 and the cut-1 source as work/src-cut1/. Unchanged: the head (0–4.30, still
pixel-matched to D), the Sources bridge, the cloud, kf08, and both contracts.

### Restructured x-ray (local 4.30–15.03)
The x-ray now lives in screen space (#xr > #xstage), as two sets. Each set has the "Sentiment by topic" chart on the LEFT
and the answer card on the RIGHT, so every torn phrase flies LEFT and swells toward the lens (Z, ×1.22) on the way.
The camera (#xstage) makes only zooms about fixed points, so no content travels right.
- 4.30: the head cut-the-curve brings the whole bank set (chart + card) in from the right.
- 4.71: the scan is 0.62 s (was 2.3 s).
- Flights land on the words: "talks" 5.71, "you" 6.23, "topic" 6.79, "topic." 7.43. The camera re-frames to a ×1.22
  close-up on each flight's path. Each row's counter rolls with a scale punch (kinetic numbers), and the label flashes.
- 7.99–9.43: one continuous re-frame onto the whole chart while the answer steps back (blur, 50 %).
- On "bank" the chart subtitle lights up.
- "sees": a push into Interest rates (×1.5).
- "AI": the other rows dim.
- "likes": orange ring, the +2 re-ticks and grows ×1.3.
- "interest rates": the label pops. The push continues to ×1.6 into the sweep.
- 12.27, "A restaurant": a fast cut-the-curve LEFT sweep (exit power4.in 640 px on screen with 12 px blur; entry mid-flight
  power4.out). The restaurant set arrives already x-rayed, at a ×1.18–1.26 close-up. Four flights run at 12.55 / 12.73 / 12.91 / 13.09.
- 13.58: kf07, now mirrored. The board grows on the LEFT (FLIP from the chart rows) while the camera eases back to ×1. The answer
  recedes in Z behind the board's right end as the ghost. The slip flies LEFT into the third Burger slot on "burger" (14.08).
  The board is read under a slow push (×1.05) into the "And fourth" exit.

### Other fixes
- Sources bridge: the lean toward the Sources row is now one continuous 1.8 s move. This removes the 16.7–17.8 hold.
- kf08 ending: a slow push (#film ×1→1.06 from 29.65, power1.in) runs into the E→F exit. This removes the 29.9–31.2 hold.
  The exit is unchanged: x −640, power4.in, blur 16, last 0.30 s.

### Checks
- freezedetect (n=0.002) finds no freeze at d=1.2 s, and none at d=1.0 s either.
- lint 0/0. check ok, layout 0/0.
- Seam gate: PASSED, 0 fail, 0 warn across 5 seams. The sweep at 12.27 has a speed ratio of 1.16.
- Strips: strip-start.png and strip-end.png are refreshed. Added strip-c2-xray-bank.png, strip-c2-sweep-kf07.png and strip-c2-endpush.png.

### Weaknesses
- kf07 is mirrored (board left, ghost right) so the slip can fly LEFT. This deviates from the key frame's placement.
- The restaurant flights are 0.18 s apart, which is dense. The restaurant chart's Price/Waiting counters tick only once.

## Cut 3 (REVISION_2 lift)
Cut 2 is kept as render-cut2.mp4 and its source as work/src-cut2/.

### Changes
- **Floor and D→E seam:**
  - The floor is #EEF1F5 from frame 0, matching D's cut-3 floor, and D's dot grid now has a 1.2 px blur.
  - The Perplexity card keeps D's exact old shadow, rect and push, so frame 0 still matches D (work/cmp3.png; PSNR 30.5 dB against D's last frame).
- **Depth:**
  - The shadow token is now layered: contact, mid and ambient.
  - The x-ray has a background depth plane (#xbg): six other answers, out of focus (7 px blur), with 45 % parallax against the camera zooms. It enters with the bank set at the head cut.
  - The answer card steps back (blur 2 px, 50 %) when the chart takes focus.
  - The chart subtitle is now 32 px. The Google label is now 44 px.
- **Restaurant ticks:**
  - The answer now carries 8 phrases (two or three per line; positions use widths measured in Chrome).
  - Waiting time ticks −1 → −2 → −1 and Price ticks +1 → 0 → +1, interleaved with Burger, 0.115 s apart.
  - Phrases lift one at a time, so neighbours never collide.
  - The kf07 board shows mixed pips: Waiting is +,−,− and Price is +,−,+. The final values are unchanged (−1 / +1).
- **Source cloud (local 19.3–21.5):**
  - The far dot field is gone. There are three clear layers, seen from a closer wide camera: 24 near icons (95–130 px, soft), 50 mid (55–75 px, sharp) and 46 back (33–42 px, soft).
  - The post-burst flights are faster (0.6–0.9 s), and the pull-back starts at B 0.92.
  - On "search results" the camera visits the Google cluster (ring, 44 px "Search results" label). Twenty-two framing icons keep the frame full, then the camera travels LEFT to r/smallagency.
- **kf08:** the destination card is ×1.12. After "next", a copy of each place card physically docks into the card's three dock slots (30.23 / 30.36 / 30.49), and the slate bar fills to 100 %. The slow push continues into the E→F exit.
- **Check hygiene:**
  - Hidden tokens and posts are display:none.
  - The spent worlds (cam, x-ray, shard stage) leave the DOM after B 3.0.
  - The shard stage declares data-layout-allow-orbit.

### Checks
- lint 0/0; check ok, layout 0 errors / 0 warnings.
- Seam gate: PASSED, 0 fail, 0 warn across 5 seams.
- freezedetect (n=0.002) finds nothing at d=1.2 s, and nothing at d=1.0 s.
- 942 frames.
- Strips: strip-start/end are refreshed. Added strip-c3-cloud, strip-c3-restaurant and strip-c3-kf08, and the stills still-c3-search and still-c3-kf08.

### Weaknesses
- During the G→R camera leg (about 21.2–21.45) the frame is sparse for about 0.25 s.
- The docked mini cards are symbolic (their text is about 17 px).
- The docking copies move right, toward the card. The orange arrow is the visible cause of this move.

## Final (REVISION_3: zoom out, title-safe)
Cut 3 is kept as render-cut3.mp4 and its source as work/src-cut3/.

### Changes
- **0.92 wrapper:** the whole foreground (#film) sits in #safe, scaled 0.92 about (960, 540). The floor and dot grid stay full-bleed, so both seams map through the same transform as the other segments.
- **Title-safe rework:**
  - X-ray flight close-ups are now ×1.06 about the frame centre (were ×1.22), so both cards stay inside 5 %.
  - "Topic by topic" is ×1.14 and the row push is ×1.25→1.29 (were ×1.5→1.6). The fixed points keep the chart inside the safe area.
  - The answer card steps back further (blur 3.5 px, 42 %): it is an out-of-focus depth plane.
  - Restaurant framing is ×1.04→1.06; the kf07 hold push is ×1.03 about the centre.
  - kf08:
    - The destination card is now fully inside the frame (960, 600, 900×400; title 32 px, sub 28 px). The three docks are 250 px wide.
    - The arrow ends on the card's top edge.
    - The tag is at right 64. The end push is ×1.03.
- **Audit:** a DOM edge audit (work/audit.js; results in work/audit2.txt, 0.2 s steps) leaves only exempt items:
  - motion entries (the sweep, the gap-card slide-in, place cards flying in);
  - the Z push into the Sources row at 16.8–18.4;
  - clipped odometer digits;
  - cloud icons as depth.

### Checks
- lint 0/0; check ok, layout 0 errors / 0 warnings.
- Seam gate: PASSED, 0 fail, 0 warn across 5 seams.
- freezedetect (d=1.2): none.
- 942 frames.
- strip-start.png and strip-end.png are re-made.
