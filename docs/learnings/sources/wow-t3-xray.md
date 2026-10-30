<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/wow/t3-xray/NOTES.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# t3-xray: Sentiment X-ray

An AI answer gets X-rayed. A navy scan line passes over a Perplexity answer, the sentiment phrases light up green (+) or red (−), tear loose from the paragraph as paper slips, and fly into a "Sentiment by topic" panel. Each slip collapses into one signed segment of a stacked bar. The same mechanic then runs again on a restaurant (ChatGPT, "Burger").

## Round 2 (after judge feedback: "document scale, no camera")
The judge scored round 1 at WOW 5. Round 2 rebuilds the piece in one world with one camera (#cam), so everything plays at cinema scale.

### Beats (s)
- 0.00-0.40: the Perplexity answer is fully present (5 lines, 40px, framed at 1.2x). There is no type-on.
- 0.45-1.95: the camera pushes in 1.2x to 1.62x (x1.35, power3.inOut), centred on the scanned lines. Key phrases render at about 65px.
- 0.60-2.90: x-ray scan, landing with "topic by topic". Filler drops to 22% with a 1.5px blur. Each key phrase comes up to ink #111827 with a signed green/red badge.
- 3.00: the phrases tear loose as white slips (rise 8px, ±1.8°, shadow). Each leaves a dashed imprint, and the paragraph sinks to 15%.
- 3.95-4.55: the camera pulls out to the split layout while the chart slides in on the same beat. Rows, tracks and "0" counters come in from 4.30.
- 5.43, 5.57, 5.71, 5.85: one slip at a time (140 ms stagger, 0.55 s each), in the order fees, mobile app, savings rates, strong interest rates. "Strong interest rates" is last and lands at 6.40 on "interest".
- 6.38: orange focus ring on Interest rates (+2); the other rows and the card dim.
- 7.30-7.65: match cut. The scan line wipes the card from the bank answer into the ChatGPT restaurant answer (clip-path wipe synced to the line). Restaurant phrases appear already x-rayed. The bank segments drain to their left ends. Row labels, the subtitle and the counters roll in place (0.2 s).
- 7.82: restaurant lift. 8.31-9.42: five flights in the order price, waiting time, burger, burger, burger. The last burger lands at 9.42 on "burger".
- 9.42: payoff. The camera moves to the Burger row at 1.5x, centred, with "+3" at 96px Space Grotesk and the focus ring. Other rows fade to 20% and the card goes out (power3.out, 0.5 s). Held to 10.44.

### Flight design
- A slip settles onto its row's lane early (y on power3.out over the first 60% of the flight) while x runs power3.inOut. Every path is a smooth L-curve on its own horizontal lane, so paths never cross.
- The flight order is chosen so a slip only rises through lines that are already empty.
- The slip morphs into its 160x48 segment in flight: text out, background compresses and turns solid, sign slides to the centre.
- A new segment enters at slot 0 and pushes the row's earlier segments right (power3.out), so nothing slides over a landed segment.
- The counter is a rolling strip that ticks on each landing.

### Iterations in round 2
- r2a: the arc bump (y -70) made slips pass over row labels and other slips. Replaced it with the lane-first L-curve, re-wrote the paragraphs for collision-free flight order, and added the insertion push.
- r2b: the morph collapsed too early, while the slip was still in the card, and the badge covered the text. The morph now runs later on power2.inOut and the badge moves after the text fades. Imprint outlines are lighter.
- r2c: restaurant chips appeared over not-yet-wiped bank text. Each chip is now revealed only after the scan line clears its line.

## Known weaknesses (round 2)
- Frame 0 is still a 0.4 s fade-up of the card (not empty, but not a hard open).
- The bars are discrete per-phrase segments, so the tracks are partly empty (by design).
- The dashed imprints in the card at split view are a bit busy.
- The drain is quick (0.22 s) and reads as a flicker at 10 fps.
- Two slips on adjacent lines touch, but do not overlap, while one passes the other.
