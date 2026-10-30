<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/film/sfx/NOTES.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# Cut 3 sound pass (current): `film-sfx-cut3.mp4`

The picture is cut 3 (`../film.mp4`, rendered 2026-10-09, 3154 frames). The master audio and the VO timing are
unchanged. Cut 2's `film-sfx.mp4`, `sfx-bus.wav` and `cues.json` are kept below as they were.

- Cut-3 files: `film-sfx-cut3.mp4` (video stream copied), `sfx-bus-cut3.wav`, `cues-cut3.json`, `work/cues3-full.json`,
  and `work/verify3.json`.
- Scripts: `cues3_draft.py` → `build3.py` → `mix3.sh` → `verify3.py` → `plots3.py`. Frame differences for the new
  render are in `work/blocks3.npy`.
- Re-derivation: every beat was re-read from the "Cut 3" / "Cut 3b" NOTES sections and checked on new 5–10 fps
  strips, `png/c3/{a1..a4,b1,b2,c1..c3,d1,d2,e1..e4,f1,f2,g1}.png`. The same motion snap was then applied as in
  cut 2.
- Rules: the per-type offsets and the masking rules are unchanged. Every cue sits 6 dB under the voice, except the
  logo riser and hit, which sit 3 dB under and are band-limited to below 300 Hz and above 6 kHz. Two-pass loudnorm
  ran in linear mode after the −2.5 dBFS oversampled limiter.

## New palette sounds (3 generations; cached by request hash like the rest)
| name | dur s | influence | prompt | file |
|---|---|---|---|---|
| `pill-drop` | 0.6 | 0.6 | Soft rubbery pill-shaped object dropping onto a padded table, short weighty muted thud with a tiny squash, dry, close | palette/pill-drop.mp3 (cache/13a95d6fb52c9a7f.mp3) |
| `dive-whoosh` | 1.8 | 0.5 | Smooth accelerating zoom-through whoosh, airy and soft, rushing forward through a tunnel then opening out, clean, no rumble | palette/dive-whoosh.mp3 (cache/6473fd00a7b760ee.mp3) |
| `tick-roll` | 1.5 | 0.6 | Soft mechanical counter rolling fast, rapid tiny ticks that speed up then slow down and settle, subtle and clean | palette/tick-roll.mp3 (cache/ff897a8e5af760da.mp3) |

- dive-whoosh is high-passed at 120 Hz (2 poles), because the generated sound carried more low end than asked.
- New sounds by event:
  - pill-drop: the A question pills, the C numeral, the row and chip drops, the B rivals, the F slab and the E docks.
  - dive-whoosh: the dive through the "o".
  - tick-roll: the "brands found" counter and the Day 1→30 counter.
- The palette is now 19 sounds. All other cues reuse the cut-2 palette.

