# TikTok study: findings

What 194 TikToks about AI, marketing, Claude, GEO and SEO do, measured by code and named by Claude, turned into
rules for Robert's reels.

Sources:
- `studies/tiktok/stats.json`: code, labelled **[stats]**.
- The 194 notes in `studies/tiktok/notes/`: Claude's names, counted, labelled **[notes]**.
- `studies/tiktok/config.yaml` and `study/tiktok/metrics.py`: what each measure means.

A number marked **[notes, keyword count]** was counted by matching words in the notes' `weaknesses` /
`why_it_works` / `for_robert` text. Treat it as approximate (±a few).

---

## 1. What was studied

**194 TikToks** ([studied.md](studied.md) lists them all with links): **AI 37, Claude 40, GEO 40, marketing 40,
SEO 37**. The plan was 200; six were photo posts and could not be measured (3 AI, 3 SEO).

**How they were found** (`studies/tiktok/candidates/`, `study/tiktok/sources.py`):
- Seeds were Robert's 50 accounts, checked through each creator's embed (`candidates/creators.jsonl`). The rest
  came from TikTok discover and tag pages for topic phrases (`topics*.jsonl`). Of the 194, **189 came from
  discover/tag pages and 5 from the creator seeds**.
- The caption had to match its topic's keyword regex (`select.topic_keywords` in `config.yaml`; first match wins;
  gaming and geography false hits are excluded).
- Filters: **≥ 50 likes**, an **English caption**, **12-180 s**, posted within the last 3 years, **≤ 5 per
  creator**, most-liked first, up to 40 per topic.
- The result: 158 creators, posted 2023-10 to 2026-10 (147 of them in 2026). The lowest like count is 61.

**How they were measured.** `study/tiktok/measure.py` reads the 576x1024 embed copy and writes `measure/<id>.json`,
summarised in `stats.json`. A Claude subagent wrote each note, 5 videos per subagent, from a contact sheet, a
0-3 s hook strip, the transcript and the measure file.

**Caveats on the measures** (from `metrics.py` and `config.yaml`):
- **Text share** is the share of 1 fps OCR samples with *any* text, TikTok's watermark removed. It counts titles,
  UI, code and captions alike, so it sits near 1.0.
- **"Caption"** means any OCR text **≥ 2.5 % of frame height**, which includes big titles, not only burned-in
  subtitles. Read `caption_share` as "big text on screen".
- **Face** is the largest face ≥ 6 % of frame height per 1 fps sample (YuNet). Faces inside B-roll or
  screenshots count too.
- **first_word_s** is the first transcribed word (faster-whisper). It is 0.0 for most videos: speech starts at
  once, but the measure cannot tell how fast inside the first second.
- **Events** are lens motion events: graphics coming in, big gestures, cut-ins. They are *not* only graphics.
- **Punches** are global zooms of ≥ 5 %; handheld push-ins count.
- **Loop** is pixel similarity between the first and last frame (1 = identical), not a narrative loop.
- **Music bed** is the RMS level in the gaps between words, so room noise also raises it.
- **Top quarter** means the 48 videos with the most plays (about 452k plays or more). "Rest" is the other 146.

---

## 2. The shape of a TikTok in this niche [stats]

