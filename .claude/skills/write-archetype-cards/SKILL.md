---
name: write-archetype-cards
description: A3 — write one scene archetype card (corpus/archetypes/<aid>.json) from `lens status --archetype <aid>`. A fill-in-the-blanks scene template in plain words; every number comes from the brief's `numbers`, copied verbatim. Used by the archetype-card-writer subagent.
disable-model-invocation: true
---

# write-archetype-cards (A3)

You write ONE scene archetype card: a reusable whole-scene template for premium SaaS explainers. A
builder (person or agent) will fill its slots with new content. Write plainly.

## Inputs
Run `uv run lens status --archetype <aid>`. The brief has:
- `numbers`: code-measured stats for the scenes sorted into this archetype (length, motion events,
  first motion, way in, beats, patterns, sound and its offsets from the scene start, examples);
- `members`: what A1 said about some of those shots (`what_happens`, `build_rebuild`) and their patterns;
- `pattern_cards`: pattern ids that have a card (you may only list these in `patterns`);
- `output` and `provenance` (copy it verbatim).

## Write `output` as JSON with exactly these fields
- `provenance`, `id`.
- `name`: 2–5 plain words, title case.
- `summary`: one or two sentences: what the viewer sees and what the scene is for.
- `when_to_use`: 1–4 bullets.
- `slots`: 1–8 pieces of content the scene takes, e.g. `{"name": "headline", "what": "one short claim",
  "required": true}`. Slot names are lowercase slugs.
- `steps`: the scene's beats in order (2–8), with no numbers.
- `patterns`: the pattern ids it uses, chosen from `numbers.pattern_mix` and `pattern_cards`.
- `build`: `gsap` (HyperFrames/GSAP: a timeline per scene, which tweens, stagger, ease families) and
  `remotion` (Sequence/spring structure).
- `sound`: how sound is cued in this scene, from `numbers.sfx_label_mix` and `sfx_offset_s_by_label`.
  Write "no typical sound" if there is no clear cue.
- `numbers`: the brief's `numbers`, **copied exactly**.
- `examples`: 1–5 entries copied from `numbers.examples`.
- `caveats`: up to 3 (few shots or videos, mixed members, no measured sound).

## Rules
- No number anywhere except inside `numbers` and `examples`.
- No brand names or quoted on-screen text in the prose. Describe the scene generically.
- Validate with `uv run lens validate <output>`, fix and re-validate until it passes.
