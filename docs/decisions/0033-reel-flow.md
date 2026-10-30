# 0033 — Reel flow: cards hand over, a motion style per video, the product area moves with the cuts

- **Status:** accepted (Robert's feedback, 2026-10-17; built the same day)
- **Date:** 2026-10-17
- **Milestone:** Phase 2, presenter reels (amends ADR 0026; uses the latitude of ADR 0031)

## Context
Robert on the acme reels (2026-10-17): the animations "are really simple considering everything that was
built", "lackluster, repeating from one video to another and not showcasing any originality or flowing
animation from one cut to the other."

What the code did, read against that:
- **Every widget was an island.** It rose in at its word, drifted, slid up and out, and the next one rose 0.12 s
  later (`hold_product`). ADR 0026's rule "two cards never crossfade" had become "nothing connects": a hard
  swap between every two cards, 16 times in a 55 s video (seo-budget).
- **The step label re-entered with every card** ("1/4  SEO ON A BUDGET" slid in from the left 16 times).
- **One entrance per kind, for every video.** Cards always rose, stickers always popped, whatever the topic,
  so two videos of one brand moved the same way. `spec.motion` existed but nothing chose it per video.
- **The product area ignored the edit.** A static canvas; the push-in reset to 1.0 at every cut, so the only
  thing the top and bottom halves shared was the seam.
- The motion route had already learned the opposite on demo15 / demo25 (config `create.motion.rules`, rule 1):
  "Every handover carries one persistent element (a card, a row, a chip) that changes shape into the next
  scene's layout. No hard cut, no fade to blank, no crossfade ghosting." The reel kit contradicted it.

## Decision
A plan names a **motion style** for the whole video; code applies it everywhere, so one video moves as one
piece and two videos move differently. Nothing here changes a plan that has no `motion:` block.

- **`motion:` in reel.yaml** (`ReelMotion`): `style` names a preset in config `create.footage.reel.styles`
  (`classic`, `paper`, `editorial`, `playful`, `terminal`) and any part can be overridden. A style sets the
  entrance per kind of widget (cards, stickers, numbers), the hand-over between product cards, whether a run
  of cards shares one step label, the background, and how the frame behaves at cuts. The reason goes in the
  plan's `# look:` comment with the colours (ADR 0031). Without `motion:` a plan renders as before (`classic`).
- **Hand-overs (`MK.handover`, motion.js).** When the next product card arrives in the same layout block, the
  last one is kept for `handover_s` (0.55 s: exports/motion-tokens.json, card moves low 507 ms, mask reveals
  median 575 ms) and the two are carried into each other:
  - `morph`: a surface in the card's own look (the carrier) is left where the last card was and changes shape
    into the next card's rectangle while the content drops out and the next content comes up on it. The
    persistent element of the motion route's rule 1. Only cards morph; a sticker or tile row pushes.
  - `push`: the last card slides up and out while the next slides up into its place, one motion.
  - `stack`: the next card lands on the last from below while the last shrinks back under it.
  - `cut`: ADR 0026's rule, unchanged (the last leaves, the next lands 0.12 s later).
  A card's own `handover:` overrides the style. The no-crossfade rule holds: no hand-over fades one card into
  another in the same place. A carried card arrives with the whoosh, not the pop.
- **One step label per run (`MK.kicker`).** Product cards in a row with the same kicker share one label: it
  enters once, its step pill flips when the step changes, it leaves with the last card. Those cards lose their
  own label, take the box below it (`kicker_h` 104 px: label, pill and a 32 px gap for the card's overshoot and drift) and are top-aligned, so the whole run keeps one top edge.
- **The product area moves with the edit.** `push_alternate`: shots push in and out in turn (1.0 → 1.05, then
  1.05 → 1.0), so the scale carries over the cut instead of snapping back. `cut_nudge`: on each cut the
  background shifts 14 px (the dots, the drifting shapes) and the cards settle from 1.012, in step with the
  jump cut below. `snap_cuts`: a card whose word starts within 0.3 s after a cut enters on the cut.
  `bg: drift`: two soft brand-tinted shapes (gradients, no blur filters: cheap per frame) drift on 18 s sine
  loops behind the cards, slower than any card, never a beat.
- **Two new entrances:** `wipe` (a straight edge reveals the card left to right, 0.55 s, from numeric clip-path
  custom properties so the shadow stays) and `unfold` (the card hinges down from its top edge). Exits match.
- **Presets** (config, with a note on when each fits): `classic` = ADR 0026 (client brands, old plans);
  `paper` = acme's default (rise, morph, drift, shared labels); `editorial` (wipe, slide, unfold, push:
  lists and steps); `playful` (pop, stack: gags, wins, mascots); `terminal` (pixel, cut: code and retro).
- **Reviews** judge flow: `create review`'s rubric gets "flow: cards hand over into each other and the top
  half moves with the cuts"; the review-reel skill looks for it on the motion strips.

## Evidence
- tests/test_motion_kit.py: every entrance (now 8) and every hand-over kind is seek-safe (the same frame
  whichever way the playhead got there), the first card is gone by its end, the next is fully on once carried
  in, the carrier is a card-sized surface mid-morph and nothing else, and a card or the carrier is on screen at
  every frame of a hand-over (no blank product area). The shared label flips its step; the background moves.
- tests/test_create_reel.py: the style is the preset with the plan's overrides (unknown styles and hand-overs
  are refused), entrances per kind leave the plan's own choice alone, carried hand-overs keep the last card
  through the next, runs share one label and top-align their cards, cards enter on a cut, carried cards whoosh.
- tests/test_create_reel_e2e.py: a `paper` plan on the synthetic take builds (hand-over, shared label, cuts,
  alternate push in the page data) and passes the Chromium layout checks.
- Three fresh-eyes rounds (lab-reviewer, contact sheets of a paper and an editorial build on the synthetic
  take): round 1 found an empty card shell for 0.45 s per morph, the pill touching the card, pushed cards
  travelling through the label and entering from below the product area, blobs too faint; round 2 found the
  clip on at rest, the label settling with the cut, the highlight ring overhanging the card; round 3: all
  fixed, whole cards with shadows at rest, no ghosts, no overlapping text. A pushed card is cut by the card
  area's edge for two or three frames while it travels: that is the scroll.
- Not yet seen on Robert's footage: this cloud session has no take. The first real render decides the numbers
  (`handover_s`, `kicker_h`, the nudge) and whether `morph` reads on a phone; they live in config.

## Consequences
- Acme and every plan without `motion:` render exactly as before. acme plans choose a style per
  video (draft-reel-plan rule 7): the look is a per-video variable (ADR 0031), the brand anchors stay.
- seo-budget's plans now carry `motion:` (`paper` for the layout version, `editorial` for the overlay) and a
  `# look:` line; the approved render is unchanged until Robert asks for a re-render.
- The kit's hand-over geometry is read when a tween first renders (after the fit) and read again when the fonts
  arrive; renders go forward in time, as the seek-safety tests do.
- New styles are config entries, not code, unless they need a new entrance or hand-over kind.
