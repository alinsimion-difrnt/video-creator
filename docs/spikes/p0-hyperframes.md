# P0 spike: HyperFrames render + lens round trip (2026-10-05)

**Question:** can this container render HyperFrames compositions, and does `lens` measure what was
authored? This is the reconstruction loop of BUILD_PLAN 12b.

**Setup:**
- `hyperframes@0.8.134` (npm, Apache-2.0), installed in a scratch folder.
- Rendered with Playwright's Chromium headless shell. Run `HYPERFRAMES_BROWSER_PATH=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell`, so nothing extra is downloaded.
- Telemetry, update checks and feedback prompts are off: `HYPERFRAMES_NO_TELEMETRY=1 HYPERFRAMES_NO_UPDATE_CHECK=1 HYPERFRAMES_NO_FEEDBACK=1`.

**Scene:** `p0-hyperframes-roundtrip.html`, 1920×1080, 30 fps, 4 s. It holds two tweens:
- a title: `fromTo(y 80→0, opacity 0→1)`, `power3.out`, starting at 1.0 s, lasting 0.6 s;
- a card: `fromTo(x −900→0)`, `back.out(1.4)`, starting at 2.0 s, lasting 0.5 s.

**Result:**
- `npx hyperframes lint`: 0 errors.
- `npx hyperframes render --fps 30`: 120 frames in 10.5 s, using software GPU and beginframe capture.
- `lens.measure.measure_element` on the decoded proxy (1280×720) gives back:

| Element | Authored | Measured (joint fit) |
|---|---|---|
| title | power3.out, 1.0 s, 0.6 s | power3.out, 1.001 s, 0.598 s (channels y, opacity) |
| card | back.out(1.4), 2.0 s, 0.5 s | back.out(1.4), 2.000 s, 0.499 s (channel x) |

**Conclusion:**
- Rendering works in the container and needs no Actions minutes.
- The measure → build → re-measure loop is exact on our own renders.
- `lens compare --fast` per scene can build on `measure_element` with the authored boxes. P4 adds it.

**Still to do in P0:** the ElevenLabs spike (ADR 0005), which needs `ELEVENLABS_API_KEY` in the
environment.
