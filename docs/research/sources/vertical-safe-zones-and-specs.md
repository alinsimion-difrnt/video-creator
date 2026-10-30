# Vertical video safe zones and specs: TikTok, Instagram Reels, YouTube Shorts

Research date: 2026-10-09. Canvas: 1080x1920 (9:16) unless stated otherwise.
Legend: **[OFFICIAL]** = platform-owned page or file. **[SECONDARY]** = agency, tool or press.
**[DERIVED]** = my own arithmetic or pixel measurement of an official file (method given).
Confidence: High / Medium / Low.

---

## 0. Key findings

1. **TikTok does publish a safe zone, but only as downloadable overlay PNGs** on the Ads Help Center. The page text has no numbers. I downloaded the PNGs and measured them. **Most commonly cited "TikTok safe zone in px" numbers are the template's own labels read at the wrong scale.** The labels are drawn on a **720x1280** canvas (top 160 / bottom 440 / sides 80 / rail 120) or a **540x960** canvas (top 126 / sides 60 / rail 120 / bottom 406–507). Many guides copy these numbers onto a 1080x1920 canvas without scaling them.
2. **The TikTok standard in-feed template, scaled to 1080x1920** [DERIVED from OFFICIAL]: top **240**, bottom **660**, left/right "may be cropped based on device type" **120 each**, and a right action-rail block **180 wide (x 780–960) from y=840 down to the bottom**. The safe rectangle is x 120–960, y 240–1260, minus that notch.
3. **Meta (official text):** "at least 14% of the top, 35% of the bottom, and 6% on each side" for Reels ads. That is 269 / 672 / 65 px. Meta also officially says that on screens taller than 9:16 it may **zoom (crop)** or **letterbox on black**, and that ads with disclaimers should keep the **bottom 40%** clear.
4. **YouTube (official Google Ads overlay PNG, 1080x1920, measured):** the safe area is x **48–888**, y **288–1248**. That gives top 288 / bottom 672 / left 48 / right 192.
5. **Proposed universal zone** (section 3.4): **x 120–780, y 288–1248 (660x960)** for anything critical. In addition, x 780–888 is usable only above y=840. This means critical content is **not centred on x=540**. The usable column's centre is x≈450.

---

## 1. TikTok safe zone

### 1.1 Official sources

**Auction In-Feed Ads spec page** [OFFICIAL]: https://ads.tiktok.com/help/article/video-ads-specifications?lang=en (page shows "Last updated: June 2026"). Fetched OK.
- Quote: "The safe zone size is determined by the dimension (vertical, horizontal, or square), ad caption length, and any additional formats used. Downloadable safe zone files are available below."
- Quote: "There might be slight differences between the preview and the live version since the ad preview is not specific to a device."
- Files offered: "In-Feed-Standard Version LTR.zip" (84.29 KB), "In-Feed with Anchor-Standard LTR.zip" (3.86 MB), "In-Feed - Arabic Version RTL.zip", "In Feed with Anchor-Arabic Version RTL.zip", "Profile cover.zip".
- The page gives no pixel numbers in text. High confidence.

**TopView spec page** [OFFICIAL]: https://ads.tiktok.com/help/article/tiktok-reservation-topview?lang=en (June 2026). It offers a "TopView safe zones" zip and says "In-feed safe zone is more restrictive than open screen." High.

**Creative best practices** [OFFICIAL]: https://ads.tiktok.com/help/article/creative-best-practices?lang=en (June 2025). Quote: "keeping your content visible within the UI safe zone as per ad specifications". No numbers. High.

**Creative Codes** [OFFICIAL]: https://ads.tiktok.com/business/en/creative-codes. Quote: "save space on screen for the TikTok UI". No numbers. High.

**TikTok Creative Center "safe zone tool":** I found no official interactive safe-zone tool. Search results returned only third-party preview tools (Rocketship, Vaizle, Poster.ly, AdKit). The official mechanism is the downloadable templates plus the Ads Manager ad preview. Medium confidence that no such tool exists; I could not log into Ads Manager to check.

### 1.2 Measured contents of the official template files [DERIVED from OFFICIAL]

