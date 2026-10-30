# 0022 — Shared brands, ElevenLabs speech-to-text, Robert's own footage

- **Status:** accepted (Robert, 2026-10-09)
- **Date:** 2026-10-09
- **Milestone:** Phase 2, M-A/M-B of `docs/research/vertical-footage-brands.md` §5

## Context
- Robert wants videos for more than one brand: Acme and his personal brand acme.example, and later others.
  Until now the brand hand-off lived inside one project (`projects/<project>/brand/`), so a second video for the
  same brand would have needed a copy.
- He also wants to film himself and have the pipeline cut, caption and animate over the footage, for 16:9 and
  TikTok-style vertical.
- The research (`docs/research/vertical-footage-brands.md`, facts in `docs/external-facts.md` §17–20) lists the
  decisions only Robert can make. His answers on 2026-10-09:
  - code changes approved, including the `brands/` move;
  - **ElevenLabs speech-to-text approved** for transcripts and captions of his footage;
  - voice: **his own recorded voice** (no clone, so no TikTok AI label for the voice);
  - language: any, per video (Romanian or English);
  - recording: phone, with or without an external mic;
  - **edits happen only in this pipeline** (no hand-off to an outside editor);
  - TikTok reference accounts: any good ones (we choose);
  - the acme.example palette comes later.

## Decision
- **Brands live in `brands/<brand>/`**: tokens.json, DESIGN.md, video.yaml, logo/*.svg, plus FONTS.md and
  REVIEW.md as for Acme.
  - The brief names its brand (`brand: <slug>`, required in the `Brief` schema; `lens validate` checks the folder
    exists).
  - `brands/{brand}/**` is an external input in `lens/stages.py`. C1, C3 and C8 read it; no stage writes it, so the
    write guard blocks brand edits during stage runs.
  - `create init <project> --brand <brand>` creates both folders.
  - Acme moved from `projects/acme-v2/brand/` to `brands/acme/`.
- **The logo exception of ADR 0019 now covers `brands/*/logo/`** (owner-supplied single-colour SVGs, no scripts or
  external references).
- **ElevenLabs is allowed for voice, sound effects (approved earlier, see PROGRESS.md) and speech-to-text on our
  own footage.**
  - The pipeline keeps a local fallback: WhisperX with local alignment, so a transcript can be made without credits.
  - Phase 1 corpus analysis stays local-only.
  - The API facts must be verified in ElevenLabs' docs and logged in `docs/external-facts.md` before the footage
    stage uses them.
- **No NLE export for now.** Cut proposals are approved in the pipeline (a human gate). OpenTimelineIO stays an
  option if that changes.

## CLAUDE.md lines (Robert applies; an agent may not edit CLAUDE.md)
Replace the ElevenLabs exception in "Hard rules":
```
- No pay-per-use APIs (no Gemini/OpenAI/Anthropic API keys). Visual annotation = Claude Code skills/subagents.
  Audio analysis = local tools/models only. Only exception: the ElevenLabs subscription in Phase 2 for voice
  (REST with-timestamps), sound effects, and speech-to-text on our own footage (Robert's voice; local
  WhisperX stays the fallback), ADR 0022. The ElevenLabs MCP is for interactive work only.
```
Replace the media rule's logo path, and add the brand rule after it:
```
- Never commit media or images (except tiny synthetic fixtures and a brand's own SVG logos under
  `brands/*/logo/`, ADR 0019/0022). Never commit secrets.
- Brands live in `brands/<brand>/` (shared hand-off, read-only for stages); a project's brief names its
  brand (`brand: <slug>`). Never copy brand values into templates or code.
```
In "Commands", replace `uv run create init|status <project>` with:
```
uv run create init <project> --brand <brand> | uv run create status <project> (Phase 2: projects/<project>/,
brands/<brand>/, stages C1-C13 in lens/stages.py) |
```
Optionally, under "Mission":
```
Before any new video: docs/learnings/readme.md and docs/research/vertical-footage-brands.md.
```

## Consequences
- A new brand is one folder and one review PR. Every project of that brand shares it.
- Changing a brand changes every project that uses it the next time C3 runs (tokens are regenerated per project).
- **M-B part 2 (done in the same branch):** C3 is no longer Acme-shaped.
  - `video.yaml` is validated (`BrandVideo`).
  - Font families are listed by role (heading and body are required, more are optional), with weights and fallback
    stacks per family.
  - The size set is named (`sizes: video1920`, so a vertical set can be added later).
  - Logo variants are semantic (`primary` required; `on_dark` and `mono` optional).
  - A brand can add glyphs it needs (`extra_glyphs`, e.g. Romanian) and set its own `accent_tint_alpha`.
  - Template UI copy comes from the brand's `strings` (templates hold none).
  - The brief has a `language` that sets `<html lang>`.
  - C3 fails when a colour role, type style or string that the templates need is missing.
  - The format is documented in `brands/README.md`.
- The new schema found two Acme contrast-pair descriptions that YAML had silently cut at a comma. They are now
  quoted.
- The footage stages (F1–F6) and vertical frame profiles are separate milestones.
