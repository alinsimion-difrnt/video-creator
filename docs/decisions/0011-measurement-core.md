# 0011 — Measurement core (S7): models, tracking, and what v1 can and cannot tell us

- **Status:** accepted
- **Date:** 2026-10-04
- **Milestone:** M4

## Context
BUILD_PLAN 7.5 asks for tracking, progress curves, linear / cubic-bezier / spring fits with AIC model
selection, the nearest GSAP ease, a Remotion spring config, text stagger and SFX offset. Acme v1's
HyperFrames source gave an exact answer key (tests/fixtures/acme-v1/): 492 timed GSAP tweens.

## Decisions
- **Curves from first principles, golden-tested.** GSAP eases and the damped spring are implemented from
  their math; `scripts/golden_curves.mjs` samples GSAP 3.14.2 and Remotion 4.0.532 and the tests require
  agreement to 1e-6 (actual 5e-9). Two facts surfaced (external-facts 12): GSAP's expo has a correction
  term; Remotion draws overdamped springs as critically damped, so exported configs carry
  `remotion_exact`.
- **Free start and duration in every fit.** "Within 2% of final" ends an expo.out at about 56% of its real
  duration, so durations come from the fit, not from the end detection.
- **Tracking:** NCC template matching backwards from the settled frame, with a ring of surroundings
  (flat elements need edges), per-frame scale steps plus refinement (scale-pops), padded frames (elements
  partly outside the frame) and held positions for frames below the confidence floor.
- **Opacity proxy:** least-squares alpha between the background and the end appearance, on lightly
  blurred crops (sub-pixel misalignment otherwise reads as transparency). Faint frames count only when the
  element was still fading when first placed; a slide-in arrives opaque.
- **Unseen starts:** an element that fades in while it moves cannot be placed at first. Its position
  channel is fitted on the visible frames with a free amplitude (`observed_start: false`) instead of
  assuming the motion began where it became visible.
- **Joint timing:** one GSAP tween usually moves and fades an element together. `timing` is a joint fit
  (one ease, start and duration; per-channel amplitude; opacity clamped at 1). It is the primary output;
  per-channel bezier and spring fits stay alongside it.
- **Class:** AIC between bezier and spring with a margin (`ambiguous` inside it); a named GSAP ease that
  fits within `measure.gsap_class_ratio` of the free bezier decides in/out/inOut.

## Results
Synthetic fixtures (24/25/30/60 fps): eases, durations and starts within 1 frame for slides, fades,
scale-pops and v1-style fade-and-rise; spring (zeta, omega0) within 5% (exact on clean input); per-word
stagger exact.

Acme v1, 80 sampled real tweens on their true end boxes (docs/evals/acme-v1-m4.md): 62 measured;
median |start error| 19 ms (< 1 frame); median |duration error| 58 ms (~2 frames); direction right 51/62,
family 33/62, exact ease name 12/62; the fitted curve redraws the true motion within 1 px (or 5 pp of
opacity) for 26/62, 12/23 of tweens with nothing else animating nearby.

## Consequences and limits
- On short, small UI moves (v1: 17-37 px in 0.3-0.5 s, ~10 frames) neighbouring eases (expo.out vs
  power4.out, power2 vs power3) draw nearly the same frames; the exact name is not identifiable and should
  not be claimed. Phase 2 should consume the fitted curve and duration, not trust the name alone.
- Entrances from off-screen show only their tail; timing is good to ~3 frames, the ease less so.
- Overlapping animations on the same pixels (parents moving, siblings staggering through) are the main
  remaining failure source; A2's box choice and S3 grouping are the levers, not the fit.
- SFX on v1: 6/14 clips detected (quiet clicks and pops at volume 0.35 are lost in stem separation);
  offsets are measured for the ones found.
