---
name: resolve-fix-take
description: Fix a raw presenter take's colour and level in DaVinci Resolve (DaVinci Resolve MCP) before anything else — flat or "log" looking footage, skin that looks orange or red, a voice that is too quiet. Detects DJI Mimo takes that are already Rec.709 (no log transform), grades node 1 with a measured CDL plus a skin LUT matched to Robert's photos, levels the voice to the destination loudness through a limiter, renders and checks the file. Use when Robert asks to fix colour or sound "in Resolve/DaVinci", or sends a DJI take that looks flat or quiet.
---

# resolve-fix-take

Learned on walmart-agents (2026-10-29). Code measures (`scripts/resolve_take.py`, `create/footage/resolve_fix.py`),
Resolve applies (the run-scripts in `resolve/`, pasted into the MCP `run_script` tool with their constants
edited). Everything else learned about Resolve (API quirks, overlays, the SFX mix, rendering, the
walmart-agents build): `docs/learnings/resolve.md`. Targets: `config/lens.yaml` `create.footage.resolve` and `targets.loudness.tiktok`. Images stay out of
the main session: numbers decide, the `lab-reviewer` agent looks (two 720 px stills at most per round).

## 1. Inspect the take (no Resolve yet)
`uv run python scripts/resolve_take.py inspect <take.mov>` prints the colour mode, the DJI/Apple tags, the
loudness and the constants block for `resolve/setup.py`.
- **`baked_rec709`** (DJI Mimo writes `filterBaked=1`, `filterID=AppleLog-Rec709`): the pixels are already Rec.709,
  only flat because his office is bright and white. NO log transform: a log → Rec.709 transform on top doubles
  contrast and saturation and turns his skin orange (what happened first on walmart-agents).
- **`apple_log`**: real log (Camera app / Blackmagic Camera). setup.py switches to colour management (DaVinci WG /
  Intermediate, Rec.709 Gamma 2.4 out). Resolve tags Apple Log on import; `apple_log_2` sets the input to
  "Apple Log 2". This branch is set up but not yet proven on a real log take: measure skin as below either way.
- **`unknown`**: look at the raw numbers (`check` on the take): blacks reaching 10-bit ~64 and natural skin
  (R/G ~1.4) mean Rec.709; treat as `baked_rec709`.

## 2. Build the project: `resolve/setup.py`
Paste its body into `run_script` with `P` (the project slug), `SOURCE`, `MODE`, `TARGET_LUFS` from step 1. It saves
the open project, opens or creates project `P`, imports the clip and builds three timelines:
- `<P>-source`: the clip's audio, Dialogue Leveler (optimise moderate levels, reduce loud, lift soft, no
  background reduction: his DJI mic track is clean) and clip gain to `TARGET_LUFS + PUSH_DB` by Resolve's analysis.
- `<P>-limiter`: `<P>-source` nested audio-only, a Fairlight Limiter on the clip, −2 dB after it.
- `<P>-out`: the raw clip's video (graded here) + `<P>-limiter` nested audio-only, `OUT_TRIM_DB`. Render this one.

## 3. Level: `resolve/render.py` with `AUDIO_ONLY = True` (3 s)
`check` the `-audiotest.mov` (`uv run python scripts/resolve_take.py check <file>` prints loudness). Target: the
destination's window (TikTok −15…−13, aim −14) with true peak ≤ −2 dBTP. Off by d LU: change `PUSH_DB` by ~1.5×d
and re-run setup.py (it is idempotent), or move `OUT_TRIM_DB` by d if the peak still has room.

## 4. Grade: `resolve/grade.py`
1. `RESET = True`, `LUT = ""`: pass-through stills to the scratchpad.
2. `uv run python scripts/resolve_take.py cdl <still.png>`: the SetCDL dict (blacks to 5 %, whites to 90 %,
   wall and shirt neutral with a hint of warmth, saturation 0.88).
3. `uv run python scripts/resolve_take.py lut <P>-skin`: the skin LUT into Resolve's `LUT/MCP/`.
4. `CDL = <that dict>`, `LUT = "MCP/<P>-skin.cube"`, `RESET = False`: graded stills; `check` them.
   Pass: `skin_ok` (Oklab hue 42 ± 3°, chroma 0.058 ± 0.01: his own photos), white R/G and B/G within ~0.02 of
   1.01/0.99, `luma_p1` ~0.05, `luma_p99` ~0.90, clipped < 0.5 %. If the face box misses his face (other
   framing), pass a better box in config `regions` for that run, not a guess at the numbers.
5. One `lab-reviewer` look at the two graded stills (720 px): natural skin, no LUT artefacts (blotches, face vs
   neck vs arms), logo and room unchanged. Then render.

## 5. Render and verify: `resolve/render.py` with `AUDIO_ONLY = False`
H.265 Main10 at the timeline size, 24-bit PCM, ~20-30 s for a minute of 4K. `check <file> --at 10,40` on the
**rendered file** (never trust Resolve's analyser or viewer alone), then send Robert the path with the numbers.

## Pitfalls (each one cost a render on walmart-agents)
- Never nest **video** under colour management: the nested timeline is converted a second time (skin went
  9°/0.6 chroma). Nest audio only; the picture is graded once on `<P>-out`.
- `AnalyzeAudioLevels` and the render disagree on where a clip's Limiter sits relative to clip volume: tune on
  audio-only test renders measured with ffmpeg, not on the analyser.
- A clip FX Limiter sees the signal before that clip's gain, so gain and limiter live on different timelines.
- The API cannot change a clip's Input Gamma once Resolve tagged it (here "Apple Log" from DJI's tag): that is why
  baked takes run without colour management instead of "Rec.709 input".
- `ExportVideo` stays off after an audio-only job: render.py sets it before the format.
- `ExportCurrentFrameAsStill` right after a grade change can return the old frame: park elsewhere, wait, export.
- A `.cube` written outside Resolve needs `RefreshLUTList()` before `SetLUT`.
- ffmpeg decodes an untagged matrix as BT.601: `load_frame` forces BT.709, or skin hue reads several degrees off.
- Whole-frame averages and HSV hue masks hide a red face: judge skin in Oklab inside the face box.
- `create take` re-levels the voice for the reel anyway (F6 `finish_voice`); this fix matters for the Resolve
  master itself and for Robert's own edits.

## Prevention (tell Robert when it fits)
Film with Log off and HDR off in DJI Mimo (Mimo bakes its own Rec.709 conversion, so Log gave no latitude), lock
exposure and white balance, and raise the DJI mic gain (walmart-agents recorded at −36.6 LUFS, +21.5 dB needed).
