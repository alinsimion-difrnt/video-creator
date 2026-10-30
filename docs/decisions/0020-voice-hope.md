# 0020 — Phase 2 voice: Hope (corporate) on ElevenLabs v4, serious delivery

- **Status:** accepted (Robert, 2026-10-06); supersedes ADR 0018's voice
- **Date:** 2026-10-06
- **Milestone:** P1

## Context
The first Acme v2 narration (Zara, warm tags) measured well (6/7 voice-spec measures in band) but Robert
heard it as "too slow and bored" and the burger chuckle as weak. He asked for "a cool 30 year old female
salesman, with interest in tech and marketing": more serious, faster, to sit under animation and music.

## Audition (same two scenes, no tags, `eleven_v4`, lens prosody)
| Voice | Articulation (wpm) | Pitch std (st) |
|---|---|---|
| Harper – Confident, Clear and Cool | 218 | 3.72 |
| **Hope – corporate training** (`WZlYpi1yf6zJhNWXih74`) | 212 | **3.86** |
| Nichalia – Bright and Friendly | 215 | 3.46 |
| Hope – Clear, Relatable and Charismatic | 213 | 3.56 |
| Kristen – Natural, Upbeat and Focused | 182 | 3.42 |
| Zara, without tags | 198 | 2.76 |

Zara without tags is flat and slower; the confident voices stay expressive with no tags.

## Decision
- **Voice:** Hope (corporate), `eleven_v4`, default settings.
- **Delivery:** serious. No playful tags (`[chuckles]`, `[sighs]`, `[thoughtful]` removed); `[curious]` kept on the
  ChatGPT question; most `...` replaced by full stops.
- **Timing:** scene tail 0.7 s → 0.5 s for a faster cut.

## Result
Acme v2 narration 105.1 s, 298 credits; whole read 6/7 in band (articulation 210.8 wpm, pitch 3.98 st,
pause mean 611 ms; energy variation 7.77 dB, just high, for the mix). A music bed built to this timeline
(9 chunks, 124 BPM) mixes to -15.4 LUFS.

## Consequences
- Short lines run fast (s08 247, s09 265 wpm articulation); watch them in review.
