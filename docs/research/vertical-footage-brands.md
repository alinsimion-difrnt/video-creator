# Research: vertical (TikTok/Reels/Shorts), presenter footage, more brands

- **Date:** 2026-10-09. Research only; no code changed.
- **Asked by Robert:** (1) the TikTok editing rules, especially where elements can and cannot go under the
  app's overlays; (2) what we need for future work: more brands (acme.example first), filmed footage of
  Robert, and TikTok-style videos.
- **Sources (full detail, URL, date and confidence for every claim):**
  - `sources/vertical-safe-zones-and-specs.md`: safe zones measured from the official TikTok and YouTube overlay
    files, Meta's percentages, and specs for all three platforms.
  - `sources/short-form-editing-craft.md`: hooks, pacing, captions, overlays, audio, filming, platform policy.
  - `sources/presenter-footage-pipeline.md`: local tools for transcription, cut finding, conforming, face
    framing and compositing; proposed stages and an EDL shape.
  - `sources/brands-and-formats-audit.md`: what in our code is Acme-only or 16:9-only (file:line), brand
    capture tools, font licences, a brand intake checklist.
- Labels used below: **official** = platform page or file; **measured** = we measured an official file;
  **practice** = practitioner or tool default (folklore until our corpus measures it).

---

## 1. Where things can go on a 1080x1920 vertical frame

### 1.1 What the platforms publish
- **None of the three platforms publishes organic safe-zone numbers as text.** TikTok and YouTube publish
  overlay images for ads; Meta publishes percentages for Reels ads.
- **Most numbers on the web are wrong at 1080x1920.** The common "150 top / 440 bottom / 120 right" figures come
  from TikTok's own templates, which are drawn at 720x1280 or 540x960. Guides copy those labels onto a 1080
  canvas without scaling them.

| Source (scaled to 1080x1920) | Top | Bottom | Left | Right | Status |
|---|---|---|---|---|---|
| TikTok in-feed, standard template | 240 | 660 | 120 (may be cropped by the device) | 120, plus the action rail x 780–960 from y 840 down | official file, measured |
| TikTok in-feed with a product anchor (Shop), 1–4 caption lines | 252 | 812 / 879 / 946 / 1014 (about 67 px per line) | 120 | everything at x ≥ 840 blocked from y 360 down | official file, measured |
| Instagram Reels ads ("14% top, 35% bottom, 6% sides") | 269 | 672 (768 with disclaimers) | 65 | 65 | official text |
| YouTube vertical ads overlay | 288 | 672 | 48 | 192 | official file, measured |

- **TikTok's two templates disagree** on where the right-hand rail starts (y 840 vs y 360). In TikTok's own
  mock-up the avatar sits at about y 579, so the safe reading is: **nothing important at x > 840 below y ≈ 360**.
- **Tall phones:** TikTok marks 11.1% per side as "may be cropped based on device type"; that covers phones up to
  about 20.6:9. Meta says officially that on screens taller than 9:16 it may zoom (crop) or letterbox.
- **Not published anywhere:** how much the expanded "...more" description covers, the comment sheet, TikTok
  Shop video overlays, guides in the TikTok editor, and any loudness target.

### 1.2 Our house profile (proposed): one layout that is safe on all three

```
x:  0   120              450        780  888 960 1080
y:0 +-----------------------------------------------+
    |           top UI (tabs, search, LIVE)          |
288 +---+-------------------------------+------+----+
    |   |                               |upper |    |  <- x 780–888 usable only above y 840
    | c |      CORE: x 120–780          | ext. | c  |     (not when TikTok Shop anchors are used)
    | r |           y 288–1248          +------+ r  |
840 | o |      (660 x 960)              | rail | o  |
    | p |      centre of core = x 450   | (like| p  |
    |   |                               | etc.)|    |
1248+---+-------------------------------+------+----+
    |  caption / username / sound / CTA / nav bar    |
1920+-----------------------------------------------+
```

- **Core: x 120–780, y 288–1248 (660x960 px).** All text, UI, numbers, logos and the face's eyes and mouth go here.
  This is the overlap of TikTok's standard template, Meta's percentages and YouTube's overlay.
- **Upper extension: x 120–888, y 288–840.** Usable for wide headlines at the top. Not with TikTok Shop anchors.
- **Centre of the core is x ≈ 450, not 540.** Centred titles either centre on 450, or stay above y 840 with
  lines no wider than 840 px.
