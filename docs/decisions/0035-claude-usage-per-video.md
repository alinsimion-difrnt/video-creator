# 0035 — Claude usage per video: the main session directs, agents build

- **Status:** proposed (Robert, 2026-10-23: "you are using waaaay too many tokens for a video … optimize
  yourself without losing quality")
- **Date:** 2026-10-23
- **Milestone:** Phase 2, presenter reels (amends the process of ADR 0034; ADR 0032 unchanged)

## Context
Five video sessions from 2026-10-17, measured from their transcripts (result events: per-model usage, the
context of every request, every tool result). Opus prices worked back from the logged cost: $0.20/M cache
read, $8/M cache write, $20/M output.

| session | route | Opus $ | main requests | context start → peak | share of cache reads from the start context |
|---|---|---|---|---|---|
| x-ads | panel | 3.36 | 58 | 83k → 173k | 64% |
| facebook-algorithm | panel | 7.41 | 120 | 83k → 246k | 47% |
| google-ai-links | kit | 5.56 | 83 | 82k → 204k | 55% |
| ai-picks | kit | 7.15 | 138 | 84k → 234k | 52% |
| acme-reel (video, then framework, ADR, PR) | kit → panel | 25.01 | 322 | 84k → 478k | 29% |

Sonnet subagents cost $0.17-2.78 per session. The cost is the main session: requests × context.
- **~83k of context before any work**, re-read on every request: the harness, its tools, the account's
  connectors (12 MCP servers, ~370 tool names) and skills. The repository's share (CLAUDE.md, skill and agent
  descriptions) is about 5k.
- **Requests made one at a time:** 49 of 54 (x-ads) and 105 of 115 (facebook-algorithm) requests carried a
  single tool call. Polling a render with sleep/tail added 5-16 requests; a hung `create panel` (Playwright
  serialising the GSAP timeline `seek` returned) cost 19 requests and 3.2M cache reads.
- **Work that grows the main context:** reading the acme-reel reference panel (20-40k chars) and writing the
  new panel page (+14-19k tokens) in the main session; both rode along in ~90 later requests. Reading other
  projects as templates (briefs, posts, learnings: 20-40k chars per session), the full presenter playbook
  (21 KB), `--help` output, an ad-hoc Whisper run before `create transcribe`.
- **Work that `create` should do:** both panel sessions hand-built the same split cover after `create cover`
  put the title on Robert's face (facebook-algorithm: 14 requests and 3.35M cache reads to redo it); assets
  (GSAP, fonts, logos) and stills sheets were assembled by hand every time.
- **Mixing tasks:** acme-reel did framework code, an ADR and PR/CI checks at 400-478k context ($8 for that
  part alone). A request after 97 idle minutes rewrote a 152k context ($1.21, google-ai-links).
- A custom agent starts at 6-9k context; a general-purpose one at ~59k.

## Decision
- **The main session writes the beat sheet and the page**, from `create/kit/panel-starter.html` instead of the
  39 KB reference (page rules in `build-panel/page.md`), with the exact on-screen copy in the beat sheet. Images
  never enter it: a `lab-reviewer` gets the per-beat stills sheet (and the densest beat full size) before the
  full render, and `create review --at <settled times>` with a `reel-reviewer` checks the finished file. Fixes
  are targeted Edits, never a rewrite. A Sonnet `panel-builder` agent was tried and dropped (evidence below).
- **Code instead of hand work:** `create take` (provisional brief, ingest, transcript with the language
  detected, tokens, cuts, the phone page, his words as text; `--approve [--keep 0:41]` when his message already
  decides the cuts: no page and no mid-session wait, which costs a full context rewrite when he answers after
  the cache hour), `create panel --init` (starter page, base plan,
  GSAP, brand fonts and logos, extra families kept across reruns), `--stills` (one stamped sheet, the budget
  printed), `--assets` (sizes, light or dark, files that are not images), `create words --times`, `create cover
  --split --onto` (title inside the grid-crop safe area above the seam, written as frame 0), `create review
  --at`, `create status` without the unused rows. The renderer: `void seek(t)`, a missing asset fails the
  render, a page that would cover the captions is refused; the starter's typing and count-ups paint from the
  playhead (seek-safe).
- **Fewer, smaller requests** (CLAUDE.md "Claude usage", process-take): chain dependent commands, send
  independent calls together, renders in the background with no polling, exact commands in skills (no
  `--help`), ranges not whole files, no other projects as templates, one video per session (framework work in
  a fresh one, and late feedback too: section 5 of process-take), the playbook's sections 0-a in the main
  session and 0-c2, d1, f2 for the reel-planner.
- **Less fixed context:** `permissions.deny` on every tool a video never uses (measured: a fresh session's
  first request 90,501 -> 68,860 tokens, -24%, on every request and every cache write); agent-only skills
  leave every request (`disable-model-invocation`); self-contained
  builder and reviewer agents skip CLAUDE.md (`omitClaudeMd`); `lab-reviewer` reads the character-animation
  rules only for lab renders; the motion-builder reads only its sections of build-motion; the SessionStart
  hook replaces the cloud image's deprecated `UV_NATIVE_TLS` (a warning line in every `uv run` output).

## Evidence: two builder-agent trials on acme-reel (2026-10-23)
The director (Opus, this session) wrote a beat sheet with v2's devices; a Sonnet panel-builder agent built it
twice; stills at 12 settled times plus the hero and chat frames went to blind Opus judges.

| build | requests | output tokens | cache reads | cost (Sonnet, fitted) | blind judge |
|---|---|---|---|---|---|
| v2 (Opus, main session, 2026-10-17) | - | - | - | - | 6/10 vs trial 1 |
| trial 1, default effort | 22 | 139.6k | 2.69M | ~$2.48 | 7/10 vs v2 (legibility 8 vs 5) |
| trial 2, effort medium, updated skill | 18 | 132.5k | 1.54M | ~$2.23 | 7/10 vs trial 1's 6 (one judge) |

Caveats: v2 was built to its own direction, not this beat sheet, and Robert approved it; one script, so a
smoke test of the builder, not of directing a new video. Trial 2 changed the effort and the skill together:
the claim is that medium did no worse, at 18 requests instead of 22, not that it is better.

Why it was dropped: most of the builder's output is one step, the page (~25k tokens) plus ~65-75k of thinking,
which then stays in its context (it peaks near 180k). Opus in the main session wrote 30-36 KB pages in x-ads and
facebook-algorithm within 42k and 73k output tokens for the whole session (page write +14k and +19k context).
Netted per session, the builder made x-ads about 35% dearer and facebook-algorithm only ~22% cheaper; with the
page back in the main session (no reference read, stills reviewed by an agent) the same waste fixes come to
roughly -15% and -35% (estimates below).

## Consequences
- Cost (estimates from the measured components; not yet measured on a new video):

  | | x-ads ($3.54) | facebook-algorithm ($7.80) |
  |---|---|---|
  | waste removed: reference read, page carried, polling, start-phase steps, render hang, cover redo, stills loop in the main session | -$1.15 | -$4.15 |
  | page written by Opus in the main session from the starter (output, carried context, stills rounds via a lab-reviewer) | +$0.60 | +$1.30 |
  | net | about -15% | about -35% |

  The waste-free part of a session is the start context (~83k) times its requests; batching and agents cut
  the requests, the account's connectors are the part of the start context Robert can trim.
- Quality is guarded by the two fresh-eyes reviews and the code checks above, and the page is written by the
  model that wrote the panels Robert approved.
- Revisit after three panel videos: cost per video from the result events, and Robert's verdicts against
  acme-reel, x-ads and facebook-algorithm.