## Cut-3 cues (67)
| t_global s | seg | sound | gain dBFS peak (pre-norm) | event | source / check |
|---|---|---|---|---|---|
| 0.371 | A | click-ui | -14.0 | Opening question pill sends | A c3: sends 0.46; strip c3/a1; notes (strip-checked or sustained) |
| 0.940 | A | whip-fast | -16.3 | Pill whips LEFT out of frame | A c3: 0.70-1.12; strip c3/a1; motion peak f29 (105.7, x8.0 median) |
| 3.900 | A | key-ticks | -16.0 | Pill grows with each keystroke: 'Where to buy running shoes?' | A c3: typed 3.90-5.02; dur 1.1; notes (strip-checked or sustained) |
| 4.373 | A | swoosh-soft | -14.0 | Dive: window frame falls away, input becomes the pill | A c3: 3.85-4.90; notes (no clear spike: 22.2 vs median 18.1) |
| 5.682 | A | pill-drop | -14.0 | Second pill stacks in | A c3: 5.56 'Where to eat'; strip c3/a2 5.6; motion peak f170 (99.3, x1.8 median) |
| 6.960 | A | key-ticks -1 st | -17.0 | Third pill types 'Which CRM should a small agency use?' | A c3: 6.96-9.30; dur 2.0; notes (strip-checked or sustained) |
| 9.251 | A | click-ui -1 st | -13.0 | Send pressed | A c3: 9.34; notes (strip-checked or sustained) |
| 10.373 | A | dive-whoosh | -21.3 | Log-zoom dive through the 'o' of 'should' (peak speed) | A c3: 9.42-11.40; strip c3/a3 fastest 10.2-10.6; notes (strip-checked or sustained) |
| 11.016 | A | card-land | -14.0 | ChatGPT answer card lands out of the lens | strip c3/a3: card settles ~11.0; notes (no clear spike: 50.6 vs median 38.5) |
| 14.266 | A | pill-drop | -15.3 | Northwind pill lands | A c3: 14.20; strip c3/a4 14.25; notes (strip-checked or sustained) |
| 15.866 | A | pill-drop +3 st | -13.0 | Tailspin pill lands | A c3: 15.76; strip c3/a4 15.8-15.9; notes (strip-checked or sustained) |
| 16.469 | A | chime-warm | -11.0 | Orange slot opens on 'five' | A c3: 16.68; motion peak f495 (64.4, x3.9 median) |
| 20.202 | B | chime-rise | -12.0 | Slot curls into the G ring; arrow locks | B 3b: morph 0.25-0.55, lock 0.40-0.70 local; strip c3/b1; motion settles f607 after peak f604 (50.2) |
| 22.000 | B | tick-roll | -20.0 | Brands boxed as read; 'N brands found' counts 2 -> 14 | B 3b: 1.6-4.45 local; strip c3/b1; dur 1.5; notes (strip-checked or sustained) |
| 24.766 | B | impact-low | -13.6 | ChatGPT disc lands out of depth | B: engine moments unchanged (cut-2 strip); notes (no clear spike: 54.1 vs median 42.5) |
| 25.966 | B | impact-low -1 st | -13.0 | Gemini disc lands | B: unchanged; notes (no clear spike: 65.7 vs median 50.3) |
| 26.716 | B | impact-low +1 st | -12.0 | Perplexity disc lands | B: unchanged; notes (no clear spike: 84.6 vs median 59.5) |
| 27.100 | B | tick-roll -2 st | -25.3 | Day 1 -> 30 time-lapse counter rolls | B 3b: 7.4-8.86 local; strip c3/b2 Day 1 at 27.0, Day 30 at 28.4; dur 1.35; notes (strip-checked or sustained) |
| 28.549 | B | pill-drop -3 st | -12.0 | Four big rival chips land with weight | B 3b: 8.92 local; strip c3/b2 28.6-28.8; motion settles f856 after peak f854 (102.2) |
| 29.802 | B | chime-warm +2 st | -15.4 | Acme row tints orange, YOU chip lands | B: 10.24-10.3 local; motion peak f895 (56.8, x5.6 median) |
| 30.773 | B | whip-fast -1 st | -16.9 | B->C exit, cut-the-curve LEFT | B: exit unchanged; motion peak f924 (42.1, x11.8 median) |
| 32.416 | C | pill-drop -4 st | -12.0 | Giant numeral '1' lands solid on 'First' | C c3: 1.48 local; strip c3/c1 32.4; notes (strip-checked or sustained) |
| 34.800 | C | key-ticks +1 st | -17.0 | Composer bar types and grows per keystroke | C c3: 3.92-5.22 local; strip c3/c1 34.8-36.1; dur 1.3; notes (strip-checked or sustained) |
| 36.431 | C | click-ui | -13.0 | Navy send presses | C c3: 5.62 local; notes (strip-checked or sustained) |
| 36.916 | C | pill-drop | -13.0 | Bar deflates into row 1, rows drop with weight, squash | C c3: 5.62+; strip c3/c2 36.9-37.0; motion settles f1107 after peak f1106 (106.0) |
| 37.389 | C | pop-soft +2 st | -15.0 | Suggested chips puff in from depth | C c3: 6.42-6.9 local; strip c3/c2; motion peak f1121 (28.9, x2.7 median) |
| 39.016 | C | pill-drop +2 st | -14.4 | Chips fall into slots 1-3, rows drop three slots | C c3: 7.64-8.24 local; strip c3/c2; motion settles f1170 after peak f1164 (54.9) |
| 39.940 | C | swoosh-soft | -15.0 | Stack leaves LEFT | C c3: 8.52-9.32 local; motion peak f1199 (116.9, x5.2 median) |
| 42.269 | C | chime-warm | -11.5 | Greg: orange Acme chip and #1 on 'CEO' | C c3: 11.36 local; strip c3/c3 42.4; motion peak f1269 (18.4, x4.9 median) |
| 43.416 | C | impact-low -2 st | -13.0 | Liam: 'Not mentioned' on 'student' | C c3: 12.26 local; strip c3/c3 43.4; notes (strip-checked or sustained) |
| 46.681 | D | click-ui | -19.5 | Navy send presses | D: 0.80 local; strip c3/d1; notes (strip-checked or sustained) |
| 47.173 | D | swoosh-reverse | -16.7 | Bar shrinks into bubble, phones arrive from depth | D: 0.92-1.20 local; strip c3/d1; motion peak f1416 (44.6, x25.2 median) |
| 48.740 | D | swoosh-soft -1 st | -15.0 | Phones fan out | D: 2.74 local; motion peak f1463 (62.3, x32.8 median) |
| 49.440 | D | whip-fast | -14.0 | Camera dives onto ChatGPT | D: 3.28-3.83 local; strip c3/d1 49.4-49.6; motion peak f1484 (111.2, x14.3 median) |
| 49.716 | D | impact-low | -13.0 | 'Not mentioned' stamps in (ChatGPT) | D: 3.68 local; motion settles f1491 after peak f1486 (104.9) |
| 50.340 | D | whip-fast +1 st | -22.7 | Phone whip to Gemini (motion-blurred near phone) | D c3: 4.18-4.68 local; strip c3/d2 50.2-50.5; motion peak f1511 (81.0, x2.3 median) |
| 51.202 | D | chime-rise | -13.8 | Orange Acme CRM lands at #1 with halo | D: 5.12 local; strip c3/d2 51.2; motion peak f1537 (114.8, x4.3 median) |
| 57.469 | E | chime-warm | -12.0 | X-ray: #1 Acme CRM badge pops | E: 2.76 local; strip c3/e1 57.5; notes (strip-checked or sustained) |
| 58.906 | E | whip-fast | -14.0 | Cut-the-curve LEFT to the bank set | E: 4.30 local; strip c3/e1 59.0; motion peak f1768 (27.6, x2.7 median) |
| 61.023 | E | pop-soft | -21.9 | Phrase lands, Interest rates +1 | strip c3/e1 61.0; notes (no clear spike: 30.4 vs median 20.7) |
| 61.623 | E | pop-soft +3 st | -18.8 | Interest rates +2 | strip c3/e1 61.6; notes (no clear spike: 30.9 vs median 21.6) |
| 65.435 | E | chime-warm +2 st | -12.3 | Orange ring on 'likes', +2 grows | E: 'likes'; strip c3/e2 65.4; motion peak f1964 (39.1, x4.3 median) |
| 66.906 | E | whip-fast -1 st | -23.6 | Restaurant sweep LEFT | E: 12.27 local; strip c3/e2 67.0; motion peak f2008 (68.9, x2.4 median) |
| 67.702 | E | glass-tick +3 st | -16.0 | Restaurant ticks (Waiting / Price interleaved) | E c3: 0.115 s apart; strip c3/e2 67.4-68.2; motion peak f2032 (52.7, x1.5 median) |
| 68.886 | E | impact-low | -19.3 | Torn slip lands in the Burger slot, +2 -> +3 | E: 14.08 local; strip c3/e2 68.8-69.0; notes (strip-checked or sustained) |
| 69.640 | E | whip-fast | -15.2 | 'And fourth': board exits LEFT | E: 15.03 local; motion peak f2090 (63.9, x5.2 median) |
| 74.166 | E | impact-low +2 st | -14.0 | Answer card shatters into the source cloud | strip c3/e3 74.1-74.3; notes (strip-checked or sustained) |
| 76.489 | E | pop-soft | -14.0 | r/smallagency pill lands | strip c3/e3 76.2-76.4; motion peak f2294 (69.2, x5.1 median) |
| 78.582 | E | card-land | -15.0 | Toddler Parents Club card | strip c3/e4 78.4; motion settles f2357 after peak f2355 (46.6) |
| 82.782 | E | card-land +2 st | -15.0 | Campus Hub card | strip c3/e4 82.6; motion settles f2483 after peak f2480 (59.0) |
| 85.136 | E | pill-drop +3 st | -15.0 | Place cards dock into the destination card | E c3: docks 30.23/30.36/30.49 local; strip c3/e4; notes (strip-checked or sustained) |
| 86.140 | F | whip-fast | -19.7 | E->F exit LEFT | E: 31.10-31.40 local; motion peak f2585 (35.2, x2.8 median) |
| 88.661 | F | click-ui | -13.0 | Cursor clicks 'New pitch report' | F c3: click 2.52 local; strip c3/f1 88.8; notes (strip-checked or sustained) |
| 89.149 | F | pill-drop | -14.0 | New Litware slab lands | strip c3/f1 89.0-89.2; motion settles f2674 after peak f2668 (69.9) |
| 91.081 | F | click-ui -1 st | -19.9 | Cursor clicks 'Send link' | F: 5.04 local; strip c3/f1 91.2; notes (strip-checked or sustained) |
| 91.406 | F | send-swish | -15.0 | Report folds into the link chip, chip flies to the phone | F c3; strip c3/f1 91.3-91.6; motion peak f2743 (71.6, x3.1 median) |
| 92.473 | F | pop-soft | -14.0 | Link lands in the thread; row flips to Sent | F: 6.24 local; notes (strip-checked or sustained) |
| 94.613 | F | pop-soft +2 st | -15.0 | 'Opened just now' appears | F: 'And you only' 8.42 local; notes (no clear spike: 6.4 vs median 4.4) |
| 95.266 | F | card-land | -15.0 | Grey billing chip lands | F: 9.08 local; strip c3/f2 95.3; notes (strip-checked or sustained) |
| 96.056 | F | stamp-felt | -11.0 | 'Signed' stamps in | F: 9.82 local; strip c3/f2 96.0; notes (strip-checked or sustained) |
| 97.343 | G | riser-air | -22.8 | Riser through the orbit and zoom-through into the logo | G: impact 0.50 local; END anchor; notes (strip-checked or sustained) |
| 97.386 | G | logo-hit | -28.5 | Orbit collapses; G ring draws out of the impact | G: 0.50 local; strip c3/g1 97.4; notes (strip-checked or sustained) |
| 98.670 | G | key-ticks +2 st | -18.0 | 'Free plan' types letter by letter | G 3b: 1.80-2.30 local; dur 0.5; notes (strip-checked or sustained) |
| 100.535 | G | glass-tick +2 st | -15.0 | 'No card needed' lands | G c3: 3.76 local; strip c3/g1 100.6-100.8; motion peak f3017 (14.4, x13.6 median) |
| 101.919 | G | chime-warm | -13.0 | Orange underline sweeps | G c3: 4.82-5.37 local; strip c3/g1 102.0; notes (strip-checked or sustained) |
| 102.473 | G | pop-soft +2 st | -15.0 | Engine discs settle under the URL (1 of 3) | G c3: 5.55-6.43 local; strip c3/g1 102.4; notes (strip-checked or sustained) |
| 102.873 | G | pop-soft +5 st | -15.0 | Engine discs settle (3 of 3) | strip c3/g1 102.8; notes (strip-checked or sustained) |

