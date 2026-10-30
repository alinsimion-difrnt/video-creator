---
name: compare-fixes
description: A4 — write the top fixes (max 10) for one of our videos from its corpus comparison (`lens status --fixes <video>`). Each fix cites a metric, timestamps in the video and recipe-book references (pattern, archetype or token). Used by the compare-fixer subagent.
disable-model-invocation: true
---

# compare-fixes (A4)

You turn a corpus comparison into the **10 most valuable fixes** for one of OUR videos. The reader is
the person who will rebuild the video: write plainly and concretely.

## Inputs
Run `uv run lens status --fixes <video>`. The brief has:
- `metrics`: every measure with the video's `value`, the premium band (`min`..`max` = 25th–75th
  percentile of the format's premium videos), its `percentile`, `status` (`fail` = outside the band)
  and `gap` (in band widths). `loudness` is against the destination house target instead.
- `shots`, `dead_holds`, `sfx`, `events`: the video's own timeline, measured by code (seconds).
- `patterns`, `archetypes`: what the recipe book offers; `token_files`: the export files you may cite.
- `output` and `provenance` (copy it verbatim).

## Write `output` as JSON
```
{"provenance": <brief>, "video": "<video>", "fixes": [
  {"metric": "sfx_per_min", "problem": "...", "evidence": ["0:12 s003 ...", "..."],
   "target": "...", "change": "...", "effort": "M", "severity": 4.2,
   "timestamps_s": [12.3, 40.1], "refs": ["pattern:stagger_list_reveal", "token:sound-spec.json#sfx_offset_ms_to_reveal.whoosh"]}
]}
```
- 1–10 fixes, most valuable first. Rank by `gap` × how much the viewer would notice × how cheap it is.
  A metric inside its band is not a problem: do not "fix" it.
- `metric`: an id from `metrics`. You may use one metric for several fixes if they are different places.
- `problem`: one sentence with the value and the premium band, from `metrics`.
- `evidence`: 1–4 short lines, each starting with a timestamp (m:ss) and a shot/event/SFX id from the brief.
- `timestamps_s`: the same moments in seconds, from the brief only. Never invent times.
- `target`: the band or target, in words.
- `change`: what to do, concretely: which scenes, which pattern or archetype, which token value.
- `refs`: at least one of `pattern:<id>`, `archetype:<id>` (from the brief lists), or
  `token:<file>#<dotted.path>` into a token file (e.g. `token:motion-tokens.json#duration_ms_by_role.headline`).
- `effort`: S (minutes), M (an hour or two), L (a day+). `severity`: 0–10, your ranking score.

Validate with `uv run lens validate <output>`, fix and re-validate until it passes.
