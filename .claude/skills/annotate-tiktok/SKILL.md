---
name: annotate-tiktok
description: TikTok study (studies/README.md, track 1) — write the notes for up to 5 TikToks (studies/tiktok/notes/<id>.json) from each video's packet: contact sheet, 0-3 s hook strip, transcript, caption and measured numbers. Names what the code measured (format, hook, beats, graphics, characters, CTA, why it works). Used by a subagent given a list of video ids.
---

# annotate-tiktok

You are studying short-form videos on AI, marketing, Claude, GEO and SEO so Robert's own TikToks get
better. Code already measured each video. Your job is to name what it does, in plain words.

## For each id you were given
1. Read these files, and only these:
   - `data/study/tiktok/work/<id>/packet.json` — `sheet_times` (contact sheet), `hook_times` (hook strip),
     `cut_times`, `event_times` (motion starts), `punch_times` (zooms), and `allowed_times` (all of them).
   - `data/study/tiktok/work/<id>/sheet.jpg` — evenly spaced frames, each labelled with its time.
   - `data/study/tiktok/work/<id>/hook.jpg` — the first 3 s.
   - `data/study/tiktok/work/<id>/words.json` — the transcript: `[word, start, end]`.
   - `studies/tiktok/measure/<id>.json` — the numbers: cuts, words/s, text layout, face, hook, density,
     sound, loop.
   - `data/study/tiktok/meta/<id>.json` or `data/study/tiktok/<id>.json` — caption, plays, likes.
   - Optional: `data/study/tiktok/work/<id>/ocr.json` — on-screen text boxes `[t, x0, y0, x1, y1, text]`,
     when you need to read a caption or title the sheet shows too small.
   In the measure file, `text_*` counts all on-screen text (code in a screen recording too); `caption_*`
   counts only caption-sized text (at least 2.5% of the frame height).
2. Write `studies/tiktok/notes/<id>.json` (the shape is below).
3. Run `uv run python -m study.tiktok validate studies/tiktok/notes/<id>.json` and fix it until it passes.

## Rules
- **Times.** Every `t` (beats, cta) must be one of `allowed_times` in the packet. Never invent a time; when
  no allowed time fits, leave the beat out or set `cta.t` to null.
- **Short quotes only.** `hook.line` is the opening line paraphrased, or quoted in under 20 words. Do not copy
  the transcript or the caption at length.
- **Numbers come from the measure file.** Your `per_minute_estimate` is the only number you estimate.
- **Be concrete.** Write "a red circle around the price at 4 s", not "engaging visuals". Each
  `why_it_works` item names a mechanism (for example: "result shown before the explanation, so the
  viewer stays to see how").
- **Formats.** `split_screen` is a face over (or beside) a screen recording or a picture; `green_screen` is
  the face cut out over a background image. With no captions, `caption_position` is `none`.
- **for_robert** answers one thing: what one move from this video his talking-head reels with a pixel-art
  mascot could use, or what to avoid.
- **characters.** Fill this when a mascot, puppet, prop or costume character appears: how it enters, what
  it does, how it exits, whether it comes back. Robert wants his fish, Fred, to act in and out of the scene.
- Only use the files above. Do not search the web. Do not open other notes, so each note stays independent.

## Shape
```json
{
  "provenance": {"schema_version": 1, "tool_version": "0.1.0", "stage": "tiktok_notes",
                 "annotator": "claude-code", "input_hash": "<the measure file's provenance.input_hash>",
                 "created_at": "<now, ISO 8601>"},
  "id": "<id>",
  "format": "talking_head | green_screen | split_screen | screen_recording | voiceover_broll | skit | podcast_clip | interview | listicle_text | tutorial_demo | news_reaction | product_demo | animation | other",
  "hook": {"type": "question | bold_claim | result_first | curiosity_gap | pattern_interrupt | problem | news | demo_first | list_promise | story | callout | other",
           "line": "...", "visual": "what the first frames show"},
  "beats": [{"t": 0.0, "what": "..."}],
  "graphics": {"captions": "none | word_by_word | sentence | native_tiktok | title_only",
               "caption_position": "top | middle | bottom | mixed | none",
               "devices": ["screen_recording", "screenshot", "arrow_or_circle", "zoom_punch", "sticker_emoji", "meme_cutaway", "b_roll", "title_text", "progress_bar", "split_screen", "green_screen_bg", "product_ui", "chart_or_number", "mascot", "prop", "sound_effect", "music_bed", "jump_cut", "camera_move", "costume_or_skit", "none"],
               "density": "minimal | moderate | heavy", "per_minute_estimate": 6},
  "characters": [{"who": "...", "enters": "...", "acts": "...", "exits": "...", "comes_back": false}],
  "cta": {"kind": "follow | comment | link_in_bio | product | save_or_share | none | other", "t": null},
  "why_it_works": ["..."],
  "weaknesses": ["..."],
  "for_robert": "..."
}
```
Up to 10 beats, 1-4 `why_it_works`, up to 4 `weaknesses`.

## Report
One line per id: `<id> ok` or `<id> failed: <why>`. Nothing else.