Five cues were dropped because the voice rule pushed them below about −27 dBFS:
- the feed-card rise at 21.45 ("is for. It tracks");
- the feed fly-past at 24.15 ("in ChatGPT");
- the column fold at 45.20 ("answer.");
- the "Next" chime at 84.90 ("next."), where the dock pill-drop carries the beat;
- the acme.example pop at 101.35 ("card.").

They are commented in `cues3_draft.py`.

## Cut-3 measurements
- Video and loudness:
  - film-sfx-cut3.mp4 has 3154 frames, and its H.264 stream is byte-identical to film.mp4.
  - ebur128: **I −15.2 LUFS, true peak −1.7 dBTP, LRA 2.6 LU**. loudnorm pass 2 ran in linear mode, offset −0.06 dB.
- Density and mix:
  - **67 SFX, 38.2/min.**
  - Mix: impact 22 (33%), swoosh 15 (22%), chime 10 (15%), pop 8 (12%), click 6 (9%), typing 6 (9%). Impacts went up because pill drops count as impacts.
- Scene starts (±2 frames): 1/67 = 1% against the hard cut (93.6 s) and the seams.
  14/67 = 21% if the 22 cut-3 push, whip, zoom and dive transitions also count as shot
  starts (target ≤ 30 %).
- Reveals: 59/67 = 88% (snapped to a motion peak/settle or checked on a 10 fps strip). A prominent local-motion peak lies within 0.5 s for
  62/67 = 93% (target ≥ 60 %).
