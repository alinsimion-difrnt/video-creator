<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/film/F/NOTES.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# Segment F (film-f): agencies pitch with a real report

Global 86.1667–96.8667 s (frames 2585–2906), local duration 10.7000 s. Scene s08, shots 29–31, key frame kf09.
Source: src/index.tpl + src/build.py (inlines real Lobe/simple-icons SVGs) -> comp/index.html. Assets from keyframes/kf09.

## Beats (local / global)
- 0.00–0.45 / 86.17–86.62 E->F seam: the whole Pitch reports page (#entry) arrives at x +640, blur 16px, moving left;
  power4.out to rest. Framing: cam x170 y-10 scale 1.1 (table uses the frame; "Example data" in the header).
- 1.00–1.85 / 87.17–88.02 oversized cursor (134 px) enters from below on "agency" and parks on the orange-outlined
  "New pitch report" (hover tint at 1.75). Held 0.7 s (stillness before the click).
- 2.52 / 88.69 click on "pitching" (2.65): cursor tap + button press; Litware Travel row inserts at the top (other rows
  slide down 341 px and dim to 45%), name types in, "Travel agency", "Not sent", "Off". Cursor steps aside.
- 3.14–4.45 / 89.31–90.62 "is a lot of work": Acme builds the report itself — a floating report card (Litware
  Travel, AI visibility report; engine icons, flow lines, 0→38% count, "Send link" button).
- 5.04 / 91.21 cursor clicks "Send link" on "send" (5.21): the report folds into the link chip
  "acme.example/share/k7q2…"; cursor exits below. 5.08–5.93 camera nudges to the kf09 framing; 5.36–6.08 the
  prospect's phone arrives from the right (the current). 5.50–6.28 the chip arcs (dotted trail) into the phone's
  address bar on "prospect".
- 6.20–7.10 / 92.37–93.27 the phone opens the shared report hero on "real report": OVERVIEW, three engines, lines
  flowing into the navy Litware Travel card, 0→38%, "of the AI answers we read name you".
- 6.24–6.66 / 92.41–92.83 the chip lands in the phone, and on that frame the row flips Not sent -> Sent (roll), so the
  story holds at every frame (coordinator fix, round 4).
- 7.58 / 93.75 "as a link": the row's Link cell turns from Off into "…/share/k7q2". 7.95–8.40 held = kf09 layout.
- 9.08 / 95.25 "pay": "No charge" appears under Sent.
- 9.55–10.37 / 95.72–96.54 (coordinator addition; gather starts 0.25 s later since round 4) the film's cast gathers radially from past the frame edges into
  segment G's orbit (same model, ring tilts, phases and spin direction as film/G/src: 3 engines, 10 sources, the
  orange Acme CRM chip; ring paths fade in 9.5; G's "Example data" tag bottom-right). F's orbit clock is G's clock
  minus 10.7 s, so F's last frame is exactly G's pose at t = -1/30 (already turning counter-clockwise).
  Meanwhile from 9.5 the page dims (header, other rows, phone to 22–30%), keeping the Litware row in focus.
- 9.76 / 95.93 "sign" (9.93): Sent -> Signed (green, check draws); 9.88 "No charge" -> "Billing starts on sign"
  (orange outline; appears only at Signed), readable from ~9.95 to the exit at 10.46. The Billing chip lives on its own layer so it stays sharp.
- 10.10–10.44 / 96.27–96.61 the Signed chip lifts out of the row (carrier) and arcs left into its front slot on
  ring C, ending 25% larger than its G size for prominence; 10.10–10.40 the page recedes (30%, blur 6px), phone gone.
- 10.46–10.70 / 96.63–96.87 F->G seam: #exit (everything incl. dots, orbit, chips) scale 1->1.3 power3.in, blur
  0->16 power3.in, opacity 1->0.15 linear, origin frame centre (= G's #cast origin).

## Seam states
- Start (strip-start.png, 30 fps, 0–0.6 s): frame 0 = page at +640 px, blur 16, opacity 1, decelerating left.
- End (strip-end.png, 30 fps, 10.1–10.7 s): orbit spinning, Signed on the front ring, zoom-through forward;
  last frame at ~scale 1.29, blur ~15px, opacity ~0.2 — matches G's frame 0 (cast 0.75 / blur 16 / 0.15, growing).

## Rounds
1. Full build incl. orbit addition. Found: duplicated Signed chip (row tween kept overriding the hand-off), Signed
   crossing the ChatGPT disc, page too legible under the orbit, stray dots from zero-length round-cap lines.
2. Hand-off via visibility, Billing chip moved above the page, stronger recede, lines hidden until drawn.
3. Signed arcs left of the engine discs (quadratic path), fully opaque, ends 1.25x; final render + seam strips.
4. Coordinator fixes: Sent flips when the link lands in the phone (6.24), not in shot 31; orbit gather, page dim and
   Signed lift start 0.25 / 0.25 / 0.08 s later and Billing enters 0.05 s earlier, so Signed + Billing hold
   together in the row ~9.9–10.1 before the cast closes. G contract unchanged (same orbit clock, same exit).

## Check
lint 0/0; check ok=true; runtime/layout/motion/contrast 0 errors, 0 warnings. Layering declared per text block
(report over table, chip flight, rolling chips, orbit over the receding page). render.mp4: 321 frames, 10.700 s, audio.

## Weaknesses
- "Billing starts on sign" is fully readable for ~0.5 s (9.95–10.46) before the exit; the line gives no more room
  (round 4 gives it a cleaner frame by delaying the orbit, not more time).
- Two orange marks in the last second (Billing chip + G's Acme CRM chip in the orbit).
- Signed is ~25% larger at the cut than in G's frame 0 (hidden by blur 16 / opacity 0.15, but a G-side tweak could match).
- 0.45–1.0 s is a held establishing frame (no motion until the cursor enters on "agency").

## Cut 2 (client: "1:30 to 1:37 feels slow"; no static holds)
Cut-1 render kept as render-cut1.mp4, source as src/index-cut1.tpl. Every beat now has its own camera move or cut:
- 0.45–2.52 slow linear push (1.1 -> 1.2, ~4.8%/s) toward "New pitch report"; the cursor glides in on "agency" and
  rides the push onto the button (no parked hold). Click 2.52, then 2.66–3.28 re-frame onto the new row.
- 3.28–5.04 slow push (1.1 -> 1.17) toward the report while Acme builds it; the cursor's Send target is computed
  from the camera pose. 5.08–5.93 nudge to kf09 framing + phone arrives; 5.50–6.28 link chip flight (unchanged).
- 6.15–7.42 close-up: the camera pushes into the phone (1.0 -> 1.3) as it opens the report; the row's Not sent ->
  Sent flip (6.24, when the link lands) stays visible at the left of this frame.
- 7.42 cut on "as a link" to a close-up of the Litware row (scale 1.30), with a continuous ~5%/s push to the end.
  The link cell fills at 7.58; on "And you only" (8.42) "Opened just now" appears under the link.
- 9.08 on "pay": the billing condition "Billing starts on sign" lands as a grey chip (the condition, not yet met).
  9.82 on "sign": "Signed" STAMPS in (scale 1.6 -> 1, power4.out) and the billing chip turns orange.
  The billing text is readable 9.2–10.46 (about 1.25 s). The close-up places it in the empty centre of the orbit rings, so the
  cast never covers it.
- Orbit pre-roll (G's model and clock) and the F->G zoom-through are unchanged. The Signed chip still lifts from
  the row into the ring (start position computed under the close-up camera).
Verify: freezedetect n=0.002 d=1.2 -> none; d=0.8 -> none. lint 0/0; check ok, all audits 0/0.
Build: the comp output drops blank and comment lines and puts the CSS on one line (lint's file-size warning). Comments stay in src/.

## Cut 3 (lift: one big physical component per beat; REVISION_2 + six/REVIEW "Ten improvements")
Cut 2 kept as render-cut2.mp4 / src/index-cut2.tpl.
- Look: #EEF1F5 floor; no table card or column headers. Each prospect is a white slab (radius 30, layered contact
  shadow). Background slabs get depth of field (blur 3px, scale 0.97, opacity 0.6). Status labels are 44 px, billing
  38 px, link 34 px and "Opened just now" 32 px. The report card is 1.24x bigger (name 44 px, sub 30 px, 38% at
  104 px). "New pitch report" and "Send link" are navy outline buttons; the trail is navy dotted. Orange is kept only for
  "Billing starts on sign" (the agency's billing moment) and G's Acme CRM chip. Signed text is #15803D (AA).
- Beats and cameras: shot 29 opens at scale 1.25 and pushes to 1.33 onto the button (click 2.52). The new Litware
  slab lands, and the camera moves to a close two-shot of slab + report (1.26 -> 1.30) while the report builds. On
  "send" the report folds into the link chip, which flies (with motion blur) into a message thread on the
  prospect's phone ("Your agency: How does AI talk about Litware Travel? Have a look:") and becomes the link bubble.
  The bubble is tapped (6.42) and the thread slides left to the shared report: a phone close-up at 1.75 with
  engines -> Litware Travel 38%.
  The Sent flip stays at 6.24 when the link lands.
- 7.42: cut to the slab close-up; the rest (Opened, grey billing condition, Signed stamp, orange billing, orbit
  pre-roll, Signed lift into the ring) is unchanged from cut 2, re-anchored to the new chip sizes.
- F->G contract (cut-3 change from the coordinator): last 0.24 s scale 1->1.3 power3.in, blur 0->12 px, opacity
  1->0.4 linear. The cast stays big and visible through the cut (no blank frame).
- Verify: freezedetect n=0.002 d=1.2 -> none. lint 0/0; check ok, every audit 0/0 (cam close-up crop declared).
  render.mp4 has 321 frames and 10.700 s, with audio.
- Weak: in the phone close-up about 25% of the right side is plain floor; Signed briefly passes under two source discs
  as it lifts into the ring.

## Final (REVISION_3: zoom out 0.92, title-safe, caption band)
Cut 3 kept as render-cut3.mp4 / src/index-cut3.tpl.
- All foreground content (#entry: camera, slabs, report, phone, cursor, orbit, tags) sits in #safe, scaled 0.92 about
  (960,540). The floor colour and dot grid stay full-bleed inside #exit. The seam contracts map through the scale
  automatically: entry x +640 / blur 16 at the start, and at the end exit scale 1.3, blur 12, opacity 0.4.
- Title-safe reframes: the report two-shot CD0/CD is now 1.17 -> 1.20 (was 1.26 -> 1.30), so the slab and the report sit
  inside 5% and above y 930. The phone close-up is 1.2, centred at x 1150 (was 1.75, cropping the report card); the
  slabs behind go out of focus (blur 5px, 70%) as a depth layer and refocus on the 7.42 cut. The row close-up
  pushes 1.16 -> 1.28 (was 1.30 -> 1.46), so "Litware Travel" and the link and Opened text stay inside the safe area.
  Shot 29 framing was already inside after the 0.92 scale.
- Exempt: the phone body bleeding past the bottom (no text there), the background prospect slabs under the caption
  band, the cursor's entry and exit, and the orbit cast bleeding off the edges (allowed).
- Verify: freezedetect d=1.2 -> none; lint 0/0; check ok, every audit 0/0; render.mp4 321 frames, 10.700 s, with audio.