The files were downloaded from `lf-tt4b.tiktokcdn.com`, the CDN links on the spec page. I measured them by colour-run analysis with PIL. Raw files were not kept in the repo.

**A. "In-Feed-Standard Version LTR" → `In-Feed/Feed.png`, 2880x5120 (4x of 720x1280).**
The TopView zip contains the same drawing with a legend:
- "Original Video (720x1280px)"
- "Red Zone: This area may be blocked by UI elements. Avoid placing critical content in this area."
- "Blue Zone: This area may be cropped based on device type. Avoid placing critical content here"
- "Blank Zone: Content safe area"

| Zone (template labels at 720x1280) | Measured px at 720x1280 | **Scaled to 1080x1920 (x1.5)** |
|---|---|---|
| Blue side bands (may be cropped by device), left and right | 80 each | **120 each** (x 0–120 and 960–1080) |
| Red top band (tabs / search / LIVE) | 160 | **240** (y 0–240) |
| Red bottom band (caption, username, sound, CTA) | 440 | **660** (y 1260–1920) |
| Red right action-rail block | 120 wide, 720 tall from bottom (x 520–640, y 560–1280) | **180 wide x 1080 tall: x 780–960, y 840–1920** |
| Content safe area | x 80–640, y 160–840, minus the rail notch | **x 120–960, y 240–1260; above y 840 the full width to x 960; below y 840 only to x 780** |

