# 0004 — Spring model without depending on Remotion

- **Status:** accepted (2026-10-03: Acme / difrnt. is 3 people → free Remotion licence applies)
- **Date:** 2026-10-03
- **Milestone:** M4

## Context
Remotion is source-available: free for individuals, for-profit companies with ≤ 3 employees,
non-profits and evaluation; others need a Company License. Remotion 5.0 will count contractors.
Using the npm package (even only for golden tests) is use (external-facts §9). GSAP, including all
plugins, is free for commercial use. HyperFrames/GSAP is our primary target.

## Decision
Implement the damped-spring model from first principles (fit in ζ, ω₀ with mass = 1) and export a
`{mass, stiffness, damping}` config as numbers. Do not copy Remotion source.
- If difrnt. qualifies for the free licence: golden-test against the `remotion` npm package's `spring()`.
- If not: golden-test against an independent reference (closed-form solution of the oscillator) and
  skip Remotion entirely unless a Company License is bought.

**Resolved:** the team is 3, so the free licence applies and the golden test may use the `remotion` npm package.

## Consequences
Remotion stays a secondary, optional output. **Revisit** before a 4th person joins, or when Remotion 5.0
(which counts contractors) is adopted. The first-principles model means only the golden test would need
to change.