| Measure | Median | p25-p75 | Top quarter (median) | Rest (median) |
|---|---|---|---|---|
| Length (s) | **59** | 39-88 | **49** (29-74) | 60 (44-91) |
| Cuts per minute | 4.1 | 0.8-11.7 | 3.9 | 4.1 |
| Median shot length (s) | 7.9 | 3.5-25 | 9.1 | 7.8 |
| First cut (s), 154 videos with a cut | 5.8 | 3.3-13.7 | 6.1 | 5.7 |
| Words per second | **3.35** | 3.0-3.8 | 3.28 | 3.38 |
| First word (s) | **0.0** | 0.0-0.0 | 0.0 | 0.0 |
| Silence share | 0.11 | 0.08-0.16 | 0.12 | 0.10 |
| Face on screen (share of samples) | **0.92** | 0.39-1.0 | **0.76** | 0.96 |
| Face height (share of frame) | **0.27** | 0.19-0.35 | 0.25 | 0.28 |
| Face centre, vertical (0 top, 1 bottom) | 0.45 | 0.38-0.52 | 0.46 | 0.44 |
| Any text on screen | 0.98 | 0.96-0.99 | 0.98 | 0.98 |
| Big text (≥ 2.5 % high) on screen | 0.97 | 0.93-0.99 | 0.97 | 0.97 |
| Big-text height (share of frame) | 0.039 | 0.033-0.047 | 0.037 | 0.040 |
| Text outside the safe core | 0.77 | 0.65-0.90 | 0.81 | 0.76 |
| Motion events per minute | **2.5** | 0.7-5.3 | **4.5** (0.9-10.7) | 2.1 (0.7-4.2) |
| Punch-ins per minute | **0** | 0-1.4 | 0 (0-1.5) | 0 (0-1.3) |
| Loudness (LUFS) | -21.6 | -25.8 to -16.5 | -21.2 | -22.1 |
| Music bed in word gaps (dBFS), 165 videos with gaps | -31.1 | -39.4 to -23.5 | **-27.1** | -32.3 |
| Loop (first vs last frame) | 0.83 | 0.77-0.88 | 0.83 | 0.83 |

What this means in plain terms:
- **The typical video:** a person starts talking on frame one at about 3.3 words/s. The face is about a quarter
  of the frame tall and slightly above centre. Big text is on screen almost all the time.
- **Cutting is mostly slow.** The median shot is about 8 s, and a quarter of videos hold shots of 25 s or more.
- **The top quarter differs from the rest in four ways:**
  - it is **shorter** (49 s vs 60 s);
  - it shows the **face less** (0.76 vs 0.96), handing the frame to proof more often;
  - it has about **twice the motion events** (4.5 vs 2.1 per minute, one every ~13 s instead of every ~28 s);
  - its **music bed is louder** (-27 vs -32 dB). The notes agree: 28 of the 48 top videos have a music bed, vs
    58 of the other 146.
- **Zooms are rare.** More than half of the videos have none.

---

## 3. Formats and what they're used for [notes; measures from stats `by_format`]

| Format | Count (top 48) | Length s | Cuts/min | Events/min | Face share | Used for |
|---|---|---|---|---|---|---|
| talking_head | **72** (12) | 72 | 2.8 | 1.1 | 1.0 | Opinions, tips, news takes; the default in GEO/SEO/marketing |
| split_screen (face + screen/visual) | 36 (7) | 54 | 10.9 | 3.0 | 0.72 | Claude/AI tool lists: face on one half, proof changing on the other |
| tutorial_demo | 23 (6) | 58 | 7.4 | 2.4 | 0.33 | Step-by-step on a real screen, often phone-filmed |
| green_screen | 15 (7) | 81 | 4.0 | 3.2 | 1.0 | The evidence (post, chart, bad example) behind the speaker |
| screen_recording | 9 (5) | 32 | 0 | 14.4 | 0.12 | Silent ChatGPT trend clips |
| skit | 8 (3) | 33 | 15.3 | 4.0 | 0.75 | Role montages, POV, a doubter character |
| news_reaction 6, animation 5, other 5, listicle_text 4, product_demo 3, voiceover_broll 3, interview 3, podcast_clip 2 | | | | | | |

How the top quarter's format mix differs from the rest (stats `named.format`):

| Format | Top quarter | Rest |
|---|---|---|
| green_screen | 15 % | 6 % |
| talking_head | 25 % | 41 % |
| screen_recording | 10 % | 3 % |

The leading formats by topic (stats `by_topic`):
- **Claude:** split screen, 16 of 40.
- **GEO:** talking head, 22 of 40.
- **SEO:** talking head 17 and tutorial 8, of 37.
- **Marketing:** talking head 18 of 40, plus 4 skits.
- **AI:** the most mixed: split screen 8, talking head 6, screen recording 5, green screen 5.

Robert's format is closest to **talking head or split screen with widgets**.

---

## 4. Hooks [notes]