- **Backgrounds, B-roll and decorative motion can run full-bleed.** Only critical content needs the zone.
- **Burned-in captions: y ≈ 900–1150** (inside the core, above the description). Viewers who turn on TikTok's own
  closed captions get a second caption layer lower down; keeping ours higher avoids a clash.
- **Ads with long captions:** move the bottom up to y ≈ 1108 (1 line) … 906 (4 lines).
- **Cover frame:** keep the cover title inside **y 420–1500, x 120–960** so it survives Instagram's 1:1, 4:5 and
  3:4 grid crops.
- **Must not be committed:** the official overlay PNGs are third-party images. The numbers above go into
  `config/lens.yaml` as a frame profile, with `source:` notes (rule: thresholds live in config).

### 1.3 Render settings for vertical (official specs, combined)
- 1080x1920, 30 fps (60 for fast UI motion; TikTok accepts 23–60), H.264 High, yuv420p, BT.709 limited range,
  `+faststart`, no edit lists, VBR about 8–12 Mbps, AAC-LC 48 kHz stereo at 192–384 kbps.
- **Loudness:** no platform publishes a target. Keep the house convention (about −14 LUFS, −1 dBTP), labelled as
  a house value.
- **Length:** TikTok lets every creator post 3 minutes (some get 5 or 10); Shorts and Reels allow up to 3 minutes.
- **Always SDR.** HDR inputs switch the HyperFrames render to HDR10 (see §3).

---

## 2. How short-form is edited (craft)

### 2.1 What TikTok itself says (official)
- Hook within the first 6 s, and the main point (the "proposition") within the first 3 s.
- On-screen text at "5–10 words per second" (fast; it means short bursts, not paragraphs).
- 9:16, 720p or better, sound on, "save space on screen for the TikTok UI".
- Six "Creative Codes": TikTok-first, trends, production-principled, structure (hook, body, close),
  stimulation, sound.
- That is all the platforms publish. **Every other number on the web is practice, not measured.**

### 2.2 Practice numbers (starting values only; our corpus should measure them)
| Topic | Practice value |
|---|---|
| Punch-ins on a talking head | 115–125%, alternated on consecutive cuts to hide jump cuts |
| Something new on screen | every 1–2 sentences (a few seconds) |
| Silence removal | auto-editor default threshold 4%, keeps 0.2 s each side; Descript example shortens gaps over 750 ms to 200 ms |
| Captions | 2–4 words per group, word-by-word highlight, bold sans, key word in an accent colour, about 60–75 px on a 1080-wide frame, 3–4 px stroke, centre band (around the chin) |
| Speaking rate | 150–180 wpm (subtitle reading limit about 160–180) |
| Music under the voice | 12–18 dB lower |
| Length | data: videos over 60 s got about 43% more reach in Buffer's 1.1M-video study (correlation; only 12% of posts are that long) |

### 2.3 What works for a SaaS or founder video
- Talking head with keyword pop-ups, real UI cards floating in, number counters and arrows. Split screen (product
  on top, face below). The "green screen" look (presenter in front of a page). A face bubble (PiP) over product
  footage.
- **For our HTML compositions, lay each scene out again at 1080x1920 instead of cropping a 16:9 render.**
  Cropping cuts through lower thirds and UI.
- Loop endings help, especially on YouTube, which now counts every replay as a view.

### 2.4 Policy (official; matters for business accounts)
- **AI label (TikTok Community Guidelines, effective 24 Sep 2026):** required for realistic AI people or scenes,
  and for AI audio that imitates a real person's voice.
  - Our code-made motion graphics and a stock ElevenLabs voice need **no** label.
  - **A clone of Robert's own voice does need the label.**
  - Fake-looking "ChatGPT answer" screens risk the "misleading content" rule. Keep the "Example data" label,
    or use real captures.
- **Music:** sounds from TikTok's Commercial Music Library are licensed for TikTok only; reposting them on other
  platforms is not allowed. Our renders carry our own original or multi-platform-licensed music. YouTube may block
  Shorts over 1 minute with a Content ID claim (YouTube's two help pages disagree; check before using licensed
  music).
- **Commercial disclosure:** for his own products, Robert turns on "Disclose commercial content" → "Your brand".
- **Reposts:** TikTok and Instagram demote videos that carry another app's watermark. Always cross-post from our
  clean export, never from a downloaded TikTok.

