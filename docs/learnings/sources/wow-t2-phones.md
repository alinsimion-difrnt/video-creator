<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/wow/t2-phones/NOTES.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# t2-phones: one question, three phones (8.82 s)

The idea: Acme asks the real consumer apps, not APIs. One typed prompt is sent into ChatGPT, Gemini and Perplexity at
once, the answers stream in each, and your brand turns up in only one of them, so the camera pushes in on that phone.

## Beats (round 6, final; word times from clip start)
- 0.00 "Second": the bar is already on screen with "B" typed, and the "2" marker fades up. Typing runs 0.02-0.98 at about 35 ms per character; send is pressed at 1.08.
- 1.20-1.46: the bar shrinks into one chat bubble at frame centre. Three copies sit exactly on top of each other.
- 1.42: the phones arrive from depth on their own timing (blur 16 to 0, expo.out) and settle as one overlapping stack: centre z -300, sides x ±520 at z -600, behind the centre phone.
- 1.46 / 1.54 / 1.62: the three copies fly on quadratic curves (power3.inOut, 0.6 s, 80 ms stagger). The side copies swing wide and drop into each phone's bubble slot, which is measured at landing. Each copy hands off to the real bubble with a 0.08 s cross-fade.
- 2.62 "open the actual apps": the stack fans out in one decisive move (expo.out, 0.9 s): side phones x ±540, rotateY ±26°, z -120; the centre phone comes to z +60, about 83% of frame height.
- 3.00 / 3.12: rows 1-2 stream in sync in all phones (46 px chips, about 48 px at 1920). Sources follow at 3.36-3.72.
- 3.62-4.57: the camera pushes into the answers (rig z +210).
- 4.98 "customers": row 3 shows the gap first, a dashed "Not mentioned" in ChatGPT and Gemini. At 5.13 the orange "Acme CRM" chip lands in Perplexity with one halo ring.
- 6.20-7.00 "so we see": the camera hands off to Perplexity, which moves to left of centre and turns to rotateY 0. The other two fall back off the left edge behind a 0.72 canvas wash plus 4 px blur.
- 6.92: "1 of 3" (200 px Space Grotesk; the "1" is in #028C77) and "apps name you" (52 px) land as one centred group with the phone. Everything is settled by about 7.5 and holds to 8.82. "Example data" sits top-right from 3.0.

## Iterations
- R1: bubbles flew inside the 3D phones and were hidden behind the centre phone. The dimmed phones were see-through (opacity).
- R2: the split was rebuilt as flat copies in frame space, moved with transforms only. Doubled text was fixed with one isolated wrapper per copy. Added the "1 of 3" verdict.
- R3: opacity dimming replaced with an opaque wash. R4: perspective 2200 to 1600.
- Judge on R4: baseline 6, WOW 4 (no camera, no climax, empty screens, late payoff).
- R5 rebuilt the timeline: typing starts at 0.0, send at 1.2, a literal ripple, the camera push-in during the fan, a reframe on "customers", payoff at 6.18, focus at 6.6, the verdict at 7.0. Grey placeholder lines were dropped. Rows are max 3 at 32px with 64px-tall chips. Engine logos sit in neutral badges. The "bar drops to the bottom" move was removed. In R5b the collapse ease was softened, the arcs were reshaped into a branching tree, and the streaming came earlier.

- Judge on R5: WOW 5 (static middle, small sequential moves). R6 rebuilt the middle as one gesture: physical copies on curved paths into a stack, a decisive fan on the cut, synced streaming plus a push-in, the turning point moved to "customers", and an end frame built as one centred group with a 200 px verdict. The tag moved to top-right so the pushed-in phone no longer meets it.

## Known weaknesses
- For about 0.1 s after the copies leave the seed bubble they overlap, so a second line of text peeks out from behind the centre copy.
- At landing, the flat copy hands off to a slightly perspective-skewed bubble on the side phones, over 0.08 s.
- 4.6-4.98: a short hold after the push-in, just before row 3.
- The Perplexity logo stays teal; it is a real brand mark and I left it unaltered.
