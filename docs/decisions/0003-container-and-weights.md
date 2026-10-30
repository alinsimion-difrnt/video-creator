# 0003 — Container image and model weights

- **Status:** accepted (revisit at M2 with measured sizes)
- **Date:** 2026-10-03
- **Milestone:** M0

## Context
Private-repo runners: 2 vCPU, 8 GB RAM, 14 GB disk. GHCR storage and bandwidth are currently free
(external-facts §4, §6). Weight licences: CLAP (LAION) CC0/Apache-2.0, Whisper MIT, msclap MS-PL
(ship licence text), htdemucs unconfirmed beyond repo MIT (§8).

## Decision
`python:3.12-slim` + ffmpeg + uv; the repo checkout is mounted at `/work` (`LENS_ROOT`). M0 image:
964 MB. From M2, add CPU-only torch and the audio/vision deps. Bake weights only if their licence
allows redistribution and the image stays well under ~6 GB; otherwise cache weights with
`actions/cache` (10 GB per repo) keyed by model version.

## Consequences
Re-measure at M2. If GHCR's free container storage ends, fall back to `uv` + `actions/cache` +
`apt-get install ffmpeg` on the runner.
