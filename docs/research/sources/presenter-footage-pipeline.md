# Presenter footage in the pipeline: research and recommendations

Research date: 2026-10-09. Scope: Robert films himself; the pipeline transcribes, proposes cuts (he approves),
cuts, uses his words as the clock, overlays animation, and does PiP or layout switches plus captions, in 16:9 and 9:16.
No generative avatars, face swaps or image generation. Local tools only (ElevenLabs only for voice, as now).

Confidence: **high** = read in an official repo, PyPI/npm/HF metadata or official docs today; **medium** = official
source read second-hand, or inferred from code; **low/heuristic** = practice or my estimate. Every heuristic number is
a starting value for `config/lens.yaml`, not a fact.

---

## 0. TL;DR (the recommended stack)

| Job | Pick | Licence (code / weights) | Version checked | Conf. |
|---|---|---|---|---|
| ASR + word times | **WhisperX** (faster-whisper backend + wav2vec2 forced alignment) | BSD-2-Clause / whisper MIT; align models Apache-2.0 | whisperx 3.8.6 (PyPI, 2026-05-25) | high |
| ASR alternative (benchmark it) | NVIDIA **Parakeet TDT 0.6B v3** via `parakeet-mlx` on the Mac | CC-BY-4.0 weights; parakeet-mlx Apache-2.0 | HF model 2026-08-05; parakeet-mlx 0.5.3 | high |
| Verbatim fillers | **Not CrisperWhisper** (weights non-commercial). Detect fillers in code: speech regions with no aligned word, plus filler tokens | n/a | — | high (licence) |
| VAD | **Silero VAD** | MIT | silero-vad 6.2.3 (2026-09-23) | high |
| Silence first pass, reference | ffmpeg `silencedetect`; auto-editor as a reference/NLE export only | ffmpeg LGPL/GPL build; auto-editor Unlicense | ffmpeg 9.0.2; auto-editor 29.3.1 PyPI / 31.7.2 Homebrew | high |
| Conform/tone map | ffmpeg (**Homebrew `ffmpeg-full`**, which has zimg + libplacebo; plain `ffmpeg` does not) | GPL-3.0-or-later build | 9.0.2 | high |
| Noise reduction | ffmpeg `arnndn` (RNNoise models) or **DeepFilterNet** `deep-filter` binary | RNNoise BSD-3; DeepFilterNet MIT/Apache-2.0 | deepfilternet 0.5.6 (2023, stale) | high |
| Loudness | ffmpeg `loudnorm` two-pass, linear | — | — | high |
| Face boxes | **OpenCV YuNet** (already have opencv) or MediaPipe Face Detector (Tasks API) | YuNet MIT; OpenCV Apache-2.0; MediaPipe Apache-2.0 | opencv-python 5.0.0.93; mediapipe 1.1.0 (2026-10-06) | high |
| Crop smoothing | Own code: dead-zone + critically-damped follow, or offline L1-optimal path; 1€ filter for live-ish | own | — | medium |
| Background removal (later) | `hyperframes remove-background` (u2net_human_seg → VP9-alpha WebM) | Apache-2.0 | hyperframes 0.8.143 | high |
| NLE hand-off | **OpenTimelineIO** `.otio` (Resolve imports natively), plus FCPXML/FCP7 XML/CMX EDL adapters | Apache-2.0 | opentimelineio 0.18.1, OpenTimelineIO-Plugins 0.18.1 | high |
| Composite | HyperFrames `<video>` with `data-media-start` per kept segment, wrapper div animated for PiP/punch-in | Apache-2.0 | 0.8.143 (repo pins 0.8.137) | high |

Biggest findings:
1. **HyperFrames already ships a talking-head workflow** (`skills/talking-head-recut`: layouts `overlay`, `pip`,
   `split`, `stack`; and `skills/embedded-captions`). Both keep the clip **uncut** ("the clip plays untouched"), so
   cutting, EDL and the word clock are ours to build, but the layout/PiP recipes are a ready reference (Apache-2.0;
   talking-head-recut is adapted from MIT `notedit/vtake-skills`). Its own caption pipeline **prefers WhisperX 3.8.6,
   CPU int8**, because "wav2vec2 forced alignment gives word timings far tighter than whisper.cpp's ... our gates are
   80ms-strict" (`skills/embedded-captions/scripts/transcribe.cjs`).
2. **CrisperWhisper weights are non-commercial.** The repo code is MIT, but CrisperWhisper 2.0 weights use the "Nyra
   Health Non-Commercial Research License"; v1 on HF is `cc-by-nc-4.0`. Client explainers are commercial, so it is out
   unless Robert buys a commercial licence.
3. **HDR footage flips the HyperFrames render to HDR10.** Render "detects HDR media ... the output uses 10-bit H.265"
   unless `--sdr`. Conform iPhone footage to SDR Rec.709 at ingest (or shoot SDR), and pass `--sdr` as a guard.
4. **HyperFrames render does not use the browser to seek video**: it pre-extracts frames with FFmpeg (VFR goes through
   `-fps_mode cfr -r`), at **source resolution**. A 4K source in a 400 px PiP still extracts 4K frames, so feed it
   pre-scaled plates per layout.
5. **Homebrew `ffmpeg` 9.0.2 lacks zimg (zscale) and libplacebo**; `ffmpeg-full` 9.0.2 has both (and rubberband).

---

## 1. Transcription with accurate word timestamps

