# 0007 — S3 signal methods (M2)

- **Status:** accepted
- **Date:** 2026-10-03
- **Milestone:** M2

## Context
The plan named PySceneDetect for cuts and "spectral-flux onsets on the accompaniment" for SFX. Building
against frame-exact fixtures showed what is needed in practice.

## Decisions
1. **Own cut/transition detector** (dropped `scenedetect`). Hard cuts use an AdaptiveDetector-style
   spike-to-neighbourhood ratio; gradual transitions need extras PySceneDetect does not give: crossfade
   by alpha-blend fit, push by phase-correlation shift (flat UI colours defeat corner trackers), and a
   zoom/whip rule (a cut spike inside sustained global motion is one transition, not a cut).
2. **Thresholds in seconds, not frames** (merge gaps, minimum event length), so 60 fps behaves like 30 fps.
3. **SFX on a REPET foreground of the accompaniment stem.** A music bed repeats every beat; the median
   of the spectrogram at ±k beat periods models it and one-off sounds remain. Onsets are refined on
   the foreground waveform (5 ms envelope) because STFT frames smear time by ~46 ms. Speech is removed
   by demucs first; without stems the full mix is used and the summary says so.
4. **Rule labels first, CLAP later.** Whoosh/riser (slow, noisy build), impact (fast, low-heavy), click
   (< 40 ms). CLAP zero-shot is added in M2c and recorded with `label_source`.
5. **faster-whisper gets a decoded array** (librosa, 16 kHz): its PyAV decoding breaks on newer PyAV.
   Word boundaries are tightened to voice energy (Whisper drifts 100-400 ms into silence).
6. **Captions:** a native-fps change signal on the bottom band, counted only when the rest of the frame
   is calm; OCR once per stable stretch in a second decode pass (memory stays flat).
7. **CPU-only torch** via a uv index for demucs; the image drops the uv cache (3.9 GB).

## Consequences
All thresholds are in `config/lens.yaml` and were tuned on synthetic fixtures; expect retuning on real
footage (Acme v1 first, then the pilot at G1/G2). The fixtures stay as regression tests.
