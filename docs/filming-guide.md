# Filming yourself for the pipeline

Short version for Robert (detail in `docs/research/vertical-footage-brands.md` §3.4). One recording can make a 16:9
video and a 9:16 TikTok.

## Phone settings
- **Turn HDR Video off** (iPhone: Settings → Camera → Record Video → HDR Video). The pipeline can convert HDR, but SDR
  looks more predictable.
- **4K at 30 fps, locked.** Don't use auto frame rate. The free Blackmagic Camera app locks frame rate, exposure,
  focus and white balance.
- **Landscape gives both formats.**
  - The 9:16 crop of 4K landscape is 1215x2160, sharp enough for TikTok, with room for a small punch-in.
  - For a vertical-only video with big zooms, film vertical 4K instead.
- Lock exposure and focus on your face: on an iPhone, long-press it in the Camera app.

## Framing
- Keep your head in the middle 60% of the width so the vertical crop can follow you. Eyes about a third from the top.
- Leave space on one side if you want product cards next to you in 16:9.
- Plain background, light in front of you (a window works), not behind you.

## Sound
- A lav or a USB/phone mic close to you is best; the phone alone works too.
- Record 10 seconds of silence in the room at the start (room tone).
- Clap once at the start of each take.

## While talking
- Pause about a second between sentences. The pipeline cuts long pauses down for you.
- If you stumble, just say the line again. False starts are found automatically.
- If you want a line gone, say **"again"** (or **"din nou"**) and repeat it. The line before the cue is removed.
- Don't worry about "um". Fillers are proposed as cuts, and you approve them.

## Then
1. Upload the files into `data/create/<project>/footage/raw/`. Name order is take order, e.g. `01-intro.mov`.
2. `uv run create ingest <project>` → `transcribe` → `cuts` → (review) `cuts --approve all` → `edl` → `reframe` → `timing` →
   `edit` → `captions` → `burn --plate data/create/<project>/footage/edited/<project>-edited.mp4`.
