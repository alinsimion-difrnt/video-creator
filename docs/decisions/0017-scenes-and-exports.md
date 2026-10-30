# 0017 — Scene archetypes, G4 and the S10 exports

- **Status:** accepted
- **Date:** 2026-10-05
- **Milestone:** M8

## Context
BUILD_PLAN 8.4–8.6 asks for a G4-approved catalog, scene archetypes seeded from handoff 7.3, and exports
(`motion-tokens`, `sound-spec`, `pacing`, `voice-spec`, `archetypes`, the skill pack) with no
third-party media or copy. Robert reviews by plain Agree/Disagree pages (ADR 0015 showed that expert
questions do not work).

## Decisions
- **G4 is plain questions.** `lens cards --g4-page [--g4-scenes]` renders a private page, one decision
  per card with Claude's recommendation, watch links and an optional note. Verdicts are applied to
  `taxonomy/proposals.yaml` / `scene_proposals.yaml` (`status`) and to `taxonomy/v1.yaml`. Decided
  proposals are kept as they are and their events/shots count toward their pattern or archetype.
- **Proposals need two brands, not two videos.** One brand's house style is not a corpus pattern. Our
  own videos never count.
- **Scene types are sorted from text** (A3 `sort-scenes`, 60 shots per brief). The brief carries what A1
  already wrote, so no image is read twice. `other` scenes are grouped by the sorter's name, and only
  near-synonym names are merged; descriptions would split identical names.
- **G4 results (2026-10-05).**
  - Patterns: 4 added, 1 merged, 1 rejected, `metric_count_up` held back.
  - Scenes: 10 corpus types added, among them `product_ui_tour`, the most common scene in the corpus.
    `presenter_to_camera` was kept on Robert's call, against Claude's "leave out".
    `hero_product_render` was rejected on Robert's call: "not relevant for a SaaS".
    Filmed scenes and plain transitions were rejected.
  - Seed archetypes with no corpus examples (`question_relay`, `title_step_rail`, `shortlist_card`)
    are held back.
- **Exports are rebuilt from stats and approved cards only** (`lens export`):
  - Each value is a `Range`: the median plus the 25–75% band, n and the number of videos.
  - Easing classes carry the corpus's most used GSAP ease and a weighted-median CSS cubic-bezier. A
    linear class is exported as `linear`.
  - Spring clusters are named by behaviour: `bouncy` (low damping ratio), `snappy` and `smooth` (by
    settle time).
  - `voice-spec.brief` turns the ranges into plain instructions for the voice.
  - Held cards are left out, and archetype pattern lists only name exported patterns.
- **Leak check.** An export fails if it contains a corpus brand, a corpus video id or corpus on-screen
  text of four or more words. Brands that are ordinary words (config `synth.export_word_brands`) match
  only as a capitalised name that does not start a sentence, heading or list item.

## Consequences
- Phase 2 reads `exports/` and `exports/skill/premium-explainer-patterns/` only.
- Archetypes from A1-only videos have no motion events. Their cards rely on the A1 descriptions and say
  so. Annotating more events (after the Actions minutes reset) will fill them.
