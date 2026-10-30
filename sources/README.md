# Sources

`sources.yaml` lists every video in the corpus. Each entry:

| Field | Meaning |
|---|---|
| `id` | lowercase slug, unique; used for every path |
| `url` | `https://…mp4`, `r2://inbox/<file>` or `file://…` (`null` only with `status: draft`) |
| `format` | one of `taxonomy/v1.yaml` → `format` |
| `tier` | `reference` (derives tokens) · `average` (calibrates scores, A1 only) · `own` (compared only) · `competitor` |
| `media` | `full` · `frames_only` (A1 only, excluded from motion/audio stats) · `audio_only` |
| `refetchable` | `false` → the original is never deleted from R2 |
| `status` | `ready` · `draft` (skipped by the pipeline) |
| `segment` | optional `{start, end}` in seconds; default cap is `analysis.max_minutes` |

YouTube, X and LinkedIn are fetched **locally** with `scripts/local_fetch.sh` (M1), which uploads to `r2://inbox/`.
Aim for at least 15 `narrated_explainer` references so `lens compare` has a like-for-like cohort.