### 1.1 faster-whisper (in repo already, `lens/signals/speech.py`, `small.en`, int8)
- PyPI faster-whisper 1.2.1 (2025-10-31), MIT. https://pypi.org/project/faster-whisper/ (high)
- `word_timestamps=True` = "cross-attention pattern and dynamic time warping" (docstring in
  `faster_whisper/transcribe.py`, HEAD). DTW timings are attention-derived, not acoustic: good to roughly a word,
  not frame-tight. (high for the method; precision claim medium)
- `vad_filter` uses Silero VAD; README: "The default behavior is conservative and only removes silence longer than 2
  seconds"; VAD defaults in `vad.py` HEAD: `threshold 0.5, min_silence_duration_ms 2000, speech_pad_ms 400`. https://github.com/SYSTRAN/faster-whisper (high)
- Other knobs: `initial_prompt`, `hotwords` ("Hotwords/hint phrases to the model. Has no effect if prefix is not
  None"), `multilingual` ("Perform language detection on every segment"), `hallucination_silence_threshold`,
  `condition_on_previous_text`. (high, docstring)
- Known issues (user reports, not maintainer-confirmed; medium):
  - Hallucination on silence/near-silence; VAD does not always remove near-silence, and denoising before VAD made it
    worse in one report: https://github.com/SYSTRAN/faster-whisper/issues/843
  - Word times shifted 0.5–1 s early in one setup (VAD off): https://github.com/SYSTRAN/faster-whisper/issues/812
  - whisper-timestamped notes that untranscribed disfluencies push the next word's start back to the disfluency
    onset (so "um, Acme" can make "Acme" start at the "um"): https://github.com/linto-ai/whisper-timestamped
  - HyperFrames' own transcriber guards against "Whisper hallucinates trailing words over a silent tail" with
    `silencedetect=noise=-35dB:d=0.6` and a mean-volume no-speech gate (`transcribe.cjs`). (high, code read)
- On Apple Silicon CTranslate2 runs on CPU (backends listed: MKL, oneDNN, OpenBLAS, Ruy, Apple Accelerate; no Metal).
  https://github.com/OpenNMT/CTranslate2 (medium: inferred from the backend list)

### 1.2 WhisperX (recommended for cut detection and captions)
- PyPI whisperx 3.8.6 (2026-05-25), BSD-2-Clause, Python >=3.10,<3.14. https://github.com/m-bain/whisperX (high)
- Pipeline: VAD → batched faster-whisper → **wav2vec2 phoneme forced alignment** per language → word times; optional
  pyannote diarization (needs an HF token + licence acceptance; we do not need it for one speaker).
- Alignment models (`whisperx/alignment.py`): `en` = torchaudio `WAV2VEC2_ASR_BASE_960H`; `ro` =
  `gigant/romanian-wav2vec2` (HF tag **apache-2.0**). HF `facebook/wav2vec2-base-960h` and
  `jonatasgrosman/wav2vec2-large-xlsr-53-english` are apache-2.0. (high) The torchaudio pipeline weights come from
  fairseq (MIT) (medium; check torchaudio docs before relying on it).
- Mac: README says run with `--compute_type int8 --device cpu`. (high)
- Limitations (README): words with characters outside the alignment dictionary ("2014.", "£13.60") get **no timing**;
  overlapping speech is weak. So: numbers/brand names with digits need interpolated times (flag them
  `source="interpolated"`). (high)
- HyperFrames runs it as `uvx --python 3.12 --from whisperx==3.8.6 whisperx wav --model <m> --device cpu
  --compute_type int8 --no_align_deletes`. (high, code read)

### 1.3 Others
| Tool | Version / licence | Useful bits | Verdict |
|---|---|---|---|
| stable-ts | 2.19.1 (2025-08-16), MIT | Silence suppression of timestamps (`suppress_silence`, Silero `vad` option, `vad_threshold` 0.35 default), regrouping, can wrap faster-whisper | Good fallback if WhisperX alignment fails on a language; MIT. (high) |
| whisper-timestamped | 1.15.9, **GPLv3** | per-word confidence, `detect_disfluencies` ("[*]" marks) | Licence: keep out of the codebase (GPL). (high) |
| mlx-whisper | 0.4.3 (2025-08-29), MIT | Metal GPU on Apple Silicon, `word_timestamps=True` | Fast Mac transcription; DTW timings like faster-whisper. (high) |
| whisper.cpp | Homebrew `whisper.cpp` 1.9.5, MIT | Metal + Core ML encoder ("more than x3 faster compared with CPU-only"), `-ml 1` word-level | HyperFrames' built-in `transcribe` uses it; segment-interpolated word times (HF's own comment). (high) |
| WhisperKit | Homebrew `whisperkit-cli` 1.1.1, MIT | Apple-native | Optional. (high for licence/version only) |
| Parakeet TDT 0.6B v3 | HF CC-BY-4.0 (attribution needed), 25 EU languages incl. **ro** and **en**, auto language detect, word timestamps; `parakeet-mlx` 0.5.3 Apache-2.0 | HyperFrames uses "Parakeet on macOS" for transcribe (`skills/media-use/references/setup-providers.md`) | Benchmark against WhisperX on Robert's RO/EN footage. Filler behaviour **unknown** (card says nothing). (high for facts; medium for fit) |
| CrisperWhisper | Code MIT (2026); **weights non-commercial** (2.0: Nyra Health Non-Commercial Research License; 1.0 HF `cc-by-nc-4.0`); 1.0 is EN/DE only; 2.0 claims disfluency F1 87.8 on Nyra's own benchmark | Verbatim fillers, repetitions, cut-offs | **Out for client work** unless Robert buys a licence. https://github.com/nyrahealth/CrisperWhisper , https://huggingface.co/nyralabs/CrisperWhisper (high) |

