# 0019 — Brand assets in git, rendering on Robert's machine

- **Status:** accepted (Robert, 2026-10-06; closes G5); brand folder moved to `brands/<brand>/` by ADR 0022
- **Date:** 2026-10-06
- **Milestone:** Phase 2 prep

## Context
The Acme design hand-off (Claude Design, @acme/ui@0.1.0) arrived with tokens, rules, logo SVGs, two
woff2 font subsets and component PNGs (`projects/acme-v2/brand/REVIEW.md`). The repo rule says no media or
images in git, and R2 credentials are not set up. Phase 2 also needs Chrome + Node to render, and the
Actions minutes reset only on Nov 1.

## Decision
- **The brand's own SVG logos are committed** under `projects/<project>/brand/logo/` (~10 KB text each,
  single-colour paths, no scripts or external references). This is the only exception to "no images".
- **Fonts are not committed:** the video loads Inter and Space Grotesk from Google Fonts (OFL 1.1, full
  character sets; the shipped woff2 files are subsets missing ≈ ✓ →).
- **Reference PNGs stay out of git.** Templates are built from tokens, not traced from images.
- **Rendering (C12) runs on Robert's machine.** CI runs only the code checks; the render stage is local and
  its MP4 goes to R2 (or stays local until R2 is configured).

## Consequences
- `CLAUDE.md` names the logo exception.
- The render command must work on macOS (handoff lessons: no `timeout`, case-insensitive file names).
