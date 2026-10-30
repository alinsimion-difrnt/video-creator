# 0021 — Phase 2 (Create) plan adopted

- **Status:** accepted (Robert, G5, 2026-10-05)
- **Milestone:** G5

## Decision
- docs/phase2-plan.md is the Phase 2 plan. It has 12 stages, milestones P0–P6 and three human
  approvals (script, sketch sheet, motion).
- The first video is **Acme v2** on the v1 story. It must meet the v2 targets taken from the v1 grade
  (`reports/compare/acme-explainer-v1/`).
- The voice is picked after the P0 audition (ADR 0005 spike), from 3–4 voices in Robert's ElevenLabs
  library.
- The ElevenLabs key is read from the environment variable `ELEVENLABS_API_KEY`. It is never in chat,
  the repo or logs, and Pay As You Go stays off.
- Rendering uses HyperFrames in the container (external-facts 14), not GitHub Actions.

_Renumbered from 0018 (drafted on branch `claude/gifted-mayer-7839e3`, never merged); 0018 is the Phase 2 voice ADR._
