# DaVinci Resolve, driven by Claude (learned on walmart-agents, 2026-10-29)

Everything learned fixing and then building one presenter TikTok entirely inside DaVinci Resolve Studio 21.1.2 on
Robert's Mac, through the DaVinci Resolve MCP. The colour and level fix is a tested skill
(`.claude/skills/resolve-fix-take/`); this page holds the rest: API behaviour, the edit/overlay/SFX build, the
mix and the render. Verified facts are also in `docs/external-facts.md` §25.

Robert's verdict on the result: "Looks good". On the colour: the first grade made him "orange" (section 2).

## 1. The MCP and the scripting sandbox
- Tools: `get_resolve_status`, `launch_resolve`, `run_script` (sandboxed Python 3.14), `run_script_unsafe`,
  `search_scripting_api`, `get_scripting_api [as_file]`, `get_scripting_docs`, `get_whats_new`, `generate_lut`,
  `update_dctl`, `list_luts`/`list_dctls`. `resolve` and `project` are injected; set `result` to return data.
- `run_script` blocks `os`, `sys`, `pathlib` and file access (`import os` raises); `time` works. Constants (paths,
  segment lists, CDLs) are pasted into the script; it cannot read the repo. Timeout max 60 s: render-and-wait
  loops stop at ~55 s and re-run to keep waiting.
- `get_scripting_api(as_file=True)` writes the 152 KiB stub to a temp file: grep it instead of loading it.
  Enumerated values (colour spaces, gammas) are not documented: set, then read back to learn the valid strings.
- `generate_lut(path, size, transform)` runs a Python body per lattice point (no `globals()`; precompute matrices
  as constants) and writes into `/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT/MCP/`
  (writable by us too: `scripts/resolve_take.py lut` writes there directly). A `.cube` written outside the tool
  needs `project.RefreshLUTList()` before `Graph.SetLUT(1, "MCP/<name>.cube")`.
- Switching projects (`LoadProject`/`CreateProject`) can drop unsaved work in the open one: `pm.SaveProject()`
  first. `pm.DeleteProject(name)` works once another project is loaded.

## 2. Colour
- **DJI Mimo "Log" takes are already Rec.709** (`filterBaked=1`, `filterID=AppleLog-Rec709`, blacks at 10-bit
  44-73, natural skin R/G ~1.4); they only look flat because the office is white. Resolve still tags them
  "Apple Log", and the API then refuses every `Input Gamma` value (`SetClipProperty` returns False; project input
  settings do not override it). A log transform on top doubled contrast and saturation: skin Oklab chroma 0.07 ->
  0.17, "Mate, I am orange!". Fix: no colour management at all (`colorScienceMode: davinciYRGB`, Rec.709 Gamma
  2.4 timeline and output) so pixels pass through untouched, then a CDL. `scripts/resolve_take.py inspect` decides.
- Resolve 21.1.2 does have an "Apple Log 2" input colour space (gamma reads "Apple Log"; Apple Wide Gamut). Under
  RCM: `colorScienceMode: davinciYRGBColorManagedv2`, `separateColorSpaceAndGamma: "1"`, timeline `"DaVinci WG"`
  (not "DaVinci Wide Gamut") + `"DaVinci Intermediate"`, output `"Rec.709"` + `"Gamma 2.4"`.
- The API has no node or CST insertion: node 1's `SetCDL` and `Graph.SetLUT` are the grading tools. Under
  colour-space-aware tools in a log timeline, white balance belongs in per-channel **Offset** (~0.073 per stop in
  DaVinci Intermediate); per-channel slope there rotates skin (it moved skin 28° -> 19°, redder).
- Skin-selective correction without nodes: a 3D LUT that converts to Oklab and moves only a hue window
  (`create/footage/resolve_fix.py: skin_transform`), with ramps that leave neutrals, the saturated red logo and
  deep shadows alone. Target from Robert's own photos: Oklab hue 42°, chroma 0.058 (camera gives ~36°, 0.07).
- **Measure, never trust averages or HSV masks.** A whole-frame chroma mean hid a red face; an HSV "skin" mask
  picked up the wall and wood. Judge skin in Oklab inside the face box, whites on near-white regions, clipping as a
  share of pixels at 0.995. ffmpeg decodes untagged video with the BT.601 matrix: force BT.709 or hue reads off.
