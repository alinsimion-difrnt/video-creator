<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/wow/chain-36/NOTES.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# chain-36: x-ray -> sources, one film (26.78 s)

Idea: one hero object, the ChatGPT answer card for "Is Patty Lane worth a visit?". The X-ray reads it. The camera then comes back to
the same card, its Sources row lights up, and the camera pushes into that row. The card shatters past the lens and the cloud of
sources pours out of its pills. One composition, one canvas (#F5F7FA), one card design, power3/power4/expo eases, one orange accent.

## Build
src/index.tpl + src/build.py -> comp/index.html (script compacted to keep lint's file-size rule; readable source is the tpl).
- World A (#cam, a 2D camera): the t3 x-ray world, plus a clean copy of the same card (#acard) at the x-ray card's rect.
- World B (#world + #cstage): the t4 cloud, projected by render(tb), with tb = film - 13.80 (t4's word times are +13.80).
- The card is re-hosted in B at the identical screen rect while the camera is at rest: #cardB, plus the pills (#pillsB on a layer
  above the shards), plus 20 shards. Each shard is a clipped clone of the same card.

## Seam plan (ledger.json; gate output in seam-gate.txt: PASSED, 0 fail, 0 warn)
1. 7.49 (wipe 7.30-7.68), bank -> restaurant match cut. The scan line is now VERTICAL and sweeps right to left (the current).
   Faces clip in step with the line, and each restaurant chip is unveiled by the same line. Carrier: the card. Its gate row is trivial
   (the card itself does not move).
2. 10.40, "And fourth", cut-the-curve LEFT.
   - Exit: the Burger +3 payoff frame moves 300 px left (power4.in, 0.34 s) with an 8 px wrapper blur. Its fade (power2.in) dies at the cut.
   - Entry: the answer card arrives from the right mid-flight (power4.out, 300 px / 0.34 s, ignites at 0.35 opacity) at 1.15x.
   - Measured: -1898 px/s on both sides, ratio 1.00, zero overlap.
3. 11.30-12.10: the camera leans in (Z+, 1.15 -> 1.45) toward the Sources row. Staged reveal: the rest of the card dims to 40% at 11.40.
   The pills light on the words: Tripadvisor 11.42 "where", Yelp 11.98 "AI", Reddit 12.46 "gets", Google 12.70 "its", +12 13.12 "answers".
4. 13.10-13.90: Z forward into the Sources row (1.45 -> 2.0). 13.95: the re-host morph, A -> B (gate carrier delta 0 px / 0 %).
   14.16 "sources": the pills lift 10 px. 13.90-14.50: stillness (dramatic comma).
5. 14.64 "go", scale-burst. A 0.14 s power3.in lunge (push resumes, 1.00 -> 1.10) punches through, and the card shatters past the lens.
   Shards keep growing (z 380-820, power2.out). Tokens pour out of the four pills (the pills stay crisp on top and fade over 0.28 s).
   - Measured z+ on both sides (0.77 / 2.21 es/s, ratio 2.86). The z-sign scan is clean.
   - 14.92 "far beyond": the cloud camera pulls back (Z backward = arrival of the bigger world). From here t4 runs unchanged.

## Changes from the source tests
- t3: the card is 800 tall and carries its own Sources row from frame 0, dimmed as filler by the x-ray. The chart is 800 tall (rows re-spaced).
  The dot-grid background is removed (it would vanish at the world swap). The match-cut wipe is vertical and moves leftward.
  The payoff now exits into seam 2 instead of holding to the end.
- t4: the Perplexity card is replaced by the t3 ChatGPT card itself, framed at 2.0x on its Sources row. The opening rise is gone.
  - Shards: 20 instead of 12. They carry the real dimmed answer text, fly toward and past the lens, and have smaller tumble rotations
    (rotationX/Y ±12°).
  - Token origins: the pill icon centres, computed from the A camera framing, the lift and the lunge.
  - The 14.44 squeeze anticipation became a forward lunge (no Z sign flip into the burst).
  - Google cluster: y 150 -> 230, so it lands below the old row.
- New bridge (10.40-13.95): the clean card returns, the pills light one by one, and the two-stage push into the row.

## Rounds
- r1: seam 1 read as a fade-to-empty, because the linear fade killed the chart before it moved, and the card arrived small (1.0x).
  The pills were too small to read lighting up.
- r2: fixes were a power2.in fade, 300 px travel, the card at 1.15x, a camera lean-in (1.45x) during the pill reveal, and a push to 2.0x.
  New problem: white shards covered the pills at the shatter frame.
- r3: the pills moved to their own layer above the shards (same lunge). Shard tumble was reduced and the lunge raised to 10% so the
  z-sign scan and the speed match pass.
- Checks: lint 0/0; check --at-transitions ok, layout 0/0.

## Known weaknesses
- Phrase flights (5.4-9.4 s) still travel RIGHT into the chart, against the current. This is in-scene causal motion, not a seam,
  but it is the one sustained counter-current.
- Shards are white paper pieces and partly linger at the frame edges until ~15.2 s. They briefly read as blank rectangles.
- The burst has a sign mix: shards come toward the lens while tokens fly into depth, and 0.3 s later the camera pulls back.
  This is justified as an explosion followed by an arrival, but a purist would call the 14.64 -> 14.92 pair a Z+ then Z- sequence.
- Gate row 1 (the wipe) only checks that the card stays put. The leftward direction of the wipe is verified by eye (strip-seam-7.49.png).
- The gate's entry selector for the burst is a full-screen shard wrapper, so its bounding box inflates under rotation and the
  measured entry speed is high.

## Round 4-5 (client: "from 17 s it feels empty, focus small/late")
Everything before ~16.4 s and all 4 seams are unchanged (cloud placement keeps its PRNG stream; new content uses its own PRNG,
mulberry32(36036)). Seam gate re-run: PASSED, 0/0. Lint 0/0, check ok (layout 0/0).
- Close-up cluster shots: the camera sits 520 from each cluster (was 760) via camNear(). Each cluster also has 10 of its own
  foreground tokens (120-170 px) that frame the edges and arrive staggered with the camera. On screen:
  - pill: ~135 px tall, label ~58 px Space Grotesk;
  - post cards: re-designed as mini-cards (title ~40 px, meta ~27 px, reply counts tick up after landing). There are 2 at Reddit and
    3 at Facebook and the forum, forming one pill-over-cards block.
  - Non-focal tokens: 25%. Anything in front of the block is cleared.
- Word sync (local = film - 13.80):
  - camera legs: 0.45 s, power3.inOut, at 16.40-16.85, 17.75-18.20 and 21.02-21.47.
  - Reddit: pill lands on "Reddit" 17.00; cards at 17.10 and 17.46 ("threads" 17.56).
  - Facebook: pill on "Parent groups" 18.08-18.40; cards on "Facebook" 18.90, "children's" 20.26, "products" 20.78.
  - Forum: pill on "Student" 21.36; cards on "forums" 21.94, at 22.50 and on "college" 23.14.
  - The R->F leg moves content LEFT (the current). Wide->R and F->S are forced by the fixed cluster positions.
- Payoff:
  - 23.85-24.45: the three focal pills fly out of the cloud as carriers into a centred stack (1.9x: ~137 px tall, ~57 px labels).
    The cloud recedes, dims to 12% and blurs.
  - Orange rings: 24.52 / 24.60 / 24.68 ("places" 24.60).
  - "show up next" 25.10-25.60: one orange arrow sweeps down the stack, and "Next" (#028C77) lands on "next". Hold to 26.78.
  - The Example data tag now stays to the end.
- Remaining weaknesses:
  - The Facebook shot holds one card from 18.9 to 20.26; only its reply counter animates.
  - Departing cards are readable for only ~0.3 s while the camera leaves (Facebook card 3, forum card 3).
- Fresh strips: strip-cloud-16 / 18.5 / 21 / 23.5 (10 fps) and strip-payoff.png (23.8-26.8).