| Hook type | All (194) | Top 48 | Rest 146 |
|---|---|---|---|
| bold_claim | 40 | 8 | 32 |
| list_promise | 29 | 6 | 23 |
| result_first | 21 | 4 | 17 |
| news | 21 | 5 | 16 |
| callout (names the viewer) | 18 | 5 | 13 |
| curiosity_gap | 17 | **9** | 8 |
| story / question / pattern_interrupt | 11 / 11 / 11 | 2 / 2 / **5** | 9 / 9 / 6 |
| problem / demo_first / other | 10 / 4 / 1 | 1 / 1 / 0 | 9 / 3 / 1 |

- **The top quarter leans on curiosity gaps** (19 % vs 5 %) **and pattern interrupts** (10 % vs 4 %) [stats].
  Several of those top curiosity-gap videos are silent ChatGPT trend screen recordings, so part of this is a
  format effect.
- **Speech starts at 0.0 s** in at least 75 % of videos [stats `first_word_s`].
- **Slow starts hurt.** About 16 notes flag credentials or an intro before the first tip, sometimes 20-55 s long
  [notes, keyword count].

**Strong opening patterns from the notes** (paraphrased):
1. **The result in frame one.** A sales bar climbs from $0 to five figures, or a view counter ticks to 1M, while
   the promise is spoken; the method comes after. (@profaura_, @bryanfahim)
2. **A physical move in the first second.** Glasses whipped off at the lens (@viralbestiesclub), a lunge into
   frame (@majiqq), a box sliding into an empty shop on its own (@kiri.visual).
3. **A mascot acts out the hook verb.** A pixel mascot swings a hammer and greys out "agency" cards at 1.5-2.8 s,
   then a hard cut back to the face (@nathanhodgson.ai).
4. **A number promise with hands and a title pill.** Five fingers held up, the title swapping to "#1 …" by 2 s
   (@maverickgpt, @taki.gpt).
5. **A callout that names one exact viewer.** "So you finally moved to Claude from ChatGPT" (@bigpictureclub);
   "Don't use Claude Code unless…" (@milesreevesai).
6. **One picture per word.** Each key word of the first line gets its own cutaway in the first 3 s, then the
   video settles on the face (@agilesingh).
7. **An equation in frame one.** Logo + logo = $0 (@forcceee_).
8. **Claim, then the answer within 2 s.** "SEO is dead", then an hourglass and "the future is GEO" (@isiqat).
9. **A reversal in one sentence.** "Stop creating content, start creating culture" (@dmitrihasideas); "Google
   gave you 10 blue links; AI gives one answer" (@beardpreneur).
10. **A cold open on the most surprising line** from later in the video, then the context (@realhorrortok).

---

## 5. Graphics: how much is enough

**Density as named by Claude** [notes]:

| | All | Top 48 | Rest 146 |
|---|---|---|---|
| Minimal | 82 (42 %) | **22 (46 %)** | 60 (41 %) |
| Moderate | 70 (36 %) | 14 (29 %) | 56 (38 %) |
| Heavy | 42 (22 %) | 12 (25 %) | 30 (21 %) |

**What the tiers mean in numbers:**

| Tier | Claude's estimate of graphic changes per minute [notes `per_minute_estimate`] | Measured motion events per minute [`measure/*.json`] |
|---|---|---|
| Minimal | 3 (2-5) | 1.2 |
| Moderate | 10.5 (8-14) | 3.0 |
| Heavy | 25 (20-30) | 3.8 |

The estimates are Claude's, not a measurement.

**Face-led formats only** (talking head, split screen, green screen) [computed from `measure/*.json`]:

| | Videos | Events per minute, median | p25-p75 | Punches per minute, p75 |
|---|---|---|---|---|
| Top quarter | 26 | **3.5** (one every ~17 s) | 1.0-7.0 | 0 |
| Rest | 97 | 1.7 | 0.5-3.6 | 0.7 |

**Devices** [notes, out of 194, top 48 in brackets]:

| Device | Count | Device | Count |
|---|---|---|---|
| title text | 170 (40) | camera move | 39 (11) |
| jump cut | 128 (29) | sticker or emoji | 33 (8) |
| music bed | 86 (28) | arrow or circle | 21 (8) |
| product UI | 85 (24) | green-screen background | 19 (8) |
| screenshot | 76 (15) | prop | 15 |
| screen recording | 71 (17) | meme cutaway | 7 |
| zoom punch | 61 (14) | sound effect | 6 (4) |
| chart or number | 49 (11) | mascot | 4 (2) |
| split screen | 44 (10) | progress bar | 3 |
| B-roll | 41 (only 5 in the top quarter) | | |

A video uses a median of 5 devices (p25-p75: 3-6), the same in the top quarter.

**What the notes complain about** [notes, keyword count over `weaknesses`]:

| Weakness | Notes (top 48 in brackets) |
|---|---|
| **Too static**: long holds, one take, no visual change. The most common weakness. | **87 of 194** (21) |
| Text too small or unreadable | 92 (22) |
| Claims told, not shown | about 30 |
| **Clutter** (read by hand): captions fighting UI text or a second text block, captions jumping bands, cards flashing too fast to read, busy backgrounds behind captions | about **23** (7) |
| Graphics or the head covering the thing being shown | 13 |

**Robert's "animations are overused", answered in numbers:**
- **The norm in this niche is few graphic events.** The median is 2.5 per minute and p75 is 5.3. Even the top
  quarter's face-led videos sit at about **3.5 per minute (p75 7)**, one graphic event every 9-17 s.
- **Most top videos are minimal** (22 of 48). Claude's "heavy" tier is about 25 graphic changes a minute, one
  every ~2.4 s. Only 12 of the 48 top videos are heavy, and many of those are faceless (animation, screen
  recordings) or very short.
- **What top videos do is one visual per idea, on the word that names it.** "Each claim / step / item gets its
  own …" appears in the `why_it_works` of 83 notes, 26 of them in the top quarter [notes, keyword count].
- **Clutter means layers competing**, not just a high count: text over text, captions over UI, things passing
  too fast.
- **The fix:** fewer graphics, each larger, one at a time, each tied to an idea.
- **And still change the picture at least every 10-15 s.** Most videos fail by being too static, not too busy.

---

## 6. Captions and on-screen text

| Caption style [notes] | All | Top 48 |
|---|---|---|
| word_by_word | **101** | 22 |
| title_only | 43 | **15** |
| sentence | 41 | 10 |
| native_tiktok | 5 | 1 |
| none | 4 | 0 |

| Caption position [notes] | All | Top 48 |
|---|---|---|
| bottom | 66 | 11 |
| middle | 63 | **19** |
| mixed | 35 | 8 |
| top | 26 | 10 |
| none | 4 | 0 |

- **The top quarter** uses title-only more (31 % vs 19 %) and middle placement more (40 % vs 30 %) [stats].
- **Size** [stats]: big text has a median height of **0.039 of the frame** (p25-p75 0.033-0.047), about 63-90 px
  on a 1920-px frame.
  - 92 notes call text too small or unreadable [notes, keyword count].
  - They mostly mean UI and screenshots at about 2 % of frame height, and small word captions at about
    3.3-3.5 %.
- **Persistent title:** title text is in 170 of 194 videos. 24 notes praise a fixed or pinned title or label that
  tells late joiners the topic [notes].
- **Safe area:** 77 % of text sits outside the safe core (median) [stats]. 52 notes flag a risk of collision with
  TikTok's UI [notes, keyword count].
- **Jumping caption bands** (top, then seam, then bottom) are named as a weakness in 5 notes.

---

## 7. Characters, mascots and props [notes]

**21 of 194 videos (11 %) have a character**, and 7 of the top 48 (15 %). They have 22 characters between them:
- 14 come back after leaving; 8 appear once.
- 4 are pixel-art mascots, all in Claude or AI split-screen videos.
- 9 are props used as characters: glasses, a foam pointer hand, an Apple Pencil, a laptop, a Mac stack, cardboard
  hands, a delivery box, a surfboard, a mic.
