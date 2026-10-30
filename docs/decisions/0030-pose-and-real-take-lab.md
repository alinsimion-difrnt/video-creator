# 0030 — The presenter's pose, a carp Fred, and lab tests on Robert's own take

- **Status:** accepted (Robert, 2026-10-12, on take 1 of the Fred & Pixie video)
- **Date:** 2026-10-12
- **Milestone:** Phase 2, presenter reels (follows ADR 0029)

## Context
Robert filmed take 1 (docs/briefs/fred-and-pixie-take1-prompt.md). Reviewing the first redesign and the
motion test, he said:
- "I don't want Fred to have a metallic arm and leg, I want me to have it." In Fullmetal Alchemist it is the
  **right arm and the left leg** (Edward Elric's automail), and the transmutation circle belongs **under his
  feet**, not over them.
- "I would like to have my own voice for the tests, cause you are using my video." Generated voices are for the
  black-hole explainer only.
- When he puts Fred on the floor, Fred "should follow my hands".
- Fred is to be based on the family's real fish, a common carp. The redesign is "decent".

None of this can be placed from the face alone: it needs his arms, legs and hands, frame by frame.

## Decision
- **Pose (create/footage/pose.py).**
  - The model is MediaPipe BlazePose (full-body landmarks) as ONNX from the OpenCV zoo
    (`pose_estimation_mediapipe_2023mar`, Apache-2.0, external-facts §19). It runs locally with `cv2.dnn`,
    with no API. It is pinned by sha256 in `create.footage.pose`, like YuNet.
  - It gives 33 body points per sample (15 fps), in master pixels, with a visibility for each.
  - The first crop comes from the face (a seated body below it). Every later crop comes from the last
    pose's own box, as tracking.
  - Points are smoothed with a short moving average. Gaps (a lost frame, a hidden hand) hold the last pose.
  - Tracks are cached by master, span and settings (data/create/_cache/pose/).
  - Checked on a 4K still of take 1: shoulders, elbows, wrists, hips, knees and ankles sit on his body.
- **`follow: hand` (a prop beat).**
  - From its word, the prop rides the presenter's hand: keyed moves at the pose's rate.
  - It settles into the palm over the first 30 % of the carry, so it does not jump.
  - It is released at the hand's lowest point, the put-down, and stays there.
  - The hand is the one that reaches lowest in the span. In v22, the nearest hand at the start went to his
    knee while the other hand set Fred on the floor.
  - If the release point is under the platform's UI, the prop hops into the safe area. A new
    `props.safe_right` (888, TikTok's action rail) joins `safe_bottom` for every named spot.
- **`automail` (an effect).**
  - The presenter's limbs (default `right_arm` and `left_leg`, as Edward's) turn to gunmetal plates keyed
    to the pose's joints.
  - The steel spreads from the shoulder or hip down, with a flash. The drawing is original, studied from a
    reference sheet Robert shared (not saved, not copied).
  - Plate width comes from the lower segment, because a seated thigh is foreshortened.
  - Pair it with `alchemy` under the chair.
- **The alchemy circle goes under his feet.** With a matte, the circle is drawn behind the presenter's
  cut-out, and `matte_spans` now includes alchemy spans. Without a matte it is drawn over him, as before.
- **`create lab` on a real take.** A spec with `take: {project, from, to, x}` cuts that span of the
  master. It crops it vertically around `x` and keeps his own sound. The words are Scribe's transcript of
  the span. No voice is generated.
- **Cut notes (`projects/<p>/cut-notes.yaml`, an optional F3 input).** Robert's own instructions, applied
  over the proposals:
  - the start and the end;
  - spans that must stay whole (the 15.6 s black-hole silence, the chase);
  - extra cuts (a false start the proposer missed).
- **Fred is a carp in all three styles.**
  - The colours: an olive back to a golden belly, scales behind the gill line, a long amber dorsal fin,
    orange fins and a forked orange tail, peach lips and barbels, a gold-ringed eye.
  - The 3D materials take a per-point texture, pinned to the body so the scales never slide.
  - The pixel renderer gains a scallop `net` pattern.
  - The rig waves with the far fin (a raised near fin covered his face).

## Consequences
- Anything that must touch the presenter's body (a hand-off, a held prop, a costume) can be keyed to the
  pose instead of guessed from the face.
- Tests use Robert's own footage and voice once a take exists. The stock photo and TTS lab stays for gags
  before filming.
- **Cost:** the pose model takes about 0.1 s a frame on the cloud CPU (15 fps sampling: about 1.5 s per
  second of video). Tracks are cached.
- **Limits:**
  - The pose is one person, front-facing and seated or standing. Fast dives blur it, and gaps hold the last
    pose.
  - The automail overlay is drawn over him, not cut into his silhouette (Robert: "a rough overlay is fine").
  - The circle under his feet needs `create matte` for its span.
- Robert still applies the CLAUDE.md lines below.

## CLAUDE.md lines (Robert applies; an agent may not edit CLAUDE.md)
In "Commands", change the lab line to:
```
uv run create lab docs/lab/<v>.yaml --photo <photo> [--draft] [--preview s,s] [--matte] [--force] (ADR 0029; a `take:` spec tests on Robert's own footage, ADR 0030) |
```