- `project.ExportCurrentFrameAsStill(path)` right after a grade or property change can return the cached, old
  frame (a Log 1 vs Log 2 comparison came back byte-identical): park the playhead elsewhere, wait ~2 s, export.
- **Never nest video under colour management**: a nested timeline used as a clip is colour-converted again (skin
  went 9°/0.6 chroma). In a non-managed (YRGB) project nesting is safe: the picture passes through 1:1.

## 3. Audio
- Resolve's per-clip **Dialogue Leveler** is scriptable through `SetProperty`: `AudioDialogueLevelerEnabled`,
  `...Mode` (`resolve.DIALOGUE_LEVELER_MODE_OPTIMIZE_MODERATE_LEVELS`), `...ReduceLoudDialogue`,
  `...LiftSoftDialogue`, `...BackgroundReduction` (off for his clean DJI mic), `...OutputGain` (0-6). Clip gain:
  `AudioVolumeEnabled` + `AudioVolume` (-100..+30 dB).
- `TimelineItem.AddEffect("audio", "Audio FX/Fairlight FX/Limiter")` adds a Limiter, but its parameters cannot be
  set (ceiling ~0 dBFS, true peak ~-0.2 dBTP). `GetEffectsList("audio")` lists Fairlight FX and AU effects.
  Track FX, bus FX and the master bus are not scriptable; `GetFairlightPresets()` is empty unless Robert saves one.
- **Order differs between analysis and render.** `AnalyzeAudioLevels("ITU-R BS.1770-4")` treats a clip's FX as
  before its clip volume; in the render the Limiter acts after the clip volume. So the analyser cannot predict a
  limited mix: tune on 3 s audio-only test renders measured with ffmpeg `ebur128=peak=true`.
- Working chains (each level is a timeline nested **audio-only**, `mediaType: 2`):
  - Fix of the raw take: `<p>-source` (Leveler + gain to target + 4 dB "push") -> `<p>-limiter` (Limiter, -2 dB)
    -> `<p>-out` (linear trim 0): -14.0 LUFS, -2.2 dBTP. Codified in `resolve-fix-take/resolve/setup.py`.
  - Final mix with SFX: voice + SFX into `-final` (Limiter, 0 dB; edit tracks pushed +2.5 dB) -> `-master`
    (linear trim -2.3 dB): -14.0 LUFS, -2.5 dBTP before AAC, -2.4 after. Without the limiter SFX stacked on voice
    peaks reached +0.5 dBTP; a trim on the limiter's own clip did not lower the peak.
- Hard audio cuts at the edit points were clean because every cut falls in a pause (no crossfades via the API).
- ElevenLabs SFX (`create/footage/sfx.py: el_sound`, cached by prompt) come back at very different levels
  (-48 to -13 LUFS): set each clip's gain to min(-24 - LUFS, -10 - peak), capped at +15 dB.

## 4. Editing, framing and overlays
- `mp.AppendToTimeline([{mediaPoolItem, startFrame, endFrame, mediaType (1 video, 2 audio), trackIndex,
  recordFrame}])` builds the edit from `projects/<p>/edl.json` (`src_in`, `src_out`, `rec_in`): `endFrame` is
  **exclusive** (using n-1 lost the last frame). `recordFrame` = `timeline.GetStartFrame()` + rec frame.
- Audio-only media pool items have no `Frames` property: derive frames from `Duration` (hh:mm:ss:ff).
- Per-timeline resolution: `tl.SetSetting("useCustomSettings", "1")` first, then width/height (1080x1920 for the
  TikTok while the project stays 2160x3840; the 4K source gives zooms headroom).