### 2.5 What our pipeline should measure instead of trusting practice numbers
On a small vertical reference corpus (10–20 premium SaaS or founder clips): cuts and visual changes per minute,
punch-in scale, gaps between phrases after editing, filler rate, wpm, caption style (words per group, size, y
band, highlight, onset vs word), safe-zone violations, hook anatomy (first 3 s), SFX density, music-to-voice
dB, and how the loop closes. Accounts named by the research to study are listed in
`sources/short-form-editing-craft.md` §8; Robert picks which to add.

---

## 3. Filmed footage of Robert

### 3.1 Five findings that change the plan
1. **HyperFrames already ships talking-head skills.** `talking-head-recut` has overlay, PiP, split and stack
   layouts; `embedded-captions` does captions. Both play the clip uncut, so cutting, the edit list and the
   word clock are ours to build. The layouts are a ready reference (Apache-2.0).
2. **CrisperWhisper (the model that keeps "um/uh") has non-commercial weights.** It is ruled out for client
   work. Fillers are found in code instead: speech the voice detector hears but no aligned word covers.
3. **iPhone HDR footage switches the HyperFrames render to HDR10** unless `--sdr` is passed. Convert to SDR at
   ingest; better, film in SDR.
4. **The HyperFrames render pulls video frames with FFmpeg at source resolution.** A 4K clip in a 400 px bubble
   still decodes 4K. Feed it pre-scaled 1080p plates per layout.
5. **Homebrew `ffmpeg` has no zscale or libplacebo** (needed for HDR→SDR); `ffmpeg-full` has both.

### 3.2 Recommended local tool stack (all free and local; licences verified)
| Job | Tool | Licence |
|---|---|---|
| Transcript and word times | WhisperX 3.8.6 (faster-whisper + wav2vec2 alignment; English and Romanian alignment models) | BSD-2 / Apache-2.0 |
| Benchmark on the Mac | Parakeet TDT 0.6B v3 via `parakeet-mlx` | CC-BY-4.0 / Apache-2.0 |
| Voice activity | Silero VAD 6.2.3 | MIT |
| Silence pass | ffmpeg `silencedetect`; auto-editor as reference only | — / Unlicense |
| Conform, HDR→SDR | `ffmpeg-full` 9.0.2 (zscale + tonemap) | GPL build, used as a CLI |
| Noise, de-ess, loudness | ffmpeg `arnndn` (RNNoise) or DeepFilterNet, `deesser`, `loudnorm` two-pass | BSD-3 / MIT-Apache |
| Face box for crops | OpenCV YuNet (OpenCV is already a dependency) | MIT |
| Smooth crop path | our own code (dead zone + damped follow) | — |
| Hand-off to an editor | OpenTimelineIO 0.18.1 (`.otio` for Resolve; FCPXML/EDL adapters) | Apache-2.0 |
| Background removal (later, optional) | `hyperframes remove-background` (transparent WebM) | Apache-2.0 |

- **Avoid (GPL-3.0, would infect our code):** whisper-timestamped, praat-parselmouth, pedalboard, RobustVideoMatting.
- **Outside the current rule:** ElevenLabs Scribe (speech to text) and Voice Isolator. Robert decides; it needs his
  CLAUDE.md edit plus an ADR, as with SFX.
- Brand names are fixed with `initial_prompt`/hotwords plus a spelling list applied in code. Words containing
  digits get no alignment time and need interpolated times.

### 3.3 Proposed stages (replace C4 voice when the voice is Robert's own)
| Stage | Writes | Notes |
|---|---|---|
| F1 ingest footage | `data/create/{p}/footage/**` | probe, 30 fps CFR master, SDR Rec.709, proxy, external mic sync by cross-correlation |
| F2 transcript | `projects/{p}/transcript.json` | aligned words, VAD, unaccounted speech (filler candidates) |
| F3 cut proposals | `projects/{p}/cuts.json` | silences, fillers, false starts, retakes; **human gate: Robert approves** |
| F4 edit list | `projects/{p}/edl.json` (+ `.otio` in data/) | integer frames, separate audio/video in-outs, J/L offsets |
| F5 presenter timeline | `projects/{p}/timeline.json` | same schema as C5; words remapped onto the edited clock |
| F6 reframe | `data/create/{p}/plates/**` | crop paths and pre-scaled plates per layout and frame |

