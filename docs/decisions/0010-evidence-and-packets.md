# 0010 — Visual evidence and packets: choices made in M3

- **Status:** accepted
- **Date:** 2026-10-03
- **Milestone:** M3

## Context
BUILD_PLAN 7.2–7.3 specifies S4/S5. Building them on Acme v1 settled several details the plan left open.

## Decision
- **Bursts are frame ranges, not copies.** The proxy is CFR at native fps, so `evidence.json` stores each
  burst as `[b0, b1]` and S7 decodes the proxy itself. Copying ~30 frames × 70 events would be ~200 MB
  per video for no gain. Bursts are clipped to the event's shot.
- **Two decode passes.** Pass 1 measures motion energy inside each event's crop; filmstrip frames are
  picked at quantiles of its cumulative sum (`evidence.filmstrip_quantiles`). Pass 2 keeps only the frames
  the images need, so memory stays at a few frames per active event.
- **Candidate boxes:** diff components (start vs settled end frame, inside the crop only), OCR lines
  that changed (≥ `ocr_min_changed`), and the S3 box. Ranked by changed pixels, NMS. The S3 `union` box
  is a fallback: it never suppresses a specific box (on v1 it hid the panel entering), but is dropped when
  a specific box nearly duplicates it.
- **Burned-in captions:** every word switch changes the caption band, so S3 event boxes on v1 reached
  down into it. With captions detected, S4 clips event boxes to above the band; events entirely inside
  it are skipped by triage as `caption_band` (S3 already measures captions).
- **Spectrograms use the accompaniment stem** when S3 produced one: SFX are visible without the voice.
- **Pass 1 parts:** shots are packed in order into tasks of ≤ `annotate.max_images_per_task` images; a
  video with more than one part writes `videos/<id>/a1.p<n>.json` (registered in the stage registry).
  M5 decides how parts are merged.
- **Status lives on disk:** `packets/<id>/manifest.json` lists tasks with input hashes and outputs; it never
  changes during annotation. `lens status` derives done/pending from the outputs.
- **Dedupe is conservative:** same shot, same-sized box, similar duration and dHash of the settled crop.
  On v1 it merges nothing (S3 splits staggers into events of different extents); tested on fixtures.

## Consequences
Acme v1: 71 events → 60 A2 tasks (11 skipped: 7 caption band, 4 low energy) + 5 A1 parts, 286 images,
every image ≤ 1500 px. That is a lot of quota for one video; if M5 shows it is too much, raise
`packets.min_event_energy` or teach S3 to group staggers.
