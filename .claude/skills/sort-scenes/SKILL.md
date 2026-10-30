---
name: sort-scenes
description: A3 — sort every shot of one batch into a scene archetype (taxonomy scene_archetype) or `other` with a proposed name, from text only (`lens status --scenes <batch>`). Used by the scene-sorter subagent.
disable-model-invocation: true
---

# sort-scenes (A3)

You sort shots of premium SaaS explainers into **scene archetypes**: reusable whole-scene templates a
builder can fill with new content. You see no images. Each shot comes with what the A1 annotator wrote
about it (`what_happens`, `focal_element`, `shot_type`, `composition`, `text_word_count`), its story beat,
its place in the video, and the motion patterns of its events.

## Inputs
Run `uv run lens status --scenes <batch>`. The brief has `shots`, `output` (the only file you write) and
`provenance` (copy it verbatim). Read `taxonomy/v1.yaml` for the `scene_archetype` list and its comments.

## Write `output` as JSON
```
{"provenance": <from the brief>, "batch": "<batch>", "items": [
  {"video": "...", "shot": "s003", "archetype": "stat_count_up", "confidence": "high"},
  {"video": "...", "shot": "s004", "archetype": "other", "proposed_name": "chat demo panel", "confidence": "medium"}
]}
```
Write exactly one item per shot in the brief, in the brief's order.

## How to choose
- Pick the archetype whose **layout and job** match the scene as a whole, not one element of it.
  A shot that ends on the brand mark after the CTA is `logo_close` even if text animates first.
- Use `other` when none fits. Give a reusable `proposed_name` of 2–4 plain words that names the
  scene type, not the brand. For example "presenter to camera", "product ui tour", "chat demo panel",
  "lifestyle footage", "hero product render" or "title card".
  - Reuse the same proposed names across shots for the same kind of scene, so they can be grouped.
    Names already in use (prefer these when they fit): "product ui tour", "prompt input card",
    "title card", "kinetic statement card", "presenter to camera", "lifestyle footage",
    "hero product render", "logo intro sting", "screenshot timeline carousel", "search query stage",
    "ai working loader", "chat demo panel".
- `confidence`: high when the text clearly describes the archetype, medium when it is likely, low when
  you are guessing between two.
- Do not invent details that are not in the brief.

Validate with `uv run lens validate <output>`, fix and re-validate until it passes.
