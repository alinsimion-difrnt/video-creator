---
name: annotate-pixel
description: Pixel-art study (studies/README.md, track 2) — write the note for up to 5 pixel-art subjects (studies/pixel-art/notes/<id>.json): a game, style, artist, creator, tutorial or talk from studies/pixel-art/sources.yaml, or a pixel-art TikTok clip from studies/pixel-art/tiktok.yaml. Names the palette, lighting, silhouette, motion, texture, camera and how characters act in and out of the scene, plus what Fred and Pixie should take from it. Used by a subagent given a list of ids.
---

# annotate-pixel

You are studying pixel art so Robert's pixel characters, Fred (a carp) and Pixie (a cat), look and act
better in his TikToks. Robert's complaint about the last reel: the animations were overused, and Fred never
acted *in and out* of the scene. He should exit, come back, do the thing again, go away, appear small in the
background and do something there. So pay most attention to acting and timing.

## For each id you were given
1. Find it in `studies/pixel-art/sources.yaml` (a subject) or `studies/pixel-art/tiktok.yaml` (a clip).
2. Read what exists for it:
   - **Clip:**
     - `data/study/pixel/work/<id>/sheet.jpg` (12 frames with times);
     - `studies/pixel-art/clips/<id>.json` (holds, palette, scale; code-measured: hold numbers on a TikTok
       copy are rough, because compression and camera moves add changes);
     - the caption in tiktok.yaml.
   - **Subject with GIFs:**
     - `data/study/pixel/work/<id>/*.png` (GIF frames labelled with their delays);
     - `studies/pixel-art/metrics/<id>.json` (exact frame timings, palette sizes, ramps).
   - **Game, style or artist:** `data/study/pixel/work/<id>/clip*.jpg`, frame sheets (12 frames with
     times) of up to 3 of the most-liked TikToks under the subject's tag. They show how it really looks
     and moves. Look at every sheet, and ignore a clip that is clearly not the subject (fan art in another
     style, a meme). When a note already exists (written from text only), rewrite it with what the
     frames show.
   - **Every subject:** fetch its `refs` URLs that are articles or wiki pages with WebFetch, and ask for
     what the page says about the art, animation, palette, lighting and characters. Skip `video` refs:
     YouTube is blocked here.
3. Write `studies/pixel-art/notes/<id>.json` (shape below).
4. Run `uv run python -m study.pixel validate studies/pixel-art/notes/<id>.json` and fix it until it passes.

## Rules
- **Numbers come from the metrics files** when they exist: palette size, hold times, frame counts.
  Otherwise describe; do not invent figures. `colours_estimate` stays null when you cannot see or measure it.
- **feel** is one line in Robert's style: "low-contrast background + high-contrast hero + 2-frame idle
  bounce = readable cozy mood".
- **techniques** are named and concrete: "hue-shifted ramps: shadows to purple, lights to yellow",
  "smear frame on the swing", "2-frame anticipation before the jump", "selective outline, dark only on the
  shadow side".
- **acting:** how characters enter, act, exit, come back and use depth (small in the background, close in
  front). If the subject shows no characters, say what its scenes teach about staging.
- **for_fred:** one or two moves Fred or Pixie should adopt, or one thing to avoid, with how to do it in a
  short vertical reel.
- **Quoting:** no quotes longer than a short phrase from articles; paraphrase.
- **sources:** list the URLs and files you actually used.

## Shape
```json
{
  "provenance": {"schema_version": 1, "tool_version": "0.1.0", "stage": "pixel_notes", "annotator": "claude-code",
                 "input_hash": "<the metrics/clip file's provenance.input_hash, or 64 zeros when there is none>",
                 "created_at": "<now, ISO 8601>"},
  "id": "<id>",
  "kind": "game | style | artist | creator | tutorial | talk | clip",
  "palette": {"colours_estimate": 16, "shadows": "cool | warm | neutral | mixed | unknown", "notes": "..."},
  "lighting": "...",
  "silhouette": "...",
  "motion": {"timing": "...", "principles": ["anticipation", "squash and stretch"]},
  "texture": "...",
  "camera": "...",
  "sound": "",
  "acting": {"enters": "...", "acts": "...", "exits": "...", "comes_back": true, "depth": "..."},
  "techniques": ["...", "..."],
  "feel": "...",
  "for_fred": "...",
  "sources": ["https://...", "data/study/pixel/work/<id>/sheet.jpg"]
}
```

## Report
One line per id: `<id> ok` or `<id> failed: <why>`. Nothing else.
