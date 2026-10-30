---
name: annotate-event
description: A2 — annotate one motion event (which elements move, by candidate box id; SFX review; pattern; build hint). Code measures all timing; you identify and label. Used by the event-annotator subagent with one task from `lens status --task`.
disable-model-invocation: true
---

# annotate-event (A2)

You annotate ONE motion event. Code measures all timing; you identify and label.

## Inputs
Run `uv run lens status --task <video>/<task>` first. It prints your brief: `images`, `files`, `event`,
`siblings`, `output` (the only file you write) and `provenance` (copy it verbatim). Read every image and file:
- `filmstrip.jpg`: frames left→right, top→bottom, timestamps stamped;
- `end_marked.jpg`: the settled end frame with numbered candidate boxes (b01, b02, ...);
- `end_clean.jpg`: the same frame unmarked;
- `spectrogram.jpg`: audio around the event, SFX candidates marked with their ids and classifier labels;
- `facts.json`: energy curve, camera summary, SFX candidates (id, time, CLAP label and score), nearby words.
  `camera.move` is the camera verdict. `pan_x`, `pan_y` and `scale` are raw whole-frame shift sums over the
  burst: when `move` is "none" the change covers only part of the frame, so they describe content moving
  inside it (a scroll, a reflow, a card sliding), not a camera move. Do not report a camera move then.
- `candidates.json`: the candidate boxes (id, pixel box, OCR text when there is any).

## Tasks
1. Elements that visibly move or change (max 12). For each, pick the best candidate box id (`box`).
   If none fits, give `manual_box` [ymin, xmin, ymax, xmax] in 0–1000 on the end frame plus
   `manual_reason`. For each: `label`, `role` (taxonomy element_role), `change_types` (taxonomy
   change_type), `is_text`, `text` (verbatim), `text_unit` (whole | line | word | char | unknown).
   Optional `estimates` {duration_ms, easing_class} — clearly guesses; code will measure.
   Never list elements that are static in all frames. Never reuse one box for two elements.
2. SFX: review EVERY candidate in facts.json `sfx` — no more, no fewer. Confirm or override the
   classifier label from the spectrogram shape and what happens visually at that moment
   (`verdict` confirm | override, `label` from taxonomy sfx), or `verdict: unsure` with `label: unsure`.
   Do not add candidates. If there are none, `sfx_review` is [].
3. Pattern: the closest canonical id from taxonomy `patterns` — read the whole list, including the UI-demo
   patterns (prompt_type_on, ai_answer_stream, input_text_cycle, chip_append, skeleton_resolve,
   masked_scroll, blur_crossfade, layout_reframe). Use "other" with `proposed_name` (2–4 words, reusable)
   only when none fits; `description`; `why_premium` (concrete).
4. `build_hint`: renderer-agnostic — which properties animate, order, stagger, spring vs ease.
   `gsap` first (HyperFrames phrasing, e.g. `fromTo` + ease name + stagger), then `remotion`.
5. `confidence` (high | medium | low) and `notes` on any ambiguity.

## Output shape (`exports/schemas/a2.schema.json` is the full schema)
```json
{"provenance": {...from the brief...}, "video": "<id>", "event": "e012", "task": "a2-e012",
 "elements": [{"box": "b03", "manual_box": null, "manual_reason": null, "label": "Headline",
               "role": "headline", "role_other": null, "change_types": ["fade", "slide_up"],
               "change_other": null, "is_text": true, "text": "...", "text_unit": "word",
               "estimates": {"duration_ms": 450, "easing_class": "ease_out"}}],
 "sfx_review": [{"id": "x004", "verdict": "confirm", "label": "whoosh", "note": null}],
 "pattern": {"id": "kinetic_word_reveal", "proposed_name": null, "description": "...", "why_premium": "..."},
 "build_hint": {"gsap": "...", "remotion": "..."}, "confidence": "medium", "notes": null}
```

## Finish
Write `output`, then run `uv run lens validate <output>`. Fix every reported error and re-validate
(at most 3 rounds). Report: the task id, valid or not, and any ambiguity.