- Grade per item: `SetCDL` and `GetNodeGraph().SetLUT(1, ...)` on every video segment (20 calls, all fine).
- Transform properties: `ZoomX/ZoomY`, `Pan`, `Tilt` (**positive Tilt moves the image up**), in timeline pixels
  for a clip that fills the frame. Presenter under the split seam: Tilt = 960 + (head_top - 960) * zoom - 1140,
  Pan = (540 - face_cx) * zoom clamped to (1080 * zoom - 1080) / 2, head_top = face_y - 0.35 * face_h from
  `framing.json`; punch-ins alternate zoom 1.0 / 1.12 (framing's own values). Verified on stills: forehead at
  y ~1250, no black below the seam.
- **A smaller overlay clip uses different Tilt units**: the 1080x980 panel needed Tilt 920-922 to move ~470 px
  (about half-pixel units, likely scaled against the 2160x3840 project). Measure the black band on an exported
  still and iterate; 1 px offsets show as a soft top row.
- The panel as an overlay: the build-panel page rendered by `render_panel` (playwright frames -> mp4), made
  1080 x 980 with its own caption strip (840-980) because the base render that normally carries captions is not
  used; `create qa` then reports `captions_present: 0 groups` (a false fail: captions are burned into the panel).
- Re-runnable scripts: delete what a previous run made (`tl.DeleteClips(items)`, `mp.DeleteTimelines([tl])`)
  before appending again. `mp.AddSubFolder(root, name)` keeps panel and SFX media in their own bins.
- A cover as frame 0: prepend 1 frame of the chosen moment (`startFrame: n, endFrame: n + 1`) at the timeline
  start and shift every other item by one frame; picture and sound stay in sync.

## 5. Rendering
- `SetRenderSettings({"ExportVideo": ..., "ExportAudio": ...})` **persists** across jobs: after an audio-only test
  the next "full" render came out audio-only. Set both explicitly first, then the format and the rest.
- `SetCurrentRenderFormatAndCodec("mov", "H265")` + `"EncodingProfile": "Main10"`, `"AudioCodec": "lpcm"`,
  `"AudioBitDepth": 24`: masters. TikTok/feeds: `("mp4", "H264")`, `"AudioCodec": "aac"`,
  `"NetworkOptimization": True` (moov first; `create qa` faststart fails without it).
- `GetCurrentRenderFormatAndCodec()` can report a stale value right after setting: read the job back from
  `GetRenderJobList()` (`IsExportVideo`, `VideoCodec`, `TimelineName`) before trusting it.
- Speed on this Mac: 62 s at 4K H.265 ~32 s; 54 s 1080x1920 H.264 ~17 s; a 3 s audio-only test ~3 s. Much faster
  than the ffmpeg/HyperFrames composite of the standard route (~4 min per minute).
- Animated GIF (`("gif", "Animated_GIF")`) has no palette or frame-rate control (`FrameRate` is refused): a 10 s
  card was 40 MB at 720 px, 20 MB at 480 px. For LinkedIn/X send the silent MP4 loop instead (4.6 MB).

## 6. The walmart-agents build (reference)
Project `walmart-agents` in Resolve; files in `projects/walmart-agents/` (EDL, framing, captions, panel page and
beat sheet, square card page, post text).
- `walmart-agents-source` / `-limiter` / `-out`: the raw-take fix (skill resolve-fix-take).
- `walmart-agents-edit` (1080x1920): V1 the 20 cut segments (grade + zoom), V2 the panel video (1080x980, top),
  A1 the cut `-limiter` audio (+2.5 dB push), A2 33 ElevenLabs SFX cues on the panel's word times.
- `walmart-agents-final` (edit nested, Limiter) -> `walmart-agents-master` (edit nested again, -2.3 dB trim,
  1-frame cover at 3.9 s first): render this one.
- `walmart-agents-card` (1080x1080): the 10 s silent card for LinkedIn and X, cover frame (8.6 s) first.

## 7. Seen on the way (not Resolve, fix in a fresh session)
- `create prep` crashes in `run_edit` (JSONDecodeError "Extra data" parsing ffmpeg/loudnorm output) on this take;
  the stages before it (EDL, reframe, timing) and `run_captions` run fine on their own.
- `create review` fails on this Mac: its contact sheet uses ffmpeg `drawtext` with font "DejaVu Sans".
- ffmpeg here needs `trim=start_frame=n:end_frame=n+1` to grab an exact frame (`select` + `-vsync 0` returned
  nothing).

## 8. When to use Resolve (Robert asked, 2026-10-29)
- Colour and level fix of a raw take: Resolve (the skill), unless he films with Log off.
- Assembly: the standard route is cheaper per video and runs anywhere (cloud, teammates); Resolve renders faster
  and lets Robert hand-edit cuts, zooms, SFX and levels. Most of the walmart-agents cost was one very long session
  learning the quirks above. Next step if Resolve stays: one "assemble in Resolve" script that prints the
  run_script constants (EDL, framing, panel, SFX cues and gains) from the project files, so the build is one call.
