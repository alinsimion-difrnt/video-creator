# 0018 — Phase 2 voice: Zara (warm) on ElevenLabs v4

- **Status:** superseded by ADR 0020 (Hope, corporate; 2026-10-06). Was: Robert's choice by ear, covers the voice part of G5
- **Date:** 2026-10-06
- **Milestone:** Phase 2 prep

## Context
BUILD_PLAN 12b and G5 need an ElevenLabs voice for Phase 2. The account was moved to the Starter plan
(the free plan refuses Voice Library voices over the API). Auditions used a Acme-style script built
from the Acme v1 on-screen copy (226-246 words), were generated with REST `with-timestamps`, and were
measured with lens' own speech code (local whisper words, `tighten`, `prosody`) against
`exports/voice-spec.json`. Audio was kept out of the repo.

## Decision
- **Voice:** Zara – The Warm, Real-World Conversationalist, `jqcCZkN6Knx8BJ5TBdYR` (Voice Library,
  added to My Voices).
- **Model:** `eleven_v4`, default voice settings (no `speed`, `stability` or `style` override).
- **Delivery ("warm"):** a light touch of audio tags, about one every two or three sentences:
  `[curious]`, `[thoughtful]`, `[chuckles]`, one `[sighs]`, and a few `...` for weight. The brand is
  written `Ack-me` in spoken lines (heard back as "Acme").
- **Not chosen:** the "playful" level (pace between phrases above the corpus range) and the "energetic"
  level with `speed` 1.06/1.10 (too energetic by ear; `speed` had almost no effect on v4).

## Evidence (one read each, whisper-measured)
| Read | Words/min | Articulation | Pause mean | Pause p90 | Pitch std | Energy std | Phrase CV | In range |
|---|---|---|---|---|---|---|---|---|
| Zara warm, v4 | 158.2 | 209.3 | 493 ms ↓ | 690 ms ↓ | 3.62 | 7.40 | 0.225 | 5 / 7 |
| Zara, multilingual v2, no tags | 181.1 ↑ | 250.6 ↑ | 533 ms ↓ | 782 ms ↓ | 2.61 ↓ | 7.11 | 0.218 | 2 / 7 |

Tags lifted Zara's pitch variation into the premium band and slowed her to the corpus pace. No tag was
spoken as a word (whisper round trip).

## Consequences
- Pauses run short (about 0.5 s vs the corpus' 0.7 s). The voice stage should synthesise per scene and
  place silence in the edit rather than rely on `...` or `[short pause]`.
- Takes vary; generate 2-3 per line and keep the best measured one.
