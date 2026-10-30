# M6 eval: annotation layer, machine checks (2026-10-05)

`uv run lens eval --run m6-c1`; full result in `runs/eval/<hash>.json` (ADR 0015).

## Answer key: Acme v1, 60 annotated events

| Check | Baseline | After tuning | n |
|---|---|---|---|
| Box precision: picked elements that are real tween targets | 59.3% | 59.3% | 194 judged, 34 unjudged |
| Box recall: real tween targets covered by a pick | 43.4% | 43.4% | 286 |
| Change types: true changes named by Claude's labels | 63.9% | 63.9% | 266 |
| Change types, with the record's measured changes | — | **85.3%** | 266 |
| SFX: S3 classifier alone, on SFX Claude reviewed | 0% | 0% | 2 |
| SFX: after Claude's review | 100% | 100% | 2 |
| Easing: Claude's guesses (estimates only) | 100% | 100% | 13 |
| Easing: S7 measured class vs true ease | 32.4% | **57.8%** | 102 |

The tuning round changed S8, not the annotations (ADR 0015):
- measured elements carry the directions S7 measured;
- the easing class comes from the joint fit.

Most missed labels were `slide_up` (40 cases: fade-and-rise read as a plain fade) and `scale_up` (21).

Misses on box choice:
- Most of the 34 unjudged picks are the cycling question text and the caption pill. The answer key has no
  box for those (they are not box tweens).
- The judged misses are mostly picks of a whole line or group where the key animates single words.
  Recall also counts every per-word span.

Only 2 key SFX clips fall on a reviewed candidate. The SFX numbers are too small to conclude anything.

## Consistency: blind second annotation, 10 events (run m6-c1)

Sample: Acme e001 e011 e020 e030 e041 e052 e063, Loom e004, Notion AI Connectors e012 e024.

| Check | Agreement | n |
|---|---|---|
| Candidate box ids (intersection over union) | 80.6% | 36 |
| Pattern id | 70% | 10 |
| Role, on boxes both picked | 75.9% | 29 |
| Change types (intersection over union) | 72.3% | 47 |
| SFX labels | 100% | 1 |

The pattern disagreements are near-synonyms the annotators flagged themselves:
- `card_wall_stagger` vs `stagger_list_reveal`;
- `kinetic_word_reveal` vs `parallax_layers`.

## Measured share: reference videos

297 of 461 annotated events (64.4%) have at least one S7-measured element. Target ≥ 60%: **met**.

The three videos that timed out in finalize run 1 count as unmeasured. Re-running them after the
Actions minutes reset raises the share.
