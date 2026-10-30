---
name: annotate-video
description: A1 — annotate the structure of one part of a SaaS explainer video (shots, text, typography, what happens, how to rebuild it), plus the per-video summary and scores in the last part. Used by the video-annotator subagent with one task from `lens status --task`.
disable-model-invocation: true
---

# annotate-video (A1)

You annotate the STRUCTURE of one SaaS explainer/launch video for a measured reference library.
You cannot watch video. You read contact sheets (2 fps, timestamps stamped, one header per shot id),
mid-shot keyframes, and `anchors.json` (shots, transcript with word indices, BPM, loudness, palette,
SFX, event counts per shot). Treat anchors as ground truth.

## Inputs
Run `uv run lens status --task <video>/<task>` first. It prints your brief:
- `images`, `files`: read every one (paths are repo-relative);
- `shots`: the shot ids you annotate — exactly these, no more, no fewer;
- `output`: the only file you write;
- `writes_summary` / `earlier_parts`: if `writes_summary` is true you also write the per-video `summary`.
  Read the `earlier_parts` files first (they describe the earlier shots), then judge the whole video;
- `provenance`: copy it verbatim into your output.

## Rules
1. Annotate EVERY shot id in your brief; never add, merge or split shots, and never invent times.
   Use word indices (`words[].i` in anchors) for anything tied to speech.
2. Enums come only from `taxonomy/v1.yaml` (shot_type, composition, transition, depth_cue, beat,
   hook_technique). Otherwise use "other" and fill the matching `*_other` text.
3. Quote on-screen text verbatim (`on_screen_text`, one entry per text block) and count its words.
   Describe typography (style, weight, case, tracking); font names only as low-confidence guesses.
   Do not output colours: the palette comes from code.
4. `build_rebuild`: one concrete sentence a developer can implement.
5. Scores 1–5 with evidence; 3 = competent, 5 = best-in-class. `refs` are shot ids ("s003") or word
   indices ("w12"). `sound_design` is judged from the audio facts in anchors (SFX density, loudness,
   beats) plus visuals — say so in its evidence. Use `score: null` only where a score does not apply
   (e.g. `vo_script_quality` with no voice-over); hook, clarity, motion_polish and overall always score.
6. `works_muted`: is the story understandable with sound off? `localization_friendliness`: baked-in text,
   voice-over dependence.
7. At most 3 `signature_moments`, each with why it elevates perceived quality.
8. `confidence` per shot (high | medium | low). Do not guess what you cannot see; say so instead.

Context: insights inform Acme.ai (an AI-visibility SaaS for SEO agencies). Don't let that bias scores.

## Output shape (`exports/schemas/a1.schema.json` is the full schema)
```json
{"provenance": {...from the brief...}, "video": "<id>", "task": "a1-p1",
 "shots": [{"shot": "s001", "shot_type": "ui_closeup", "shot_type_other": null,
            "composition": "centered", "composition_other": null, "focal_element": "...",
            "transition_in": "hard_cut", "transition_other": null, "on_screen_text": ["..."],
            "text_word_count": 3, "typography": "...", "depth_cues": ["shadow"],
            "what_happens": "...", "build_rebuild": "...", "confidence": "high"}],
 "summary": null}
```
`summary` (last part only): `beats` [{beat, shots, words: [first, last] | null}], `hook` {text, technique,
technique_other, shots, words}, `cta` {text | null, shots}, `tone`, `signature_moments` [{shots, description,
why_premium}], `scores` {hook, clarity, ui_showcase, motion_polish, sound_design, vo_script_quality,
brand_consistency, works_muted, overall: {score, evidence, refs}}, `localization_friendliness` {score,
baked_in_text, vo_dependent, notes}.

## Finish
Write `output`, then run `uv run lens validate <output>`. Fix every reported error and re-validate
(at most 3 rounds). Report: the task id, valid or not, and anything you could not see.