- Voice masking: 65 cues: 1032 voice-active 400 ms windows, min margin 6.2 dB, violations(<6 dB) 0; logo riser+hit (relaxed rule): 26 windows, min margin 3.1 dB, violations(<3 dB) 0; whole bus min margin 3.1 dB.
- SFX peaks before normalisation: median -15.0, range -28.5 to -11.0; 57/67 in -20..-12.
- Listen-proxy:
  - `png/c3/mix-full.png`
  - `png/c3/mix-094s.png`: F stamp → logo → end card, 10 cues.
  - `png/c3/mix-042s.png`: 9 cues.
  - `png/c3/mix-082s.png`: 8 cues.
  - The end-card pops and chime after the VO ends (101.3 s) are the most exposed SFX in the film, and they read
    cleanly in the spectrogram.

## Cut-3 credits
- 3 new generations, 4.9 s of audio, `character-cost` 39.
- Running total: 21 generations, cost 208.
- The balance is still unreadable, because the key lacks `user_read`.

## Cut-3 weak spots
- The logo sting is unchanged: hit −28.5 and riser −22.8 dBFS peak, capped by the 3 dB rule at the "Ack-me" onset.
- The B live feed has only the low tick-roll. Its card rise and fly-past were masked by the VO.
- The Day 1→30 tick-roll was ducked to −25.3 dBFS. It reads as texture.
- The dive-whoosh is ducked to −21.3 dBFS. It runs under "a small agency use? / And when someone asks".
- 8 cues still sit on NOTES/strip times without a clear frame-diff spike.

---

# Cut 2 sound pass (kept): Acme v2, cut 2 (ElevenLabs SFX)

Output: `film-sfx.mp4` (video stream copied bit-for-bit from `../film.mp4`, new AAC 192k audio), `sfx-bus.wav`
(the SFX bus alone, 44.1 kHz, before the final gain), `palette/` (16 sounds), `cues.json` (the brief's fields:
t_global, sound, gain_db, event, why), `work/cues-full.json` (adds notes time, measured reveal, offset, pitch, anchor
and how each cue was checked). Re-run: `.venv/bin/python build.py && ./mix.sh && .venv/bin/python verify.py && .venv/bin/python plots.py`.

