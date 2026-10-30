<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/film/D/NOTES.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# Segment D (film-d): s05 "2. Real browser runs" (shots 17–19, kf06)

Global 45.967–54.767 s, frames 1379–1643, local duration 8.8000 s (264 frames, verified).
The build is based on the judged three-phones test (wow/t2-phones, round 6) with the data and layout of kf06.
Source: src/d.tpl, built with `python3 src/build.py src/d.tpl comp/index.html`, which inlines the real Lobe and simple-icons SVGs. Rounds r1–r3 are kept as src/d-r*.tpl.

## Beats (local / global)
- 0.00 / 45.97 (seam C→D): the kf01 prompt bar at scale 1.0. It is 1100x112, centred, with the full text and the orange send button. Its inner layout is copied from C's bar: plus 68 px, text 40 px at x+116, send 78 px. A step "2" fades in at 0.05, just after "Second".
- 0.80 / 46.77: send presses. From 0.92 to 1.20, on "real", the bar shrinks into one grey question bubble at the centre (power3.inOut). The plus, send and text fade out, then the step marker leaves.
- 1.02 / 46.99, "browser": three phones arrive from depth (blur 16 to 0, expo.out) and land as a row in depth.
- 1.10–1.90 / 47.07–47.87, "runs": the physical ripple. The seed bubble is three stacked copies with a hairline and shadow. The side copies peel away first (1.22 and 1.27), then the centre copy (1.32). Each flies on a quadratic arc (power3.inOut, 0.58 s) into its phone's bubble slot, which is measured at landing, and hands off over 0.08 s.
- 2.10 / 48.07: "Thinking…" appears once in each app; no loop.
- 2.78 / 48.75, "open the actual apps": one expo.out move fans the row out to the kf06 positions. The sides go to x ±600, z −420, rotateY ±30; Perplexity comes forward to z 0.
- 3.22–3.46: answers stream in sync in all three apps. Perplexity's row 1 is held as a blank skeleton chip. Its sources (Reddit, G2, YouTube) follow at 3.60–3.9, and "Example data" appears at 3.2 (top-right).
- 3.55–4.90: the camera moves in to the exact kf06 framing. The centre phone is 880 px, 81% of the frame height.
- 5.06 / 51.03, "customers": dashed "Not mentioned" lands in ChatGPT and Gemini. At 5.16, the orange "Acme CRM" chip drops into Perplexity's #1 slot with one halo ring. From 5.45 the side apps wash to 0.42, and at 5.9 the frame is kf06 (still-kf06.png).
- 6.20 / 52.17, "so we see": the side apps fall out past the frame edges (x ×2.6, blur 8, wash 0.85). The camera pushes into Perplexity.
- 6.85–7.85 / 52.82–53.82, "the answers they see": the phone becomes the answer card. The bezel and chrome fade out (status bar, island, sources, input). The screen reshapes from tall to wide, the bubble slides right and the list slides left. The card has a hairline and shadow.
- 7.85–8.80: the card holds its layout while the camera keeps pushing.

