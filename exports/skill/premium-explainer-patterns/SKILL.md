---
name: premium-explainer-patterns
description: Build premium SaaS explainer scenes from measured patterns. Use when storyboarding or building an explainer in HyperFrames/GSAP or Remotion: pick a scene archetype per beat, fill its slots, animate with the listed patterns, and take timing, easing, springs, sound cues, pacing and voice from the bundled specs.
---

# Premium explainer patterns

Measured from premium SaaS explainers by `lens` (explainer-video-creator). Timing numbers are
code-measured medians with their typical range; the words are written from those measurements.

## How to use
1. **Storyboard:** give each beat of the script one scene archetype below. Fill its slots with your
   content; keep scene lengths inside the archetype's measured range (`pacing.json` has them all).
2. **Animate:** use the archetype's patterns. Take durations from `motion-tokens.json`
   (`duration_ms_by_role`, `duration_ms_by_change`), easing from `easing` (GSAP name and CSS
   cubic-bezier per class) and springs from `springs` (Remotion configs).
3. **Sound:** place SFX with `sound-spec.json` (`sfx_offset_ms_to_reveal`: onset relative to the
   motion landing) and mix to a destination in `targets`.
4. **Voice:** brief the voice with `voice-spec.json` (`brief` lists plain instructions).

## Scene archetypes
- [Abstract Shape Metaphor](references/archetypes/abstract_shape_metaphor.md) (`abstract_shape_metaphor`): A brief, full-frame abstract image of soft shapes, gradient orbs, outlines or dot fields stands in for an idea such as growth, voice or data. It bridges two scenes and gives the narration a visual metaphor instead of literal interface.
- [AI Working Loader](references/archetypes/ai_working_loader.md) (`ai_working_loader`): A small status pill, card or row shows the AI at work: a spinner or sparkle turns, a shimmer sweeps the label, and the status words cycle through what it is doing. It is a short bridge between a request and its result that makes the wait feel purposeful.
- [App Icon Orbit](references/archetypes/app_icon_orbit.md) (`app_icon_orbit`): App icons or interface cards gather in a ring around a central brand mark or headline, then turn, glow or change state together. It shows the product as the hub that connects or replaces many tools.
- [Chart Card Build](references/archetypes/bars_ring.md) (`bars_ring`): A clean chart card appears and its data builds on screen: bars grow, a line draws across, or a ring fills in, often with a tooltip value following along. It turns a product claim into visible proof during the demo.
- [Feature Cards Triptych](references/archetypes/cards_triptych.md) (`cards_triptych`): A small set of cards, panels or icon tiles enter together and settle side by side or in an overlapping cascade, each standing for one feature, theme or benefit. It lets the viewer take in a few parallel ideas at once before the video unpacks them.
- [Chat Demo Panel](references/archetypes/chat_demo_panel.md) (`chat_demo_panel`): A cropped chat or agent panel plays a scripted conversation: messages pop in one at a time, the assistant's answer streams in, and the thread scrolls up as it grows. It is the longer demo scene that shows the product actually doing the work.
- [Comparison Split](references/archetypes/comparison_split.md) (`comparison_split`): Two sides share the frame, left and right or in stacked lanes, so the viewer compares the old way with the new one or the product against the alternatives. It sets up a contrast that the narration then resolves in the product's favour.
- [Document Highlight Callout](references/archetypes/document_highlight.md) (`document_highlight`): A document, report, table or answer card fills the frame while the camera holds close and highlights or outline boxes land on the exact lines the narration talks about. It points the viewer's eye at the one detail that proves the point.
- [Kinetic Statement Card](references/archetypes/kinetic_statement_card.md) (`kinetic_statement_card`): A short headline builds word by word on a clean background, sometimes with one word or chip that cycles through options or a small icon that supports it. The scene states one idea loudly between demos: the hook, the problem, the mechanism or the outcome.
- [Logo Close](references/archetypes/logo_close.md) (`logo_close`): The last scene: a closing tagline or call to action builds, then shapes or the final UI resolve into the brand mark and wordmark, which hold on a clean background. It leaves the viewer with the brand and one thing to do next.
- [Logo Intro Sting](references/archetypes/logo_intro_sting.md) (`logo_intro_sting`): The brand mark or wordmark resolves at the centre of a clean background, often with a product line or tagline, and holds briefly before handing off to the first idea. It opens the video and tells the viewer whose story this is.
- [Presenter To Camera](references/archetypes/presenter_to_camera.md) (`presenter_to_camera`): A person speaks directly to the viewer in a locked or gently drifting medium shot, sometimes with a name tag or a supporting graphic beside them. The scene gives the explainer a human voice and carries claims, reasons and proof in the speaker's own words.
- [Product UI Tour](references/archetypes/product_ui_tour.md) (`product_ui_tour`): The viewer watches the real or recreated product interface being used: a cursor clicks through views while the frame pushes in on the part that matters. The scene shows how the product works rather than telling.
- [Prompt Input Card](references/archetypes/prompt_input_card.md) (`prompt_input_card`): A clean, rounded prompt box sits on a calm background while a request types into it with a caret, often followed by a press on the send button. It shows the viewer how simply they ask the product for something, usually as the hook or the start of a demo.
- [Stat Count Up](references/archetypes/stat_count_up.md) (`stat_count_up`): A big number counts or ticks up at the centre of a styled backdrop and lands on the headline figure, with a short label, timed to the narration saying it. It turns a claim into proof the viewer can feel.
- [Tile Grid](references/archetypes/tile_grid.md) (`tile_grid`): Many tiles, such as app windows, integration icons, video clips or small UI widgets, sit in a grid or wall that the camera pulls out to reveal or glides across. The scene shows breadth: many use cases, integrations or projects at once.
- [Title Card](references/archetypes/title_card.md) (`title_card`): A short, centred headline on a clean field reveals word by word or rises from a mask, sometimes with a small label pill or drifting media tiles around it. It names the product, feature or chapter so the viewer knows what comes next.

