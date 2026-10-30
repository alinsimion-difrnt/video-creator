---
name: write-pattern-cards
description: A3 — write one pattern card (corpus/patterns/<pid>.json) from `lens status --card <pid>`. Plain words for what the pattern is, when to use it and how to build it; every number comes from the brief's `numbers`, copied verbatim. Used by the pattern-card-writer subagent.
disable-model-invocation: true
---

# write-pattern-cards (A3)

You write ONE pattern card for a motion pattern found across premium SaaS explainers. The reader is a
designer or developer rebuilding it, and also someone with no motion vocabulary: write plainly.

## Inputs
Run `uv run lens status --card <pid>`. The brief has:
- `numbers`: the pattern's measured corpus stats (durations, easing, change and role mixes, sound,
  examples). Code measured these.
- `members`: what the annotators said about some of its events (description, why premium, build hint,
  elements) in their own words;
- `output`: the only file you write;
- `provenance`: copy it verbatim.

## Write `output` as JSON with exactly these fields
- `provenance`: from the brief, verbatim.
- `id`: the pattern id.
- `name`: 2–5 plain words, title case (e.g. "Words Rise In One By One").
- `summary`: one or two sentences anyone can follow: what the viewer sees.
- `when_to_use`: 1–4 short bullets (the message or moment it suits).
- `avoid_when`: up to 3 bullets (optional).
- `steps`: 2–7 build steps in order. Use no numbers here; timing lives in `numbers`.
- `build`: `gsap` (HyperFrames/GSAP phrasing: tween type, properties, ease family, stagger) and
  `remotion` (spring vs interpolate, what animates). Name ease families from `numbers.easing_mix`,
  never a duration.
- `sound`: how sound goes with it, from `numbers.sfx_label_mix` and `sfx_offset_ms`. Write "no typical
  sound" if the mix is empty or mostly `unsure`/`music`.
- `why_premium`: one concrete paragraph, synthesised from the members. Do not copy one verbatim.
- `numbers`: the brief's `numbers` object, **copied exactly** (validation compares it).
- `examples`: 1–5 entries copied from `numbers.examples`.
- `caveats`: up to 3, e.g. "seen in only 2 videos" or "few measured elements". Base them on
  `numbers.videos`, `numbers.duration_ms.n` and `ci`.

## Rules
- No number anywhere except inside `numbers` and `examples` (no "300 ms", no "3 items").
- No brand names or quoted on-screen text in the prose. Describe the motion generically.
- Never invent measurements. If `numbers.duration_ms.median` is null, say timing was not measured in
  `caveats`.
- Validate with `uv run lens validate <output>`. Fix and re-validate until it passes.