- New archetypes: `presenter_full`, `presenter_punch`, `presenter_pip`, `presenter_split`, `presenter_lower_third`.
  The corpus already has `presenter_to_camera` and the `footage_with_ui_overlay` pattern.
- **Cut defaults (practice; go into config):** keep 80–150 ms before a word and 120–250 ms after; 10–20 ms
  audio crossfades; J/L cuts only at layout switches; alternate a 112–120% punch-in on consecutive cuts.
- **Retakes:** if there is a script, align the transcript to it and keep the last complete take. Without a
  script, look for repeated 3+ word phrases whose first copy ends in a cut-off word. A clap or cue word marks a retake.
- **Compositing:** one `<video>` per kept segment (`data-media-start`, `data-start`, `data-duration`); animate a
  wrapper div for the bubble and punch-ins; all clips muted, with one cleaned voice track built from the edit list.
- The EDL JSON shape is in `sources/presenter-footage-pipeline.md` §7.1.

### 3.4 Filming guide for Robert (one recording → 16:9 and 9:16)
- **Camera:** 4K landscape at a locked 30 fps; **HDR Video off**; lock exposure, focus and white balance. The free
  Blackmagic Camera app makes this easy on iPhone.
- **Why 4K landscape:** the 9:16 crop is 1215x2160, scaled down to 1080x1920, so there is no upscaling; it even
  leaves room for a ~112% punch-in. From 1080p the vertical crop would be upscaled 1.78× and soft. If a video is
  vertical-only with big punch-ins, shoot 4K vertical instead.
- **Framing:** keep your head inside the central ~60% of the width (so the vertical crop can follow you), eyes
  about a third from the top. For 16:9, sit on one third and leave the other side clear for product cards.
- **Sound:** lav or close mic at 48 kHz/24-bit, record 10 s of room silence, clap at the start of each take.
- **Retakes:** say a cue word ("again") before a retake and pause about 1 s between sentences. The cut finder
  does the rest.

---

## 4. More brands (acme.example first)

### 4.1 What blocks a second brand today (detail with file:line in the audit)
- **One brand folder per project** (`projects/<p>/brand/`); the brief has no `brand:` field, and `product`
  doesn't fit a person.
- **Token code shaped like Acme:**
  - a `video1920` type key;
  - exactly two font families, from Google Fonts only, at weights 400–700;
  - logo variants named `main/on_navy/navy`.
- **Acme rules in global config:** accent tint, em-dash ban, one voice, required glyphs without Romanian
  ă â î ș ț, and `lang="en"`.
- **Acme copy in templates:** "AI suggested", "Asked as", "Your brand", "Example data".
- **The learnings write Acme taste as house rules:** white and orange, the Inter 600 navy caption pill, the
  Acme CRM cast.
- **The premium film kit is still in R2, not in `create/`.**

### 4.2 Recommended structure
```
brands/acme/
  brand.yaml    identity, spoken name, handles, languages, voice, copy rules, accent meaning, data cast
  tokens.json   raw palette and scales (DTCG 2025.10 format)
  video.yaml    colour roles, contrast pairs, fonts + sources, per-frame (landscape/vertical) type scale,
                safe insets, caption style, lower third, logo sizes, motion personality
  DESIGN.md  FONTS.md  REVIEW.md  logo/*.svg
projects/<p>/brief.yaml   brand: acme
                          deliverables: [{destination: tiktok, frame: vertical, length: ...}, ...]
```
- The brand is a read-only external input in `lens/stages.py` (`brands/{brand}/**`). No stage writes there, so
  the guard hook blocks brand edits during stage runs, and brand changes go through normal PRs.
- Acme moves to `brands/acme/` in the same change.
- **Needs Robert:** an edit to the logo-exception line in `CLAUDE.md` (it names `projects/*/brand/logo/`), plus an ADR.

### 4.3 acme.example, read from the live site's CSS (to confirm with Robert)
- **Fonts:** Geist and Geist Mono, OFL 1.1, on Google Fonts, so no licence problem. Geist covers ș ț ă î â ≈ →
  but has **no ✓**, so it needs a fallback (same issue as Space Grotesk).
- **Colours:** ink #0A0A0A, paper #FFFFFF, **cobalt #A70056** (7.56:1 on white), cobalt-soft #FFE4F0, greys, and
  "prism" lav/mint/sky accents.