### 1.4 Fillers: normal Whisper drops them
- Whisper "is designed to generate clean output ... mostly excludes filler words" (research summary; medium). A
  filler-laden `initial_prompt` (the OpenAI prompting guide's example, quoted second-hand: "Umm, let me think like,
  hmm... Okay, here's what I'm, like, thinking.") raises filler recall but can cause hallucination. (medium)
  https://huggingface.co/spaces/openai/whisper/discussions/30
- **Recommended (code measures, Claude names):**
  1. Transcribe with WhisperX (`--no_align_deletes` off or on: test), keep every word with `score`.
  2. Run Silero VAD at fine settings (`min_silence_duration_ms` ~150, `speech_pad_ms` ~30; heuristic).
  3. **Unaccounted speech** = VAD speech not covered by any aligned word (± 40 ms). Each region ≥ 120 ms is a filler
     candidate (an "um/uh/ăă" is a sustained voiced sound: steady F0 via `librosa.pyin`, low spectral flux). These
     become `filler` cut proposals with their measured span.
  4. Token list for the words that do come through (`um, uh, er, ah, hmm, like, you know, I mean`; Romanian `ăă,
     îî, păi, deci, adică`), only proposed, never auto-cut (`deci`/`adică` are often real words).
  5. Optional second pass with the filler prompt on the candidate windows only, to label them.
- ElevenLabs **Scribe** (STT) exists and scores high on disfluency in Nyra's table, but it is outside the rule (voice
  only). https://elevenlabs.io/docs/api-reference/speech-to-text/convert (high that it exists)

### 1.5 Romanian + English, brand names
- Whisper picks one language per 30 s window; faster-whisper `multilingual=True` re-detects per segment. Mid-sentence
  code-switching is unreliable (medium, general Whisper behaviour). WhisperX aligns with **one language model per
  run**. Rule: one primary language per video (`--language ro` or `en`); English product terms inside Romanian speech
  align with the RO model as Latin letters (medium; test).
- Never use `.en` models for Romanian. HyperFrames docs warn `.en` models translate non-English audio. (high)
- Vocabulary: put brand names in `initial_prompt` and `hotwords` (faster-whisper), then a **lexicon post-fix in code**
  (`projects/<p>/lexicon.yaml`: `{"geo flux": "Acme"}`) applied to text only, times unchanged. Times for words with
  digits are interpolated (WhisperX limitation).

### 1.6 Which to pick
- **(a) Cut detection:** WhisperX `large-v3` (MIT on HF via Systran/faster-whisper-large-v3) or `large-v3-turbo`
  (MIT) + Silero VAD gaps + unaccounted-speech filler detection. Benchmark Parakeet v3 (MLX) on the same takes.
- **(b) Captions:** the same aligned words **after the EDL is applied** (remapped times), fillers dropped, lexicon
  fixed. No second transcription needed; optionally re-run alignment on the cut audio as a check (time error ≤ 1
  frame = gate).
- Speed: no measured Apple Silicon numbers here; measure on Robert's Mac with a fixture (`make fixtures` already
  generates espeak-ng narration). Don't quote vendor speed-ups as facts.

---

## 2. Cut suggestion