## Patterns
- [AI Answer Streams In](references/patterns/ai_answer_stream.md) (`ai_answer_stream`)
- [Avatar Grows Into Hero](references/patterns/avatar_hero_expand.md) (`avatar_hero_expand`)
- [Blur Out, Blur In](references/patterns/blur_crossfade.md) (`blur_crossfade`)
- [Cards Fill The Wall](references/patterns/card_wall_stagger.md) (`card_wall_stagger`)
- [Chat Bubble Pops In](references/patterns/chat_bubble_append.md) (`chat_bubble_append`)
- [Chip Pops Onto Element](references/patterns/chip_append.md) (`chip_append`)
- [Cursor Leads The Demo](references/patterns/cursor_guided_demo.md) (`cursor_guided_demo`)
- [UI Wipes Over Title](references/patterns/diagonal_ui_wipe_in.md) (`diagonal_ui_wipe_in`)
- [UI Layered Over Footage](references/patterns/footage_with_ui_overlay.md) (`footage_with_ui_overlay`)
- [Rotating Word Slot](references/patterns/input_text_cycle.md) (`input_text_cycle`)
- [Words Arrive With Momentum](references/patterns/kinetic_word_reveal.md) (`kinetic_word_reveal`)
- [Layout Shifts Into Place](references/patterns/layout_reframe.md) (`layout_reframe`)
- [Logo Builds Into Lockup](references/patterns/logo_resolve.md) (`logo_resolve`)
- [Content Scrolls Inside A Window](references/patterns/masked_scroll.md) (`masked_scroll`)
- [Match Cut On Shared Shape](references/patterns/match_cut_element.md) (`match_cut_element`)
- [Message Card Pops In](references/patterns/notification_pop.md) (`notification_pop`)
- [Layers Drift At Different Speeds](references/patterns/parallax_layers.md) (`parallax_layers`)
- [Prompt Types Itself In](references/patterns/prompt_type_on.md) (`prompt_type_on`)
- [Zoom And Dissolve Transition](references/patterns/scale_dissolve_transition.md) (`scale_dissolve_transition`)
- [Placeholders Resolve Into Data](references/patterns/skeleton_resolve.md) (`skeleton_resolve`)
- [Spotlight On One Thing](references/patterns/spotlight_focus.md) (`spotlight_focus`)
- [List Items Arrive In Turn](references/patterns/stagger_list_reveal.md) (`stagger_list_reveal`)
- [Virtual Camera Move Over UI](references/patterns/ui_camera_push_in.md) (`ui_camera_push_in`)
- [Fast Whip To Next Scene](references/patterns/whip_transition.md) (`whip_transition`)

## Files
`motion-tokens.json`, `sound-spec.json`, `pacing.json`, `voice-spec.json`, `archetypes.json`,
`patterns.json` (alongside this skill in `data/`), `references/` (one page per archetype and pattern).