## Method
- **Times.** Each cue starts from a NOTES beat (the latest cut per segment; B's cut 3 is what the render shows). It is
  then checked against the render. `work/blocks.npy` holds per-frame max block difference (12x9 grid, 192x108 grey).
  A cue snaps to the motion peak (appearances, swooshes) or to the frame where motion settles (landings, max +6
  frames) within ±0.2 s. If no clear spike stands out from the moving camera, I checked a 10 fps strip
  (`png/strip-*.png`: B count, engines and rivals; E sources and slip; F click, chip and stamp; A names; G logo) and
  set the time by hand. 8 cues kept the NOTES time with no clear spike (listed as "no clear spike" below).
- **Offsets** (exports/sound-spec.json medians): chime −31 ms, impact +16 ms, swoosh −27 ms, click −89 ms,
  pop +23 ms, typing 0. Each sound has an internal anchor: its onset for transients, its RMS peak for swooshes and
  the riser. Placement: start = reveal + offset − anchor.
- **Variation.** One sound is reused with pitch shifts (±4 semitones, resampled) and per-cue gain. Swooshes pan
  right→left (±0.35) to match the leftward current.
- **Voice masking.** The voice is estimated as narration.mp3 × 1.494. That is the least-squares fit inside
  master-audio, aligned at 0 ms lag; the stem is `../../acme-v2-audio/narration.mp3`. For every 400 ms window
  (50 ms hop) where the voice is active (window RMS ≥ voice mean − 20 dB), the SFX bus RMS must be ≤ voice RMS − 6 dB.
  build.py lowers the cue that contributes most to each failing window until no window fails. Cues pushed below
  about −27 dBFS were dropped or moved instead (see "Dropped").
- **Logo exception (coordinator, round 2).** The logo riser and logo-land hit are a brand sting under "Ack-me".
  They follow a relaxed rule: their own signal stays ≥ 3 dB under the voice in every voice-active window. Both are
  band-limited to below 300 Hz and above 6 kHz, so they stay out of the voice's mids. Their gains were raised to that
  limit in 0.5 dB steps. The other 60 cues keep their round-1 gains, frozen from `work/cues-full-v1.json`.
- **Mix.** master-audio + SFX bus → 4x-oversampled limiter at −2.5 dBFS (it only touches the few samples where an
  SFX sits on a master peak; the master alone peaks at −1.7 dBTP) → two-pass loudnorm I −15.2, TP −1.2, LRA 11.
  The second pass ran in **linear** mode (offset −0.04 dB) → 48 kHz → AAC.

## Palette (16 sounds, 18 generations, eleven_text_to_sound_v2, mp3_44100_128)
| name | dur s | influence | prompt | file | processing |
|---|---|---|---|---|---|
| `swoosh-soft` | 0.8 | 0.5 | Soft airy whoosh, gentle quick air movement passing by, clean modern UI transition, subtle, no reverb tail | palette/swoosh-soft.mp3 (cache/833d57303c709d96.mp3) | as generated |
| `whip-fast` | 0.6 | 0.5 | Fast airy whip pan swish, quick light swish of air, clean and crisp, short | palette/whip-fast.mp3 (cache/2bba12e3ef346de4.mp3) | as generated |
| `swoosh-reverse` | 0.8 | 0.5 | Soft reverse whoosh swelling up and cutting off abruptly, airy and clean, subtle | palette/swoosh-reverse.mp3 (cache/746c9d78ffaf2e5a.mp3) | as generated |
| `click-ui` | 0.7 | 0.6 | Mouse click sound effect, a single crisp clicky computer mouse button press, close up, dry, isolated | palette/click-ui.mp3 (cache/aac5f9e939383934.mp3) | first click only (0–90 ms) |
| `key-ticks` | 2.0 | 0.5 | Soft quiet laptop keyboard typing, gentle quick keystrokes, close and clean, no room noise | palette/key-ticks.mp3 (cache/09c0f525a3e56bd8.mp3) | sliced to the typing length |
| `chime-warm` | 1.2 | 0.5 | Single warm glassy bell chime, soft bright note, premium notification, short gentle decay | palette/chime-warm.mp3 (cache/93538a51a2904058.mp3) | as generated |
| `chime-rise` | 1.0 | 0.5 | Two-note rising glass chime, soft warm marimba and glass, positive success notification, short | palette/chime-rise.mp3 (cache/ba727ebb96acfa52.mp3) | as generated |
| `stamp-felt` | 0.6 | 0.5 | Felt rubber stamp pressed firmly on paper, soft dull thud, satisfying, dry | palette/stamp-felt.mp3 (cache/0310e1a59dd8260d.mp3) | 0.19–0.62 s (the thud), low-pass 2.6 kHz |
| `impact-low` | 1.0 | 0.5 | Low soft cinematic impact, deep warm muffled thump, subtle, short decay, no rumble | palette/impact-low.mp3 (cache/c28bb231f9a4716a.mp3) | as generated |
| `riser-air` | 2.0 | 0.5 | Airy shimmering riser building up smoothly, soft swelling whoosh with light sparkle, ending abruptly at peak | palette/riser-air.mp3 (cache/5f1824aa09ad3d37.mp3) | 0.30–0.95 s, atempo 0.8, 0.2 s fade-in (0.81 s, ends on the swell's peak); band-limited: <300 Hz + >6 kHz only (4th-order LP/HP, summed) |
| `logo-hit` | 2.0 | 0.5 | Satisfying premium logo reveal hit, soft deep thump with bright glassy shimmer tail, modern tech brand | palette/logo-hit.mp3 (cache/066952b898cd10d9.mp3) | high-pass 45 Hz, fade from 0.08 s over 0.5 s, 0.6 s; band-limited: <300 Hz + >6 kHz only |
| `pop-soft` | 0.5 | 0.5 | Soft subtle bubble pop, gentle UI element appearing, clean and round | palette/pop-soft.mp3 (cache/a17b30538c4f8906.mp3) | as generated |
| `send-swish` | 0.5 | 0.5 | Quick soft message sent swoosh, short airy upward swish, clean UI sound | palette/send-swish.mp3 (cache/045630c393dee43e.mp3) | as generated |
| `count-ticks` | 1.0 | 0.5 | Fast soft digital counter ticking, numbers rolling up, subtle tiny clicks | palette/count-ticks.mp3 (cache/d406935486f58ceb.mp3) | sliced to the roll length |
| `glass-tick` | 0.7 | 0.6 | A single light tap on a glass with a metal spoon, bright short ding, isolated, dry | palette/glass-tick.mp3 (cache/4ffa5b36641dc062.mp3) | as generated |
| `card-land` | 0.5 | 0.5 | Soft paper card landing on a table, gentle muted tap, dry | palette/card-land.mp3 (cache/b0d2062e20c2ccd8.mp3) | as generated |

Two first attempts came back silent (−63 dB): "Single tight crisp UI button click…" and "Tiny soft glass tap, single
bright delicate tick", both 0.5 s. They were replaced with the new prompts above. Their files stay in `cache/`
(9fcfa349…, 2d7f2628…), and the cache is keyed by a hash of the request body, so nothing is regenerated.
`png/palette-spectra.png` shows all 16.

## Cues (62)
| t_global s | seg | sound | gain dBFS peak (pre-norm) | event | source / check |
|---|---|---|---|---|---|
| 3.035 | A | chime-warm | -18.7 | Crowd dims, hero send turns orange on 'now.' | A cut2 r2: 3.24-3.26; motion peak f92 (13.0, x3.9 median) |
| 3.900 | A | key-ticks | -16.0 | Hero types 'Where to buy running shoes?' | A r3: word-synced 3.90-5.02; dur 1.1; notes (strip-checked or sustained) |
| 4.573 | A | swoosh-soft | -14.0 | Dive: hero frame falls away, wall flies past the lens | A cut2: 3.85-4.80, frame falls 4.40; motion peak f138 (18.2, x2.6 median) |
| 6.960 | A | key-ticks -1 st | -17.0 | Types 'Which CRM should a small agency use?' | A r4: 6.96-9.30; dur 2.0; notes (strip-checked or sustained) |
| 9.251 | A | click-ui -1 st | -13.0 | Send button pressed | A r3: send press 9.34; notes (strip-checked or sustained) |
| 9.473 | A | send-swish | -21.0 | Question lifts into the centred bubble | A cut2: 9.44 lift; motion peak f285 (31.1, x5.5 median) |
| 11.406 | A | swoosh-reverse | -16.0 | Answer card blooms, ChatGPT mark lands | A cut2: 11.40, mark 11.46; motion peak f343 (28.6, x4.2 median) |
| 14.286 | A | card-land | -13.0 | Northwind flies in and lands | A cut2: 14.20; strip a-names: settles 14.25-14.30; notes (strip-checked or sustained) |
| 15.916 | A | card-land +4 st | -13.0 | Tailspin lands | A cut2: 15.76; motion settles f477 after peak f474 (53.8) |
| 16.469 | A | chime-warm | -11.0 | Orange slot opens on 'five' | A beats: 16.68; motion peak f495 (56.4, x8.8 median) |
| 20.802 | B | chime-rise | -17.6 | Acme arrow swings in and locks (mid-film logo) | B: arrow 0.88-1.22 local; motion settles f625 after peak f623 (22.7) |
| 22.120 | B | count-ticks | -19.0 | Visibility number counts 0 -> 41% | strip b-count: 22.1-22.9; dur 0.8; notes (strip-checked or sustained) |
| 24.766 | B | impact-low | -13.6 | ChatGPT disc lands out of depth | strip b-engines: full at 24.8; notes (no clear spike: 52.8 vs median 35.4) |
| 25.966 | B | impact-low -1 st | -13.0 | Gemini disc lands | strip b-engines: 26.0; notes (no clear spike: 65.4 vs median 51.6) |
| 26.716 | B | impact-low +1 st | -12.0 | Perplexity disc lands | strip b-engines: 26.6; notes (no clear spike: 86.7 vs median 60.8) |
| 28.382 | B | card-land -2 st | -12.0 | Four rivals land with weight | strip b-rivals: 28.5-28.7; motion settles f851 after peak f849 (88.3) |
| 29.640 | B | swoosh-soft +1 st | -16.0 | Cast flies into the kf04 table | B cut3: 9.8-10.3 local; motion peak f890 (44.5, x5.1 median) |
| 29.769 | B | chime-warm +2 st | -14.3 | Acme row tints orange, YOU chip lands | B: 10.24-10.3 local; motion peak f894 (45.7, x6.3 median) |
| 30.773 | B | whip-fast -1 st | -16.9 | B->C exit, cut-the-curve LEFT | B: 10.93-11.23 local; spike f925; motion peak f924 (42.0, x14.6 median) |
| 34.371 | C | click-ui | -16.1 | Add prompt pressed, dialog opens | C: 3.56 local; notes (strip-checked or sustained) |
| 34.920 | C | key-ticks +1 st | -17.0 | 'Simplest CRM for a 3-person team?' types in | C: 4.02-5.27 local; dur 1.25; notes (strip-checked or sustained) |
| 36.431 | C | click-ui +1 st | -13.0 | Add pressed, typed line flies into row 1 | C: 5.62 local; notes (strip-checked or sustained) |
| 37.116 | C | card-land | -14.0 | New row lands, count 4 -> 5 | C: 6.10 local; spike f1110; motion settles f1113 after peak f1110 (41.5) |
| 39.082 | C | card-land +2 st | -15.4 | Suggested prompts fly into rows 1-3 | C: spike f1163; motion settles f1172 after peak f1168 (37.2) |
| 39.740 | C | swoosh-soft | -15.0 | Table exits LEFT, bubble rises to centre | C: 8.52-9.41 local; spike f1193; motion peak f1193 (99.6, x5.2 median) |
| 40.623 | C | pop-soft +2 st | -14.0 | Greg / Nadia / Liam land | C: 9.70-9.84 local; notes (no clear spike: 19.9 vs median 13.7) |
| 42.069 | C | chime-warm | -11.0 | Greg's list lands: Acme CRM #1 in orange | C: 11.40 local; motion peak f1263 (6.9, x1.6 median) |
| 43.496 | C | impact-low -2 st | -13.0 | 'Not mentioned' for Liam | C: 12.58 local; notes (no clear spike: 5.8 vs median 4.5) |
| 46.681 | D | click-ui | -18.9 | Send presses on the prompt bar | D: 0.80 local; notes (strip-checked or sustained) |
| 47.206 | D | swoosh-reverse | -16.0 | Bar shrinks into bubble, phones arrive from depth | D: 0.92-1.20 local; spike f1415; motion peak f1417 (42.9, x29.0 median) |
| 48.740 | D | swoosh-soft -1 st | -15.0 | Phones fan out to kf06 | D cut2: 2.74 local; spike f1463; motion peak f1463 (48.2, x24.5 median) |
| 49.540 | D | whip-fast | -14.0 | Camera dives onto ChatGPT | D cut2: 3.28-3.83 local; spike f1485; motion peak f1487 (90.5, x14.4 median) |
| 49.716 | D | impact-low | -13.0 | 'Not mentioned' stamps in (ChatGPT) | D cut2: 3.68 local; motion settles f1491 after peak f1487 (90.5) |
| 50.406 | D | whip-fast +1 st | -22.6 | Whip-pan to Gemini | D cut2: 4.18-4.68 local; spike f1512; motion peak f1513 (71.5, x1.7 median) |
| 51.102 | D | chime-rise | -13.5 | Orange Acme CRM lands at #1 with halo | D cut2: 5.12 local; motion peak f1534 (113.9, x4.5 median) |
| 57.499 | E | chime-warm | -12.0 | X-ray: #1 Acme CRM badge pops (orange) | E: 2.76 local; notes (no clear spike: 11.7 vs median 9.5) |
| 58.906 | E | whip-fast | -14.0 | Cut-the-curve LEFT to the bank set | E cut2: 4.30 local; spike f1775; motion peak f1768 (27.3, x2.6 median) |
| 60.656 | E | pop-soft | -14.0 | Phrase flight lands, counter punches ('talks') | E cut2: 5.71 local; motion peak f1819 (28.5, x1.8 median) |
| 61.583 | E | pop-soft +4 st | -18.6 | Flight lands ('topic') | E cut2: 6.79 local; notes (no clear spike: 30.9 vs median 21.5) |
| 65.435 | E | chime-warm +2 st | -12.3 | Orange ring on 'likes', +2 grows | E cut2: 'likes'; motion peak f1964 (39.1, x4.3 median) |
| 66.906 | E | whip-fast -1 st | -23.6 | Restaurant sweep LEFT | E cut2: 12.27 local; spike f2013; motion peak f2008 (68.0, x2.8 median) |
| 68.886 | E | impact-low | -19.3 | Torn slip lands in the Burger slot | E cut2: 14.08 local; strip e-slip: slot fills 68.85-68.9; notes (strip-checked or sustained) |
| 69.673 | E | whip-fast | -15.2 | 'And fourth': board exits LEFT | E: 15.03 local; spike f2092; motion peak f2091 (63.4, x5.1 median) |
| 74.116 | E | impact-low +2 st | -14.0 | Answer card shatters into the source cloud | strip e-sources: 74.1-74.2; notes (strip-checked or sustained) |
| 76.489 | E | pop-soft | -14.0 | r/smallagency pill lands on 'Reddit' | E: pill 21.63 local; strip 76.2; motion peak f2294 (69.1, x22.9 median) |
| 83.735 | E | chime-warm | -12.0 | kf08 stack: orange rings | E: 29.21 local; motion peak f2513 (29.8, x5.4 median) |
| 84.702 | E | chime-rise +2 st | -12.0 | Orange arrow draws, 'Next' lands | E: 30.09 local; motion peak f2542 (4.6, x1.8 median) |
| 86.040 | E | whip-fast | -19.8 | E->F exit LEFT | E: 31.10-31.40 local; spike f2583; motion peak f2582 (30.3, x9.2 median) |
| 88.661 | F | click-ui | -13.0 | Cursor clicks 'New pitch report' | strip f-click: 88.75; notes (strip-checked or sustained) |
| 89.800 | F | count-ticks +1 st | -20.0 | Report builds, 0 -> 38% counts | strip f-click: 89.8+; dur 0.7; notes (strip-checked or sustained) |
| 91.081 | F | click-ui -1 st | -19.9 | Cursor clicks 'Send link' | F: 5.04 local; notes (strip-checked or sustained) |
| 91.406 | F | send-swish | -15.0 | Report folds into the link chip | F: 5.04+ local; motion peak f2743 (62.6, x3.2 median) |
| 91.806 | F | swoosh-soft | -17.0 | Prospect's phone arrives from the right | F: 5.36-6.08 local; spike f2752; motion peak f2755 (59.1, x2.1 median) |
| 92.573 | F | pop-soft | -14.0 | Link chip lands in the phone, row flips to Sent | F: 6.24-6.66 local; strip f-chip: Sent flip 92.55; notes (strip-checked or sustained) |
| 93.719 | F | glass-tick +1 st | -15.0 | Link cell fills '.../share/k7q2' | F cut2: 7.58 local; notes (strip-checked or sustained) |
| 95.266 | F | card-land | -15.0 | 'Billing starts on sign' chip lands | F cut2: 9.08 local; notes (no clear spike: 6.3 vs median 4.7) |
| 96.056 | F | stamp-felt | -11.0 | 'Signed' stamps in | F cut2: 9.82 local; strip f-stamp: stamp 96.0, settled 96.1; notes (strip-checked or sustained) |
| 97.343 | G | riser-air | -22.8 | Riser through the orbit gather and zoom-through into the logo | F 9.55-10.70 + G collapse; END anchor 97.40; notes (strip-checked or sustained) |
| 97.386 | G | logo-hit | -28.5 | Orbit collapses into the arrow tip; Acme G ring draws out of the impact | G: impact 0.50 local = 97.37; strip g-logo: 97.4, mark complete 97.6; sits in the voice gap 96.85-97.45; notes (strip-checked or sustained) |
| 98.889 | G | pop-soft | -15.0 | 'Free plan' lands | G: 1.96 local; motion peak f2966 (10.8, x107.8 median) |
| 100.002 | G | glass-tick +2 st | -15.0 | 'No card needed' lands | G: ~3.3 local; motion peak f3001 (23.1, x230.7 median) |
| 100.835 | G | chime-warm | -13.0 | Orange underline under acme.example | G: 4.20-4.60 local; motion peak f3026 (4.6, x23.7 median) |


### Dropped (masking or density)
- Masked: they fell under −27 dBFS after the voice rule. These were the monogram whip 23.97 (on "in ChatGPT"), the
  Perplexity push swoosh 52.10, the burger chime 68.95 (the impact carries it), the Toddler camera swoosh 77.32 and
  the Parent and Campus pills (77.60, 80.82), which land on the words.
- Density (to stay under 40/min): 2nd hero send, the Where-to-eat swap, Contoso and Fabrikam, Rank #2, the B
  pull-back, step "1", Track clicks, Nadia, Gemini "Not mentioned", the phone-to-card landing, #2 badge, the 2nd
  flight pop, restaurant flights, Sources pills, 2 cluster cards, the cluster swoosh, Litware typing and billing
  orange. The exact lines are commented in `cues_draft.py`.

## Measurements (verify.py, `work/verify.json`)
- Frames: film-sfx.mp4 has 3154 video frames. The H.264 stream is byte-identical to film.mp4 (`cmp` of the
  extracted streams). Duration 105.133 s.
- Loudness (ebur128 on film-sfx.mp4): **I −15.2 LUFS, true peak −1.9 dBTP, LRA 2.7 LU** (master alone: −15.5 LUFS,
  −1.7 dBTP).
- SFX: **62 cues, 35.4/min** (corpus median 38, range 13–57). Mix: swoosh 17 (27%), impact 15 (24%), chime 13 (21%), click 6 (10%), pop 6 (10%), typing 5 (8%).
  The corpus shares (swoosh 14 %, impact 11 %, chime 11 %, click 2 %) include music hits and "unsure". Among labelled
  SFX the ratio swoosh : impact : chime = 17 : 15 : 13 here, against 14 : 11 : 11 in the corpus.
- At scene start (±2 frames): 0/62 = 0% against the hard cut (scdet: 93.6 s) and the 7 segment
  seams. Counting declared push, whip and zoom transitions as shot starts too: 9/62 = 15%
  (target ≤ 30 %).
- On reveals: 54/62 = 87% (snapped to a motion peak/settle or checked on a 10 fps strip). A code check finds a prominent local-motion peak within 0.5 s for
  61/62 = 98%. This check is lenient because the camera always moves. Target ≥ 60 %.
- Voice masking: 60 cues: 990 voice-active 400 ms windows, min margin 6.0 dB, violations(<6 dB) 0; logo riser+hit (relaxed rule): 26 windows, min margin 3.1 dB, violations(<3 dB) 0; whole bus min margin 3.1 dB.
- SFX peaks before normalisation: median -15.0, range -28.5 to -11.0; 54/62 in -20..-12. The final gain is −0.04 dB.
- Listen-proxy: `png/mix-full.png` and the 3 busiest 10 s windows: `png/mix-091s.png` (12 cues),
  `png/mix-042s.png` (9) and `png/mix-029s.png` (8). Each shows the waveform with cue markers, voice and SFX-bus RMS,
  and a spectrogram. The SFX envelope sits under the voice everywhere. Transients show as narrow vertical bands in
  the voice gaps; nothing smears across words.

## Credits
- Generated: 18 calls, 16.9 s of audio. The summed `character-cost` response headers come to **169**. The docs
  price this at 40 credits/s, which would be ≈ 676; this is unverified, see FACTS.md.
- Balance: unknown. `GET /v1/user/subscription` returns 401 because the key lacks `user_read`.

## Weak spots
- **Logo sting (round 2).** It is now band-limited and sits 3.1 dB under the voice at its closest. Riser peak
  −22.8 dBFS, was −25.5. Hit peak −28.5 dBFS, was −27.8; its peak is lower than before because only the sub-300 Hz
  and air bands remain. In-band it stands well clear of the bed. At 97.40 s the hit's low band is 17 dB above the
  master's below-300 Hz energy (−31 vs −48 dB, 100 ms RMS). Over 97.0–97.3 s the riser's air is 18–25 dB above the
  master's content above 6 kHz. The binding window is 97.15–97.55 s, where the hit's attack meets the first syllable
  of "Ack-me". A louder hit would need a margin under 3 dB, or the word moved.
- With a near-continuous VO, most cues land between words. The typing ticks and count ticks are mixed low
  (−16 to −20 dBFS peaks, RMS about −45). Expect them to read as texture.
- 8 cues rely on NOTES times without a clear frame-diff spike: the three B engine discs, C pop and "Not mentioned",
  E #1 badge and 3rd pop, and F billing chip. The engine discs were checked on a strip.
- No human listening was done; the evidence is the plots above.