### 2.1 Silences
- ffmpeg `silencedetect`: `noise` default **-60 dB**, `d` default **2 s**; prints `silence_start/end`. (high,
  https://ffmpeg.org/ffmpeg-filters.html#silencedetect) For speech use relative thresholds: noise floor measured per
  take (e.g. 10th percentile RMS) + 6–10 dB (heuristic). Prefer Silero VAD probabilities over dB in noisy rooms.
- **auto-editor** (Unlicense; PyPI 29.3.1, Homebrew 31.7.2; now written in Nim): default `--edit
  audio:threshold=0.04`, default `--margin 0.2sec`, asymmetric `--margin 0.3s,1.5sec`; `--edit motion:...`; exports
  `--export premiere|resolve|final-cut-pro|shotcut|kdenlive`; has a "v3" JSON timeline format. (high,
  https://pypi.org/project/auto-editor/ , https://auto-editor.com/docs) Use as a **reference and quick NLE rough cut**,
  not as our engine (it cuts by loudness only, no words).
- Silero VAD 6.2.3, MIT, https://github.com/snakers4/silero-vad (high).

### 2.2 Retakes and false starts (text-based, Descript-style)
Descript's model is "edit the transcript, the media follows". Its "Smooth jump cuts" is **generative regeneration**
(AI credits) so it is excluded by our rules. https://help.descript.com/script-editing/smooth-jump-cuts (high)

Algorithm (code, deterministic, test-first on synthetic transcripts):
1. Normalise words (lowercase, strip punctuation, fold diacritics for matching only).
2. **Script alignment when a script exists** (Robert reads from `script.yaml`): align the word stream to script lines
   with `difflib.SequenceMatcher`/Needleman-Wunsch. Every script line gets its candidate takes; propose to keep the
   **last complete take** with the fewest fillers and highest mean word score; earlier takes become `retake` cuts.
3. **No script:** repeated n-grams (n ≥ 3) within a window (≤ 30 s) where the first copy ends in a cut-off word
   (word duration < 120 ms, low score, or followed by a pause > 300 ms) → `false_start` proposal covering the first
   copy up to the restart. Single-word stutters ("the the") → `repeat`.
4. **Slate words**: Robert says a fixed cue ("again" / "retake") or claps; clap = broadband transient (onset strength
   peak with flat spectrum) → hard boundary, everything from the previous sentence start to the clap is proposed out.
5. Every proposal: `{id, kind, start_word, end_word, t0, t1, reason, confidence, default: cut|keep}`; Robert approves
   on a page (human gate), like the G2 gold page.

### 2.3 Padding, breath, J/L cuts, jump-cut jank (heuristics; put in config)
- Pads: keep **80–150 ms before** a word onset and **120–250 ms after** the last word (auto-editor's 0.2 s is a
  symmetric default; faster-whisper's VAD pads 400 ms). Never cut inside a word; snap cut points to the quietest
  10 ms frame inside the gap.
- Breaths: keep a breath before a new sentence if the gap allows (breath = unvoiced, broadband, 150–400 ms); remove
  breaths between fused clauses. Audio crossfade 10–20 ms at every cut (removes clicks; DSP practice).
- Max kept silence between sentences ~0.35–0.6 s; inside a sentence ~0.15 s (house pacing; compare with
  `exports/pacing.json`).
- **J/L cuts:** in the EDL, video and audio can have different in/out points. Use them at **layout switches**
  (presenter → product animation): the graphic leads the word by a few frames, or the presenter stays on screen
  while the first words of the next scene play. Within a single-camera talking head, keep A/V locked.
- **Jump-cut jank:** alternate framing on consecutive cuts (punch-in 100% ↔ 112–120% scale, re-centred on the face),
  never two cuts in a row at the same framing unless a graphic covers the cut; cover dense cuts with B-roll/product
  animation (= `presenter_pip` or full product scene). Tella documents punch-ins as "Smooth" or "Hard Cut".
  https://www.tella.com/help/tips/punch-in-zoom-in-on-your-camera (medium) Upscaling limit: from a 4K source a 120%
  punch-in to 1080p is still a downscale; from 1080p it softens.

---

## 3. Media handling (ingest/conform)

All commands are starting points; codify them in code with config values. Use Homebrew **`ffmpeg-full`**
(9.0.2, zimg + libplacebo + rubberband). Plain `ffmpeg` 9.0.2 deps are dav1d, lame, libvmaf, libvpx, openssl,
opus, sdl2-compat, svt-av1, x264, x265, xz. (high, https://formulae.brew.sh/api/formula/ffmpeg.json ,
https://formulae.brew.sh/api/formula/ffmpeg-full.json)

### 3.1 Probe
```bash
ffprobe -v error -select_streams v:0 -show_entries \
  stream=codec_name,width,height,r_frame_rate,avg_frame_rate,pix_fmt,color_space,color_transfer,color_primaries:stream_side_data \
  -show_entries format=duration -of json in.mov
ffprobe -v error -select_streams v:0 -show_entries packet=pts_time -of csv=p=0 in.mov   # frame intervals → VFR test in code
```
VFR = interval std/mean above a tolerance, or `r_frame_rate != avg_frame_rate`. Phone cameras commonly record VFR
(medium; detect, don't assume). Rotation lives in display-matrix side data; ffmpeg auto-rotates when it re-encodes
(`-noautorotate` disables it) (medium; verify on a real clip).

### 3.2 Conform to a CFR SDR master (once per take)
```bash
# SDR source → 30 fps CFR, Rec.709 tags, short GOP, PCM audio
ffmpeg -i in.mov -map 0:v:0 -map 0:a:0 \
  -vf "fps=30,format=yuv420p" -fps_mode cfr \
  -c:v libx264 -crf 12 -preset slow -g 15 -keyint_min 15 -sc_threshold 0 \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -c:a pcm_s24le -ar 48000 master.mov
```
- `fps=30` resamples timestamps to a fixed grid (drops/duplicates frames), `-fps_mode cfr` (replaces `-vsync`).
  HyperFrames' extractor itself uses `-fps_mode cfr -r <fps>` for VFR (code read, high), but our cut math needs CFR
  frames **before** any EDL, so conform first and cut on that clock.
- Keep 4K masters only when 9:16 crops or punch-ins are planned; otherwise 1080p.
- ProRes alternative for the master: `-c:v prores_ks -profile:v 3` (422 HQ) (high, standard ffmpeg encoder).

### 3.3 HDR (HLG / Dolby Vision) → SDR Rec.709
iPhone 12–14 "record video in Dolby Vision HDR"; turn off at Settings > Camera > Record Video > HDR Video.
https://support.apple.com/guide/iphone/iph2cafe2ebc/ios (high). Apple: https://support.apple.com/102241
```bash
# zscale + tonemap (needs zimg → ffmpeg-full)
-vf "zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p"
# libplacebo (needs Vulkan; on macOS via MoltenVK, medium); peak_detect off for reproducible frames
-vf "libplacebo=tonemapping=bt.2390:peak_detect=false:colorspace=bt709:color_primaries=bt709:color_trc=bt709:range=tv:format=yuv420p"
```
- ffmpeg docs: `tonemap` "expects data in single precision floating point ... Another filter, such as zscale, is
  needed"; libplacebo `apply_dolbyvision` is on by default; `peak_detect` "If ... exactly reproducible frame-perfect
  results are needed, it's recommended to turn this feature off". (high, ffmpeg-filters.html)
- HyperFrames: HDR auto-detect promotes the render to HDR10 (10-bit H.265, BT.2020) unless `--sdr`; forced `--sdr`
  tone-maps HDR sources before frame extraction (changelog). https://github.com/heygen-com/hyperframes
  `docs/guides/hdr.mdx` (high). We still tone-map at ingest so lens signals, previews and plates all see the same
  pixels. Best: **shoot SDR**.

### 3.4 Scaling and plates per layout (performance)
- HyperFrames render pre-extracts frames via FFmpeg at source size, then injects them (`videoFrameExtractor.ts`;
  "Pre-extracts video frames using FFmpeg for frame-accurate rendering"). (high) So:
  - `full` plate 1920x1080 (or 1080x1920), `pip` plate at the bubble size × 2 (e.g. 800x800), crop plates already
    reframed. Never put the 4K master in a composition.
  - Plates: `libx264 -crf 14 -g 30 -keyint_min 30 -movflags +faststart` (repo practice; talking-head-recut says sparse
    GOP "freeze on seek in the renderer"). (high)
- Proxy for review pages: 540p H.264 CRF 23 (cheap; heuristic).
- Lanczos scaling: `scale=1920:1080:flags=lanczos`.

### 3.5 External mic sync and drift
- Code (numpy/scipy, BSD): cross-correlate the camera scratch track and mic track (16 kHz mono, onset-strength
  envelope or band-passed signal), `scipy.signal.correlate(method="fft")`; refine on raw audio around the peak.
  Measure offset at the start and at the end of each take; drift = Δoffset / duration. Correct if total drift
  > ½ frame (17 ms at 30 fps): `asetrate=48000*(1+d),aresample=48000` or rubberband. Recorder clock error of tens of
  ppm is typical (estimate, low): 20 ppm over 10 min = 12 ms.
- Ready-made: `audalign` 1.3.1 MIT, `syncstart` 1.1.1 MIT (high for licence). praat-parselmouth is **GPLv3** (avoid).
- Clap at the start of every take makes the correlation trivial and doubles as a slate.

---

## 4. Local audio cleanup (voice chain)
Order (heuristic): high-pass → denoise → EQ → compressor → de-esser → two-pass loudnorm on the mix.
- **Noise:** ffmpeg `arnndn=m=<model>` (RNNoise; "model ... always required"; `mix` −1..1). Models from
  GregorR/rnnoise-models ("none of this work is creative and thus none of it is subject to copyright"); RNNoise itself
  BSD-3 (xiph/rnnoise COPYING). **DeepFilterNet** MIT OR Apache-2.0; pre-compiled `deep-filter` binary, "only wav
  files with a sampling rate of 48kHz are supported"; PyPI 0.5.6 is from 2023-08 (stale; prefer the binary).
  https://github.com/Rikorose/DeepFilterNet (high). `afftdn` (built-in spectral denoiser) for steady hiss. Caution:
  denoise **after** VAD/ASR analysis, never before (issue #843: noisereduce made false speech longer).
- **De-ess:** ffmpeg `deesser` (`i` intensity default 0, `m` 0.5, `f` 0.5) (high). Start `i=0.3–0.5` (heuristic).
- **EQ/compression** (heuristic starting points): `highpass=f=80`; cut 200–400 Hz −2..−4 dB if boomy; presence
  +2 dB at ~4 kHz; `acompressor=threshold=-20dB:ratio=3:attack=10:release=150:makeup=2`. Measure, then listen.
- **Loudness:** `loudnorm` (EBU R128): defaults I −24, LRA 7, TP −2; two-pass: pass 1 `print_format=json`, pass 2 with
  `measured_I/LRA/TP/thresh` + `offset` and `linear=true` (falls back to dynamic if conditions fail). (high) House
  targets are already in `config/lens.yaml` (`loudness:` −16..−14 LinkedIn, −15..−13 YouTube; the Acme master was
  −15.2 I, −1.2 TP). `ffmpeg-normalize` 1.42.0 (MIT) wraps the two passes.
- **Room echo:** fix at capture (soft room, mic close). Local dereverb option: `nara_wpe` 0.0.11, MIT (WPE; untested
  here, medium). Avoid generative "enhancers" (they re-synthesise the voice).
- **Stems:** demucs (in repo) can split voice from music bed if Robert records with music playing (avoid that).
- ElevenLabs **Voice Isolator** exists (https://elevenlabs.io/docs/capabilities/voice-isolator) but is outside the
  rule (voice generation only); list it as "Robert may extend".

---

## 5. Face detection, tracking and reframing
- **OpenCV YuNet** (`opencv_zoo/models/face_detection_yunet`): files MIT ("All files in this directory are licensed
  under MIT License"); `face_detection_yunet_2026may.onnx` has dynamic input shape for the OpenCV 5.x ONNX Runtime
  engine; `2023mar` fixed shape; int8 variant. `cv2.FaceDetectorYN`. We already depend on opencv-python-headless 5.x.
  https://github.com/opencv/opencv_zoo (high) → **first choice** (no new dependency).
- **MediaPipe** 1.1.0 (2026-10-06), Apache-2.0, macOS arm64 wheel. The 1.x wheel ships only `mediapipe/tasks` (no
  legacy `mediapipe.solutions`): use the Tasks API (`FaceDetector`, `FaceLandmarker`, `ImageSegmenter`). Face Detector
  models: BlazeFace short-range, full-range, sparse full-range, 128x128, running modes IMAGE/VIDEO/LIVE_STREAM. Page
  says text CC-BY-4.0, code Apache-2.0, **model licence is in the model cards** (historically Apache-2.0; medium —
  read the PDF before shipping). https://developers.google.com/edge/mediapipe/solutions/vision/face_detector (high)
- **AutoFlip**: a MediaPipe Legacy Solution, "We have ended support ... as of March 1, 2023"; README: "only works with
  OpenCV 3". Use as a design reference only. (high)
- **Crop path (own code, renderer-agnostic, test-first):**
  1. Detect every 2nd–3rd frame on the 540p proxy, keep the largest/most-confident face, interpolate.
  2. Target = face centre with headroom (eyes at ~⅓ from the top of the crop; heuristic).
  3. Smooth offline (we have the whole clip): dead-zone (no move while the face stays within ±6% of crop width) +
     critically damped spring follow with a max speed; or the **L1-optimal camera path** (Grundmann et al., CVPR 2011,
     "Auto-directed video stabilization with robust L1 optimal camera paths": static/linear/parabolic segments; medium)
     via `scipy.optimize.linprog`. For causal smoothing use the **1€ filter** (Casiez et al., CHI 2012;
     https://gery.casiez.net/1euro/ ; PyPI `OneEuroFilter` 0.2.1 BSD) (medium).
  4. Hold the crop constant through each kept segment unless a deliberate punch-in; re-solve per segment; cuts may
     jump framing (that's the punch-in alternation).
  5. Render the crop in ffmpeg (`crop` accepts x/y commands via `sendcmd`) or PyAV/OpenCV into a plate; record the
     path in JSON (`reframe.json`) so it's measured, reviewable and reproducible.
- **Background removal (later/optional):**
  | Tool | Licence | Note |
  |---|---|---|
  | `hyperframes remove-background` | Apache-2.0 (u2net_human_seg, Apache-2.0) | `.webm` VP9 alpha default ("Chrome-native transparent playback"), `.mov` ProRes 4444; CoreML on Apple Silicon; ~168 MB model; `--background-output` plate. Easiest path. (high) |
  | MediaPipe ImageSegmenter (selfie) | Apache-2.0 code; model card licence to check | fast, coarse edges (medium) |
  | BiRefNet | MIT code + HF weights (`license:mit`) | high quality stills, slow per frame, no temporal consistency (medium) |
  | rembg 2.0.85 | MIT (models vary) | wrapper around u2net/birefnet etc. (high) |
  | RobustVideoMatting | **GPL-3.0** | temporally stable, but GPL: keep out of the codebase (high) |

---

## 6. Compositing in HyperFrames (renderer facts, from the repo at 0.8.143)
Source: https://github.com/heygen-com/hyperframes (cloned 2026-10-09, commit 46f6cb3, CLI 0.8.143; npm latest
0.8.143). Repo pins 0.8.137: re-check lint rules after an upgrade.

- **Media attributes** (`skills/hyperframes-core/references/data-attributes.md`): `data-start`, `data-duration`
  (trims), **`data-media-start`** ("Offset into the media source, in seconds"), `data-volume` (0..3.98),
  `data-has-audio="true"` (footage with sound; else `muted`, lint `video_missing_muted`), `data-playback-rate`,
  `data-link` / `data-sync-origin` (editing contract for a video and its detached audio), `data-automation` volume
  lane for fades/ducking, `data-color-grading`. Every `<video>`/`<audio>` needs an `id`. (high)
- **One kept segment = one `<video>` clip**: `src=master_plate.mp4 data-media-start=<src_in> data-start=<rec_in>
  data-duration=<len>`. Visibility window is half-open `[start, start+duration)`, so back-to-back clips abut exactly.
  (high)
- Rules (`variables-and-media.md`): don't call `play()`/seek; **don't animate timed media dimensions — animate a
  non-timed wrapper**; never nest a `<video data-start>` inside a timed wrapper (lint error
  `video_nested_in_timed_element`); no `crossorigin`. Use a separate `<audio>` for J/L cuts and mute the video it
  replaces. (high)
- **PiP / layouts**: talking-head-recut animates `#video-wrap` with GSAP between layouts (`overlay`, `pip` e.g.
  `{left:1480, top:760, width:400, height:300}` with a `pip-pill` class for radius + ring + shadow, `split`, `stack`,
  hide = `opacity:0`) and `object-fit: cover` inside the wrapper. A circular bubble = `border-radius:50%` or
  `clip-path: circle()` on the wrapper. Punch-in = `scale` on the wrapper with transform-origin at the face. (high)
- **Seeking**: render pre-extracts frames with FFmpeg (frame-accurate; browser seeking not used for render); live
  preview uses the browser and auto-proxies HEVC to H.264. HEVC 8/10-bit renders fine. (high)
- **Alpha**: extractor "Always force[s] the alpha-aware decoder on codecs that can carry alpha" (libvpx-vp9); VP9-alpha
  WebM works in `<video>`; `render --format webm|mov` outputs transparency. (high)
- **Audio from video**: kept on the `<video>` with `data-has-audio`; for our pipeline prefer **one cleaned voice
  `<audio id="vo">`** built from the EDL (crossfaded, denoised, loudnormed) and all `<video>` clips `muted`. That
  keeps audio processing in code and gives one voice stem for SFX masking (learnings section e). (recommendation)
- **Remotion reference (do not copy):** `<OffthreadVideo>` also extracts the exact frame outside the browser with
  FFmpeg and shows it as an image; `transparent` uses PNG (slower), `toneMapped` on by default; `trimBefore` +
  `durationInFrames`. Same design as HyperFrames. https://www.remotion.dev/docs/offthreadvideo (high)

---

## 7. New stages and schemas

Footage stages slot before C5 and replace C4 (TTS voice) when the project's voice source is `presenter`. All write
small JSON in `projects/{project}/` and media in `data/create/{project}/` (never committed), and register in
`lens/stages.py` with exact paths (`lens dag --check`).

| Id | Runner | Writes | What |
|---|---|---|---|
| `f1_footage_ingest` | CODE | `projects/{p}/footage.json`, `data/create/{p}/footage/**` | probe, VFR/HDR/rotation flags, CFR SDR master, 540p proxy, 16 kHz + 48 kHz WAV, mic sync offsets + drift |
| `f2_transcript` | CODE | `projects/{p}/transcript.json` | WhisperX words `{id,w,t0,t1,score,take}`, VAD regions, unaccounted-speech regions, lexicon fixes, engine + model provenance |
| `f3_cut_proposals` | CODE (+CLAUDE labels optional) | `projects/{p}/cuts.proposed.json` | silence, filler, false_start, repeat, retake proposals with reasons; script alignment |
| `f3g_cut_review` | HUMAN GATE | `projects/{p}/cuts.approved.json` (written by an import command from the page export) | Robert approves/edits on a review page (proxy video + transcript, like the G2 gold page) |
| `f4_edl` | CODE | `projects/{p}/edl.json`, `data/create/{p}/cut/**` | applies approved cuts, pads, snapping, crossfades; renders the cut voice + plates; OTIO export |
| `f5_presenter_timeline` | CODE | `projects/{p}/timeline.json` (same schema as C5 output, `voice_source: presenter`) | words remapped to record time = the video clock; scene bounds on sentence/pause boundaries |
| `f6_reframe` | CODE | `projects/{p}/reframe.json`, `data/create/{p}/plates/**` | face track, crop paths per format (16:9, 9:16, pip), plates |

C5 must then accept either `voice.json` (TTS) or `edl.json` (presenter). New archetypes for C6/C8:
`presenter_full`, `presenter_punch`, `presenter_pip` (product animation full, presenter bubble), `presenter_split`,
`presenter_lower_third`; switching between them is a storyboard decision at sentence boundaries (J/L allowed).

### 7.1 EDL JSON (proposal)
```json
{
  "schema_version": "edl/1", "tool_version": "...", "stage": "f4_edl", "input_hash": "...", "created_at": "...",
  "fps": 30, "timebase": "frames",
  "sources": [{"id": "take01", "path": "data/create/p/footage/take01.master.mov", "frames": 9123,
               "audio": {"path": ".../take01.mic.wav", "offset_s": 0.412, "drift_ppm": 11.8}}],
  "segments": [
    {"id": "s001", "source": "take01",
     "video": {"src_in": 132, "src_out": 401},
     "audio": {"src_in": 128, "src_out": 401, "fade_in_ms": 12, "fade_out_ms": 12},
     "rec_in": 0, "words": ["w0004", "w0019"],
     "framing": {"zoom": 1.0, "reframe": "auto"},
     "cut_reason_before": null, "cut_reason_after": "c007:filler"}
  ],
  "removed": [{"cut_id": "c007", "kind": "filler", "source": "take01", "src_in": 401, "src_out": 418,
               "approved_by": "robert"}],
  "duration_frames": 2716
}
```
- Integer frames on the CFR master (no float drift); audio may differ from video only by declared J/L offsets.
- `rec_in` of segment n+1 = `rec_in + (video.src_out - video.src_in)` of segment n (checked by `lens validate`).
- Word remap: `t_rec = rec_in/fps + (t_src - src_in/fps)` for words inside a segment; words in removed spans dropped.

### 7.2 NLE hand-off
- **OpenTimelineIO** 0.18.1 (2025-11-09), Apache-2.0. Core adapters: `otio_json`, `otiod`, `otioz`.
  `OpenTimelineIO-Plugins` 0.18.1 adds `cmx_3600` (EDL), `fcp_xml` (FCP7 XML, the Premiere/Resolve XML), `AAF`, `ale`,
  … ; `fcpx_xml` is a separate contrib adapter (`otio-fcpx-xml-adapter` 1.0.0, 2023; supports multiple video tracks,
  audio tracks, gaps). https://opentimelineio.readthedocs.io/en/latest/tutorials/adapters.html (high)
- **DaVinci Resolve imports/exports `.otio` natively since 18.5** (Resolve 18.6 manual excerpt; AWS Picchu notes)
  (medium-high). Final Cut Pro: FCPXML. Premiere: FCP7 XML (OTIO support in Premiere not verified).
- Export `edl.otio` from `edl.json` (one track V1 + A1, clip `source_range` = src_in..src_out, media references to the
  conformed masters). Round-trip back into our EDL is a later milestone.

---

## 8. Filming guidance for Robert
- **Frame rate:** 30 fps locked (matches the render clock; 25 fps only if lit by 50 Hz light that flickers at 30 →
  test). Shutter 1/60 (180°) if the app allows. (heuristic)
- **Resolution: 4K landscape (3840x2160)**. 9:16 from it: crop 2160 × 2160·9/16 = **1215 x 2160**, scale to
  **1080 x 1920** (factor 0.889, a downscale, so full quality). From 1080p the 9:16 crop is 608 x 1080 → 1.78× upscale
  (soft). A 4K vertical shoot gives 16:9 = 2160 x 1215 → 1920 x 1080; equally valid, but landscape suits the 16:9
  master and product overlays. Keep his head inside the central ~60% of the width so the 1215-px window can follow him
  (window centre can range x ∈ [607, 3232]).
- **SDR, not HDR:** Settings > Camera > Record Video > HDR Video **off** (Apple). Lock exposure/focus (AE/AF lock), and
  white balance; or use **Blackmagic Camera** (free, iOS 16+, manual frame rate, shutter, ISO, WB, H.264/HEVC/ProRes,
  16:9 or vertical; reviews 2023, medium) to lock everything. Turn off auto low-light frame-rate drops (VFR source).
- **Codec:** HEVC 4K30 SDR is fine (we conform anyway); ProRes only if storage allows.
- **Mic:** lav or a small shotgun 30–60 cm off-axis, recording to the phone (one file, no sync) or a recorder at
  48 kHz/24-bit (sync by clap + cross-correlation). Peaks around −12 dBFS, never clipping. Record 10 s of room tone per
  setup (noise profile, gap fill).
- **Light:** key at 30–45° and above eye line, soft (window or softbox), fill or bounce on the other side, a little back
  light; avoid mixed colour temperatures; no flicker (check at 1/60).
- **Framing for overlays (16:9):** medium close-up, eyes on the upper third, body on one third (left or right), the
  other ~45% clean and uncluttered for product cards; keep the bottom ~150 px free for captions (repo rule: y > 930
  free at 1080p). Plain, non-busy background, 1–2 m behind him (cleaner matte later).
- **Takes:** one clap at the start; say a fixed cue ("again") before a retake and restart the whole sentence; pause
  ~1 s between sentences (gives clean cut points); read from a teleprompter/script so script alignment can pick takes.
- **Stability:** tripod, no stabilisation crop changes mid-take; do not zoom in-camera (we punch in in post).

---

## 9. Open questions for Robert (human gates)
1. Allow CrisperWhisper only if a commercial licence is bought? (Default: no.)
2. Allow ElevenLabs Voice Isolator / Scribe on presenter audio? (Default: no; rule says voice only.)
3. Primary language per video (RO or EN)?
4. Single-camera phone only, or phone + external recorder?
5. NLE of choice for fine-tuning (Resolve → `.otio`; FCP → FCPXML).

## 10. Sources (all checked 2026-10-09 unless noted)
- PyPI JSON API: faster-whisper, whisperx, stable-ts, whisper-timestamped, mlx-whisper, silero-vad, auto-editor,
  deepfilternet, mediapipe, opencv-python, opentimelineio, OpenTimelineIO-Plugins, otio-*-adapter, rembg, audalign,
  syncstart, pyloudnorm, pedalboard (GPLv3), noisereduce, ffmpeg-normalize, parakeet-mlx, nara_wpe, OneEuroFilter,
  praat-parselmouth (GPLv3) — https://pypi.org/pypi/<name>/json
- Raw LICENSE/README: github.com/{SYSTRAN/faster-whisper, m-bain/whisperX, jianfch/stable-ts,
  linto-ai/whisper-timestamped, nyrahealth/CrisperWhisper, ggml-org/whisper.cpp, ml-explore/mlx-examples,
  snakers4/silero-vad, WyattBlue/auto-editor, Rikorose/DeepFilterNet, xiph/rnnoise, GregorR/rnnoise-models,
  opencv/opencv_zoo, google-ai-edge/mediapipe, PeterL1n/RobustVideoMatting, ZhengPeng7/BiRefNet, danielgatis/rembg,
  xuebinqin/U-2-Net, AcademySoftwareFoundation/OpenTimelineIO, OpenTimelineIO/otio-fcpx-xml-adapter,
  heygen-com/hyperframes, OpenNMT/CTranslate2, argmaxinc/WhisperKit, senstella/parakeet-mlx}
- Hugging Face API: nyralabs/CrisperWhisper, nyralabs/CrisperWhisper2.0_large, openai/whisper-large-v3(-turbo),
  Systran/faster-whisper-large-v3, gigant/romanian-wav2vec2, facebook/wav2vec2-base-960h,
  jonatasgrosman/wav2vec2-large-xlsr-53-english, nvidia/parakeet-tdt-0.6b-v3, ZhengPeng7/BiRefNet
- FFmpeg filters: https://ffmpeg.org/ffmpeg-filters.html (silencedetect, loudnorm, arnndn, deesser, afftdn, tonemap,
  zscale, libplacebo); download page lists FFmpeg 9.0.2. Homebrew API (ffmpeg, ffmpeg-full, whisper.cpp,
  auto-editor).
- HyperFrames repo files: `skills/talking-head-recut/SKILL.md` + `NOTICE.md`, `skills/embedded-captions/**`,
  `skills/hyperframes-core/references/{data-attributes,variables-and-media}.md`,
  `skills/media-use/audio/references/{transcribe,remove-background}.md`, `docs/guides/hdr.mdx`, `docs/changelog.mdx`,
  `packages/engine/src/services/videoFrameExtractor.ts`.
- Remotion OffthreadVideo: https://www.remotion.dev/docs/offthreadvideo
- MediaPipe Face Detector: https://developers.google.com/edge/mediapipe/solutions/vision/face_detector (updated
  2026-10-01); AutoFlip legacy status: mediapipe `docs/solutions/autoflip.md`.
- Apple HDR video setting: https://support.apple.com/guide/iphone/iph2cafe2ebc/ios ; https://support.apple.com/102241
- Descript smooth jump cuts: https://help.descript.com/script-editing/smooth-jump-cuts ; Tella punch-in:
  https://www.tella.com/help/tips/punch-in-zoom-in-on-your-camera
- Resolve OTIO: https://github.com/AcademySoftwareFoundation/OpenTimelineIO/wiki/AWS-Picchu-Edit-OTIO-Conversion-Notes ;
  https://www.steakunderwater.com/VFXPedia/__man/Resolve18-6/DaVinciResolve18_Manual_files/part1410.htm
- faster-whisper issues #843, #812; whisper filler discussion https://huggingface.co/spaces/openai/whisper/discussions/30
- ElevenLabs: https://elevenlabs.io/docs/capabilities/voice-isolator ; https://elevenlabs.io/docs/api-reference/speech-to-text/convert
- 1€ filter: https://gery.casiez.net/1euro/ (not fetched; medium)

Not verified (say so if used): Premiere OTIO support; MediaPipe model-card licences; Apple Silicon speed numbers for any
ASR engine; Parakeet filler behaviour; torchaudio wav2vec2 weight licence; libplacebo on macOS via MoltenVK.
