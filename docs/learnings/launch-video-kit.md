# What we took from launch-video-kit (2026-10-17)

[timscheuerai/launch-video-kit](https://github.com/timscheuerai/launch-video-kit) (MIT, Tim Scheuer) turns a
website into a 30-60 s Apple-style launch film with HyperFrames, a word-timed GSAP timeline and a scripted
mix, the same stack as our motion route (ADR 0032). It was read once; nothing was copied (our wording, our code).
Its numbers come from one reference film and the owner's verdicts, not from a corpus, so we adopted only what
our own measurements agree with and listed the rest as claims to test.

## Adopted

| Idea | Where it lives now |
|---|---|
| Continuity at every cut: the outgoing element is still moving at the cut, the incoming one arrives in motion | rule in `create.motion.rules`; `create grade` warns when the frame rests `seam_rest_s` inside a handover window (`seam_findings`) |
| Mix at least 3 eases; one ease everywhere reads flat | rule; grade warns under `min_ease_families` (corpus: 5 easing classes) |
| No overshoot on the camera, cards or data | rule; grade warns on overshoot past the corpus share times `overshoot_factor`, or on a target larger than `overshoot_max_area` |
| Size range: one close-up (an element or typed text filling the frame) and one wide view; push into the part the voice names | rule (the builder's job; the reviewer sees it) |
| SFX pan follows the reveal on screen | `SfxCue.x` (share of frame width), `create.mix.sfx_pan_width`, `create/mix.py` `pan()` |
| Differentiation questions for the fresh-eyes review (logo swap, stock moves) and defects as "at t: what, why, fix" | `build-motion` skill step 5 |

## Not adopted, and why

- **Ban `back.out`, elastic and bounce everywhere.** Our corpus contradicts it: overshoot on ~14% of measured
  moves (`exports/motion-tokens.json`), and `patterns.json` recommends `back.out` for small accent pops. Kept
  as "overshoot only on small elements" instead.
- **Music drop-out about 0.1 s before the logo.** Our bed is composed to resolve on a ringing final chord under
  the close (`create.music.sections.last`); a drop-out would fight it. Robert's call if the close reads busy.
- **Forced alignment for word times.** ElevenLabs with-timestamps already gives us exact word times.
- **Higgsfield voice, music and SFX generation.** Pay-per-use; against our hard rules.
- **Key-locked synthesised SFX palette.** A good idea (one sound family, tonal cues in the bed's key), but it
  needs a synthesiser or a kit we do not have; revisit if our SFX read as stock.
- **Website to brand kit extractor** (Puppeteer: colours by role, fonts, logo, copy, an evidence file and a
  preview sheet, `reviewed: false` until a human checks). Useful for onboarding a new brand; adding brands is
  Robert's call. Candidate for a later milestone.
- **One shared body behind many hooks** (5 hook variants = 5 small JSON files). A real idea for hook A/B tests
  on TikTok and LinkedIn; needs its own ADR.

## Claims to test on our corpus (a lens milestone, not targets yet)

Each is stated in the kit as measured on premium launch films, with no data in the repo.

1. The densest stretch (most cuts, the biggest reveal) sits at 60-80% of the runtime.
2. The last visual change lands by about 80% of the runtime.
3. The positioning line plus the logo hold take 16-28% of the runtime.
4. Narration runs 2.2-2.7 words per second.
5. Designed SFX: 2-3.5 per second in action sections, at most 1 per second in statement sections, the logo
   with its sting alone.
6. Loudness range 1.5-6 LU (one reference: 1.6).
7. A key word whose visual lands 0.1-0.3 s after it reads as off beat (we measure reveal offsets to words).
8. The end card holds about 4 s in near silence.

What holds goes into config with its source; what does not is worth a line here.
