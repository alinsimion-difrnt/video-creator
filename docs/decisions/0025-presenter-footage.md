# 0025 — Presenter footage: ingest, verbatim transcript, cut proposals, edit

- **Status:** accepted (Robert: own voice, ElevenLabs speech-to-text, edits only in this pipeline; 2026-10-09)
- **Date:** 2026-10-09
- **Milestone:** M-F of `docs/research/vertical-footage-brands.md` §5

## Context
- Robert wants to film himself on a phone, with or without a mic, in any language. The pipeline should:
  - cut the pauses, fillers and retakes;
  - put his words on the video's clock;
  - caption the result;
  - later lay animations over it or put him in a corner bubble.
- Research: `docs/research/sources/presenter-footage-pipeline.md`.

## Decision
- **A brief with `voice: presenter` switches a project to footage.** `create status` then marks C4 (TTS) as unused
  and C2 (script) as optional. TTS projects mark the footage stages unused.
- **F1 `create ingest`** takes every video in `data/create/<p>/footage/raw/` (name order = take order) and writes:
  - a master per take: constant 30 fps, H.264 CRF 16, GOP 30, Rec.709, PCM audio, shorter side ≤ 2160;
  - a 16 kHz mono wav per take;
  - `projects/<p>/footage.json`.
  - Rotation is applied. HDR (PQ or HLG, e.g. iPhone HDR Video) is tone-mapped to SDR with zscale + hable, so a
    render never flips to HDR10.
- **F2 `create transcribe`** uses ElevenLabs Scribe (`scribe_v2`, word timestamps, audio events tagged).
  - Brand names go in as `keyterms`.
  - Scribe is verbatim by default, so fillers ("um") and false starts ("to--") come back as words. External facts §21.
  - Fallback: local faster-whisper (`create.footage.stt_engine: whisper`), which drops most fillers.
  - Raw responses are cached by audio hash.
- **F3 `create cuts`** proposes cuts; every gap between two kept words is at most one proposal.
  - **fillers** (config lists, en and ro);
  - **cue words**: "again" or "din nou" cancel the line they end;
  - **false starts**: a run of 3+ words repeated within 25 words, where the first attempt never finished a
    sentence (two complete sentences that start alike are both kept);
  - **long pauses**: over 0.45 s; 0.10 s kept before a word and 0.18 s after it;
  - **silence at a take's ends**.
- **Human gate:** Robert's decisions live in `projects/<p>/cuts-approved.yaml` (`approve: all | [ids]`,
  `reject: [ids]`).
  - It is an external input that no stage writes. `create cuts <p> --approve ...` writes it on his behalf.
  - No outside editor is used (Robert, 2026-10-09).
- **F4 `create edl`** turns the approved cuts into frame-exact segments on one clock (`projects/<p>/edl.json`,
  contiguity checked).
- **C5 `create timing` (presenter mode)** moves the kept words onto the edited clock.
  - Fillers and events stay in the sound but not in the timeline.
  - A sentence's first kept word is capitalised.
  - Scenes split at the first sentence end after 8 s.
  - The output is the same `timeline.json`, so captions, storyboard and build work unchanged.
- **F6 `create edit`** renders the edited video at the destination's frame.
  - Each segment is scaled to cover the frame and centre-cropped; face-aware reframing comes later.
  - 15 ms audio fades at each cut.
  - Output: `data/create/<p>/footage/edited/`.

## Evidence (2026-10-09, sandbox)
- **Input:** a 19 s ElevenLabs TTS take (27 credits) with a false start, a long pause, "Um" and a cue-word retake,
  as a 29.97 fps vertical clip, plus a 3 s HLG HDR landscape clip.
- **Ingest:** both conformed to 30 fps; HDR detected and tone-mapped.
- **Scribe:** 42 words. Kept "to--", "Um,", "Acme" (keyterm) and "[beep]".
- **Cuts:**
  - c001: the leading silence and "So today I want to--";
  - c002: the pause and "Um,";
  - c003: the cue line "It tracks the brands, again.".