- **Radii:** 6 px and 8 px.
- **Spelling:** the site title uses "vîja", so Romanian glyph checks matter.

### 4.4 Capturing a brand fast
- **Capture tools:** `hyperframes capture <url> --skip-vision` writes tokens, fonts, colours, SVGs and design styles;
  without `--skip-vision` it calls a paid captioning service. Dembrandt (MIT) adds `--dtcg`, `--wcag` and
  `--design-md`. Both must run on Robert's Mac, because the sandbox browser fails on the proxy.
- **Outputs are drafts.** They stay in `data/`, and a human-checked `video.yaml` is still the source of truth.

### 4.5 Fonts: what to check for any new brand
- **Google Fonts / OFL:** fine.
- **Adobe Fonts:** not usable as built. Our bundle copies font files, and Adobe's terms forbid that.
- **Monotype/MyFonts desktop licences:** usually need a video/broadcast extension; check per foundry.
- The audit has a 7-question checklist.

### 4.6 Legibility on phones (derived; no official spec)
- At 1080x1920, nothing readable under about 30 px; labels at least 44 px; captions 56–72 px. Our 16:9
  minimum (24 px) is too small for vertical.
- WCAG 2.2 AA stays the contrast gate. APCA is for information only (beta, restrictive licence).

### 4.7 Brand intake checklist
14 steps, 8 of them Robert's answers. The answers that are Robert's to give:
- identity and spoken name;
- logo SVGs;
- font licences (if not OFL);
- what the accent colour means;
- motion taste;
- voice (own, clone or stock);
- personal furniture (lower third, end card, cover, footage yes/no);
- destinations.

The full list is in `sources/brands-and-formats-audit.md` §C1.

---

## 5. Roadmap: one milestone per branch/PR

| # | Milestone | Effort | Unlocks |
|---|---|---|---|
| M-A | ADR + Robert's CLAUDE.md edit: `brands/<brand>/`, logo exception moves to `brands/*/logo/` | S | everything below |
| M-B | Brand lookup from the brief; move Acme to `brands/acme/`; generalise C3 (DTCG, any number of fonts with sources, semantic logo names, brand-level rules, `lang`) | M | a second brand |
| M-C | Frame profiles in config (`landscape`, `vertical` with the §1.2 safe zone and type minimums) + `tiktok`, `instagram_reels`, `youtube_shorts` destinations; **done (ADR 0023)**, the frame comes from the destination | M | vertical |
| M-D | Bring the v2 film kit (camera rig, captions, edge audit, assemble) from R2 into `create/kit/`, driven by brand and frame. The edge audit checks the safe zone | L | premium output for any brand and frame |
| M-E | acme brand intake (Robert's answers + capture on the Mac) and a first short 16:9 video | M | proof of brand switching |
| M-F | Footage F1–F6 + presenter archetypes + filming guide; first test clip from Robert | L | filmed videos |
| M-G | Vertical reference corpus (10–20 clips Robert picks) so pacing and captions are measured, not guessed; vertical caption style; first TikTok | M | measured vertical targets |

Order: M-A → M-B → M-C → M-D, then M-E, M-F and M-G in any order. M-A to M-C are small enough to start now; M-D
is what keeps the Acme v2 quality.

## 6. Robert's decisions (2026-10-09, ADR 0022)
1. **Code changes approved**, including the `brands/<brand>/` move (done: Acme is in `brands/acme/`, briefs
   name their brand). The CLAUDE.md lines are written out in ADR 0022 for Robert to apply.
2. **ElevenLabs speech-to-text: yes**, for transcripts and captions of his footage. Local WhisperX stays the
   fallback. The API facts still need checking against ElevenLabs' docs before F2 uses it.
3. **Voice: his own recorded voice** (no clone, so no TikTok AI label for the voice).
4. **Language: any**, set per video.
5. **Recording: phone, with or without an external mic.** F1 must work with phone audio alone; mic sync is optional.
6. **Edits only in this pipeline.** No NLE export; cut proposals are approved in the pipeline.
7. **TikTok reference accounts: our choice.** Use the list in `sources/short-form-editing-craft.md` §8; clips are
   fetched on Robert's machine (`scripts/fetch_batch.py`).
8. **acme.example palette: Robert sends it later.** Until then the values in §4.3 are only what the live CSS shows.