## Seam states
- **C→D:** frame 0 matches C's last frame (I rendered C's comp to compare): mean luma difference 0.06, edge antialiasing only. The bar starts static at scale 1.0. The dot grid matches, because tokens.css is shared.
- **D→E, at the cut:**
  - The card rect is exactly x 410–1510, y 120–960, radius 32, with a 1 px #E5E7EB hairline and the shadow token.
  - The camera is still pushing at +6%/s. Scale is 1.44 and the camera z velocity is 75 px/s, so for E: scale(t) = 1800 / (1250 − 75·t), with t in seconds after the cut.
  - Content (frame px at the cut):
    - Perplexity icon tile: 86 px at (445, 178), with "Perplexity" in Inter 600 at 49 px.
    - Hairline: y 293.
    - Question bubble: 432 px wide, right edge 1478, top 327, Inter 36/49 px, #EEF0F3.
    - Rows: numbers at x 447 (Space Grotesk 55 px); chips at x 511, tops 512 / 650 / 788, 115 px tall, Inter 600 60 px.
    - Row 1 "Acme CRM" is orange (tint fill, 4.3 px #00AA90 ring, #028C77 text). Rows 2 and 3 are Northwind and Contoso.
  - "Example data" tag: right 56, top 44.
  - Simplest way for E to match: reuse `#fp` from src/d.tpl with `mo.m = 1` and the fp scale from the formula above.

## Checks
- lint: 0 errors, 0 warnings.
- check --at-transitions: ok true; layout 0/0; runtime 0; contrast 21/21 passed (check.json).
- Deliberate layering is declared on the phones, the bar and the flying copies.

## Review artefacts
- strip-start.png and strip-end.png: 30 fps, first and last 0.6 s.
- strip-1..4.png: 10 fps over the whole segment.
- still-kf06.png and still-end.png.
- review/: per-round strips, the split close-up, the morph strip, a 480 px legibility still, and the C/D seam diff (seam-cd.png).

## Iterations
- R1: the full pipeline worked; the 5.9 frame matches kf06 and the end card is on the contract rect. Problems: the copies read as one mushy overlap at the split, the bezel faded to a grey outline phone mid-morph, and 1.9–2.8 was dead.
- R2: hairline and shadow on the copies, faster bezel and chrome fades, the one-shot "Thinking…".
- R3: the split order changed so the side copies peel out from under the centre copy.
- R4: the bar internals were matched to segment C's actual bar (C has no caret, so the caret was removed). Re-verified the seam.

## Weaknesses
- At the split (about 1.3–1.45) the copies still overlap for a few frames; one copy's text edge peeks out from under the top copy.
- 0.0–0.8 is a static bar. The contract requires it and only the step "2" moves.
- The end card is left-heavy: the list sits left and the bubble right, so the lower-right quarter is empty white.
- Perplexity's blank row-1 skeleton during 3.2–5.1 is a staging device; a real stream would not hold row 1 back.

## Cut 2 (client note "0:50–1:15 feels slow")
The cut-1 render is kept as render-cut1.mp4 and its source as src/d-cut1.tpl. 0–2.7 s is unchanged; the C→D bar start is identical.

Beats (local time):
- 2.74: the fan, which is now faster (expo.out 0.8 s).
- 2.96–3.12: answers stream faster (0.08 s stagger). Sources follow at 3.2.
- 3.28–3.83: the camera dives onto ChatGPT (cam z 900, pan −600). "Not mentioned" stamps in at 3.68.
- 4.18–4.68: a whip-pan to Gemini; the near Perplexity phone wipes across the frame. "Not mentioned" lands at 4.58.
- 4.86–5.48: on "customers" the camera pulls back to the kf06 wide as orange Acme CRM lands at #1 (5.12) with the halo. The side phones wash at 5.2.
- 5.52: a strong push into Perplexity starts on "do", 0.7 s earlier than cut 1. Scale goes from 0.92 to 1.44 and the side phones fly past (power3.in, blur 10).
- 6.38–7.33: the phone becomes the answer card, landing on "answers" (7.19).
- 7.33–8.8: the push continues at 3.3–6%/s and is still +6%/s at the cut.

The D→E end state is unchanged: card rect 410–1510 × 120–960, scale 1.44, cam z velocity 75 px/s.

Verification:
- freezedetect (n=0.002, d=1.2): no freezes. At d=0.8 the only freeze is 0–1.0 s, the contracted bar plus the step "2".
- lint 0/0; check ok, layout 0/0 (the rig's off-frame placement is declared), contrast 0 errors.
- 264 frames.
- Close-ups: review/c2-quad.png.

Weakness: during the ChatGPT close-up the near Perplexity bezel shows as a dark slab at the right edge. It is deliberate depth, but heavy.
- Cut 2b: the slab is fixed. The near Perplexity phone dissolves out over 3.30–3.70 (opacity 0, blur 14). It returns over 4.84–5.12, before Acme lands. The cut-2 source is kept as src/d-cut2.tpl. freezedetect still finds no freezes; lint and check are clean; both seams are unchanged.

## Cut 3 (polish, REVISION_2)
The cut-2 render is kept as render-cut2.mp4 and its source as src/d-cut2b.tpl.

- **Floor and depth:** the floor is #EEF1F5 and the dot grid is softened with a 1.2 px depth-of-field blur. Phones have layered contact shadows (contact, mid and ambient).
- **Navy send:** the send button is navy #3E0863 with a navy shadow; orange is reserved for Acme.
- **Bigger phones:** the base camera is z +100, so the wide focus phone is 932 px (86% of frame height) and the stack phase is about 10% bigger.
- **Close-ups:** cam z 1000, pan ±424, app at the left or right third. Answer chips are about 62 px and "Not mentioned" about 47 px.
  - The near Perplexity phone is now a soft foreground plane (blur 10 px) on the opposite third. This replaces the cut-2b fade-out, so no frame is empty, and it is not a hard slab.
  - The whip adds motion blur (near phone 16 px, stage 6 px) at peak speed; the blurred phone fills the middle of the whip.
- **No placeholder state:** Perplexity's blank row-1 skeleton is gone. It shows "Thinking…" (a status) until the hit. Its whole list then streams on "customers": Acme CRM at 5.12 with the halo, then rows 2 and 3, then Sources. In the wide after the hit, the side phones get a 3 px depth-of-field blur plus the wash.
- **Seams:** the C→D bar is still the same component, except the send button is now navy. The D→E card content, rect, scale (1.44) and +6%/s push are unchanged.
  - **C must also end with a navy send button.**
  - **E's frame 0 must use the #EEF1F5 floor.** The floor colour changed under the card; the card itself did not change.
- **Verification:**
  - freezedetect (n=0.002, d=1.2): none.
  - lint 0/0; check ok, layout 0/0, contrast 0 errors.
  - 264 frames.
  - Review images: review/c3r3-quad.png (close-ups and whip) and review/c3-overview.png (first frame, wide, kf06 beat, end).
- **Known gaps:**
  - Phone-internal question bubbles stay 25 px (34 px on screen in the wide). The D→E card must stay pixel-identical to what E already matches, so I did not reflow them.
  - The opening bar text is C's 40 px.

## Final (REVISION_3: zoom out 0.92, title-safe)
The cut-3 render is kept as render-cut3.mp4 and its source as src/d-cut3.tpl.

- **Zoom-out:** all foreground content (step, stage and rig, the focus phone, bar, flying copies, tag) sits in `#world`, which is `scale(.92)` about (960, 540). The floor and dot grid stay full-bleed.
- **Flying copies:** their landing rects are measured in frame space and mapped back into world space (÷0.92).
- **Seam contracts** map through the transform automatically:
  - Start bar: 1012x103 centred.
  - End card: x 454–1466, y 154–926.
  - The scale velocity ratio is unchanged (+6%/s).
- **Edge-audit fix** (local 3.43–5.03): the close-ups now use camera pan CY 0 instead of 90, which moves the app content down about 120 px.
  - The ChatGPT and Gemini headers and question bubbles now start below y ≈ 80. The "Not mentioned" slots end above y ≈ 900, clear of the caption zone.
  - Only the out-of-focus foreground phone and the whip motion-blur frames bleed off the edges, which the rule allows.
- **Edge-audit fix** (local 6.03–6.63): these frames show the side phones flying out past the lens (a deliberate exit). The readable Perplexity phone stays inside the safe area.
- **Verification:**
  - lint 0/0; check ok, layout 0/0, contrast 0 errors.
  - freezedetect (d=1.2): none.
  - 264 frames.
  - strip-start.png, strip-end.png, strip-1..4.png and stills re-made; review/final-quad2.png.
- Final pass 2: there was a near-still across the C→D join. From frame 0 the camera now pushes slowly on the bar: scale 1→1.045 over 0–0.92 s, power1.in from rest (frame 0 is unchanged). The scale eases back as the bar collapses into the bubble. The join test (C's last 1 s plus D's first 2 s) and freezedetect results are in review/join.mp4.
