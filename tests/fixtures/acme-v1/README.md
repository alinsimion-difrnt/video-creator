# Acme v1 answer key

`answer-key.json` is ground truth for the Acme explainer v1 render (our own video), extracted from its
HyperFrames source with `scripts/hyperframes_answer_key.py` (no media; the source files are not
committed). It lists:

- `scenes` and `transitions` (scene overlaps: 12 x 0.5 s, 2 x 0.4 s), `voice`, `music`, `sfx` (14 clips,
  each starting on a scene start, volume 0.35);
- `tweens`: every GSAP tween (642, of which 492 have a duration) with absolute start, duration, ease,
  tweened properties and the target's box at the tween's end, in 1920x1080 composition pixels. Boxes
  were measured with fallback fonts (the project's fonts are not included), so text boxes are approximate.

Regenerate from the project folder:

    uv run --with playwright python scripts/hyperframes_answer_key.py PROJECT_DIR tests/fixtures/acme-v1/answer-key.json

Score lens against it (needs the video's S2/S3 outputs): `scripts/eval_answer_key.py`;
the M4 run is in `docs/evals/acme-v1-m4.md`.
