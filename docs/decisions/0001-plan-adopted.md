# 0001 — Adopt BUILD_PLAN v2.2

- **Status:** accepted
- **Date:** 2026-10-03
- **Milestone:** M0

## Context
v2.1 was audited before implementation (docs/plan-audit.md) against itself, the v1 handoff
(docs/handoff-v1.md) and verified external facts (docs/external-facts.md). Robert decided:
one repo for research, understanding and creation; usage limits accepted for internal use;
ElevenLabs (subscription) for voice.

## Decision
BUILD_PLAN v2.2 is the source of truth. Phase 1 (`lens`, M0–M10) first; Phase 2 (`create`) is
planned in detail at gate G5. M4.5 (baseline audit of Acme v1 against absolute targets) runs
right after M2.

## Consequences
Early value from M4.5 before any annotation quota is spent. The plan file is edited in place;
later changes get their own ADR.