- 7 are people in skits: a doubter, clones, a sibling's voice, a crew member.
- 2 are non-human "voices": AI phones, an AI comic.

**Mascots are underused.** 3 of the 4 pixel mascots appear once, as a static badge or a single gag, and never
return. The notes say so directly ("the mascot appears once and is gone", "the gag is used once and never
returns").

What the good ones do:
- **Enter on the hook, act out every point, return for the ask.** An orange Claude cube drops in at 0 s, spawns
  mini-cubes, splits into "plans" and "builds", makes way for UI and comes back (@nocode.joshua).
- **A one-second gag that makes the claim visible,** then a hard cut back to the face (@nathanhodgson.ai). The
  note advises bringing it back once later.
- **The doubter who cuts in.** A second character asks the viewer's question ("five of what?"), the expert
  answers, and the follow ask lands as the doubter's punchline (@personalbrandlaunch0).
- **An off-camera questioner.** A voice asks the hook question and reacts once, so the speaker answers instead of
  lecturing (@silentmiddlechild). The note advises bringing it back.
- **The pointer.** A foam hand or pencil enters to tap each item as it is named and leaves during other shots
  (@androoagi, @katesmoothy). This is the move Robert's widgets need.
- **A small side task** (peeling a mandarin) gives a long single take motion without cuts (@sellanythingonline).
- **Labelled roles that trade lines in a fixed order,** e.g. SEO / AEO / GEO clones (@neilpatel).

The `for_robert` lines name Fred in 174 of 194 notes. The jobs they suggest:

| Job for Fred | `for_robert` lines |
|---|---|
| Point at, tap or circle the exact thing named | 57 |
| Hold up a sign, card or number | 57 |
| Enter, pop in, swim off, duck out or come back | 49 |

78 of those lines include an "avoid" or "instead of" [notes, keyword count].

---

## 8. Story shapes and CTAs [notes]

**Beats.** The median note lists **9 beats** (8-10). The recurring shapes:
1. **Promise, numbered items, ask.** 29 list promises; 79 `why_it_works` lines credit a number or progress marker
   (fingers, "1/4", ordinal cards, "Step N").
2. **Result or proof first, then the method, then the ask.** 21 result_first and 4 demo_first hooks; 43
   `why_it_works` lines credit showing the result or proof before the explanation.
3. **News, why it matters, the take, a comment question.**
4. **Claim, the one mechanism, the proof screenshot.** Its weakness is skipping the proof (about 30 "told, not
   shown").
5. **Why, a pivot ("so how do you do it?"), how.** The halfway pivot is where to add fresh visuals.

Also recurring:
- **One layout change to mark the payoff,** e.g. the speaker shrinks to a corner so the chart takes the frame.
- **Series framing** ("Part 4", "Day 15", "episode 2") is credited in 19 notes.
- **A loop ending** (cut right after the payoff, or end on the opening line) is credited in 28 notes, 11 of them
  in the top quarter.

**CTA type:**

| CTA | All | Top 48 |
|---|---|---|
| none | **66** | 16 |
| comment | **57** | 15 |
| follow | 34 | 8 |
| save_or_share | 12 | 4 |
| other | 9 | 1 |
| product | 8 | 2 |
| link_in_bio | 8 | 2 |

- **Comment-a-keyword** (comment a word to get the prompt, guide or link) is the dominant working ask. It is
  mentioned in 49 notes, 13 of them in the top quarter, and the notes often tie it to comment counts in the
  thousands.
- **Timing** (118 videos with a timed CTA): the ask comes at **0.92 of the length** at the median (0.89-0.97), or
  **3.6 s before the end** (1.3-7.3 s). Only 9 put it in the first half.
- **Problems** [notes, keyword count]:
  - two or more stacked asks: 14 notes;
  - no ask at all, or the ask only in the post caption: about 56;
  - ending mid-sentence or abruptly: 24, sometimes on purpose for the loop.

---

## 9. By topic [stats `by_topic`; top-quarter counts from notes + plays]

| | AI (37) | Claude (40) | GEO (40) | Marketing (40) | SEO (37) |
|---|---|---|---|---|---|
| In top quarter | **16** | 11 | **2** | 13 | 6 |
| Length s | 49 | 50 | 63 | 68 | **76** |
| Cuts/min | 3.1 | **7.8** | 3.5 | **8.1** | 2.7 |
| Events/min | 2.2 | 3.1 | **0.9** | **4.1** | 2.6 |
| Face share | 0.70 | 0.79 | **1.0** | 0.85 | 0.96 |
| Words/s | 3.15 | 3.33 | 3.31 | 3.60 | 3.49 |
| Density heavy / minimal | 27 % / 43 % | 30 % / 28 % | **3 % / 63 %** | 35 % / 28 % | 14 % / 51 % |
| Lead format | split 22 % | **split 40 %** | talking head 55 % | talking head 45 % | talking head 46 %, tutorial 22 % |
| Lead hook | bold claim 27 %, curiosity gap 22 % | list promise 23 % | bold claim 18 %, result first 15 % | bold claim 25 % | list promise 22 % |
| Lead CTA | **comment 43 %** | none 40 %, comment 35 % | none 33 % | **follow 35 %** | none 38 % |
| With characters | 14 % | 10 % | 10 % | 15 % | 5 % |

- **AI:** trend-driven. It has the most viral reach here, including faceless ChatGPT screen recordings. Hooks are
  bold claims and curiosity gaps; comment-keyword asks are common.
- **Claude:** split screen (face below, cards or UI above), "N secret codes / N plugins" lists, ordinal title
  cards, fast cutting. All 4 pixel mascots live here.
- **GEO:** almost all single-take talking heads with very few visuals (0.9 events/min). It is the weakest topic by
  plays (2 of the top 48). The notes keep asking for the missing proof: the AI answer screenshot, the citation.
  There is room to stand out here with clear proof visuals.
- **Marketing:** the fastest cutting and busiest graphics, plus most of the skits. Follow is the main CTA.
- **SEO:** the longest videos. Mostly "how to get out of view jail" TikTok-SEO tutorials and phone-filmed
  screens. "Reply to comment" stickers and persistent "Part N" titles recur.

---

## 10. Rules for Robert's reels

Each rule names its source. "Events" means a widget, prop or Fred action coming in, or a layout change.

| # | Rule | Traced to |
|---|---|---|
| 1 | **Length 30-75 s; aim for about 50 s.** One idea per reel. | Top-quarter length median 49 s (p25-p75 29-74) vs rest 60 [stats] |
| 2 | **First word at 0.0 s.** No intro or credentials before the hook; credentials take one line at most. | first_word_s median and p75 = 0 [stats]; about 16 slow-start weaknesses [notes] |
| 3 | **By 2 s, show the result, the object or the one-line reversal**, not a logo or a title card alone. | Result/proof first credited in 43 notes; opening patterns in §4 [notes] |
| 4 | **Speak at 3.0-3.8 words/s, with silence ≤ 15 %.** | words_per_s p25-p75 3.0-3.8; silence p75 0.16 [stats] |
| 5 | **Face on screen 60-90 % of the time, 0.19-0.35 of the frame tall, centred around 0.45.** Hand the full frame to proof only for its beat. | face_share top 0.76 vs rest 0.96; face_height p25-p75; face_cy [stats] |
| 6 | **3-7 graphic events per minute in a talking reel, one per idea, on the word that names it.** Never more than one new animated element at a time. | Top-quarter face-led events 3.5/min (p75 7) [measure files]; 83 "each claim gets its own visual" [notes] |
| 7 | **Do not go "heavy".** Stay under about 10 graphic changes a minute, counting caption pops; heavy (~25/min) is a faceless-format style. | per_minute_estimate moderate 10.5, heavy 25; 22 of 48 top videos minimal [notes] |
| 8 | **The picture still changes at least every 10-15 s** (a cut, punch, layout change or Fred). No 30-100 s static holds. | Too-static weakness in 87 of 194 [notes]; shot median 7.9 s [stats] |
| 9 | **0-1.5 zoom punches per minute**, saved for the key line. | punches_per_min median 0, p75 1.4 [stats] |
| 10 | **Captions word-by-word or in 2-3-word chunks, at least 0.045 of frame height (about 86 px at 1920), in one fixed band.** The band never jumps, and Fred and widgets never overlap it. | caption_height p75 0.047 [stats]; 92 small-text and 5 jumping-band weaknesses [notes] |
| 11 | **All text inside the safe core** (x 120-780, y 288-1248 of 1080x1920). | outside_safe_share median 0.77; flagged in 52 notes [stats, notes] |
| 12 | **One persistent title label (topic, plus "Part N" for a series), pinned top or middle.** | title_text in 170 of 194 (40 of 48); pinned title credited in 24 notes [notes] |
| 13 | **Show every claim within about 3 s of saying it** (screenshot, number, AI answer), large enough to read. | Told-not-shown in about 30 notes; unreadable proof in 92 [notes] |
| 14 | **Fred acts in and out: 2-4 appearances per reel, 1-3 s each, each with a job** (act out the hook verb, point at or tap the proof, hold the number or keyword, doubt or react). He **exits between appearances**, **returns for the CTA**, and is not on screen all the time. | 14 of 22 characters return; 3 of 4 mascots used once and flagged; 57 point/tap and 49 enter/exit/return suggestions [notes] |
| 15 | **For lists, an on-screen counter** (fingers, "2/4", Fred holding the number). | 29 list promises; 79 notes credit numbers or progress [notes] |
| 16 | **One CTA, ideally comment-a-keyword, 2-7 s before the end.** Never two stacked. | CTA at 0.92 of length, 3.6 s before the end (1.3-7.3) [notes]; keyword in 49 notes; 14 stacked-CTA weaknesses |
| 17 | **End on the line or frame that leads back to the start** (cut right after the payoff). | loop median 0.83 [stats]; loop credited in 28 notes, 11 top [notes] |
| 18 | **Loudness about -16 to -21 LUFS, with a quiet music bed in the gaps (about -27 dBFS).** Sound effects are rare; save them for Fred's actions. | loudness p75 -16.5; top music bed -27.1 vs -32.3; quiet audio flagged in 35 notes; SFX 6 of 194 (4 top) [stats, notes] |

---

## 11. Limits

- **Plays are a weak success signal.** They reflect account size, ads and trends as much as editing (one brand
  account had 1.6M plays on about 3k likes). The top quarter is also skewed by topic (AI 16, GEO 2), so top vs
  rest partly compares topics.
- **Selection bias.**
  - Videos came from discover and tag pages, chosen by likes (≥ 50), so failures are not in the sample.
  - Only 5 came from Robert's own seed accounts.
  - "English" was tested on the caption only; a few videos speak Taglish, Filipino or Russian.
  - 3 are off-topic: an "AEO" musician, an "AEO" motocross team, and an SEO-tagged skit.
- **Measure limits.**
  - **OCR:** text share counts any text (UI, code); "caption" means any text ≥ 2.5 % of frame height, so titles
    count. It samples at 1 fps on a 432-px-wide copy, so small or fast text is missed.
  - **Faces:** faces in B-roll, screenshots or clones count; faces under 6 % of frame height do not.
  - **Events** include gestures and cut-ins, not only graphics.
  - **Punches** miss crop zooms of less than 5 %.
  - **Loop** is pixel similarity, not story.
  - **Music bed** includes room noise.
  - **first_word_s** is 0.0 for most videos, so it cannot rank hooks within the first second.
- **Claude's names are judgments.** Density tiers, `per_minute_estimate` and devices come from a contact sheet and
  a hook strip, not from every frame. Keyword counts in this file are approximate.
- **6 of the 200 are missing** (photo posts: 3 AI, 3 SEO). One extra trial note on disk (`7623424611530640647`)
  is outside the 194 and not counted.
- **YouTube Shorts are not included yet.** They need the laptop fetch (`scripts/study_youtube_fetch.py`,
  `studies/youtube-fetch.md`).
- **Robert's own reels are not measured here.** To check a reel against these rules, run the same measure on it.
