# Research: the craft of high-performing TikTok / Reels / Shorts editing (B2B SaaS, founders, tech educators)

Prepared 2026-10-09 for the explainer-video-creator pipeline (Acme.ai, acme.example). Web research only.

## How to read this

Each claim carries:
- **Source type**: `OFFICIAL` (platform's own docs/policy), `TOOL-DOC` (a vendor documenting its own product), `DATA` (a study with a stated sample), or `PRACTITIONER` (editor, agency or vendor blog giving advice).
- **Confidence**: H / M / L.
- **Flag**: `MEASURED` (comes from a dataset), `RULE` (official policy text), `FOLKLORE` (repeated advice without data behind it).

**The main finding:** official platform guidance has almost **no editing numbers**. TikTok gives two: a 5–10 words/second text pace and hook timing (3 s / 6 s). Every common number for cuts per second, punch-in percentage, silence thresholds, caption pixel size, SFX density or music level comes from practitioners or tools, and none of it is measured. Our `lens` pipeline measures these things, so it can produce better numbers than the web has. Measure the corpus; don't copy the folklore. (Section 10 lists what to measure.)

How I verified things: TikTok's policy pages render with JavaScript, so I fetched the server-rendered HTML with curl and decoded it. The quotes from the TikTok Community Guidelines (2026-H2), Branded Content Policy (Aug 2026), CML Terms and Creative Codes are verbatim from TikTok's own pages. They are not taken from secondary coverage.

---

## 1. Structure: hook, retention, payoff, loop, CTA

| # | Claim | Source | Type | Date | Conf. | Flag |
|---|---|---|---|---|---|---|
| 1.1 | "Prioritize your hook in the first 6 seconds" (engagement, watch time). "Introduce your content proposition in the first 3 seconds" (recall, awareness). | https://ads.tiktok.com/help/article/creative-best-practices | OFFICIAL (ads) | updated Jun 2025 | H | RULE / guidance |
| 1.2 | Structure is **hook, body, close**. "The hook grabs attention with a technique like suspense, surprise or emotion. The body conveys your brand message. The close anchors the ad with a strong CTA." | https://ads.tiktok.com/business/en/creative-codes (Creative Codes #4 "Stick to a structure") | OFFICIAL | undated (live 2026) | H | guidance |
| 1.3 | "Hold attention with stimulation": "music, dynamic transitions, movement, text overlays, and emojis keep viewers interested". | same, Creative Code #5 | OFFICIAL | — | H | guidance, no numbers |
| 1.4 | End with "a clear call-to-action". Use "transitions, stickers, and graphics" to hold view time. Feature "creators, employees, or customers". Test 3–5 creatives per ad group. | ads.tiktok.com creative-best-practices | OFFICIAL | Jun 2025 | H | guidance |
| 1.5 | Vidmob x TikTok hook analysis (1,678 ads, 7.3B impressions, Jan–Oct 2023): talent speaking directly to camera engages best in the first 6 s. | https://www.vidmob.com/wp-content/uploads/2024/02/Vidmob-x-Tik-Tok-Hook-Analysis-.pdf (now 404; numbers seen only in a search snippet) | DATA (3rd party, paid ads) | Feb 2024 | M | MEASURED (ads, not organic) |
| 1.6 | A "triple hook": the **visual**, **spoken** and **text** hooks are aligned in the first 1–3 s. Misalignment is a common cause of failure. Keep reopening "curiosity loops" through the video (re-hooks). | Kallaway (Kane Kallaway) via podcast summary https://www.castmagic.io/de/podcast/rhythm-hooks-and-a-billion-views-kane-kallaways-short-form-video-content-secrets | PRACTITIONER | — | M | FOLKLORE (widely used, no data) |
| 1.7 | Jenny Hoyos (Shorts specialist, ~1.6B views over 124 Shorts per Demand Curve): no preamble, "get right into it… explain as you go". Hold back the answer until the end. Plan the hook visually, like a thumbnail. | https://www.demandcurve.com/newsletters/growth-newsletter-187 ; https://www.tubefilter.com/2023/09/27/creators-on-the-rise-jenny-hoyos/ | PRACTITIONER | 2023 | M | FOLKLORE (proven by her results, not a controlled test) |
| 1.8 | Loop endings: YouTube now counts a Shorts view on **every play or replay**, with no minimum watch time (from 31 Mar 2025). The old metric is kept as "engaged views". So loops directly raise the public view count on YouTube. | https://ppc.land/youtube-changes-how-shorts-views-are-counted-from-march-31/ ; https://www.digitalmusicnews.com/2025/03/27/how-does-youtube-shorts-count-views-2025/ | Secondary report of an OFFICIAL change | Mar 2025 | H | RULE |
| 1.9 | Practitioner loop advice: end straight after the resolution, with no outro. The last line or frame flows back into the first. | https://subscribr.ai/youtube-strategy/perfect-youtube-short-length-structure-hooks | PRACTITIONER | — | L–M | FOLKLORE |
| 1.10 | Retention diagnosis: use the platform retention graph. A big drop in the first seconds means a hook problem. One guide puts most "retention cliffs" around 20–30% of runtime, which is a good spot for a re-hook. | subscribr.ai (above); https://socialk.it/en/blog/best-video-editing-apps-for-creators | PRACTITIONER | — | L | FOLKLORE (the 20–30% figure is unsourced) |

**Hook patterns that recur in practitioner material** (FOLKLORE; useful as a taxonomy for our annotators):
- **Verbal**: contrarian statement ("Stop doing X"), a specific number or result ("We got cited by ChatGPT 3x more in 30 days"), a direct question to the target persona, a negative frame or mistake, "here's how/why", the start of a story ("Last week a customer…").
- **Visual**: start mid-action, show the result or reveal first, a strong face close-up, a punch-in or motion in frame 1, an unusual prop or screen (e.g., a ChatGPT answer screenshot), green-screen with the proof behind the speaker.
- **Text**: 3–8 word on-screen headline that restates or sharpens the spoken hook. It stays on through the first 1–2 spoken lines; one guide says 4–6 s is fine for hook text (https://jupitrr.com/how-to/edit-talking-head-videos, Sep 2026, PRACTITIONER, M).

### Durations
| # | Claim | Source | Type | Date | Conf. | Flag |
|---|---|---|---|---|---|---|
| 1.11 | Buffer, 1.1M TikToks: >60 s videos get ≥43.2% more reach and 63.8% more watch time than 30–60 s videos. Median watch time is 11.3 s for >60 s and 6.9 s for 30–60 s. Only 12.3% of posts are >60 s. Buffer says the hook and quality matter more than length. | https://buffer.com/resources/longer-tiktoks-get-more-views-data/ | DATA | 2024 | M–H | MEASURED (correlation; no breakdown above 60 s) |
| 1.12 | TikTok Creator Rewards (monetisation) needs **original videos over 1 minute**, a **personal** (not Business) account, ≥10k followers and 100k views in 30 days. Qualified views are For You views of ≥5 s. | via https://www.sirency.com/blog/tiktok-creator-rewards-program-eligibility (summarises TikTok's eligibility page) | Secondary report of OFFICIAL | 2025–26 | M | RULE |
| 1.13 | YouTube Shorts: up to **3 minutes**, square or vertical (uploads from 15 Oct 2024). Shorts **>1 min with any active Content ID claim are blocked globally**. | https://support.google.com/youtube/answer/15424877 | OFFICIAL | 2024–25 | H | RULE |
| 1.14 | Instagram Reels: up to 3 min (from Jan 2025; earlier 90 s). Reels over 90 s became eligible for recommendations. | https://www.lindseygamble.com/blog/instagram-three-minute-reels ; https://routenote.com/blog/instagram-expands-reels-limit-to-3-minutes/ | Secondary report of OFFICIAL | Jan 2025 | M–H | RULE |
| 1.15 | Duration in practice (inference): educational/B2B organic is commonly **30–60 s** for single-idea clips and **60–90 s** for explainers or teardowns (fits the Creator Rewards >60 s rule and Buffer's reach correlation). | synthesis of 1.11–1.14 | — | — | M | inference |

### Words per minute (speech)
| # | Claim | Source | Type | Conf. | Flag |
|---|---|---|---|---|---|
| 1.16 | On-screen **text**: TikTok recommends "displaying 5–10 words per second when using text". | ads.tiktok.com creative-best-practices | OFFICIAL | H | guidance (very fast; meant for ad text bursts) |
| 1.17 | Spoken pace benchmarks: conversation 125–150 wpm; explainer/e-learning narration 130–160 wpm; "high energy" short form or ads 150–180 wpm. TTS for Shorts: 140–160 wpm. | https://www.teleprompter.com/blog/how-to-time-your-script ; https://flowshorts.app/blog/words-per-minute-speaking | PRACTITIONER (calculator sites) | L–M | FOLKLORE (no measured TikTok data found) |
| 1.18 | Reading-speed ceiling for captions: BBC 160–180 wpm (about 0.33–0.375 s/word). Netflix English adult 20 chars/s (reported). | BBC guidance as quoted at https://clevercast.com/bbc-subtitling-guidelines ; Netflix via 3rd-party tools | OFFICIAL (broadcast), secondary copy | M | RULE (for subtitles, not karaoke captions) |

Takeaway: plan about 150–170 wpm for founder talking-head after dead-air removal (so a 60 s script is about 150–170 words). This is an inference. Our corpus should measure it with word timestamps.

---

## 2. Pacing numbers

**No official or measured source gives cut frequency for short-form talking heads.** Everything below is practitioner advice.

| # | Claim | Source | Type | Conf. | Flag |
|---|---|---|---|---|---|
| 2.1 | "Screen changes or moves every few seconds". Visual reset "if roughly two sentences go by with nothing changing on screen". | https://subscribr.ai/youtube-strategy/editing-talking-head-videos-engaging ; https://jupitrr.com/how-to/edit-talking-head-videos (Sep 2026) | PRACTITIONER | M | FOLKLORE |
| 2.2 | Average clip length "1–2 seconds" on TikTok/Reels. | https://vidpros.com/video-clip-length/ | PRACTITIONER | L | FOLKLORE (no dataset) |
| 2.3 | Counterpoint: framing that changes every few seconds is "exhausting". Tie punch-ins to sentence starts and hold them. Use them for emphasis only, so most of the video has none. | https://agent.vizard.ai/how-to/stop-the-punch-ins-cycling-too-fast-in-a-talking-head-edit.html ; jupitrr | PRACTITIONER | M | FOLKLORE |
| 2.4 | **Punch-in scale**: alternate full frame and a **15–20%** punch-in (115–120%) at sentence breaks to hide jump cuts. An AI zoom tutorial uses **~120–122%**. A slow "cinematic push" is 100→115%. Without a second angle: duplicate the clip and scale it 20–30%. TimeBolt presets: 125/150/175%. | jupitrr; https://elevenpercent.net/blogs/our-latest-tutorials/automatic-zoom-ins-premiere-pro-ai-autoedit ; https://ninefivetofreedom.com/add-zoom-punch-ins-to-your-videos/ | PRACTITIONER / TOOL-DOC | M | FOLKLORE, but sources converge on **115–125%** |
| 2.5 | A punch-in is a *step*: two keyframes a few frames apart, or a hard cut. A whoosh's peak sits on the landing frame. | https://echowave.io/tools/zoom-video/ ; https://morphic.com/resources/sounds/zoom-sound-effects | PRACTITIONER | M | FOLKLORE |
| 2.6 | **Silence removal defaults** (auto-editor, open source): silent threshold **4%** of loudness. **Margin 0.2 s** of padding kept before and after each loud section. | https://github.com/wyattblue/auto-editor (README) ; https://pypi.org/project/auto-editor/ | TOOL-DOC | H | tool default (not a quality target) |
| 2.7 | Descript "Shorten word gaps": its documented example shortens gaps **>750 ms to 200 ms**. (These are example values; Descript does not state defaults.) Users report 10–15% of suggested gaps over-cut, e.g. plural "s". | https://help.descript.com/hc/en-us/articles/10164807277453 ; feedback.descript.com | TOOL-DOC | M | example values |
| 2.8 | Cut tight on the first pass, "tighter than feels comfortable". Trim about **0.2 s** into the end of the previous line on cuts. | jupitrr | PRACTITIONER | M | FOLKLORE |
| 2.9 | Filler-word removal ("um", "uh", "like", "you know") is standard in Descript, CapCut and Submagic. Remove only when it can be done cleanly. | https://feedback.descript.com/features/p/filler-words-dont-ignoreremove-unless-they-can-be-cleanly-removed | TOOL-DOC / user | M | practice |
| 2.10 | B-roll frequency: no number found. Rule of thumb: a visual change every 1–2 sentences (see 2.1). | — | — | L | gap |

Synthesis to test against the corpus (not a recommendation yet):
- After silence removal, gaps of about 0.1–0.25 s remain between phrases.
- A visual change (cut, punch, overlay or B-roll) roughly every 2–4 s.
- Punch-ins at 115–125% tied to sentence starts and key words.
- Jump cuts hidden by alternating 100% and about 115%.

---

## 3. Captions

| # | Claim | Source | Type | Conf. | Flag |
|---|---|---|---|---|---|
| 3.1 | TikTok recommends "captions or text overlays" for context. Text at 5–10 words/s. | ads.tiktok.com creative-best-practices | OFFICIAL | H | guidance |
| 3.2 | TikTok has native auto-captions. Creators review them before posting. Viewers can set "Always show auto-generated captions" (Accessibility). Burned-in captions plus native captions can overlap: if you burn in captions, consider not enabling native ones. | https://www.businessinsider.nl/how-to-use-tiktoks-auto-caption-feature-to-enable-captions-on-your-own-videos-or-hide-captions-from-videos-youre-viewing ; https://pocketnow.com/tiktok-gets-auto-captions-a-feature-instagram-is-already-busy-replicating | Secondary | M | — |
| 3.3 | Spark Ads pull captions from the organic post, "limited to 4 lines including emojis". | https://ads.tiktok.com/help/article/tiktok-auction-in-feed-ads | OFFICIAL | H | RULE (post caption, not burned-in) |
| 3.4 | **Dominant style (Hormozi-type)**: all caps, heavy sans (Montserrat Black / Anton / "TheBoldFont"), white base with **yellow** key word (green or red as alternates), black outline or shadow, word-by-word pop-in, groups of **2–4 words**, lower-middle of frame. Submagic's "new Hormozi" preset: Anton, uppercase, slight shadow, yellow stroke, pop-in from bottom. BlitzCut preset highlight #f7c204. | https://www.submagic.co/blog/how-to-make-alex-hormozi-captions (TOOL-DOC) ; https://sendshort.ai/guides/hormozi-captions/ ; https://blitzcutai.com/hormozi-caption-app | TOOL-DOC / PRACTITIONER | M | describes a style, not official |
| 3.5 | Words per group: **3–4 words per caption chunk** is a good start. Avoid "two full lines on screen for six seconds". | jupitrr (Sep 2026) | PRACTITIONER | M | FOLKLORE |
| 3.6 | **Size**: 60–75 px on 1080×1920 is the common range (about 5.5–7% of width per glyph height). Start around 65 px, minimum about 48–55 px, up to 80–90 px for high-energy styles. 3–4 px black stroke. Weights 700–900. (One vendor mixes up % and px conversions, so trust px.) | https://blitzcutai.com/blog/best-caption-size-tiktok-2026 ; https://openclip.app/guides/caption-font-guide.md | PRACTITIONER (vendor) | L–M | FOLKLORE |
| 3.7 | **Position**: the centre band. "Just below the chin when the framing allows". Keep clear of the bottom caption/description block and the right-hand rail. Some say don't go below about 75% of frame height on TikTok. | jupitrr; https://openclip.app/guides/caption-placement-guide | PRACTITIONER | M | FOLKLORE (convergent) |
| 3.8 | Submagic: words per line is a per-template setting. Size via a SIZE slider (S/M/L per line). Vertical position via a "Position Y" slider only; **captions cannot be moved horizontally**. | https://care.submagic.co/en/category/fonts-captions-16gu1vw/ | TOOL-DOC | H | tool behaviour |
| 3.9 | OpusClip: word-by-word reveal, configurable highlight, AI picks key words and "makes them pop with color, size, or animation". Auto **emojis**. Drops a source lower third rather than cropping through it, and renders its own caption. | https://www.opus.pro/blog/add-captions-to-video-api ; https://www.opus.pro/tools/instagram-reel-caption-generator ; https://www.opus.pro/blog/the-reframe-benchmark | TOOL-DOC | M | tool behaviour |
| 3.10 | CapCut Hormozi recipe (tutorial): base size 20 (CapCut units), accent words +2–4 points and recoloured, black glow. | https://lilys.ai/en/notes/create-youtube-shorts-20260115/capcut-hormozi-captions | PRACTITIONER | L | FOLKLORE |
| 3.11 | Accessibility baseline for reading speed: ≤160–180 wpm (BBC). Minimum on-screen time about 0.3 s/word (e.g. 1.2 s for 4 words). | BBC as quoted by clevercast.com | OFFICIAL (broadcast) | M | RULE (subtitling) |
| 3.12 | MrBeast and Ali Abdaal styles: I found no sourced spec. From memory (UNVERIFIED): Ali Abdaal uses cleaner, smaller, mixed-case captions with less colour. MrBeast Shorts use large, very short groups and high-contrast colours. Measure these in the corpus rather than trusting this description. | — | — | L | unverified |

**Timing offset**: I found no source giving a lead or lag value. Karaoke tools time each word to word timestamps; the highlight turns on at word onset. Our pipeline already has word timestamps (ElevenLabs with-timestamps / alignment), so we can measure offsets in corpus videos (text appears earlier or later than the audio onset).

---

## 4. On-screen graphics over a talking head

| # | Claim | Source | Type | Conf. | Flag |
|---|---|---|---|---|---|
| 4.1 | Officially sanctioned "attention triggers": music, dynamic transitions, movement, text overlays, emojis, stickers, graphics. | Creative Codes; creative-best-practices | OFFICIAL | H | guidance |
| 4.2 | **Green Screen** is "the default format for commentary, news reaction, and educational content": the creator in front of a screenshot, dashboard, chart or headline used as evidence. Busy backgrounds and hair or hands cause keying artefacts. | https://posteverywhere.ai/glossary/tiktok-green-screen ; https://joinotto.com/blog/tiktok-green-screen-guide | PRACTITIONER | M | FOLKLORE (very common in practice) |
| 4.3 | Five layers cover almost every short-form talking head: subtitles, hook text (once, at the open), B-roll, SFX, motion ("a handful of moments per video"). | jupitrr | PRACTITIONER | M | FOLKLORE |
| 4.4 | Keep hook text, captions and overlays in "the middle band of the frame". "A 9:16 video is never seen in full." | jupitrr | PRACTITIONER | M | FOLKLORE |
| 4.5 | TikTok Creator Rewards treats "low-quality content like split screens, meaningless reactions, or low-quality images or slide videos" as **ineligible**. Split-screen or reaction formats need real added value. | via sirency.com (TikTok eligibility page) | Secondary of OFFICIAL | M | RULE (monetisation) |
| 4.6 | Formats that recur for B2B/educator talking heads (FOLKLORE, from browsing practitioner content): keyword pop-ups synced to speech; floating UI screenshots or product cards that tilt in; arrows or circles on a screenshot; number counters for stats; top/bottom split (UI demo on top, face below, or the reverse); green-screen webpage behind the presenter; PiP face over a screen recording; emoji accents. | various | PRACTITIONER | M | FOLKLORE |

**Placement given the face** (synthesis from 4.4 and section 6):
- Face and eyes in the upper-middle of the frame (eyes around 1/3 from top). Graphics go above the head (y about 150–450 px) or beside or below the chin in the centre band (y about 900–1300 px).
- Avoid the right rail (x > about 950–960 px) and the bottom about 350–480 px.
- In a split screen the face is usually in the lower half. Then captions sit at the seam between the halves.

---

## 5. Audio

| # | Claim | Source | Type | Date | Conf. | Flag |
|---|---|---|---|---|---|---|
| 5.1 | "TikTok is the only platform where ads with sound drive significant lifts in purchase intent and brand favorability" (Kantar, US cross-platform sound research, Jan 2021). "Voiceovers and narration reveal more details. Sound effects bring surprise elements." | Creative Codes #6 | OFFICIAL (cites Kantar) | 2021 | H (that it's claimed) | MEASURED (TikTok-commissioned) |
| 5.2 | **CML Terms (verbatim)**: Commercial Sounds may be used for Commercial Uses **only on TikTok**. "Commercial Uses outside of TikTok are not permitted and no rights are granted by TikTok for such uses… include… posting videos on third party digital platforms." "Commercial Sounds are the only sounds made available on TikTok for Commercial Uses." Some "Premium" tracks may cost extra. | https://www.tiktok.com/legal/page/global/commercial-music-library-user-terms/en | OFFICIAL | live Oct 2026 | H | RULE |
| 5.3 | Business accounts: the in-app sound picker is limited to the CML (it covers organic posts too). Accounts can be switched to Business by turning on Shop, connecting Ads Manager, or adding a business category. Unlicensed audio can be muted with "this sound isn't licensed for commercial use". Music you licensed yourself can be uploaded after TikTok's Music Usage Confirmation. | https://www.soundstripe.com/blogs/why-can-i-only-use-commercial-sounds-on-tiktok ; https://www.socialmediatoday.com/news/tiktok-changes-rules-on-music-usage-by-businesses/577734/ | PRACTITIONER (music vendors, conflicted) + 2020 news | 2020–26 | M | RULE as reported |
| 5.4 | Trending sounds vs original audio, for us: for a talking-head or VO-led explainer, **original audio** (voice plus our own licensed bed) is the norm for business accounts. Trends only via CML or "original sounds". Creative Code #2 still says "connect with trends", which for B2B means trend *formats* more than trend *audio*. | synthesis of 5.2–5.3 + Creative Codes | — | — | M | inference |
| 5.5 | **Music under voice**: about −12 to −18 dB below voice for tutorials and vlogs, closer in montage or B-roll. Broadcast guide: dip to "−12 to −20 or lower". Duck under speech, rise in pauses. | https://sonilo.com/blog/how-to-add-background-music-to-a-video ; https://larryjordan.com/articles/automatically-duck-background-music-under-dialog-in-davinci-resolve/ | PRACTITIONER | — | M | FOLKLORE (standard practice) |
| 5.6 | **Loudness**: TikTok and Meta publish no spec. Vendors disagree (−14 LUFS vs −10 to −12 LUFS for TikTok/IG). Common safe choice: −14 LUFS integrated, true peak about −1 to −2 dBTP. Platform normalisation can raise music disproportionately when speech is quiet (anecdotal). | https://openclip.app/learn/audio-normalization ; https://opus.pro/blog/best-loudness-normalizers | PRACTITIONER | — | L–M | FOLKLORE |
| 5.7 | **SFX density**: no numeric source. Advice: subtle, tied to cues (text card, cut, reveal), not "a notification stream". Example: "one soft click" as each of three points appears. "Not on every line." | https://socialk.it/en/blog/best-video-editing-apps-for-creators ; jupitrr | PRACTITIONER | — | L–M | FOLKLORE |
| 5.8 | Over 80% of Instagram Reels are viewed with sound on (figure attributed to Meta in vendor coverage). | https://blog.adobe.com/en/publish/2024/11/04/unlock-potential-reels-best-practices-for-creative-success-using-adobe-creative-cloud | Secondary | 2024 | L–M | MEASURED? (unverified origin) |
| 5.9 | Voice clarity: no platform spec. Practice: a lav or close mic, a treated room, light compression or noise reduction, and the voice as the loudest element. | general practice | PRACTITIONER | — | M | FOLKLORE |

---

## 6. Framing and filming for a vertical talking head

| # | Claim | Source | Type | Conf. | Flag |
|---|---|---|---|---|---|
| 6.1 | TikTok production fundamentals: "shoot vertical, and frame your content 9:16… use hi-res footage (720p or higher)… save space on screen for the TikTok UI". | Creative Codes #3 | OFFICIAL | H | RULE/guidance |
| 6.2 | Specs: 9:16 recommended, minimum 540×960. TikTok gives downloadable safe-zone overlays (.zip) but no pixel numbers. The safe zone depends on caption length and ad format. | https://ads.tiktok.com/help/article/tiktok-auction-in-feed-ads | OFFICIAL | H | RULE |
| 6.3 | **TikTok UI zones on 1080×1920** (third-party measurements, they disagree): top about 130–160 px; **right about 120 px** (action rail starts near x≈949–960); **bottom about 350–480 px** (caption, music, CTA); left about 60–120 px. A practical safe box is about x 120–960, y 150–1300 to 1450. | https://www.houseofmarketers.com/guide-to-safe-zones-tiktok-facebook-instagram-stories ; https://www.trymypost.com/blog/tiktok-ad-specs-2026-safe-zones ; https://www.remotion.dev/elements/overlays/social-safe-zones/ (PNG overlays "measured at 9:16 from representative iOS captures") | PRACTITIONER / TOOL-DOC | M | measured by vendors, not official |
| 6.4 | **Meta Reels ads**: keep top 14%, bottom 35% and sides 6% free of text or logos (about 269/672/65 px on 1080×1920). 40% bottom with a disclaimer. Organic has no official numbers. A 2026 "unified 9:16 safe zone" across FB/IG Stories+Reels is reported but unverified. | https://www.inro.social/tools/instagram-reels-safe-zone-checker ; https://billo.app/blog/meta-ads-safe-zones | Secondary of OFFICIAL (ads) | M | RULE (ads) |
| 6.5 | **YouTube Shorts**: no official template found. Vendors say bottom about 300–380 px (360 px with the description expanded) and a central safe area about 984×1500. They disagree on which corner the subscribe button is in. | https://postplanify.com/blog/social-media-safe-zones-2026-complete-guide ; https://adkit.so/tools/safe-zones/youtube | PRACTITIONER | L–M | measured by vendors |
| 6.6 | Framing: mid-chest up, **eyes near the upper third**, lens at eye level, chin and mouth clear of the caption or bottom zone. Recheck headroom after a vertical crop. | https://www.marylandcomptroller.gov/content/dam/mdcomp/md/com-docs/video-filming-guidelines.pdf (government guide) ; https://gotranscript.com/public/talking-head-framing-tips-headroom-and-eye-level | OFFICIAL-ish (gov guide) / PRACTITIONER | M | convention |
| 6.7 | **4K landscape vs native vertical**: cropping 3840×2160 to 9:16 keeps about 1215×2160 (≥1080×1920, so there is room for 1.1× punch-ins only). A 1080p 16:9 source crops to about 607 px wide and must be upscaled (soft). Native vertical 4K (2160×3840) gives the most punch-in room. | https://digitalanarchy.com/blog/video-editing-plugins/shooting-4k-to-create-vertical-videos-for-social-media/ ; https://www.streamingmediaglobal.com/Articles/Editorial/Featured-Articles/Review-Adobe-Premiere-Pro-Auto-Reframe-135118.aspx ; https://www.videomaker.com/sponsored/how-to-get-the-highest-quality-vertical-video-shoot-it-natively/ | PRACTITIONER (arithmetic checks out) | H (math) | MEASURED (arithmetic) |
| 6.8 | Lighting and mic basics: soft, diffused key light; a plain backdrop if you will use green-screen or background removal. | joinotto green-screen guide | PRACTITIONER | M | FOLKLORE |

Implication of 6.7: for a 1080×1920 delivery from a 4K-landscape crop, a 120% punch-in needs a source region of 900×1600. The 1215-wide crop covers that, so 120% stays at native resolution only just. From 1080p landscape every punch-in is an upscale. For founder shoots, **shoot vertical 4K** if punch-ins are planned, or 4K landscape when the same take must serve 16:9 and 9:16.

---

## 7. Repurposing a 16:9 explainer into 9:16 and clipping long videos

| # | Claim | Source | Type | Conf. | Flag |
|---|---|---|---|---|---|
| 7.1 | What breaks: two-thirds of the width is lost, so a static centre crop cuts the speaker or the UI. Lower thirds, slides and screen-shares get sliced ("a sliced chyron is worse than no chyron"). The wrong speaker gets framed in multi-person shots. Resolution loss from 1080p sources. | https://www.opus.pro/blog/the-reframe-benchmark (vendor); Premiere Auto Reframe review (above) | TOOL-DOC / PRACTITIONER | M | — |
| 7.2 | Active-speaker reframing (voice and motion cues) is standard in OpusClip and peers. It works best for solo monologues; check multi-person footage manually. | https://help.opus.pro/docs/article/how-to-enable-face-tracking ; https://help.opus.pro/docs/article/subject-tracking | TOOL-DOC | M | — |
| 7.3 | TikTok (2026-H2 guidelines, verbatim): **FYF ineligible**: "Reused or unoriginal content posted without creative edits, such as clips that show someone else's watermark or logo" and "Low-quality or minimally edited content". | https://www.tiktok.com/community-guidelines/en/integrity-authenticity | OFFICIAL | H | RULE |
| 7.4 | Instagram: does not recommend Reels with other apps' watermarks (your own logo is fine). Original content replaces identical reposts in recommendations. Aggregators (≥10 reposts of others' content in 30 days) are removed from recommendations. | https://www.socialmediatoday.com/news/instagram-clarifies-including-your-own-logo-on-a-reel-is-ok/730852/ ; https://techcrunch.com/2024/04/30/instagram-is-updating-its-ranking-systems-to-surface-more-content-from-smaller-original-creators | Secondary of OFFICIAL | M–H | RULE |
| 7.5 | Cross-posting the same MP4: export **clean** (no TikTok watermark) for Reels/Shorts. CML music is **not licensed off TikTok** (5.2). YouTube blocks >1 min Shorts with any Content ID claim (1.13). | combined OFFICIAL | — | H | RULE |

**Strategy for an HTML-composition pipeline** (inference, M confidence): don't crop rendered 16:9 frames. **Re-lay out** the composition at 1080×1920: stack the UI demo and the text vertically, scale type up about 1.5–2× for phone legibility, and move key content into the safe box. Our renderer can do this natively, which is the main advantage over crop-based tools. For clipping long videos, pick self-contained 30–90 s segments with their own hook. Rewrite the first line or add hook text, because the original first sentence usually isn't a hook.

---

## 8. Accounts to study (names only; for the reference corpus, no downloading)

Brand accounts that a B2B roundup (Oct 2025) and another blog noted as strong on TikTok:
- **Shopify**: entrepreneur education, AI-tool demos, "TikTok Effect" series.
- **Adobe**: user tips, motion-designer features, employer brand.
- **Canva**: humour plus product tips with the product at the centre.
- **Grammarly**: product-use-case tips, creator collabs.
- **Salesforce**: F1/McLaren sponsorship, Agentforce AI showcase.
- **HubSpot**: relatable marketing humour plus education for marketers.
- **Notion**: founder opinions, office culture, humanised brand.
- **QuickBooks**: benefits over features, customer case studies.
- **Zoom**: myth-busting, workplace humour.
- **Cisco**: employee day-in-the-life, thought leadership.
- **Morning Brew** (media, not SaaS): adapted its tone to TikTok without changing its identity.

Sources: https://blog.socialmediastrategiessummit.com/10-b2b-brands-that-are-crushing-it-on-tiktok/ (Oct 2025, PRACTITIONER) ; https://www.usepassionfruit.com/blog/tiktok-the-b2b-saas-brands-nailing-it-why (PRACTITIONER).

Founders, creators and educators known for strong short-form craft. These are from **general knowledge, not verified in this session**; check handles before adding them to the corpus:
- **Alex Hormozi**: the reference for the "Hormozi caption" style; podcast-to-shorts clipping at scale.
- **Jenny Hoyos**: YouTube Shorts structure, hooks and loops (her approach is sourced in 1.7).
- **Ali Abdaal**: productivity educator; cleaner, calmer caption and B-roll style.
- **Jeff Su**: tech-productivity tutorials; tight screen-recording overlays.
- **Kane Kallaway**: teaches short-form hooks; meta-examples.
- **Dan Martell**: SaaS-founder coaching; high-energy talking head with overlays.
- **Codie Sanchez**: business education; heavy B-roll and text.
- **Steven Bartlett / Diary of a CEO clips**: long-form to vertical clipping.
- **Matt Wolfe**, **Rowan Cheung**: AI-tool news; screenshot-heavy and green-screen formats close to Acme's topic.
- **Varun Mayya**: tech/AI explainers with dense motion graphics over the face.
- **Duolingo**: brand-persona benchmark (consumer, but the most-studied brand TikTok).

Topic-adjacent note: accounts covering "AI search / GEO / ChatGPT SEO" (e.g. SEO educators doing green-screen over ChatGPT answers) are the closest format match for Acme. I could not verify specific handles in this session.

---

## 9. Platform policy points (business content)

### 9.1 TikTok AI-generated content (AIGC): verbatim from the Community Guidelines, released 25 Aug 2026, effective 24 Sep 2026
Source: https://www.tiktok.com/community-guidelines/en/integrity-authenticity (section "Edited Media and AI-Generated Content (AIGC)"). OFFICIAL, H, RULE.

- "we require creators to label AI-generated or significantly edited content that shows **realistic-looking scenes or people**. Unlabeled content may be removed, restricted, or labeled by our team".
- AIGC definition: "Any image, video, or audio made or changed by AI. This can include realistic scenes or artistic styles, like anime, cartoons, or paintings."
- You can label with "your own clear caption, sticker, or watermark" **or** the AIGC label.
- **Disclosure needed** when content "could be confusing", including when: a face is replaced; "AI tools make it look like someone said something they didn't"; something is added or removed misleadingly; "**AI-generated audio mimics the voice of a real person**".
- **Disclosure isn't needed** when: "Making small edits like color correction, reframing, or cropping"; "Using artistic styles, like anime"; "**Using generic text-to-speech (TTS) narration, when the TTS isn't a recognizable voice of a known individual**".
- Not allowed: likeness of private figures without consent; AIGC showing "A public figure… supporting products… they haven't actually addressed"; content made to look like a real news source; and others.
- Also auto-labelling: TikTok reads C2PA Content Credentials and labels AIGC from other tools (since May 2024; https://www.nbcnews.com/tech/tech-news/tiktok-will-automatically-label-ai-generated-content-rcna151446, Secondary, H).

**What this means for us** (inference from the rule text, H):
- **HyperFrames/GSAP motion graphics, animated UI and diagrams**: these are not realistic AI depictions of people or scenes. Code-rendered animation isn't "made by AI" in the generative sense. **No label needed.**
- **Stock ElevenLabs voice** (generic, not a known person's voice) narrating a faceless explainer: covered by the generic-TTS exemption. **No label needed.**
- **A clone of Robert's own voice** saying lines he didn't record: this is "AI-generated audio mimics the voice of a real person". **Label it** (the AIGC toggle or a caption such as "voice: AI clone of Robert"). This holds even though it's his own voice and he consents. The rule is about viewer confusion, not consent.
- **AI-generated realistic B-roll or avatars** (e.g. a generated presenter or photoreal footage): **label it**.
- **Realistic-looking AI images of the ChatGPT/Gemini UI**: avoid, or use real screenshots. A synthetic "screenshot" of an AI answer that looks real is risky under "misleading" if it shows answers the AI never gave. Use genuine captures from Acme data.
- Watch C2PA metadata: assets from generative tools may carry Content Credentials and get auto-labelled.

### 9.2 YouTube and Meta, briefly
- YouTube: disclose realistic altered or synthetic content (e.g. a synthetic voice of a real person, face swaps). **No disclosure for clearly unrealistic or animated content, special effects, or production assistance.** YouTube may apply a label itself. https://9to5google.com/2024/03/18/youtube-altered-content-disclosure/ (Secondary of OFFICIAL, Mar 2024, M–H).
- Meta "AI info" labels: not researched in depth here (gap).

### 9.3 Branded content / commercial content disclosure (TikTok)
- **Branded Content Policy (published 4 Aug 2026, effective 31 Aug 2026)**, verbatim. Branded Content is "content that promotes or reviews a **third-party** brand… in exchange for payment or any other incentive" (including gifts, affiliate links or codes, ambassador relationships). "When posting Branded Content, you must enable the commercial content disclosure toggle." Content may go into the TikTok Commercial Content Library "where required by law". "You must ensure that the product or service you are promoting is sufficiently clear… explicitly identify the product or service verbally and/or in the text caption." https://www.tiktok.com/legal/page/global/bc-policy/en. OFFICIAL, H, RULE.
- **Promoting your own brand** (Robert posting about Acme): the Content disclosure setting → "Disclose commercial content" → choose **"Your brand"** (third party = "Branded content", which shows "Paid partnership"). Your brand shows a "Commercial content"/promotional label. https://ads.tiktok.com/help/article/how-to-turn-on-the-commercial-content-disclosure-setting-in-tiktok (OFFICIAL per search summary; not fetched directly, M–H). Bazaarvoice says business accounts should turn it on and choose "Your brand" (PRACTITIONER, M). Vendors disagree on the exact label text.
- If acme.example content promotes Acme, that is arguably "a brand that you have… a commercial relationship with", so disclose it as "Your brand". Inference, M.
- Sponsored content is excluded from Creator Rewards (via sirency.com, M).

### 9.4 Commercial Music Library: see 5.2 and 5.3
Core rules:
1. Business accounts are limited to CML sounds in-app.
2. CML sounds are licensed for **TikTok only**. Cross-posting to Reels or Shorts with a CML track is unlicensed.
3. A personal account keeps the full library but loses business features, and its tracks are personal-use only anyway (commercial use is still not licensed).

**Pipeline rule:** bake **our own licensed (multi-platform) or original music** into the rendered MP4, and never rely on TikTok in-app music for anything we cross-post.

---

## 10. Gaps and what our `lens` pipeline should measure instead

The web lacks credible numbers for the following, so build them from corpus measurement (code measures, Claude names):
1. **Cut, shot and visual-change rate** per minute in vertical talking-heads and hybrids (shot detection plus a "visual change" event that counts overlays and punch-ins too).
2. **Punch-in scale distribution** (scale ratio between adjacent same-camera shots; hypothesis 1.15–1.25).
3. **Inter-phrase gap distribution** after editing (from word timestamps; hypothesis median about 0.1–0.25 s), plus filler-word rate.
4. **Speech wpm** (hypothesis 150–180 for founder talking heads).
5. **Captions**: words per group, glyph cap-height as % of 1080 width, y-position of the caption band, highlight colour, lead or lag of caption onset vs word onset, % of frames with captions.
6. **Safe-zone violations**: % of text box area inside the TikTok, IG and Shorts UI masks (our box ids against the Remotion/TikTok overlay PNGs, measured once into config).
7. **Hook anatomy, first 3 s**: is there text in frame 1? face present? motion in the first 0.5 s? first spoken word onset (dead air before speech)?
8. **SFX density** (events per 10 s) and how often SFX land on cuts or overlays.
9. **Music-to-voice level difference** in dB during speech, and integrated LUFS / true peak of the exports.
10. **Loop**: similarity between the last and first frames, and whether the last sentence flows into the first.

These would become `config/lens.yaml` targets once measured, in line with the rule that numbers come from code, not folklore.