- **Result:**
  - 20.8 s of takes became 15.3 s (460 frames);
  - `create captions` gave 14 vertical groups;
  - `create burn` produced a frame-exact 1080x1920 captioned MP4.
  - About 70 s end to end.

## Addendum: framing and the corner bubble (2026-10-09)
- **F5 `create reframe`** gives each edited segment one steady crop at its median face (OpenCV YuNet 2026may, MIT,
  pinned by sha256 in config), with the eyes 36% down.
  - Consecutive jump cuts within a take alternate a 1.12 punch-in.
  - With no face, the crop is centred.
  - Output: `projects/<p>/framing.json`.
  - There is no motion within a shot, so nothing jitters.
- **F6** renders the full frame from those crops.
  - Segment audio is padded to the segment's exact length; muxes keep the video's length.
- **`create pip <p> --background video.mp4 [--corner br|bl|tr|tl]`** (create/footage/layout.py,
  create/kit/layout.html) sets the presenter's layout per timeline scene from `projects/<p>/layout.yaml` (default:
  bubble throughout):
  - `full`: the presenter fills the frame;
  - `pip`: a round bubble with a brand-surface ring;
  - `off`: only the background shows; the voice continues.
  - One full-frame video is used throughout. For the bubble it is clipped to a circle around the face (from F5
    framing) and scaled into the corner, so a layout change is one continuous move (0.6 s, power3.inOut), never a
    cut.
  - The bubble sits as far into the corner as the frame's safe rects allow, and always above the caption band. On
    vertical, the upper extension puts it above TikTok's action rail.
  - The background is cover-scaled and held on its last frame.
  - `layout.yaml` is a human/Claude-written input, validated against the timeline's scenes.
- **Evidence:** 16 s of a real presenter from the research corpus (Apollo.io, local only). YuNet found his face in
  every sample (score 0.95).
  - The 1280x720 source was cropped to a vertical frame centred on his face.
  - A `full` intro, then a shrink into the bubble over the Acme v2 film, burned with captions frame-exact.

## Addendum: TikTok finish on Robert's first take (2026-10-09)
Robert's first real take (81 s, Budapest, phone) went through every step. What changed because of it:
- **Pacing.** The take's first 18.6 s had no cut. F4 now splits any stretch longer than
  `create.footage.cuts.punch_max_s` (5 s) at a sentence end (else a comma, else a pause), with pieces of at least
  `punch_min_s`. Nothing is removed and the audio has no fade at those joins; F5's alternating punch-in makes each
  piece a visible change. The edit's first shot ends by `punch_hook_s` (2.5 s), so the hook has a change in it.
- **Loudness.** The edited take measured -26 LUFS. F6 now finishes the voice (high-pass, light denoise, compressor,
  two-pass linear loudnorm to the middle of the destination's band, then a 4x oversampled limiter at
  `create.footage.voice.true_peak_db`). Every later step copies that audio: each AAC re-encode raised the true peak
  (-1.0 to +0.6 dBTP over three passes).
- **Captions.** Robert: captions were too close to his face. Vertical captions now sit lower (the band is
  y 1050-1240) and are pushed below the chin. In split scenes they end just above the product's bottom edge
  (`create.design.caption_seam_gap_px`), never over his head.
- **Two ways to show the product** (Robert): `split` in `layout.yaml` (the product fills the top half, he moves to
  the bottom half), or `create overlay` cards over his own video (`overlays.yaml`), placed in the safe area away
  from his face and the caption band.
- **`create qa`** checks the final file: format, loudness and true peak, dead air, a visual change in the first 3 s,
  no static stretch over 6 s, and caption and overlay placement. Both versions of the take pass every check
  (-14.0 LUFS, -1.6 dBTP, first change at 2.3 s and 1.0 s, longest static stretch 5.0 s).

## Consequences
- **Not done yet:**
  - presenter archetypes (full, PiP, split) for the storyboard;
  - music under the voice;
  - an approval page that works from a phone.
- The heuristics are config (`create.footage.cuts`). They should be tuned on Robert's first real takes.
