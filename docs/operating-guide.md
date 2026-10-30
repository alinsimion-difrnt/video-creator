# Operating guide

## Local / cloud session
```bash
make setup        # uv sync (Python 3.12)
make check        # lint, typecheck, tests, dag check, validate, schema check
uv run lens --help
```
Cloud sessions run `scripts/session_start.sh` automatically (installs deps).

## Container
```bash
docker build -t evc .
docker run --rm -v "$PWD:/work" evc validate --all
```

## Ingest and normalize (M1)
```bash
make fixtures                                   # synthetic test videos (gitignored)
uv run lens storage put-inbox ~/Downloads/x.mp4 # → r2://inbox/x.mp4 (needs R2_* env)
uv run lens ingest [--video id] [--force]       # S1 → data/media/<id>/original.*
uv run lens frames [--video id] [--force]       # S2 → videos/<id>/meta.json, palette.json + data/
uv run lens storage push                        # media, verified originals, stage markers → R2
uv run lens storage lifecycle --apply           # once per bucket: expire originals/expiring/ after 30 days
```
Offline or in tests, set `LENS_STORAGE=local:/some/dir` instead of the R2 variables.
YouTube, X and LinkedIn: `scripts/local_fetch.sh <url> <source-id>` on your own machine.

## Signals and the baseline audit (M2, M4.5)
```bash
uv run lens signals [--video id] [--force]       # S3 → videos/<id>/signals.summary.json + data/signals/<id>/
uv run lens compare --video acme-explainer-v1 --targets-only [--destination youtube]
uv run lens report --video acme-explainer-v1  # re-render reports/compare/<id>/<date>.md|.html
```
First run downloads Whisper `small.en` (~460 MB, Hugging Face) and demucs `htdemucs` (~80 MB) into
`~/.cache`; CI caches both. Tests need `ffmpeg` and `espeak-ng` (`apt-get install espeak-ng`).
House targets live in `config/lens.yaml` under `targets.metrics`; edit them there, never in code.

## Batch analysis (corpus)
1. Sources to analyse are `status: ready` with `url: r2://inbox/<id>.mp4` and `page_url:` (the YouTube/X
   page). Ingest reports `waiting` until the upload arrives; nothing fails.
2. On your own machine: `uv run python scripts/fetch_batch.py --limit 10`. yt-dlp reads each length first
   and skips videos over `batch.fetch_max_seconds`. Uploading needs R2_* in your shell (an R2 token of your
   own, never pasted anywhere); without it use `--no-upload` and drag `~/lens-inbox/*` into the bucket's
   `inbox/` folder in the Cloudflare dashboard. Re-running continues where it stopped.
3. `prepare.yml` (on push to sources.yaml, daily, or by hand) runs `lens queue`: up to `batch.per_run`
   videos whose media arrived and whose S3 is not done, `batch.max_parallel` runners at once, then one
   data PR. It re-dispatches itself while the queue has more. A video that fails is marked
   (`failed/<id>.json` in R2) and skipped until `lens queue --retry-failed` / the marker is deleted.
4. Cost: about 15-20 runner-minutes per 2-3 min video (S3 dominates). Private repos have a monthly
   Actions minutes allowance; 60 videos is roughly 1,000-1,200 minutes.

## Write guard
Set `LENS_STAGE=a1_annotate_video,a2_annotate_event` (etc.) to restrict Claude's writes to those stages'
declared paths. Unset = unrestricted (normal building). See ADR 0002.

## Secrets (Actions)
`CLAUDE_CODE_OAUTH_TOKEN` (from `claude setup-token`; lasts about a year: renew before expiry),
`R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`; Phase 2: `ELEVENLABS_API_KEY`.

## Adding a stage
Declare it in `lens/stages.py` (reads, exact writes, `after`), run `uv run lens dag --check`, register
its output schema in `lens/schemas/` and its path in `lens/validate/CHECKERS`, then `make schemas`.
