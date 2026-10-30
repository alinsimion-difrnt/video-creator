<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/film/sfx/FACTS.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# Verified external facts (ElevenLabs), 2026-10-08

## Sound generation: https://elevenlabs.io/docs/api-reference/text-to-sound-effects/convert (read 2026-10-08)
- `POST https://api.elevenlabs.io/v1/sound-generation`. Headers: `xi-api-key`, `Content-Type: application/json`.
- Query `output_format` (codec_samplerate_bitrate): mp3_22050_32 … mp3_44100_192 (192 kbps needs Creator+),
  pcm_8000 … pcm_48000 (44.1 kHz PCM needs Pro+), ulaw_8000, alaw_8000, opus_48000_32 … 192. Used: `mp3_44100_128`.
- Body: `text` (string, required); `loop` (bool, default false, only for eleven_text_to_sound_v2);
  `duration_seconds` (double|null, 0.5–30, null = inferred from prompt); `prompt_influence` (double|null, 0–1,
  default 0.3); `model_id` (default and only value `eleven_text_to_sound_v2`).
- Response 200: audio file (MP3 for our format); 422: validation error (`detail[]` with loc/msg/type).

## Capability page: https://elevenlabs.io/docs/overview/capabilities/sound-effects (read 2026-10-08)
- Cost: "40 credits per second when duration is specified".
- States duration 0.1–30 s (the API reference says 0.5–30; we stayed ≥ 0.5).
- Prompt tips: concise descriptions; audio terms (impact, whoosh, …); higher prompt_influence = more literal.
- MP3 output for all effects; WAV 48 kHz for non-looping effects.

## Subscription: https://elevenlabs.io/docs/api-reference/user/subscription/get (read 2026-10-08)
- `GET https://api.elevenlabs.io/v1/user/subscription` returns `character_count`, `character_limit`,
  `next_character_count_reset_unix`, `character_refresh_period`.
- Observed: our key gets HTTP 401 `missing_permissions` ("missing the permission user_read"), so the remaining
  balance could not be read with this key.

## Observed in our calls
- Every sound-generation response carried a `character-cost` header (5–20 for 0.5–2.0 s; total 169 for 18 calls,
  16.9 s). That is ~10 per second, not the 40/s the capability page states; which one the bill uses is unverified.
