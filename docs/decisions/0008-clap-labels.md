# 0008 — SFX labels: rules first, local CLAP alongside

- **Status:** accepted
- **Date:** 2026-10-03
- **Milestone:** M2

## Context
The plan asked for local CLAP zero-shot labels plus acoustic rules (no API). Licences (external-facts §8):
LAION CLAP checkpoints CC0 / the Hugging Face port `laion/clap-htsat-unfused` Apache-2.0; `msclap`
weights MS-PL. On the synthetic SFX, CLAP labelled the whoosh correctly but heard the synthetic
impact, click and riser as glitch/pop/whoosh: zero-shot CLAP is unreliable on short, unusual sounds.

## Decision
- Use `laion/clap-htsat-unfused` through `transformers` (Apache-2.0, CPU, ~600 MB, cached in CI).
- Rule labels (measured features) stand whenever they decide. CLAP replaces only an `unsure` rule
  label, and only above `signals.clap.min_score`. Both labels, CLAP's probability and their agreement
  (same family: whoosh/swoosh/riser, click/tick/pop) are recorded per candidate; the summary reports
  the agreement share.
- The choice between this model and `msclap` is made on measured accuracy at G2 (gold set), not now.

## Consequences
The gold set will show which labeller is right where they disagree; the policy (and `min_score`)
is tuned then. A CC0 calibration set from freesound.org still needs an account/API key (open item).
