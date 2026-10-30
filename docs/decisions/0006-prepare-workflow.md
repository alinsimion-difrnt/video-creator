# 0006 — prepare workflow: state in R2, compact JSON via a data PR

- **Status:** accepted
- **Date:** 2026-10-03
- **Milestone:** M1

## Context
Stages are idempotent via marker files under `data/state/` (gitignored). A fresh Actions runner has
none, so without persistence every run would re-fetch and re-encode every video. Facts
(external-facts §5): pushes and merges made with `GITHUB_TOKEN` start no workflows; PRs it opens run
CI only after a person approves. Cloud IPs get bot-blocked by YouTube/LinkedIn, and their terms
restrict automated downloading.

## Decision
- Stage markers are pushed to `state/<video>/<stage>.json` in R2 and pulled at the start of a run
  (`lens storage pull-state`). With `meta.json` in git and the markers pulled, ingest and normalize
  report `cached` without downloading anything (tested).
- `prepare.yml` commits only `videos/*/meta.json` and `palette.json`, through a PR on branch
  `data/prepare` (`peter-evans/create-pull-request`). CI on that PR needs one approval click, which
  doubles as a human look at new corpus entries.
- Until the M2 image carries the heavy dependencies, `prepare` runs on the runner with `uv` and
  `apt-get install ffmpeg` (ADR 0003 permits this). It switches to the GHCR image in M2.
- YouTube, X and LinkedIn are fetched only locally (`scripts/local_fetch.sh`), for internal analysis.
  Media stays in a private bucket and is never published.

## Consequences
The R2 bucket is the source of truth for media and markers; git holds compact JSON. Losing the
bucket's `state/` prefix only costs a recompute.