- RTL (Arabic) version: identical, with the rail mirrored to the left (measured x 80–200 at 720, i.e. x 120–300 at 1080).
- TopView "After 3-second phase" is the same as the standard in-feed template.
- TopView "Initial 3-second phase" (full-screen takeover): top 160 / bottom 160 / sides 80 at 720. That is top 240 / bottom 240 / sides 120 at 1080, with no rail.
- Confidence: High for the measurements. Medium on how these map to today's live UI; TikTok itself warns about device differences.
- Independent corroboration [SECONDARY]: AdKit (https://adkit.so/tools/safe-zones/tiktok, version 2026-09-10) reports the same 240/660/120 and "right 300 px below y=840" (= 180 rail + 120 crop). It says it scaled the 720x1280 template x1.5.

**B. "In-Feed with Anchor - Standard LTR" (the Shop/product "anchor" variant).**
- Contents: `1. Vertical Feed- 540x960/feed_1..4.png` (750x1334 mock-ups drawn over a TikTok UI screenshot with "Following / For You", rail, "Viewproduct" anchor, @username, caption, "Sponsored" label, sound, "Download" CTA, and bottom nav bar).
- Also square (640x640) and horizontal (960x540) variants.
- Instruction file text: "The 4 versions of in-feed safe zone show how safe zone varied when clients provide different lines of copy. From one line to 4 lines."
- Labels are in 540x960 units. Green safe box measured, then scaled to 1080x1920 (x2):

| Item | 540x960 label/measure | **1080x1920** |
|---|---|---|
| Top | 126 | **252** |
| Left | 60 | **120** |
| Right (top strip, above rail) | 60 | **120** |
| Right rail exclusion (from right edge) | 120, starting y=180 (780 tall) | **240 from right edge (x ≥ 840) from y=360 down** |
| Bottom, 1-line ad caption | 406 (measured 405.6) | **812** (safe bottom y=1108) |
| Bottom, 2 lines | 439 | **879** (y=1041) |
| Bottom, 3 lines | 473 | **946** (y=974) |
| Bottom, 4 lines | 507 | **1014** (y=906) |

- Each extra caption line costs ≈ 67 px at 1080 [DERIVED].
- With an anchor, the safe box is only x 120–840 (below y 360) by y 252–906…1108. High confidence on measurement.

**C. UI element positions read from TikTok's own mock-up (anchor template feed_1.png), scaled x1.44** [DERIVED, approximate ±10 px; visual reading]. This is an older UI with the nav bar drawn over the video.

| Element | Position at 1080x1920 |
|---|---|
| "Following / For You" tabs | y ≈ 94–144 |
| Avatar | x ≈ 922–1060, y ≈ 579–717 |
| Like / comment / share / more | x ≈ 940–1045; y ≈ 830–1500 |
| Sound disc | y ≈ 1606–1742 |
| Anchor bar | y ≈ 1234–1310 |
| @username | y ≈ 1339–1390 |
| "Sponsored" | y ≈ 1485–1525 |
| CTA "Download" | y ≈ 1649–1742 |
| Bottom nav | from y ≈ 1778 |

### 1.3 Disagreement between TikTok's own two templates

- The **standard** template rail starts at y=840 (43.75%) and is 180 wide (x 780–960). Most of the real icons sit in the blue crop band (x>960).
- The **anchor** template blocks everything x ≥ 840 from y=360 (18.75%) down.
- The avatar in TikTok's own mock-up starts around y≈579. **The standard template's rail start (y 840) is therefore too optimistic for the avatar and like button region.**
- Conservative TikTok rule [DERIVED]: **nothing critical at x > 840 below y ≈ 360**, and nothing at x > 960 anywhere.

### 1.4 Commonly cited numbers (verified against the above)

| Claim | Source | Verdict |
|---|---|---|
| "150 top / 440 bottom / 120 right / 60 left" on 1080x1920 | Widely repeated [SECONDARY], e.g. trymypost, zuuvi guides | **Not right at 1080.** 440 and 120/60 match the 720x1280 / 540x960 template labels. At 1080 they become 660 bottom / 120 sides / 180–240 rail. "150 top" matches no official file (closest: 160@720 or 126@540). |
| 160 top / 480 bottom / 120 sides → 840x1280 | Poster.ly (https://www.poster.ly/tools/tiktok-safe-zone-checker, "2026", no derivation) [SECONDARY] | Again looks like template labels (160) mixed with an estimate; under-reserves the bottom vs official 660. |
| 130 top / 480 bottom / 150 right → 870x1310 | moda.app ("measured rather than published") [SECONDARY] | Plausible for organic (no CTA); not official. |
| 150 top / 270 bottom / 40 sides | adaptlypost [SECONDARY] | Too small vs any official file. |
| 108 top / 320 bottom / 60 left / 120 right | Ignite Social Media (https://www.ignitesocialmedia.com/content-creation/what-are-the-safe-zones-for-tiktoks-and-instagram-reels/, "accurate as of July 2026"); its diagram is on **576x1024** [SECONDARY] | Numbers are on a 576-wide canvas. Scaled to 1080 (x1.875): ≈ 203 / 600 / 113 / 225, which is close to the official template. Shows the scale confusion. |
| 254 top / 707 bottom / 242 right | AdKit, "measured from official ad previews, March 2026" [SECONDARY] | Close to the anchor-template values. |
| 120 top / 240 bottom / 50 sides | Predis [SECONDARY] | Too small. |

### 1.5 Organic vs ads

- **No official TikTok organic safe zone exists.** I found none. Medium-High confidence.
- Organic posts lack the "Sponsored" label, the CTA button and the anchor, so the real bottom overlay is shorter.
- TikTok's ad templates still include caption, username and sound, which organic has too.
- **Spark Ads** use the organic post. Official: "Ad captions: Extracted directly from the organic video captions. A maximum of 4 lines can be displayed, including emojis." Spark Ads add the ad CTA. Design organic posts to the ad template if they may be boosted.
- **Non-Spark captions:** "Displayed in white with a uniform font that can't be customized. Does not support any clickable links, symbols (@), or hashtags." [OFFICIAL, spec page]
- **"...more" expansion:** officially only modelled for ads, as 1–4 lines with ≈ 67 px per line at 1080 (table B).
  - For organic, a long description is truncated and tapping "more" expands it over the video. I found **no official pixel figure** for the expanded state.
  - Secondary tools note the expanded caption covers substantially more of the lower half. Low confidence on any number.
  - Practical rule: assume the bottom ~50% can be covered momentarily. Keep the at-rest design inside the 1–2-line zone.
- **TikTok Shop elements** (product anchor, Shop tab overlay): covered only by the "with Anchor" template (table B). I found no separate Shop-video safe-zone file. Medium.
- **Comment sheet:** when opened it covers most of the lower screen and the video is pushed up/scaled. I found **no official spec**. Not a design target; nothing to verify. Low.
- **Progress bar / scrubber:** sits just above the nav bar at the bottom edge. It is within the 660 px bottom band, so no extra margin is needed. No official figure. Low.

---

## 2. Device aspect variation

- **TikTok [OFFICIAL]:** the blue side bands "may be cropped based on device type". Each is 80/720 = **11.1% of width per side** (120 px at 1080).
  - [DERIVED] If the player fills height and crops sides, 11.1% per side covers viewports up to 840:1920 = 0.4375 (≈ 9:20.6). That covers 19.5:9 (0.4615) and 20:9 (0.45) phones even when the video runs full-screen.
  - The newer TikTok UI on tall phones places the nav bar below the video, so the video viewport is closer to 9:16 than the raw screen. I did not verify this officially.
  - On screens wider than 9:16 (tablets, old 4:3 iPads, desktop), the video is letterboxed/pillarboxed, not cropped. Secondary only; I found no official TikTok doc.
- **TikTok desktop web:** the action buttons sit beside the video, not over it [SECONDARY: Hootsuite, https://blog.hootsuite.com/tiktok-desktop]. The overlay problem is smaller on desktop. Low-Medium.
- **Meta [OFFICIAL]:** https://www.facebook.com/business/help/980593475366490 ("About text overlays and safe zones for ads in Stories and Reels"). WebFetch failed; text extracted from the page's embedded HTML.
  - Quote: "On devices with screens that are taller than the 9:16 aspect ratio, we may either zoom the creative to better fill the whole screen (which can crop areas outside the safe zone), or show the creative in its original 9:16 aspect ratio and use a black background to fill any extra space."
  - Quote: "9:16 video ads in Instagram Feed use the same safe zone guidance as Reels and Stories."
  - In Ads Manager you can "toggle on the Safe zone guardrail" (yellow overlay). High.
- **YouTube [OFFICIAL]:** "When uploading other aspect ratios such as vertical or square, the player automatically adapts itself to the size of the video" (https://support.google.com/youtube/answer/1722171). There is no official statement on Shorts crop on tall phones.
- **Always-visible central area** [DERIVED]: crop up to 11.1% per side (TikTok's figure) plus top/bottom UI.
  - For any phone up to 20:9, the crop-proof column is **x 120–960**.
  - Combined with UI, the core is roughly **x 120–780, y 288–1248** (section 3.4).

---

## 3. Instagram Reels and YouTube Shorts

### 3.1 Instagram Reels [OFFICIAL unless noted]

- **Reels ads guide:** https://www.facebook.com/business/ads-guide/update/video/instagram-reels. No date visible; inro.social cites it as "August 2026". Fetched OK.
  - Quote: "Consider leaving at least 14% of the top, 35% of the bottom, and 6% on each side of your asset free from text, logos, or other important creative elements. This will help ensure that key parts of your design are not cropped, covered by the profile icon or call-to-action, or placed too close to the edges of devices with screens taller than a 9:16 aspect ratio."
  - Ratio 9:16. "Resolution: 1440 x 2560 pixels".
  - "H.264 compression, square pixels, fixed frame rate, progressive scan and stereo AAC audio compression at 128kbps+".
  - Duration "0 seconds to 15 minutes"; max file 4GB.
  - "Minimum Width: 250 pixels for ads less than 30 seconds; 500 pixels for ads 30 seconds or longer".
  - Captions "Optional, but recommended"; Sound "Optional, but strongly recommended"; "Primary Text: 44 characters".
  - Also: no "Videos that contain edit lists or special boxes in file containers". High.
  - [DERIVED] At 1080x1920 this is top 269, bottom 672, sides 65 → safe x 65–1015, y 269–1248 (950x979).
- **Disclaimers:** "If you're including disclaimers on your Reels ads, you should leave the bottom 40% of your ad free" (help/980593475366490). That is 768 px. High.
- **Organic Reels:** no official Meta/Instagram organic safe zone found. Medium-High.
  - The Instagram help page "Reel size & aspect ratios on Instagram" (https://help.instagram.com/1038071743007909) exists. Its meta description: "Learn about resolution sizes for Instagram Reels, including Reels aspect ratios, cover photo sizes and how to choose upload quality."
  - **The body could not be fetched** (client-rendered). Not verified.
- Secondary organic measurements vary 2–4x (inro.social table, https://www.inro.social/tools/instagram-reels-safe-zone-checker): top 108–288, bottom 250–576, right 35–140 px. Low.
- **Profile grid crop:**
  - Instagram moved from 1:1 to **3:4** tiles in Jan 2025. Mosseri announcement, reported 20–21 Jan 2025 [SECONDARY: Business Today, https://www.businesstoday.in/technology/news/story/instagram-head-announces-big-changes-3-minute-reels-and-new-look-for-profile-grid-461527-2025-01-21; Planoly]. I did not find the primary Instagram post. Medium-High.
  - [DERIVED] A centred 3:4 crop of 1080x1920 = 1080x1440 = **y 240–1680**.
  - Old 1:1 crop (still used by some surfaces/thumbnails) = **y 420–1500**.
  - 4:5 (1080x1350) = **y 285–1635**.
  - Secondary claims of "1013x1350" or "420x654 (1:1.55)" cover sizes conflict. Low.
  - Instagram feed historically displayed organic Reels cropped to 4:5. Meta now officially says 9:16 *ads* in IG Feed use the Reels safe zone. Unverified for organic.
- **Reels length (organic):** up to **3 minutes**, announced Jan 2025 [SECONDARY: Business Today, Buffer]. Some sources claim uploads under 15 min become Reels. Unverified. Medium.

### 3.2 YouTube Shorts [OFFICIAL]

- **Length:** https://support.google.com/youtube/answer/15424877 ("Understand three-minute YouTube Shorts").
  - "Videos uploaded after October 15, 2024: Any videos uploaded on or after this date with a square or vertical aspect ratio up to three minutes in length will be categorized as Shorts". High.
  - Shorts over 1 minute with an active Content ID claim: this page says they "will be blocked globally".
  - https://support.google.com/youtube/answer/10343433 says such Shorts "will no longer be automatically blocked and may remain playable". **The two official pages disagree.** Check before using licensed audio.
  - Music: "most songs for up to 90 seconds in a 3 minute Short".
- **Upload:** https://support.google.com/youtube/answer/12779649. "Up to 3 minutes. With a square or vertical aspect ratio". https://support.google.com/youtube/answer/10059070: "You can upload Short videos with a maximum resolution of 1080p"; title "max 100 characters". High.
- **Safe zone:** **no organic Shorts safe zone published.** Google Ads offers "Universal safe zones for video ads on YouTube" with transparent PNGs (https://support.google.com/google-ads/answer/13547298).
  - Vertical file: https://services.google.com/fh/files/misc/youtubesafezoneoverlay_vertical_final.png, 1080x1920. Measured transparent area: **x 48–888, y 288–1248** → top 288, bottom 672, left 48, right 192. High (measurement).
  - Google: overlays "may appear in different places depending on the format, campaign type, and screen".
  - Secondary organic Shorts estimates: top 120–380, bottom 300–381, right 96–201 (postplanify, vidpros, adkit). Low.
- **Encoding** (https://support.google.com/youtube/answer/1722171, "YouTube recommended upload encoding settings"):
  - Container: MP4 (moov atom at front, no edit lists).
  - Video: H.264 High Profile, progressive, closed GOP of half the frame rate, CABAC, VBR, 4:2:0.
  - Audio: AAC-LC or Opus, 48 kHz.
  - 1080p SDR bitrate 8 Mbps (24–30 fps) / 12 Mbps (48–60 fps); HDR 1080p 10/15 Mbps.
  - Audio stereo 384 kbps.
  - Colour: BT.709 for SDR; "YouTube converts full color range to limited color range." High.
- **Shorts thumbnail:** frame selection in the mobile app is well established. Custom image uploads for Shorts are reported as rolling out (2025–2026) [SECONDARY: alternativeto.net news 2026-07, routenote]. No official page fetched. Low-Medium.

### 3.3 Side-by-side (1080x1920, "keep critical content inside")

| Platform / source | Left | Right (rail) | Top | Bottom | Status |
|---|---|---|---|---|---|
| TikTok in-feed std (scaled template) | 120 | 120 all heights; 300 below y 840 | 240 | 660 | OFFICIAL file, DERIVED px |
| TikTok anchor, 1–4 lines | 120 | 120 above y 360; 240 below | 252 | 812 / 879 / 946 / 1014 | OFFICIAL file, DERIVED px |
| Meta Reels ads | 65 | 65 | 269 | 672 (768 with disclaimers) | OFFICIAL % |
| YouTube vertical ads overlay | 48 | 192 | 288 | 672 | OFFICIAL file, measured |

### 3.4 Proposed universal vertical safe zone (1080x1920)

Method: intersection of the three official sources, using TikTok's standard (no-anchor, ≤2-line caption) template, which is also the stricter case for organic posts.

- **Core zone, critical text/UI/face features: x 120–780, y 288–1248 (660 x 960 px).**
  - Left 120: TikTok crop band. It beats Meta's 65 and YouTube's 48.
  - Right edge 780: TikTok rail notch (x ≥ 780 below y 840) and anchor rail (x ≥ 840 below y 360). Stricter than YouTube's 888.
  - Top 288: YouTube. Stricter than TikTok's 240/252 and Meta's 269.
  - Bottom 1248: Meta and YouTube (672 px). Stricter than TikTok std's 1260.
- **Upper extension: x 120–888, y 288–840.** This is allowed by TikTok std (x<960), YouTube (x<888) and Meta (x<1015). It is not clear of TikTok's anchor-template rail (x ≥ 840 from y 360), so avoid it if TikTok Shop anchors are used.
- **Horizontal centre of the core is x = 450, not 540.** For centred titles, either centre on x≈450 or keep line width ≤ 2x(540−120)=840 px *and* above y 840. A symmetric box x 120–960 is only valid on YouTube if text stays left of 888.
- **For TikTok ads with long captions/anchors:** move the bottom up to y ≈ 1108 (1-line) … 906 (4-line). For Meta ads with disclaimers: y ≤ 1152.
- **Profile-grid cover:** keep the cover title within **y 420–1500** so it survives the old 1:1 crop as well as 3:4 (y 240–1680) and 4:5 (y 285–1635). Also keep it within x 120–960.
- **Full-bleed background, B-roll and decorative motion may extend everywhere**, including the bleed. Only "critical" elements need the safe zone.
- Confidence: High that this box is clear on all three platforms per their published guidance. Medium that it matches every live UI version, since all three warn layouts vary by device and app version.

---

## 4. Video specs

| Item | TikTok | Instagram Reels | YouTube Shorts |
|---|---|---|---|
| Resolution / aspect | Ads: 9:16 ≥540x960 (also 1:1 ≥640, 16:9 ≥960x540) [OFFICIAL spec page]. Best practice "at least 720P" [OFFICIAL]. API: 360–4096 px each side [OFFICIAL dev docs] | 9:16; ads recommend 1440x2560 [OFFICIAL] | Square or vertical; upload max 1080p [OFFICIAL] |
| fps | API: 23–60 fps [OFFICIAL, https://developers.tiktok.com/doc/content-posting-api-media-transfer-guide, updated 2026-08-04] | "fixed frame rate" [OFFICIAL ads] | Upload at recorded frame rate; 24/25/30/48/50/60 common [OFFICIAL] |
| Length | Non-Spark ads "up to 10 minutes"; Spark (pull) "No restrictions" [OFFICIAL, Jun 2026]. TopView/reservation: 5–60 s, 9–15 s recommended [OFFICIAL]. Organic: API says "All TikTok creators can post 3-minute videos, while some have access to post 5-minute or 10-minute videos" [OFFICIAL dev docs]. 60-min uploads were in test (May 2024) [SECONDARY: TechCrunch, https://techcrunch.com/2024/05/16/tiktok-upload-60-minute-videos]. Many blogs claim "10 min in-app record / 60 min upload" [SECONDARY]; I could not verify (support.tiktok.com is client-rendered and failed to fetch). Older ad guides cite 21–34 s recommended (old version of spec page; no longer on it) | Ads 0 s–15 min [OFFICIAL]; organic 3 min [SECONDARY] | ≤3 min (from 2024-10-15) [OFFICIAL] |
| File size | Ads ≤500 MB [OFFICIAL]; API ≤4 GB [OFFICIAL]; web/in-app limits conflicting (72 MB–10 GB claims) [SECONDARY, Low] | 4 GB (ads) [OFFICIAL] | Not stated for Shorts; 256 GB general [SECONDARY] |
| Codec / container | Ads: .mp4 .mov .mpeg .3gp .avi [OFFICIAL]; API: MP4 (rec.), WebM, MOV; H.264 (rec.), H.265, VP8, VP9 [OFFICIAL] | MP4/MOV, H.264, AAC stereo 128 kbps+ [OFFICIAL ads] | MP4, H.264 High, AAC-LC/Opus 48 kHz [OFFICIAL] |
| Bitrate | Non-Spark ads ≥516 kbps; TopView/Spark Push ≥2,500 kbps [OFFICIAL] | not stated | 1080p 8 Mbps (30 fps) / 12 Mbps (60 fps) [OFFICIAL] |
| Audio | TopView: "Audio must remain clear and be available (video must not be completely silent)" [OFFICIAL]. No sample rate published | AAC stereo 128 kbps+ [OFFICIAL ads] | 48 kHz; stereo 384 kbps [OFFICIAL] |
| Loudness / LUFS | **Not published by TikTok** (none found). Secondary blogs repeat "≈ −14 LUFS" without primary source. Low | **Not published** | **Not published** in the pages fetched. "≈ −14 LUFS" is community-measured. Low |
| HDR | Not found in any official TikTok page. Unverified | Not found | Supported; HDR 1080p bitrates published; non-HDR BT.2020 converted to BT.709 8-bit [OFFICIAL] |
| 1080p / compression | "Upload HD" toggle (1080p) introduced 2021 in select countries [SECONDARY: Adweek, TechCrunch, GSMArena]; 4K is downscaled to 1080p [SECONDARY] | Help page mentions "how to choose upload quality" (body not fetched) | Max 1080p for Shorts upload [OFFICIAL] |

**Recommendation for our renders** [DERIVED]: 1080x1920, 30 fps (or 60 for UI motion; both inside TikTok's 23–60 band), H.264 High, yuv420p, BT.709, limited range, `+faststart`, no edit lists. Use VBR at about 8–12 Mbps (meets YouTube's guidance and TikTok's ≥2.5 Mbps floor; well under 500 MB). AAC-LC 48 kHz stereo, 192–384 kbps. Master around −14 LUFS integrated and −1 dBTP as an unofficial convention, flagged as such.

**Cover / thumbnail:**
- TikTok: choose a frame or upload a cover image in the post flow; text can be added. Secondary only; the TikTok support pages failed to fetch. TikTok ad profile photo: 98x98, key element in centre 66x66, <50 KB [OFFICIAL].
- Instagram: grid crops as in 3.1.
- YouTube Shorts: frame picker on mobile; custom image rolling out (3.2).

**Auto captions:**
- TikTok [OFFICIAL, Newsroom 2021-04-06, https://newsroom.tiktok.com/introducing-auto-captions]: creators "select auto captions in the editing page"; they "can edit the text"; viewers turn them off via "the share panel, tapping the captions button".
- TikTok [OFFICIAL, Newsroom 2022-07-21, https://newsroom.tiktok.com/auto-translations-and-captions]: "viewers now have the option to turn on closed captions", plus translations of captions, descriptions and "text stickers".
- **Placement:** no official page states where they render.
  - Secondary sources (Kapwing, RNID https://developer.rnid.org.uk/...tiktok/) say creator-generated captions can be dragged.
  - Viewer-side closed captions are drawn by the app, typically in the lower-middle above the description. Not officially documented. Low.
  - Implication: burn-in captions inside the core zone (y ≤ 1248). Viewers who also turn on CC may get a second caption layer near the bottom. Keep burned-in captions in the upper/middle of the core (y ≈ 900–1150 is a reasonable band) rather than at the very bottom.

---

## 5. TikTok native editor placement guides

- **No official documentation found** of safe-zone guides in the TikTok in-app editor. Searched Newsroom, Ads Help, Creative Codes. support.tiktok.com pages (e.g. `/en/using-tiktok/creating-videos/camera-tools` → redirects to `tiktok.com/support/faq_detail?id=7581821547946580492`) are client-rendered and **could not be fetched**.
- Secondary sources likewise give no confirmation. BlitzCut says safe-zone lines appear "in some tools" without naming TikTok.
- From general product knowledge (not verified here, Low): the editor shows centre snap/alignment lines when dragging text/stickers, and the post preview shows the overlay UI. **Treat as unverified;** verify on device.
- Official alternative: Ads Manager ad preview (with caveat "not specific to a device") and the template PNGs.

---

## 6. Official TikTok creative best-practice numbers

| Claim | Source | Date | Conf. |
|---|---|---|---|
| "Prioritize your hook in the first 6 seconds"; "Introduce your content proposition in the first 3 seconds" | https://ads.tiktok.com/help/article/creative-best-practices?lang=en [OFFICIAL] | Jun 2025 | High |
| "We recommend displaying 5-10 words per second when using text" (verbatim; note this is fast) | same | Jun 2025 | High (that it says this) |
| "3-5 different creatives per ad group and 3-5 diversified ad groups per campaign" | same | Jun 2025 | High |
| 9:16, "at least 720P", sound/music, UI safe zone | same + Creative Codes ("hi-res footage (720p or higher)", "save space on screen for the TikTok UI") | Jun 2025 / undated | High |
| Six Creative Codes: Think TikTok-first; Connect with trends; Be production-principled; Stick to a structure (hook, body, close); Hold attention with stimulation; Build with sound | https://ads.tiktok.com/business/en/creative-codes [OFFICIAL] | undated | High |
| "ads with sound drive significant lifts in purchase intent and brand favorability" (Kantar, Jan 2021) | Creative Codes [OFFICIAL] | — | High |
| "90% of ad recall impact is captured within the first six seconds" (TikTok "Value of View", 2020) | https://ads.tiktok.com/business/en-US/blog/creative-best-practices-top-performing-ads [OFFICIAL blog] | undated | High |
| "88% of TikTok users, sound is vital" (Kantar 2022); "74% … catch their attention" TikTok-first (Ipsos 2022); 77% like brands using trends (2021); product on screen +65% brand affinity, +25% recall (Lumen 2021); CTA cards +45% recall (2020) | same | — | High |
| ">63% of videos with highest CTR highlight key message/product in first 3 seconds"; vertical "25% higher 6-second watch-through rate"; "40% of auction ads with highest VTR" use text overlay; tracks "above 120 BPM" | https://ads.tiktok.com/business/en-US/blog/9-creative-tips-to-drive-auction-ad-performance [OFFICIAL blog] | 2020-10-21 (old) | High (dated) |
| "93% prefer sound on" | third-party only; no primary found | — | Low; do not use |

---

## 7. Pages that could not be fetched / gaps

- support.tiktok.com / tiktok.com/support (all articles): client-rendered, empty shell. So the official organic length, file size, cover and auto-caption how-to are unverified.
- help.instagram.com/1038071743007909 (Reel size): client-rendered; body not retrieved.
- facebook.com/business/help/980593475366490: WebFetch returned title only. **Text was recovered from embedded HTML via curl** (quotes in §2/§3 are verbatim).
- ads.tiktok.com/business/nl-NL/blog/66: 504 (the en-US version was fetched instead).
- Not found anywhere official: a TikTok organic safe zone, a TikTok/Instagram/YouTube loudness target, TikTok HDR handling, TikTok editor guides, comment-sheet geometry, or expanded "...more" caption geometry.
- The official template PNGs were downloaded to session scratch only for measurement. They are third-party images and are not in the repo (CLAUDE.md media rule); re-download from the spec pages above to re-measure.
