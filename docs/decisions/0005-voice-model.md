# 0005 — ElevenLabs voice model: eleven_v3

- **Status:** superseded by ADR 0018 (model `eleven_v4`, 2026-10-06); spike results below
- **Date:** 2026-10-03
- **Milestone:** Phase 2 (G5)

## Context
The v1 brief asked for a playful, sassy, chill US female voice with pauses, breaths and giggles
controlled from the script text (handoff §1, §5.1). Facts (external-facts §10):
- `eleven_v3`: audio tags such as `[laughs]`, `[sighs]`, `[whispers]`; 5k characters per request;
  pronunciation-dictionary support not documented.
- `eleven_v4`: newer, 10k characters; tags `[short pause]`, `[long pause]`, `[laughs]`, `[chuckles]`;
  **no** pronunciation dictionaries or phoneme tags.
- Neither supports SSML `<break>`. The with-timestamps endpoint lists no model restriction, but the
  docs don't confirm it works with v3 or v4.

## Decision
Use `eleven_v3`, the more established expressive model, as the default. It covers the tags the brief
asked for, and the 5k limit is not a constraint because v1 generated one request per line (the whole
v1 script was ~2.5k characters). The model id lives in config so v4 can be swapped in by changing it.
Brand names use a respelling (`Ack-me` worked in v1), unless the spike shows dictionaries work on v3.

**G5 spike (about 10 credits' worth, before any Phase 2 build):**
1. with-timestamps on `eleven_v3` returns alignment (character → word aggregation works);
2. tags `[laughs]`, `[sighs]` and pauses via punctuation/ellipses render, and the tag text is not spoken or captioned;
3. `Acme` pronunciation, checked by round-trip transcription (dictionary first, respelling fallback);
4. take-to-take variance: generate 3 takes of one line and pick by `lens` prosody metrics.

## Consequences
If step 1 fails on v3, fall back to whisper word timings on the generated audio (v1's route, with
its brand-word normalisation), or move to v4 if v4 passes. v3 is less deterministic than older
models, so plan for multiple takes per line and selection by measured prosody.

## Spike results (2026-10-05/06, external-facts §10 f)
1. with-timestamps returns alignment on `eleven_v3`, `eleven_multilingual_v2` and `eleven_v4`; character →
   word aggregation works (audio tags are skipped).
2. On v4, tags render and are not spoken (whisper round trip on 4 tagged reads). Not tag-tested on v3.
3. `Ack-me` respelling is heard as "Acme" (one "Ackma" in a playful take). Dictionaries were not
   tested; v4 does not support them.
4. Takes vary (same voice and script: 1:30 vs 1:23); select per scene by measured prosody.
v4 was chosen by ear and by measures (ADR 0018).
